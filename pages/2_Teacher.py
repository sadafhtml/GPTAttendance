import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

st.set_page_config(page_title="Teacher Panel", layout="wide")
st.title("👩‍🏫 Teacher Panel")

# =====================================================
# FILE PATHS
# =====================================================
TEACHERS_FILE = "teachers.csv"
CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
SESSIONS_FILE = "sessions.csv"

# =====================================================
# REQUIRED SESSION COLUMNS
# =====================================================
REQUIRED_COLUMNS = [
    "SessionID","TeacherID",
    "ClassID","ClassName",
    "SubjectID","SubjectName",
    "SessionCode","CreatedAt",
    "ExpiryMinutes","Active"
]

# =====================================================
# ENSURE sessions.csv EXISTS & SAFE
# =====================================================
if not os.path.exists(SESSIONS_FILE):
    pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(SESSIONS_FILE, index=False)

sessions = pd.read_csv(SESSIONS_FILE, dtype=str)
for col in REQUIRED_COLUMNS:
    if col not in sessions.columns:
        sessions[col] = ""

# =====================================================
# LOGIN STATE
# =====================================================
if "teacher" not in st.session_state:
    st.session_state.teacher = None

# =====================================================
# LOGIN PAGE
# =====================================================
if st.session_state.teacher is None:

    st.subheader("🔐 Teacher Login")

    if not os.path.exists(TEACHERS_FILE):
        st.error("teachers.csv not found")
        st.stop()

    teachers = pd.read_csv(TEACHERS_FILE, dtype=str)
    teachers = teachers.fillna("")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pwd")

    if st.button("Login"):
        match = teachers[
            (teachers["Email"].str.strip() == email.strip()) &
            (teachers["Password"].str.strip() == password.strip())
        ]

        if match.empty:
            st.error("❌ Invalid credentials")
            st.stop()

        st.session_state.teacher = match.iloc[0].to_dict()
        st.session_state["reload"] = True
        st.experimental_set_query_params()

    st.stop()

# =====================================================
# LOGGED IN
# =====================================================
teacher = st.session_state.teacher
st.success(f"Welcome {teacher['TeacherName']}")

if st.button("🚪 Logout"):
    st.session_state.teacher = None
    st.session_state.clear()
    st.experimental_set_query_params()
    st.stop()

st.divider()

# =====================================================
# LOAD MASTER DATA
# =====================================================
classes = pd.read_csv(CLASSES_FILE, dtype=str).fillna("")
subjects = pd.read_csv(SUBJECTS_FILE, dtype=str).fillna("")

# =====================================================
# CREATE SESSION
# =====================================================
st.subheader("📚 Create New Session")

class_sel = st.selectbox(
    "Select Class",
    classes["ClassName"],
    key="class_select"
)

class_id = classes.loc[
    classes["ClassName"] == class_sel, "ClassID"
].values[0]

filtered_subjects = subjects[subjects["ClassID"] == class_id]

if filtered_subjects.empty:
    st.warning("No subjects mapped to this class.")
    st.stop()

subject_sel = st.selectbox(
    "Select Subject",
    filtered_subjects["SubjectName"],
    key="subject_select"
)

subject_id = filtered_subjects.loc[
    filtered_subjects["SubjectName]()_
