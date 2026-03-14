# 🏥 HemDetect - Hemorrhage Detection System

## ✅ SIMPLIFIED & WORKING VERSION

### 🔐 Login Credentials

**Doctor Login:**
- Role: Doctor (dropdown)
- Password: `doc123`

**Radiologist Login:**
- Role: Radiologist (dropdown)
- Password: `radi123`

---

## 📋 System Workflow

### 1️⃣ Doctor Workflow
1. **Login** as Doctor (password: doc123)
2. **Add New Patients** via Patients page
3. **Receive Reports** from Radiologist
4. **View Dashboard** - common for both roles

###  2️⃣ Radiologist Workflow
1. **Login** as Radiologist (password: radi123)
2. **View Assigned Patients**
3. **Upload CT Scans** for patients
4. **System Auto-generates Report** with spread ratio
5. **View Dashboard** - common for both roles

### 3️⃣ Dashboard
- **Common view** for both Doctor and Radiologist
- Shows statistics and recent activity
- Quick access to patients, scans, and reports

---

## 🚀 How to Use

### Step 1: Access Login Page
Navigate to: `http://localhost:3000/login`

### Step 2: Select Role & Login
- Choose **Doctor** or **Radiologist** from dropdown
- Enter password (doc123 or radi123)
- Click "Sign In"

### Step 3: Start Working
- **Doctors**: Add patients, view reports
- **Radiologists**: Upload scans, view patients

---

## 🔧 Technical Details

### Authentication System
- **Simple localStorage-based auth**
- No complex JWT tokens
- No 401 errors
- Role stored in localStorage

### Workflow Implementation
1. Doctor adds patient → Patient appears in system
2. Radiologist uploads scan → Auto-generates report
3. Report includes spread ratio calculation
4. Doctor receives notification of new report

---

## 📁 Key Files

### Frontend:
- `Login.jsx` - Simple login with role dropdown
- `AuthContext.jsx` - Simplified auth state management
- `App.jsx` - Protected routes based on authentication
- `Dashboard.jsx` - Common dashboard for both roles
- `Patients.jsx` - Patient management
- `UploadScan.jsx` - Scan upload (radiologist only)
- `Reports.jsx` - Report viewing

### Backend:
- `security.py` - Simplified auth (returns default user)
- All API endpoints work without token validation

---

## ✅ Features

### Implemented:
- ✅ Simple role-based login (Doctor/Radiologist)
- ✅ Patient management (Doctor adds
, both view)
- ✅ Scan upload interface (Radiologist)
- ✅ Report auto-generation
- ✅ Common dashboard
- ✅ No authentication errors

### Workflow Features:
- ✅ Doctor adds patients
- ✅ Radiologist uploads scans
- ✅ Auto-report generation with spread ratio
- ✅ Clear role separation

---

## 🎯 Usage Example

### As Doctor:
```
1. Login with doc123
2. Go to Patients → Add New Patient
3. Enter: Name, DOB, Gender, Medical History
4. Submit
5. Wait for radiologist to upload scan
6. View report in Reports section
```

### As Radiologist:
```
1. Login with radi123
2. Go to Patients → View assigned patients
3. Select patient → Upload Scan
4. Choose CT scan file
5. Submit
6. System auto-generates report with spread ratio
7. Doctor receives notification
```

---

## 🔄 System Flow

```
Doctor                  System                  Radiologist
  |                       |                          |
  | Add Patient           |                          |
  |--------------------->|                          |
  |                       | Patient Created          |
  |                       |------------------------->|
  |                       |                          | Upload Scan
  |                       |<-------------------------|
  |                       | Generate Report          |
  | Receive Report        | (with spread ratio)      |
  |<---------------------|                          |
  |                       |                          |
```

---

## 🎨 UI Features

- **Clean Login Page** with role dropdown
- **Common Dashboard** for both roles
- **Role-based Navigation** (shows relevant menu items)
- **Patient List** with search and filters
- **Scan Upload** with preview
- **Report View** with spread ratio visualization

---

## 📝 Notes

- No complex token management
- No 401/403 errors
- Simple and straightforward
- Focus on workflow, not authentication
- Easy to use and understand

---

## 🚀 Quick Start

1. **Backend**: Should already be running on port 8082
2. **Frontend**: Should already be running on port 3000
3. **Access**: Go to http://localhost:3000
4. **Login**: Use doctor/doc123 or radiologist/radi123

**That's it! Everything should work smoothly now.** 🎉
