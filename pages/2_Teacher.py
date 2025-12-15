import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

st.set_page_config(page_title="Teacher Panel", layout="centered")
st.title("👩‍🏫 Teacher Attendance Panel")

CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
SESSION_FILE = "session.json"

# ----------------------
# FILE CHECKS
# ----------------------
for file, label in [
    (CLASSES_FILE, "Classes"),
    (SUBJECTS_FILE, "Subjects"),
]:
    if not os.path.exists(file):
        st.error(f"❌ {label} file missing. Contact Admin.")
        st.stop()

# ----------------------
# LOAD CSVs
# ----------------------
classes = pd.read_csv(CLASSES_FILE)
subjects = pd.read_csv(SUBJECTS_FILE)

# Normalize columns
classes.columns = classes.columns.str.strip()
subjects.columns = subjects.columns.str.strip()

# Required columns
if not {"ClassID", "ClassName"}.issubset(classes.columns):
    st.error("❌ classes.csv has invalid structure.")
    st.stop()

if not {"SubjectID", "SubjectName", "ClassID"}.issubset(subjects.columns):
    st.error("❌ subjects.csv has invalid structure.")
    st.stop()

# Clean values
classes["ClassID"] = classes["ClassID"].astype(str).str.strip()
classes["ClassName"] = classes["ClassName"].astype(str).str.strip()

subjects["ClassID"] = subjects["ClassID"].astype(str).str.strip()
subjects["SubjectName"] = subjects["SubjectName"].astype(str).str.strip()
subjects["SubjectID"] = subjects["SubjectID"].astype(str).str.strip()

# ----------------------
# SELECT CLASS
# ----------------------
class_name = st.selectbox(
    "Select Class",
    classes["ClassName"].unique()
)

class_row = classes[classes["ClassName"] == class_name]

if class_row.empty:
    st.error("❌ Invalid class selected.")
    st.stop()

class_id = str(class_row.iloc[0]["ClassID"])

# ----------------------
# FILTER SUBJECTS
# ----------------------
filtered_subjects = subjects[subjects["ClassID"] == class_id]

if filtered_subjects.empty:
    st.error("❌ No subjects mapped to this class.")
    st.stop()

# ----------------------
# SELECT SUBJECT
# ----------------------
subject_name = st.selectbox(
    "Select Subject",
    filtered_subjects["SubjectName"].unique()
)

subject_row = filtered_subjects[
    filtered_subjects["SubjectName"] == subject_name
]

if subject_row.empty:
    st.error("❌ Subject not mapped correctly.")
    st.stop()

subject_id = str(subject_row.iloc[0]["SubjectID"])  # 🔥 FORCE STRING

# ----------------------
# SESSION CODE
# ----------------------
session_code = st.text_input(
    "Enter Session Code",
    help="Valid for 30 minutes"
).strip()

if not session_code:
    st.warning("Please enter a session code.")
    st.stop()

# ----------------------
# ACTIVATE SESSION
# ----------------------
if st.button("🚀 Activate Session"):

    session_data = {
        "session_code": str(session_code),
        "class_id": str(class_id),
        "subject_id": str(subject_id),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "created_at": datetime.now().isoformat()
    }

    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f, indent=2)

    st.success("✅ Session activated successfully!")
    st.info("📢 Share this session code with students")

    st.json(session_data)
