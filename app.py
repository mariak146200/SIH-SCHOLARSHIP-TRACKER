"""
Flask Application Server for Scholarship Tracker
Handles REST API endpoints, ML predictions, server-side validations, and static/template routing.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import joblib
from flask import Flask, render_template, request, jsonify

from database import (
    init_db,
    get_applications,
    get_application_by_id,
    create_application,
    update_application,
    validate_application_payload
)

app = Flask(__name__)

# Ensure DB and ML model exist on startup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'scholarship_model.pkl')
ENCODER_PATH = os.path.join(BASE_DIR, 'model', 'encoder.pkl')
METRICS_PATH = os.path.join(BASE_DIR, 'model', 'model_metrics.pkl')

def ensure_model_exists():
    if not (os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH)):
        print("[App] ML Model artifacts not found. Training model now...")
        from model.train_model import train_and_save_model
        train_and_save_model()

@app.before_request
def startup_checks():
    # Lazy init on first request
    if not hasattr(app, '_db_initialized'):
        init_db()
        ensure_model_exists()
        app._db_initialized = True

@app.route('/')
def index():
    """Renders main dashboard."""
    return render_template('index.html')

@app.route('/applications', methods=['GET'])
def api_get_applications():
    """Fetches applications with search & filter support."""
    try:
        search = request.args.get('search', '')
        stage = request.args.get('stage', '')
        documents_status = request.args.get('documents_status', '')

        apps = get_applications(search=search, stage=stage, documents_status=documents_status)
        return jsonify({
            'status': 'success',
            'count': len(apps),
            'data': apps
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Failed to retrieve applications: {str(e)}"
        }), 500

@app.route('/applications/<int:app_id>', methods=['GET'])
def api_get_single_application(app_id):
    """Fetches single application by database ID."""
    try:
        record = get_application_by_id(app_id)
        if not record:
            return jsonify({
                'status': 'error',
                'message': f"Application with ID {app_id} not found"
            }), 404
        return jsonify({
            'status': 'success',
            'data': record
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/applications', methods=['POST'])
def api_create_application():
    """Creates a new application with server-side validation."""
    data = request.get_json() or {}

    is_valid, err_msg = validate_application_payload(data, is_update=False)
    if not is_valid:
        return jsonify({
            'status': 'error',
            'message': err_msg
        }), 400

    try:
        new_record = create_application(data)
        return jsonify({
            'status': 'success',
            'message': 'Application created successfully',
            'data': new_record
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({
            'status': 'error',
            'message': f"Application ID '{data.get('application_id')}' already exists."
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Server error: {str(e)}"
        }), 500

@app.route('/applications/<int:app_id>', methods=['PUT'])
def api_update_application(app_id):
    """Updates an existing application."""
    data = request.get_json() or {}

    is_valid, err_msg = validate_application_payload(data, is_update=True)
    if not is_valid:
        return jsonify({
            'status': 'error',
            'message': err_msg
        }), 400

    try:
        updated = update_application(app_id, data)
        if not updated:
            return jsonify({
                'status': 'error',
                'message': f"Application with ID {app_id} not found."
            }), 404

        return jsonify({
            'status': 'success',
            'message': 'Application updated successfully',
            'data': updated
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Server error: {str(e)}"
        }), 500

@app.route('/predict', methods=['POST'])
def api_predict_delay():
    """Predicts application delay likelihood using trained ML model."""
    data = request.get_json() or {}

    scheme = data.get('scheme')
    stage = data.get('stage')
    documents_status = data.get('documents_status')
    sanctioned_amount = data.get('sanctioned_amount')

    if not (scheme and stage and documents_status and sanctioned_amount is not None):
        return jsonify({
            'status': 'error',
            'message': 'Missing required prediction features (scheme, stage, documents_status, sanctioned_amount)'
        }), 400

    try:
        sanctioned_amount = float(sanctioned_amount)
        if sanctioned_amount < 0:
            return jsonify({
                'status': 'error',
                'message': 'Sanctioned amount cannot be negative'
            }), 400
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Sanctioned amount must be a numeric value'
        }), 400

    try:
        ensure_model_exists()
        clf = joblib.load(MODEL_PATH)
        preprocessor = joblib.load(ENCODER_PATH)

        # Prepare single row DataFrame
        input_df = pd.DataFrame([{
            'scheme': scheme,
            'stage': stage,
            'documents_status': documents_status,
            'sanctioned_amount': sanctioned_amount
        }])

        encoded_input = preprocessor.transform(input_df)
        pred_class = clf.predict(encoded_input)[0]
        probs = clf.predict_proba(encoded_input)[0]

        # Get confidence score (max probability)
        confidence = float(np.max(probs))
        confidence_pct = round(confidence * 100, 2)

        is_confident = confidence >= 0.60
        message = f"Predicted outcome: {pred_class} ({confidence_pct}% confidence)"
        if not is_confident:
            message = f"Prediction Not Confident ({confidence_pct}% confidence < 60% threshold)"

        return jsonify({
            'status': 'success',
            'prediction': pred_class,
            'confidence': confidence_pct,
            'is_confident': is_confident,
            'message': message
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Prediction engine error: {str(e)}"
        }), 500

@app.route('/api/model-info', methods=['GET'])
def api_model_info():
    """Returns model accuracy and confusion matrix."""
    try:
        ensure_model_exists()
        if os.path.exists(METRICS_PATH):
            metrics = joblib.load(METRICS_PATH)
            return jsonify({
                'status': 'success',
                'data': metrics
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Metrics not found'
            }), 444
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("[App] Starting SIH 2026 Scholarship Tracker Server...")
    init_db()
    ensure_model_exists()
    app.run(host='0.0.0.0', port=5000, debug=True)
