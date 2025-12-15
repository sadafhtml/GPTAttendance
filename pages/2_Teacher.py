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
# BASIC FILE CHECKS
# ----------------------
for file, name in [
    (CLASSES_FILE, "Classes"),
    (SUBJECTS_FILE, "Subjects"),
]:
    if not os.path.exists(file):
        st.error(f"❌ {name} file missing. Contact Admin.")
        st.stop()

# ----------------------
# LOAD DATA
# ----------------------
classes = pd.read_csv(CLASSES_FILE)
subjects = pd.read_csv(SUBJECTS_FILE)

# Clean column names
classes.columns = classes.columns.str.strip()
subjects.columns = subjects.columns.str.strip()

# Required columns check
required_class_cols = {"ClassID", "ClassName"}
required_subject_cols = {"SubjectID", "SubjectName", "ClassID"}

if not required_class_cols.issubset(classes.columns):
    st.error("❌ classes.csv has invalid columns.")
    st.stop()

if not required_subject_cols.issubset(subjects.columns):
    st.error("❌ subjects.csv has invalid columns.")
    st.stop()

# ----------------------
# CLEAN SUBJECT DATA (CRITICAL)
# ----------------------
subjects["SubjectName"] = subjects["SubjectName"].astype(str).str.strip()
subjects["ClassID"] = subjects["ClassID"].astype(str).str.strip()

classes["ClassID"] = classes["ClassID"].astype(str).str.strip()
classes["ClassName"] = classes["ClassName"].astype(str).str.strip()

# ----------------------
# SELECT CLASS
# ----------------------
class_name = st.selectbox(
    "Select Class",
    classes["ClassName"].unique()
)

class_row = classes[classes["ClassName"] == class_name]

if class_row.empty:
    st.error("❌ Invalid class selection.")
    st.stop()

class_id = class_row.iloc[0]["ClassID"]

# ----------------------
# FILTER SUBJECTS BY CLASS
# ----------------------
filtered_subjects = subjects[subjects["ClassID"] == class_id]

if filtered_subjects.empty:
    st.error("❌ No subjects mapped to this class. Contact Admin.")
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
    st.error("❌ Subject not mapped to this class. Check subjects.csv.")
    st.stop()

subject_id = subject_row.iloc[0]["SubjectID"]

# ----------------------
# SESSION CODE INPUT
# ----------------------
session_code = st.text_input(
    "Enter Session Code",
    help="Share this code with students (valid for 30 minutes)"
)

if not session_code:
    st.warning("Please enter a session code to activate.")
    st.stop()

# ----------------------
# ACTIVATE SESSION
# ----------------------
if st.button("🚀 Activate Session"):

    session_data = {
        "session_code": session_code.strip(),
        "class_id": class_id,
        "subject_id": subject_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "created_at": datetime.now().isoformat()
    }

    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f, indent=2)

    st.success("✅ Session activated successfully!")
    st.info("📢 Share the session code with students.")

    st.json(session_data)
