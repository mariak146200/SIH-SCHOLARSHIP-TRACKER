# SIH 2026: Student Scholarship Application and Disbursement Tracker

An end-to-end, production-ready Full Stack Web Application and Machine Learning solution built for the **Smart India Hackathon (SIH) 2026 Internal Practical Assessment**. 

The system enables scholarship administrative officers to monitor student scholarship applications across multiple processing workflow stages, track document verification statuses, manage disbursement pipelines, and leverage machine learning to proactively predict application delays.

---

## 📌 Problem Statement

Scholarship applications in educational institutions and state/national portals frequently experience bottlenecks and delays across multi-tier verification workflows (Institute Verification, District Verification, Sanctioning, and Disbursement). Administrative teams lack real-time visibility into application stage progression and risk scoring tools to identify applications that are likely to be stalled due to document issues, scheme-specific delays, or processing backlogs.

This tracker resolves this issue by providing:
1. **Real-time Tracking**: Centralized dashboard to view, search, and filter scholarship records.
2. **Predictive Delay Risk Analytics**: Machine Learning model (Random Forest Classifier) that scores delay risks based on workflow features.
3. **Automated Server Validation & Persistent Storage**: SQLite backend with strict data validation.

---

## ✨ Features

- 🔍 **Live Search & Multi-Criteria Filtering**: Filter by student name, application ID, processing stage, or document status without full page refresh.
- 🤖 **Machine Learning Delay Predictor**: Random Forest Classifier trained on historic workflow data to predict delay risks.
- ⚡ **Confidence Score Thresholding**: Displays explicit **"Prediction Not Confident"** alert whenever model prediction confidence falls below **60%**.
- 📊 **Interactive Model Metrics & Confusion Matrix**: Real-time visualization of model accuracy score and confusion matrix counts (TP, TN, FP, FN).
- 📝 **CRUD Application Management**: Modal forms to create new applications and update existing application statuses.
- 🛡️ **Strict Server-Side Validation**: Returns consistent JSON error messages `{"status": "error", "message": "..."}` with standard HTTP status codes.
- 🎨 **Responsive Corporate Blue UI**: Built using HTML5, Vanilla CSS3 (modern glassmorphism, responsive grid, status badges), and Vanilla JS.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python Flask |
| **Database** | SQLite3 (`scholarship.db`) |
| **Frontend** | HTML5, CSS3 (Vanilla), JavaScript (Vanilla) |
| **Machine Learning** | Python, Pandas, Scikit-learn, Joblib |
| **Data Format** | JSON REST APIs, CSV Dataset |

---

## 📁 Project Folder Structure

```text
Scholarship-Tracker/
│
├── app.py                  # Flask REST API server and routing
├── database.py             # SQLite schema, dataset seeder & CRUD methods
├── requirements.txt        # Python package dependencies
├── README.md               # Complete project documentation
├── scholarship.db          # Auto-generated SQLite database
│
├── dataset/
│   └── scholarship_data.csv  # 100 realistic records with edge cases
│
├── model/
│   ├── train_model.py      # ML model training & evaluation script
│   ├── scholarship_model.pkl# Serialized Scikit-learn Random Forest model
│   ├── encoder.pkl         # Serialized OneHotEncoder / preprocessor
│   └── model_metrics.pkl   # Serialized accuracy & confusion matrix metrics
│
├── templates/
│   └── index.html          # Responsive single-page dashboard UI
│
├── static/
│   ├── style.css           # Blue theme styling system & UI components
│   └── script.js            # Fetch API client, live search, modals & UI state
│
└── screenshots/            # Dashboard & ML predictor screenshots
```

---

## 📊 Dataset Description (`dataset/scholarship_data.csv`)

The dataset consists of **100 realistic scholarship application records** containing the following columns:

- `application_id`: Unique identifier (e.g., `SCH2026-001`)
- `student_id`: Student registration ID (e.g., `STU-1001`)
- `student_name`: Student full name
- `scheme`: Scholarship scheme (Post-Matric, National Merit, Pragati, Central Sector, State Pre-Matric)
- `applied_date`: Application submission date (YYYY-MM-DD)
- `documents_status`: Verification status (`Verified`, `Pending`, `Under Resubmission`, `Rejected`)
- `stage`: Current processing stage (`Application Submitted`, `Institute Verification`, `District Verification`, `Sanctioned`, `Disbursed`, `Rejected`)
- `sanctioned_amount`: Financial grant amount in INR
- `disbursed_date`: Disbursement completion date (if applicable)
- `outcome`: Target outcome (`Delayed`, `Disbursed`, `In Progress`, `Rejected`)

### Included Edge Cases:
1. **Missing Value**: Row `SCH2026-042` contains an empty `documents_status` field to test dataset cleaning.
2. **Similar Names**: Records `SCH2026-001` (`Aarav Sharma`) and `SCH2026-002` (`Arav Sharma`) test substring search precision.
3. **Incomplete Record**: Row `SCH2026-099` contains invalid scheme (`UNKNOWN_SCHEME`) and negative amount (`-100.0`) to test validation handling.

---

## 🤖 Machine Learning Approach

- **Model**: `RandomForestClassifier` (`n_estimators=100`, `random_state=42`)
- **Features Used**: `scheme`, `stage`, `documents_status`, `sanctioned_amount`
- **Features Excluded**: `outcome` (target leakage prevention), `disbursed_date`
- **Train/Test Split**: 80% Training / 20% Testing (`random_state=42`)
- **Confidence Logic**:
  - Probability score is calculated via `clf.predict_proba()`.
  - If `max_probability < 0.60`, the system triggers an alert: **"Prediction Not Confident"**.

---

## 📡 REST API Endpoints

### 1. Get Applications
- **Endpoint**: `GET /applications`
- **Query Params**: `search`, `stage`, `documents_status`
- **Response**:
  ```json
  {
    "status": "success",
    "count": 100,
    "data": [...]
  }
  ```

### 2. Create Application
- **Endpoint**: `POST /applications`
- **Body**:
  ```json
  {
    "application_id": "SCH2026-105",
    "student_id": "STU-1105",
    "student_name": "Rohan Kumar",
    "scheme": "Post-Matric Scholarship",
    "applied_date": "2026-07-26",
    "documents_status": "Pending",
    "stage": "Institute Verification",
    "sanctioned_amount": 25000.0,
    "outcome": "In Progress"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "status": "success",
    "message": "Application created successfully",
    "data": { ... }
  }
  ```

### 3. Update Application
- **Endpoint**: `PUT /applications/<id>`
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Application updated successfully",
    "data": { ... }
  }
  ```

### 4. Delay Risk Prediction API
- **Endpoint**: `POST /predict`
- **Body**:
  ```json
  {
    "scheme": "Post-Matric Scholarship",
    "stage": "Institute Verification",
    "documents_status": "Pending",
    "sanctioned_amount": 25000.0
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "prediction": "Delayed",
    "confidence": 88.0,
    "is_confident": true,
    "message": "Predicted outcome: Delayed (88.0% confidence)"
  }
  ```

### 5. Validation Error Response Example (HTTP 400)
```json
{
  "status": "error",
  "message": "Student Name is required"
}
```

---

## ⚡ Installation & Setup Instructions

### Prerequisites
- Python 3.8 or higher installed on system.

### Step 1: Clone or Navigate to Project Directory
```bash
cd Scholarship-Tracker
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Train Machine Learning Model (Optional)
*Note: The Flask application automatically trains the model on first launch if model files are missing.*
```bash
python model/train_model.py
```

### Step 4: Run Flask Application
```bash
python app.py
```

### Step 5: Access Web Application
Open your web browser and navigate to:
```text
http://127.0.0.1:5000/
```

---

## 📷 Screenshots Section

*(Place your application screenshots in the `screenshots/` directory)*

- `screenshots/dashboard.png`: Main dashboard overview showing KPI cards and application table.
- `screenshots/search_filter.png`: Live search and stage filter in action.
- `screenshots/ml_predictor.png`: ML Delay Risk prediction modal with confidence scoring.
- `screenshots/add_application.png`: Add new application modal form with validation error handling.

---

## 🚀 Future Enhancements

1. **SMS/Email Notifications**: Automated alerts to students when document resubmission is required.
2. **Role-Based Access Control (RBAC)**: Distinct permissions for Students, Institute Verifiers, and State Officers.
3. **Advanced ML Ensemble**: Gradient Boosting (XGBoost / LightGBM) models for enhanced accuracy.
4. **Export Reports**: PDF and Excel report generation for sanctioned scholarship batches.
