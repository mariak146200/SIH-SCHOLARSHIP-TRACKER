"""
Verification and Test Suite for Scholarship Tracker APIs
Runs Flask test client to verify all REST endpoints, validations, DB operations, and ML predictions.
"""

import os
import unittest
import json
from app import app
from database import init_db

class ScholarshipTrackerTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_db()

    def test_01_get_applications(self):
        """Test GET /applications with search and filter."""
        response = self.client.get('/applications')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertGreater(data['count'], 0)

        # Test Search (e.g. "Aarav")
        search_res = self.client.get('/applications?search=Aarav')
        self.assertEqual(search_res.status_code, 200)
        search_data = json.loads(search_res.data)
        self.assertTrue(any('Aarav' in row['student_name'] for row in search_data['data']))

        # Test Filter (stage="Disbursed")
        filter_res = self.client.get('/applications?stage=Disbursed')
        self.assertEqual(filter_res.status_code, 200)
        filter_data = json.loads(filter_res.data)
        self.assertTrue(all(row['stage'] == 'Disbursed' for row in filter_data['data']))

    def test_02_create_application_valid_and_invalid(self):
        """Test POST /applications validation and creation."""
        # Invalid payload: Missing student_name
        invalid_payload = {
            "application_id": "SCH2026-TEST999",
            "scheme": "Post-Matric Scholarship",
            "stage": "Application Submitted",
            "documents_status": "Pending",
            "sanctioned_amount": 25000.0
        }
        res_invalid = self.client.post('/applications', json=invalid_payload)
        self.assertEqual(res_invalid.status_code, 400)
        err_data = json.loads(res_invalid.data)
        self.assertEqual(err_data['status'], 'error')
        self.assertIn('Student Name is required', err_data['message'])

        # Invalid payload: Negative sanctioned_amount
        invalid_amt = {
            "application_id": "SCH2026-TEST998",
            "student_name": "Test Student",
            "scheme": "Post-Matric Scholarship",
            "stage": "Application Submitted",
            "documents_status": "Pending",
            "sanctioned_amount": -500.0
        }
        res_amt = self.client.post('/applications', json=invalid_amt)
        self.assertEqual(res_amt.status_code, 400)
        self.assertIn('cannot be negative', json.loads(res_amt.data)['message'])

        # Valid Payload
        valid_payload = {
            "application_id": "SCH2026-TEST100",
            "student_id": "STU-TEST100",
            "student_name": "Test Unit Student",
            "scheme": "Post-Matric Scholarship",
            "applied_date": "2026-07-26",
            "stage": "Application Submitted",
            "documents_status": "Verified",
            "sanctioned_amount": 35000.0,
            "outcome": "In Progress"
        }
        res_valid = self.client.post('/applications', json=valid_payload)
        self.assertEqual(res_valid.status_code, 201)
        succ_data = json.loads(res_valid.data)
        self.assertEqual(succ_data['status'], 'success')
        self.assertEqual(succ_data['data']['application_id'], 'SCH2026-TEST100')

    def test_03_update_application(self):
        """Test PUT /applications/<id>."""
        # Update existing record
        update_payload = {
            "student_name": "Test Unit Student Updated",
            "stage": "Sanctioned",
            "sanctioned_amount": 40000.0
        }
        res = self.client.put('/applications/1', json=update_payload)
        self.assertEqual(response_code := res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['stage'], 'Sanctioned')

    def test_04_predict_api(self):
        """Test POST /predict endpoint."""
        pred_payload = {
            "scheme": "Post-Matric Scholarship",
            "stage": "Institute Verification",
            "documents_status": "Pending",
            "sanctioned_amount": 25000.0
        }
        res = self.client.post('/predict', json=pred_payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('prediction', data)
        self.assertIn('confidence', data)

    def test_05_model_info_api(self):
        """Test GET /api/model-info."""
        res = self.client.get('/api/model-info')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('accuracy', data['data'])
        self.assertIn('confusion_matrix', data['data'])

if __name__ == '__main__':
    unittest.main()
