# Hemorrhage Detection & Report Generation System

An AI-powered medical imaging system for detecting brain hemorrhages in CT scans with automated report generation and real-time doctor notifications.

## Features

- **AI-Powered Detection**: Hybrid CNN (ResNet50 + 3D CNN) for accurate hemorrhage detection
- **Severity Scoring**: Continuous spread ratio (0-100%) indicating hemorrhage severity
- **Automated Reports**: PDF report generation with findings and CT images
- **Role-Based Access**: Separate dashboards for radiologists and doctors
- **Real-Time Alerts**: WebSocket notifications for severe cases (>70% severity)
- **CT Viewer**: Interactive slice-by-slice CT scan viewer with heatmap overlay

## Tech Stack

### Backend
- Python 3.10+
- FastAPI (REST API + WebSocket)
- PostgreSQL (Database)
- SQLAlchemy (ORM)
- TensorFlow/Keras (ML)
- ReportLab (PDF Generation)

### Frontend
- React 18
- Vite (Build Tool)
- Tailwind CSS (Styling)
- React Router (Navigation)
- Axios (HTTP Client)
- React Query (Data Fetching)

### ML Model
- Hybrid CNN Architecture
- ResNet50 (Transfer Learning)
- 3D CNN (Temporal Features)
- GradCAM (Interpretability)

## Project Structure

```
hemorrhage-detection-system/
├── backend/
│   ├── app/                 # FastAPI application
│   │   ├── api/            # API routes
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   └── ml/                  # Machine Learning
│       ├── models/         # Model architectures
│       ├── training/       # Training scripts
│       └── inference/      # Inference pipeline
├── frontend/
│   └── src/
│       ├── components/     # React components
│       ├── pages/          # Page components
│       ├── services/       # API services
│       └── context/        # React context
└── docker-compose.yml
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.10+ (for local backend development)
- CUDA-capable GPU (recommended for training)

### Using Docker (Recommended)

```bash
# Clone and navigate to project
cd hemorrhage-detection-system

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Training the Model

```bash
cd backend/ml
python -m training.train --data_path "path/to/Data" --epochs 50 --batch_size 16
```

## API Documentation

Once running, access the interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Workflow

1. **Radiologist** uploads CT scan with patient details
2. **AI System** analyzes scan, detects hemorrhage, calculates severity
3. **Report Generated** with findings, severity score, and CT images
4. **Radiologist** reviews and verifies the report
5. **Report Sent** to assigned doctor
6. **Doctor Notified** (immediate alert for severe cases >70%)
7. **Doctor Reviews** and takes appropriate action

## Severity Levels

| Range | Level | Action |
|-------|-------|--------|
| 0-30% | Mild | Standard review |
| 30-70% | Moderate | Priority review |
| 70-100% | Severe | **Immediate alert** |

## License

MIT License - See LICENSE file for details.
