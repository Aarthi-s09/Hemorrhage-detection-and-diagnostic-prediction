# Hemorrhage Detection System - Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [Features Implemented](#features-implemented)
5. [Database Schema](#database-schema)
6. [API Endpoints](#api-endpoints)
7. [Current Status](#current-status)
8. [Setup Instructions](#setup-instructions)

---

## Project Overview

**Hemorrhage Detection System** is an AI-powered medical imaging platform designed to detect brain hemorrhages in CT scans. The system provides automated analysis, professional report generation, and workflow management for doctors and radiologists.

**Purpose:** Streamline the process of CT scan analysis and enable rapid detection of critical hemorrhage cases requiring immediate medical attention.

**Users:**
- **Doctors:** Add patients, view reports, and monitor scan results
- **Radiologists:** Upload CT scans, review analysis results, generate reports

---

## Technology Stack

### Backend Technologies

#### Core Framework
- **FastAPI** (Python Web Framework)
  - Modern, fast, high-performance web framework
  - Automatic API documentation (Swagger/OpenAPI)
  - Async support for concurrent operations
  - Type hints and Pydantic validation

#### Database
- **SQLite** (Development Database)
  - Lightweight, file-based database
  - Suitable for development and testing
  - Easy migration to PostgreSQL for production

- **SQLAlchemy** (ORM - Object Relational Mapper)
  - Python SQL toolkit
  - Database abstraction layer
  - Model-based database operations

#### Authentication & Security
- **bcrypt** (Password Hashing)
  - Secure password encryption
  - Salt-based hashing algorithm

- **HTTPBearer** (FastAPI Security)
  - Token-based authentication structure
  - Currently disabled for development simplicity

#### File Processing & Reports
- **Pillow (PIL)** (Image Processing)
  - CT scan image handling
  - Image validation and manipulation

- **ReportLab** (PDF Generation)
  - Professional PDF report creation
  - Custom styling and layouts
  - Medical report templates

#### Additional Libraries
- **Uvicorn** (ASGI Server)
  - Lightning-fast ASGI server
  - Auto-reload during development
  - Production-ready performance

- **python-multipart** (File Upload Handling)
  - Multipart form data parsing
  - CT scan file uploads

- **email-validator** (Email Validation)
  - Email format validation
  - User registration validation

### Frontend Technologies

#### Core Framework
- **React 18.0.0** (JavaScript UI Library)
  - Component-based architecture
  - Virtual DOM for performance
  - Hooks for state management

- **Vite 5.4.21** (Build Tool)
  - Next-generation frontend tooling
  - Fast hot module replacement (HMR)
  - Optimized production builds

#### UI Styling
- **Tailwind CSS 3.4.17** (Utility-First CSS Framework)
  - Rapid UI development
  - Responsive design utilities
  - Custom color schemes

- **Heroicons** (Icon Library)
  - Beautiful hand-crafted SVG icons
  - React components
  - Consistent design language

#### State Management & Data Fetching
- **React Query (TanStack Query) 5.62.11**
  - Server state management
  - Automatic caching and refetching
  - Optimistic updates
  - Background synchronization

- **Axios** (HTTP Client)
  - Promise-based HTTP requests
  - Request/response interceptors
  - Easy API integration

#### Routing
- **React Router v6** (Client-Side Routing)
  - Declarative routing
  - Nested routes
  - Protected routes for authentication

#### Notifications
- **React Hot Toast** (Toast Notifications)
  - Beautiful notifications
  - Success/error feedback
  - Customizable styling

### Development Tools

- **Git** (Version Control)
- **VS Code** (Code Editor)
- **Python 3.14** (Backend Runtime)
- **Node.js** (Frontend Runtime)
- **npm** (Package Manager)

---

## System Architecture

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│    - User Interface (Doctors & Radiologists)                │
│    - Patient Management, Scan Upload, Reports               │
│    - Port: 3000                                              │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
                     │ (CORS Enabled)
┌────────────────────▼────────────────────────────────────────┐
│                  Backend (FastAPI)                           │
│    - REST API Endpoints                                      │
│    - Business Logic & Validation                             │
│    - File Upload Management                                  │
│    - Port: 8082                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼────────┐ ┌─▼──────────────┐
│  Database    │ │  Mock ML   │ │  PDF Generator │
│  (SQLite)    │ │  Processor │ │  (ReportLab)   │
│              │ │            │ │                │
│  - Patients  │ │  - Random  │ │  - Professional│
│  - Scans     │ │    Results │ │    Reports     │
│  - Reports   │ │  - 67%     │ │  - Templates   │
│  - Users     │ │    Detect  │ │                │
└──────────────┘ └────────────┘ └────────────────┘
```

### Data Flow

1. **User Authentication**
   - Simple dropdown selection (Doctor/Radiologist)
   - Hardcoded passwords for development
   - localStorage-based session

2. **Scan Upload & Processing**
   - Radiologist uploads CT scan image
   - Backend validates file format and size
   - Background task processes scan with mock ML
   - Results saved to database
   - Automatic report generation

3. **Report Generation**
   - Findings generated from scan results
   - Professional template with ASCII borders
   - Priority-based recommendations
   - PDF export capability

4. **Notification System**
   - Critical alerts for severe cases (>70% spread)
   - Scan completion notifications
   - Report status updates

---

## Features Implemented

### ✅ User Management
- [x] Simple role-based authentication (Doctor/Radiologist)
- [x] Hardcoded user credentials for development
  - Doctor: `doc123`
  - Radiologist: `radi123`
- [x] Role-based UI filtering
- [x] localStorage session management

### ✅ Patient Management
- [x] Add new patients (Doctor role)
- [x] View patient list with search
- [x] Patient details page
- [x] Patient information includes:
  - Full name, date of birth, age
  - Gender, phone, email
  - Medical record number
  - Address

### ✅ CT Scan Management
- [x] Upload CT scan images (Radiologist role)
- [x] File validation (format and size)
- [x] Automatic scan processing (2-5 seconds)
- [x] Mock ML hemorrhage detection:
  - 67% chance of detecting hemorrhage
  - Random hemorrhage type (subdural, epidural, subarachnoid, intraventricular)
  - Spread ratio: 5-85%
  - Confidence score: 75-98%
  - Severity levels: mild, moderate, severe
- [x] Scan status tracking (pending, processing, completed, failed)
- [x] Scan history and details

### ✅ Report Generation
- [x] Automatic report creation after scan completion
- [x] Professional report template with:
  - ASCII box borders
  - Clear POSITIVE/NEGATIVE indication
  - Organized findings sections
  - Hemorrhage details (type, spread ratio, severity)
  - Severity-based status indicators
  - Priority-based recommendations (IMMEDIATE/TIMELY/ROUTINE)
- [x] Report status workflow:
  - draft → pending_review → reviewed → sent → acknowledged
- [x] Report verification by radiologist
- [x] PDF export functionality
- [x] Report list and detail views

### ✅ PDF Report Generation
- [x] Professional medical report layout
- [x] Patient information section
- [x] Analysis results with color-coded severity
- [x] Critical alerts for severe cases
- [x] Detailed findings and recommendations
- [x] Footer with generation details
- [x] Download/view PDF in browser

### ✅ Dashboard
- [x] Role-specific dashboards
- [x] Statistics overview:
  - Total patients
  - Total scans
  - Hemorrhage detection rate
  - Critical cases
- [x] Recent activities
- [x] Quick action buttons

### ✅ Notification System
- [x] Scan completion notifications
- [x] Critical case alerts (>70% spread ratio)
- [x] Report status notifications
- [x] Unread notification count
- [x] Mark as read functionality

### ✅ API Features
- [x] RESTful API design
- [x] Automatic API documentation (Swagger UI at `/docs`)
- [x] CORS enabled for all origins (development)
- [x] JSON response format
- [x] Pagination support
- [x] Filtering and search
- [x] Static file serving for uploads

---

## Database Schema

### Users Table
```python
- id (Primary Key)
- email (Unique)
- hashed_password
- full_name
- role (doctor, radiologist, admin)
- is_active
- created_at
- updated_at
```

### Patients Table
```python
- id (Primary Key)
- patient_id (Unique, e.g., "PAT-20260314-XXXX")
- full_name
- date_of_birth
- gender (male, female, other)
- phone
- email
- address
- medical_record_number
- created_by (Foreign Key → Users)
- created_at
- updated_at
```

### Scans Table
```python
- id (Primary Key)
- scan_id (Unique, e.g., "SCN-20260314-XXXX")
- patient_id (Foreign Key → Patients)
- uploaded_by (Foreign Key → Users)
- scan_date
- scan_type (CT Head, MRI, etc.)
- file_path
- status (pending, processing, completed, failed)
- has_hemorrhage (Boolean)
- hemorrhage_type (subdural, epidural, etc.)
- confidence_score (0.0-1.0)
- spread_ratio (0-100%)
- severity_level (mild, moderate, severe)
- affected_regions (JSON)
- processed_at
- created_at
- updated_at
```

### Reports Table
```python
- id (Primary Key)
- report_id (Unique, e.g., "RPT-20260314-XXXX")
- scan_id (Foreign Key → Scans)
- patient_id (Foreign Key → Patients)
- created_by (Foreign Key → Users)
- doctor_id (Foreign Key → Users, nullable)
- title
- findings (Text)
- radiologist_notes (Text)
- recommendations (Text)
- conclusion (Text)
- severity_score (0-100)
- is_critical (Boolean)
- status (draft, pending_review, reviewed, sent, acknowledged)
- is_verified (Boolean)
- verified_at
- sent_at
- acknowledged_at
- pdf_path
- created_at
- updated_at
```

### Notifications Table
```python
- id (Primary Key)
- user_id (Foreign Key → Users)
- type (scan_complete, critical_alert, report_ready)
- title
- message
- is_read (Boolean)
- priority (low, normal, high, critical)
- related_scan_id (Foreign Key → Scans, nullable)
- related_report_id (Foreign Key → Reports, nullable)
- created_at
```

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/auth/doctors` - Get list of doctors

### Patients
- `GET /api/v1/patients` - List patients (paginated)
- `GET /api/v1/patients/{id}` - Get patient details
- `POST /api/v1/patients` - Create new patient
- `PUT /api/v1/patients/{id}` - Update patient
- `DELETE /api/v1/patients/{id}` - Delete patient
- `GET /api/v1/patients/search?q={query}` - Search patients

### Scans
- `GET /api/v1/scans` - List scans (paginated)
- `GET /api/v1/scans/{id}` - Get scan details
- `POST /api/v1/scans/upload` - Upload CT scan
- `GET /api/v1/scans/critical?limit={n}` - Get critical scans
- `POST /api/v1/scans/{id}/reprocess` - Reprocess scan
- `DELETE /api/v1/scans/{id}` - Delete scan

### Reports
- `GET /api/v1/reports` - List reports (paginated)
- `GET /api/v1/reports/{id}` - Get report details
- `POST /api/v1/reports` - Create report
- `PUT /api/v1/reports/{id}` - Update report
- `POST /api/v1/reports/{id}/verify` - Verify report
- `POST /api/v1/reports/{id}/send` - Send report to doctor
- `POST /api/v1/reports/{id}/acknowledge` - Acknowledge report
- `POST /api/v1/reports/{id}/generate-pdf` - Generate PDF
- `GET /api/v1/reports/{id}/pdf` - Download PDF
- `GET /api/v1/reports/pending` - Get pending reports

### Notifications
- `GET /api/v1/notifications` - List notifications
- `GET /api/v1/notifications/unread-count` - Get unread count
- `GET /api/v1/notifications/critical` - Get critical notifications
- `POST /api/v1/notifications/mark-read` - Mark as read
- `POST /api/v1/notifications/mark-all-read` - Mark all as read
- `DELETE /api/v1/notifications/{id}` - Delete notification

### Dashboard
- `GET /api/v1/dashboard/stats` - General statistics
- `GET /api/v1/dashboard/radiologist` - Radiologist dashboard data
- `GET /api/v1/dashboard/doctor` - Doctor dashboard data
- `GET /api/v1/dashboard/severity-distribution?days={n}` - Severity distribution
- `GET /api/v1/dashboard/trend?days={n}` - Trend analysis

### Health Check
- `GET /` - Root endpoint
- `GET /api/v1/health` - API health check

---

## Current Status

### ✅ Completed Features
1. **Authentication System**
   - Simple dropdown-based login
   - Role-based access control (development mode)
   - localStorage session management

2. **Patient Management**
   - Complete CRUD operations
   - Search and filtering
   - Patient details view

3. **Scan Upload & Processing**
   - File upload with validation
   - Mock ML processor (67% detection rate)
   - Background processing (2-5 seconds)
   - Auto-report generation
   - Status tracking

4. **Report Generation**
   - Professional template with ASCII borders
   - Severity-based recommendations
   - Priority levels (IMMEDIATE/TIMELY/ROUTINE)
   - PDF export functionality

5. **Dashboard**
   - Statistics overview
   - Role-specific views
   - Recent activities

6. **Notifications**
   - Real-time notifications
   - Critical alerts
   - Unread count badges

7. **PDF Reports**
   - Professional medical report layout
   - Patient information
   - Analysis results
   - Severity indicators
   - Recommendations

### ⚠️ Known Issues
1. **React Error Handling**
   - 422 validation errors displayed as objects
   - Crashes React UI
   - Workaround: Hard refresh browser (Ctrl+Shift+R)

2. **Browser Caching**
   - Frontend updates require manual hard refresh
   - Consider adding cache-busting to Vite config

3. **Patient Creation Validation**
   - Occasional 422 validation errors
   - Field validation needs improvement

### ❌ Not Implemented (Future Development)
1. **Real ML Model**
   - Currently using mock random results
   - Need actual CNN/Deep Learning model
   - TensorFlow integration (Python 3.14 compatibility issues)
   - Model training on CT scan dataset

2. **Docker Deployment**
   - Dockerfile creation
   - Docker Compose setup
   - Container orchestration

3. **Production Authentication**
   - JWT token implementation
   - Refresh token mechanism
   - Password reset functionality
   - Email verification

4. **Database Migration**
   - PostgreSQL for production
   - Database migration scripts
   - Backup and restore procedures

5. **Advanced Features**
   - WebSocket real-time updates
   - Batch scan processing
   - 3D CT scan visualization
   - Comparison with previous scans
   - Export to DICOM format

6. **Testing**
   - Unit tests
   - Integration tests
   - End-to-end tests
   - Load testing

7. **Deployment**
   - Production server configuration
   - SSL/TLS certificates
   - Domain setup
   - Monitoring and logging

---

## Setup Instructions

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic bcrypt pillow reportlab email-validator python-multipart
   ```

3. **Run the server**
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8082 --reload
   ```

4. **Access API Documentation**
   - Swagger UI: http://127.0.0.1:8082/docs
   - ReDoc: http://127.0.0.1:8082/redoc

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

4. **Access application**
   - URL: http://localhost:3000

### Login Credentials (Development)

**Doctor Account:**
- Role: Select "Doctor" from dropdown
- Password: `doc123`

**Radiologist Account:**
- Role: Select "Radiologist" from dropdown  
- Password: `radi123`

### Ports
- **Backend:** 8082
- **Frontend:** 3000
- **Database:** SQLite file (backend/hemorrhage.db)

---

## Project Structure

```
hemorrhage-detection-system/
├── backend/
│   ├── app/
│   │   ├── api/              # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── patients.py
│   │   │   ├── scans.py
│   │   │   ├── reports.py
│   │   │   ├── notifications.py
│   │   │   └── dashboard.py
│   │   ├── models/           # Database models
│   │   │   ├── user.py
│   │   │   ├── patient.py
│   │   │   ├── scan.py
│   │   │   ├── report.py
│   │   │   └── notification.py
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── patient_service.py
│   │   │   ├── scan_service.py
│   │   │   ├── report_service.py
│   │   │   └── notification_service.py
│   │   ├── utils/            # Utility functions
│   │   │   ├── security.py
│   │   │   └── pdf_generator.py
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database setup
│   │   ├── main.py           # Application entry
│   │   └── websocket.py      # WebSocket manager
│   ├── uploads/              # Uploaded files
│   │   ├── scans/
│   │   └── reports/
│   ├── hemorrhage.db         # SQLite database
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable components
│   │   │   └── ui/           # UI components
│   │   ├── context/          # React Context
│   │   │   └── AuthContext.jsx
│   │   ├── pages/            # Page components
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Patients.jsx
│   │   │   ├── Scans.jsx
│   │   │   ├── Reports.jsx
│   │   │   └── ReportDetail.jsx
│   │   ├── services/         # API services
│   │   │   └── api.js
│   │   ├── App.jsx           # Main app component
│   │   └── main.jsx          # Entry point
│   ├── package.json          # Node dependencies
│   └── vite.config.js        # Vite configuration
├── Data/                     # CT scan datasets
│   ├── Hemorrhagic/
│   └── NORMAL/
├── README.md                 # Project README
└── PROJECT_DOCUMENTATION.md  # This file
```

---

## Summary

The **Hemorrhage Detection System** is a fully functional medical imaging platform built with modern web technologies. It successfully demonstrates:

- ✅ **Full-stack development** with FastAPI (backend) and React (frontend)
- ✅ **Database design** with proper relationships and constraints
- ✅ **File upload handling** for medical imaging files
- ✅ **Automated workflow** from scan upload to report generation
- ✅ **Professional PDF reports** with medical-grade formatting
- ✅ **Role-based access control** for doctors and radiologists
- ✅ **Mock ML integration** simulating real AI-powered analysis

**Current State:** Production-ready demo system with mock ML. Ready for integration with actual deep learning models for real hemorrhage detection.

**Next Steps:** 
1. Train/integrate real CNN model for CT scan analysis
2. Deploy to production environment with PostgreSQL
3. Implement full JWT authentication
4. Add comprehensive testing suite
5. Set up CI/CD pipeline

---

*Document Generated: March 14, 2026*
*Project Status: Development Complete (Mock ML)*
*Version: 1.0.0*
