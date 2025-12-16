import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

st.set_page_config(page_title="Teacher Panel", layout="wide")
st.title("👩‍🏫 Teacher Dashboard")

# ================= FILE PATHS =================
TEACHERS_FILE = "teachers.csv"
CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
SESSIONS_FILE = "sessions.csv"
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "Students.xlsx"

# ================= HELPERS =================
def safe_csv(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]

# ================= SESSION STATE =================
if "teacher" not in st.session_state:
    st.session_state.teacher = None

# ================= LOGIN =================
if st.session_state.teacher is None:
    st.subheader("🔐 Teacher Login")

    teachers = safe_csv(
        TEACHERS_FILE,
        ["TeacherID", "TeacherName", "Email", "Password"]
    )

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        match = teachers[
            (teachers["Email"] == email) &
            (teachers["Password"] == password)
        ]
        if match.empty:
            st.error("Invalid credentials")
            st.stop()

        st.session_state.teacher = match.iloc[0].to_dict()
        st.experimental_set_query_params()

    st.stop()

# ================= LOGGED IN =================
teacher = st.session_state.teacher
st.success(f"Welcome {teacher['TeacherName']}")

if st.button("🚪 Logout"):
    st.session_state.clear()
    st.experimental_set_query_params()
    st.stop()

# ================= LOAD DATA =================
classes = safe_csv(CLASSES_FILE, ["ClassID", "ClassName"])
subjects = safe_csv(SUBJECTS_FILE, ["SubjectID", "SubjectName", "ClassID"])
sessions = safe_csv(
    SESSIONS_FILE,
    [
        "SessionID","TeacherID","ClassID","ClassName",
        "SubjectID","SubjectName",
        "SessionCode","CreatedAt","ExpiryMinutes","Active"
    ]
)
attendance = safe_csv(ATTENDANCE_FILE, ["Date","SessionID","RollNumber"])
students = pd.read_excel(STUDENTS_FILE) if os.path.exists(STUDENTS_FILE) else pd.DataFrame()

# ================= CREATE SESSION =================
st.divider()
st.subheader("📚 Create New Session")

class_name = st.selectbox(
    "Select Class",
    classes["ClassName"].tolist(),
    key="create_class"
)

class_id = classes.loc[
    classes["ClassName"] == class_name, "ClassID"
].values[0]

class_subjects = subjects[subjects["ClassID"] == class_id]

if class_subjects.empty:
    st.warning("No subjects for this class")
    st.stop()

subject_name = st.selectbox(
    "Select Subject",
    class_subjects["SubjectName"].tolist(),
    key="create_subject"
)

subject_id = class_subjects.loc[
    class_subjects["SubjectName"] == subject_name, "SubjectID"
].values[0]

session_code = st.text_input("Session Code")
expiry = st.number_input("Expiry (minutes)", 5, 180, 30)

if st.button("🚀 Activate Session"):
    sessions.loc[
        (sessions["TeacherID"] == teacher["TeacherID"]) &
        (sessions["ClassID"] == class_id) &
        (sessions["SubjectID"] == subject_id),
        "Active"
    ] = "False"

    new_row = {
        "SessionID": str(uuid.uuid4())[:8],
        "TeacherID": teacher["TeacherID"],
        "ClassID": class_id,
        "ClassName": class_name,
        "SubjectID": subject_id,
        "SubjectName": subject_name,
        "SessionCode": session_code,
        "CreatedAt": datetime.now().isoformat(),
        "ExpiryMinutes": str(expiry),
        "Active": "True"
    }

    sessions = pd.concat([sessions, pd.DataFrame([new_row])], ignore_index=True)
    sessions.to_csv(SESSIONS_FILE, index=False)

    st.success("Session activated")

# ================= MY SESSIONS =================
st.divider()
st.subheader("📋 My Sessions")

my_sessions = sessions[sessions["TeacherID"] == teacher["TeacherID"]]

if my_sessions.empty:
    st.info("No sessions created yet")
else:
    st.dataframe(
        my_sessions[
            ["SessionCode","ClassName","SubjectName","CreatedAt","ExpiryMinutes","Active"]
        ],
        use_container_width=True
    )

# ================= ATTENDANCE REPORT =================
st.divider()
st.subheader("📊 Date-wise Attendance Report (Till Date)")

rep_class = st.selectbox(
    "Select Class",
    classes["ClassName"].tolist(),
    key="rep_class"
)

rep_class_id = classes.loc[
    classes["ClassName"] == rep_class, "ClassID"
].values[0]

rep_subjects = subjects[subjects["ClassID"] == rep_class_id]

if rep_subjects.empty:
    st.warning("No subjects mapped")
    st.stop()

rep_subject = st.selectbox(
    "Select Subject",
    rep_subjects["SubjectName"].tolist(),
    key="rep_subject"
)

rep_subject_id = rep_subjects.loc[
    rep_subjects["SubjectName"] == rep_subject, "SubjectID"
].values[0]

# ---- ALL sessions till date for this teacher + subject
subject_sessions = sessions[
    (sessions["TeacherID"] == teacher["TeacherID"]) &
    (sessions["ClassID"] == rep_class_id) &
    (sessions["SubjectID"] == rep_subject_id)
].copy()

if subject_sessions.empty:
    st.warning("No sessions conducted yet")
    st.stop()

# ---- sort by time
subject_sessions["SessionDate"] = pd.to_datetime(
    subject_sessions["CreatedAt"]
).dt.date.astype(str)

subject_sessions = subject_sessions.sort_values("CreatedAt")

session_ids = subject_sessions["SessionID"].tolist()
session_dates = subject_sessions["SessionDate"].tolist()

# ---- students of this class
stu = students[students["ClassID"].astype(str) == str(rep_class_id)]

if stu.empty:
    st.warning("No students in this class")
    st.stop()

rows = []

for i, s in stu.iterrows():
    row = {
        "Sr No": len(rows) + 1,
        "RollNumber": s["RollNumber"],
        "Enrollment": s["EnrollmentNumber"],
        "Name": s["StudentName"]
    }

    present_count = 0

    for sid, sdate in zip(session_ids, session_dates):
        is_present = (
            (attendance["SessionID"].astype(str) == str(sid)) &
            (attendance["RollNumber"].astype(str) == str(s["RollNumber"]))
        ).any()

        row[sdate] = "P" if is_present else "A"
        present_count += int(is_present)

    total_sessions = len(session_ids)
    row["Total Present"] = present_count
    row["% Attendance"] = round((present_count / total_sessions) * 100, 2)

    rows.append(row)

report_df = pd.DataFrame(rows)

# ---- highlight below 70%
def highlight_low(val):
    try:
        return "background-color: #ffcccc" if float(val) < 70 else ""
    except:
        return ""

# ================= PER-DATE TOTAL ROW =================

total_row = {
    "Sr No": "",
    "RollNumber": "",
    "Enrollment": "",
    "Name": "TOTAL PRESENT"
}

for d in session_dates:
    total_row[d] = (report_df[d] == "P").sum()

total_row["Total Present"] = ""
total_row["% Attendance"] = ""

report_df = pd.concat(
    [report_df, pd.DataFrame([total_row])],
    ignore_index=True
)

st.dataframe(
    report_df.style.applymap(highlight_low, subset=["% Attendance"]),
    use_container_width=True
)

st.download_button(
    "⬇️ Download Date-wise Attendance CSV",
    report_df.to_csv(index=False).encode("utf-8"),
    f"{rep_class}_{rep_subject}_datewise_attendance.csv",
    "text/csv"
)

