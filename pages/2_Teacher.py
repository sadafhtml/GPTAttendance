import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

st.set_page_config(page_title="Teacher Panel", layout="wide")
st.title("👩‍🏫 Teacher Panel")

# ---------------- FILE PATHS ----------------
TEACHERS_FILE = "teachers.csv"
CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
SESSIONS_FILE = "sessions.csv"
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "Students.xlsx"

REQUIRED_COLUMNS = [
    "SessionID","TeacherID","ClassID","ClassName","SubjectID","SubjectName",
    "SessionCode","CreatedAt","ExpiryMinutes","Active"
]

# ---------------- ENSURE SESSIONS FILE ----------------
if not os.path.exists(SESSIONS_FILE):
    pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(SESSIONS_FILE,index=False)

# ---------------- TEACHER LOGIN ----------------
if "teacher" not in st.session_state:
    st.session_state.teacher = None

if st.session_state.teacher is None:
    if not os.path.exists(TEACHERS_FILE):
        st.error("❌ teachers.csv not found")
        st.stop()
    teachers = pd.read_csv(TEACHERS_FILE, dtype=str)
    for col in ["Email","Password"]:
        teachers[col] = teachers[col].str.strip()
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("🔐 Login"):
        match = teachers[(teachers["Email"]==email.strip())&(teachers["Password"]==password.strip())]
        if match.empty:
            st.error("❌ Invalid credentials")
            st.stop()
        st.session_state.teacher = match.iloc[0].to_dict()
        st.experimental_rerun()
    st.stop()

teacher = st.session_state.teacher
st.success(f"Welcome {teacher['TeacherName']}")
if st.button("🚪 Logout"):
    st.session_state.teacher = None
    st.experimental_rerun()

st.divider()

# ---------------- LOAD MASTER DATA ----------------
classes = pd.read_csv(CLASSES_FILE, dtype=str)
subjects = pd.read_csv(SUBJECTS_FILE, dtype=str)

# ---------------- CREATE NEW SESSION ----------------
st.subheader("📚 Start New Session")
if classes.empty:
    st.warning("No classes available.")
else:
    class_name = st.selectbox("Select Class", classes["ClassName"])
    class_id = classes.loc[classes["ClassName"]==class_name,"ClassID"].values[0]
    filtered_subjects = subjects[subjects["ClassID"]==class_id]
    if filtered_subjects.empty:
        st.info("ℹ️ No subjects mapped to this class yet.")
        subject_name = None
        subject_id = None
    else:
        subject_name = st.selectbox("Select Subject", filtered_subjects["SubjectName"])
        subject_id = filtered_subjects.loc[filtered_subjects["SubjectName"]==subject_name,"SubjectID"].values[0]
    session_code = st.text_input("Session Code")
    expiry_minutes = st.number_input("Session Validity (minutes)", min_value=5,max_value=180,value=30)
    if st.button("🚀 Activate Session"):
        if not session_code.strip():
            st.error("❌ Session code cannot be empty")
            st.stop()
        if filtered_subjects.empty:
            st.error("❌ Cannot activate session without a subject")
            st.stop()
        sessions = pd.read_csv(SESSIONS_FILE,dtype=str)
        for col in REQUIRED_COLUMNS:
            if col not in sessions.columns:
                sessions[col] = ""
        sessions.loc[
            (sessions["TeacherID"]==teacher["TeacherID"]) &
            (sessions["ClassID"]==class_id) &
            (sessions["SubjectID"]==subject_id) &
            (sessions["Active"]=="True"),
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
        sessions = pd.concat([sessions,pd.DataFrame([new_session])],ignore_index=True)
        sessions.to_csv(SESSIONS_FILE,index=False)
        st.success(f"✅ Session activated successfully\nSession Code: {session_code.strip()}")

# ---------------- VIEW TEACHER'S ACTIVE SESSIONS ----------------
st.divider()
st.subheader("🟢 My Active Sessions")
sessions = pd.read_csv(SESSIONS_FILE,dtype=str)
for col in REQUIRED_COLUMNS:
    if col not in sessions.columns:
        sessions[col] = ""
my_sessions = sessions[(sessions["TeacherID"]==teacher["TeacherID"]) & (sessions["Active"]=="True")]
if my_sessions.empty:
    st.info("No active sessions")
else:
    st.dataframe(
        my_sessions[["SessionCode","ClassName","SubjectName","CreatedAt","ExpiryMinutes"]],
        use_container_width=True
    )

# ---------------- VIEW ATTENDANCE REPORT FOR TEACHER ----------------
st.divider()
st.subheader("📊 Attendance Report for Your Subjects")
if os.path.exists(ATTENDANCE_FILE):
    attendance = pd.read_csv(ATTENDANCE_FILE,dtype=str)
    students_df = pd.read_excel(STUDENTS_FILE)
    my_subjects = subjects.copy()
    my_subjects = my_subjects[my_subjects["ClassID"].isin(classes["ClassID"])]
    selected_class = st.selectbox("Select Class for Report", classes["ClassName"].tolist(), key="teacher_class")
    class_id = classes.loc[classes["ClassName"]==selected_class,"ClassID"].values[0]
    subject_options = subjects[subjects["ClassID"]==class_id]["SubjectName"].tolist()
    selected_subject = st.selectbox("Select Subject for Report", subject_options, key="teacher_subject")
    subject_id = subjects.loc[subjects["SubjectName"]==selected_subject,"SubjectID"].values[0]
    subject_sessions = sessions[(sessions["ClassID"]==class_id)&(sessions["SubjectID"]==subject_id)&(sessions["TeacherID"]==teacher["TeacherID"])].sort_values("CreatedAt")
    if subject_sessions.empty:
        st.info("No sessions held yet for this subject.")
    else:
        class_students = students_df[students_df["ClassID"]==class_id].copy()
        session_dates = []
        session_map = {}
        for _, row in subject_sessions.iterrows():
            date = pd.to_datetime(row["CreatedAt"]).strftime("%Y-%m-%d")
            session_dates.append(date)
            session_map[row["SessionID"]] = date
        report_df = class_students[["RollNumber","EnrollmentNumber","StudentName"]].copy()
        for date in session_dates:
            report_df[date] = "A"
        for _, att in attendance.iterrows():
            sid = att["SessionID"]
            roll = att["RollNumber"]
            if sid in session_map and roll in report_df["RollNumber"].astype(str).values:
                date_col = session_map[sid]
                report_df.loc[report_df["RollNumber"].astype(str)==roll,date_col] = "P"
        report_df["Total Present"] = report_df[session_dates].apply(lambda x:(x=="P").sum(),axis=1)
        report_df["% Attendance"] = (report_df["Total Present"]/len(session_dates)*100).round(2)
        st.dataframe(report_df.style.applymap(lambda x: 'background-color:#f8d7da' if isinstance(x,float) and x<70 else '', subset=["% Attendance"]),use_container_width=True)
        st.download_button(
            "⬇️ Download CSV",
            report_df.to_csv(index=False).encode("utf-8"),
            f"Attendance_{selected_class}_{selected_subject}.csv",
            "text/csv"
        )
