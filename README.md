# 🧑‍💻 Online Attendance System

This is a **dynamic online attendance system** built with **Python and Streamlit**, designed for small institutes or colleges.  
It allows **Admin, Teacher, and Students** to manage attendance easily.

---

## 📂 Folder / File Structure

attendance-system/
├── app.py # Student Attendance Page
├── pages/
│ ├── 1_Admin.py # Admin Panel (manage students, classes, subjects)
│ └── 2_Teacher.py # Teacher Attendance Control
├── students.xlsx # Student data (Roll, Name, Enrollment, ClassID)
├── classes.csv # Classes data (ClassID, ClassName)
├── subjects.csv # Subjects data (SubjectID, SubjectName, ClassID)
├── attendance.csv # Attendance records
├── session.json # Current active session info
└── README.md


---

## 🛠️ Features

### Admin Panel (`1_Admin.py`)
- Add / Edit / Delete Students
- Add / Edit / Delete Classes
- Add / Edit / Delete Subjects
- Download attendance CSV
- Password-protected for security

### Teacher Panel (`2_Teacher.py`)
- Select Class & Subject
- Generate Session Code (valid 30 minutes)
- Students can mark attendance only for that class & subject

### Student Page (`app.py`)
- Enter session code
- Select Roll Number (auto-filled for their class)
- Auto-fill Name & Enrollment Number
- Prevent duplicate attendance
- Session code expires after 30 minutes

---

## ⚡ Daily Usage

1. **Admin**: Add students, classes, and subjects (if new)
2. **Teacher**: Select class + subject → generate session code
3. **Students**: Enter session code → mark attendance
4. **Admin**: Download attendance CSV anytime

---

## 📦 Dependencies

- Python 3.8+  
- Streamlit  
- pandas  
- openpyxl  

Install dependencies:

```bash
pip install streamlit pandas openpyxl
