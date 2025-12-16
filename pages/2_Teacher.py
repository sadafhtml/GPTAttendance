import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

st.set_page_config(page_title="Teacher Dashboard", layout="wide")
st.title("👩‍🏫 Teacher Dashboard")

# ---------------- FILE PATHS ----------------
TEACHERS_FILE = "teachers.csv"
CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
SESSIONS_FILE = "sessions.csv"
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "Students.xlsx"

# ---------------- SAFE RERUN HELPER ----------------
def safe_rerun():
    st.session_state["reload"] = True
    st.experimental_set_query_params()

# ---------------- ENSURE FILES ----------------
REQUIRED_SESSION_COLS = [
    "SessionID","TeacherID","ClassID","ClassName",
    "SubjectID","SubjectName","SessionCode",
    "CreatedAt","ExpiryMinutes","Active"
]

if not os.path.exists(SESSIONS_FILE):
    pd.DataFrame(columns=REQUIRED_SESSION_COLS).to_csv(SESSIONS_FILE, index=False)

# ---------------- LOGIN STATE ----------------
if "teacher" not in st.session_state:
    st.session_state.teacher = None

# ==================================================
# 🔐 LOGIN
# ==================================================
if st.session_state.teacher is None:

    if not os.path.exists(TEACHERS_FILE):
        st.error("teachers.csv not found")
        st.stop()

    teachers = pd.read_csv(TEACHERS_FILE, dtype=str)
    teachers = teachers.apply(lambda c: c.str.strip())

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("🔐 Login"):
        match = teachers[
            (teachers["Email"] == email.strip()) &
            (teachers["Password"] == password.strip())
        ]

        if match.empty:
            st.error("Invalid credentials")
            st.stop()

        st.session_state.teacher = match.iloc[0].to_dict()
        safe_rerun()

    st.stop()

# ==================================================
# ✅ LOGGED IN
# ==================================================
teacher = st.session_state.teacher
st.success(f"Welcome {teacher['TeacherName']}")

if st.button("🚪 Logout"):
    st.session_state.teacher = None
    safe_rerun()

st.divider()

# ==================================================
# LOAD MASTER DATA
# ==================================================
classes = pd.read_csv(CLASSES_FILE, dtype=str)
subjects = pd.read_csv(SUBJECTS_FILE, dtype=str)
sessions = pd.read_csv(SESSIONS_FILE, dtype=str)

# ==================================================
# 📚 CREATE NEW SESSION
# ==================================================
st.subheader("📚 Start New Session")

class_name = st.selectbox("Select Class", classes["ClassName"])
class_id = classes.loc[classes["ClassName"] == class_name, "ClassID"].values[0]

filtered_subjects = subjects[subjects["ClassID"] == class_id]

if filtered_subjects.empty:
    st.info("No subjects mapped to this class.")
else:
    subject_name = st.selectbox("Select Subject", filtered_subjects["SubjectName"])
    subject_id = filtered_subjects.loc[
        filtered_subjects["SubjectName"] == subject_name, "SubjectID"
    ].values[0]

    session_code = st.text_input("Session Code")
    expiry_minutes = st.number_input(
        "Session Validity (minutes)", min_value=5, max_value=180, value=30
    )

    if st.button("🚀 Activate Session"):
        if not session_code.strip():
            st.error("Session code required")
            st.stop()

        sessions.loc[
            (sessions["TeacherID"] == teacher["TeacherID"]) &
            (sessions["ClassID"] == class_id) &
            (sessions["SubjectID"] == subject_id),
            "Active"
        ] = "False"

        new_session = {
            "SessionID": str(uuid.uuid4())[:8],
            "TeacherID": teacher["TeacherID"],
            "ClassID": class_id,
            "ClassName": class_name,
            "SubjectID": subject_id,
            "SubjectName": subject_name,
            "SessionCode": session_code.strip(),
            "CreatedAt": datetime.now().isoformat(),
            "ExpiryMinutes": str(expiry_minutes),
            "Active": "True"
        }

        sessions = pd.concat([sessions, pd.DataFrame([new_session])], ignore_index=True)
        sessions.to_csv(SESSIONS_FILE, index=False)

        st.success(f"Session activated: {session_code}")
        safe_rerun()

# ==================================================
# 🟢 MY SESSIONS
# ==================================================
st.divider()
st.subheader("🟢 My Sessions")

my_sessions = sessions[sessions["TeacherID"] == teacher["TeacherID"]]

if my_sessions.empty:
    st.info("No sessions created yet.")
else:
    st.dataframe(
        my_sessions[[
            "SessionCode","ClassName","SubjectName",
            "CreatedAt","ExpiryMinutes","Active"
        ]],
        use_container_width=True
    )

# ==================================================
# 📊 MY SUBJECT ATTENDANCE REPORT
# ==================================================
st.divider()
st.subheader("📊 My Subject Attendance Report")

attendance = pd.read_csv(ATTENDANCE_FILE, dtype=str)
students = pd.read_excel(STUDENTS_FILE)

teacher_subjects = my_sessions[["ClassID","ClassName","SubjectID","SubjectName"]].drop_duplicates()

if teacher_subjects.empty:
    st.info("No subjects handled yet.")
    st.stop()

class_sel = st.selectbox("Select Class", teacher_subjects["ClassName"])
class_id = teacher_subjects[teacher_subjects["ClassName"] == class_sel]["ClassID"].values[0]

subject_sel = st.selectbox(
    "Select Subject",
    teacher_subjects[teacher_subjects["ClassID"] == class_id]["SubjectName"]
)

subject_id = teacher_subjects[
    (teacher_subjects["ClassID"] == class_id) &
    (teacher_subjects["SubjectName"] == subject_sel)
]["SubjectID"].values[0]

subject_sessions = my_sessions[
    (my_sessions["ClassID"] == class_id) &
    (my_sessions["SubjectID"] == subject_id)
].sort_values("CreatedAt")

if subject_sessions.empty:
    st.warning("No sessions conducted yet.")
    st.stop()

class_students = students[students["ClassID"] == class_id].copy()

session_dates = {
    row["SessionID"]: pd.to_datetime(row["CreatedAt"]).strftime("%Y-%m-%d")
    for _, row in subject_sessions.iterrows()
}

report = class_students[["RollNumber","EnrollmentNumber","StudentName"]].copy()

for d in session_dates.values():
    report[d] = "A"

for _, att in attendance.iterrows():
    if att["SessionID"] in session_dates:
        report.loc[
            report["RollNumber"].astype(str) == att["RollNumber"],
            session_dates[att["SessionID"]]
        ] = "P"

report.insert(0, "Sr. No.", range(1, len(report) + 1))
report["Total Present"] = report[list(session_dates.values())].apply(
    lambda r: (r == "P").sum(), axis=1
)
report["% Attendance"] = (
    report["Total Present"] / len(session_dates) * 100
).round(2)

def highlight_low(val):
    return "background-color: #ffcccc" if isinstance(val, float) and val < 70 else ""

st.dataframe(
    report.style.applymap(highlight_low, subset=["% Attendance"]),
    use_container_width=True
)

st.download_button(
    "⬇️ Download CSV",
    report.to_csv(index=False).encode("utf-8"),
    f"MyAttendance_{class_sel}_{subject_sel}.csv",
    "text/csv"
)
