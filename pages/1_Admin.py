import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("🧑‍💼 Admin Dashboard")

# ---------------- FILE PATHS ----------------
SESSIONS_FILE = "sessions.csv"
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "Students.xlsx"
CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
TEACHERS_FILE = "teachers.csv"

# ---------------- ADMIN LOGIN ----------------
ADMIN_PASSWORD = "admin123"
pwd = st.text_input("Enter Admin Password", type="password")
if pwd != ADMIN_PASSWORD:
    st.stop()
st.success("✅ Logged in as Admin")

# ---------------- SAFE LOAD ----------------
def load_csv(path, required_cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.DataFrame(columns=required_cols)
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
    return df[required_cols]

sessions = load_csv(SESSIONS_FILE, ["SessionID","TeacherID","ClassID","SubjectID","SessionCode","CreatedAt","ExpiryMinutes","Active"])
attendance = load_csv(ATTENDANCE_FILE, ["Date","SessionID","RollNumber"])
classes = load_csv(CLASSES_FILE, ["ClassID","ClassName"])
subjects = load_csv(SUBJECTS_FILE, ["SubjectID","SubjectName","ClassID"])
teachers = load_csv(TEACHERS_FILE, ["TeacherID","TeacherName","Email","Password"])

# Ensure proper types
for df, col in [(sessions, "ClassID"), (sessions, "SubjectID"), (sessions, "TeacherID")]:
    df[col] = df[col].astype(str)
for df, col in [(classes, "ClassID"), (subjects, "SubjectID"), (subjects, "ClassID"), (teachers, "TeacherID")]:
    df[col] = df[col].astype(str)

# ---------------- AUTO EXPIRE SESSIONS ----------------
now = datetime.now()
if not sessions.empty:
    def is_active(row):
        try:
            created = datetime.fromisoformat(row["CreatedAt"])
            return now <= created + timedelta(minutes=int(row["ExpiryMinutes"]))
        except:
            return False
    sessions["Active"] = sessions.apply(is_active, axis=1)
    sessions.to_csv(SESSIONS_FILE, index=False)

# ===================== TABS =====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📌 Sessions",
    "📊 Attendance Reports (List)",
    "🗂 Subject-wise Attendance",
    "🎓 Students",
    "👨‍🏫 Teachers"
])

# ==================================================
# 📌 TAB 1 – SESSIONS
# ==================================================
with tab1:
    st.subheader("All Sessions")
    if sessions.empty:
        st.info("No sessions available.")
    else:
        view = pd.merge(sessions, subjects[["SubjectID","SubjectName"]], on="SubjectID", how="left")
        view = pd.merge(view, classes[["ClassID","ClassName"]], on="ClassID", how="left")
        view["SubjectName"].fillna("—", inplace=True)
        view["ClassName"].fillna("—", inplace=True)
        view = view[[
            "SessionCode","TeacherID","ClassName","SubjectName","SessionID","CreatedAt","ExpiryMinutes","Active"
        ]]
        st.dataframe(view, use_container_width=True)

        st.divider()
        st.subheader("⛔ Deactivate Session")
        active_sessions = view[view["Active"] == "True"]
        if not active_sessions.empty:
            selected_code = st.selectbox("Select Session Code", active_sessions["SessionCode"])
            if st.button("Deactivate Selected Session"):
                sessions.loc[sessions["SessionCode"] == selected_code,"Active"] = "False"
                sessions.to_csv(SESSIONS_FILE, index=False)
                st.success(f"Session {selected_code} deactivated")
                st.experimental_rerun()

# ==================================================
# 📊 TAB 2 – ATTENDANCE REPORTS (List)
# ==================================================
with tab2:
    st.subheader("Attendance Reports")
    if attendance.empty:
        st.info("No attendance recorded.")
    else:
        report = attendance.merge(sessions, on="SessionID", how="left")
        report = report.merge(subjects[["SubjectID","SubjectName"]], on="SubjectID", how="left")
        report = report.merge(classes[["ClassID","ClassName"]], on="ClassID", how="left")
        report["SubjectName"].fillna("—", inplace=True)
        report["ClassName"].fillna("—", inplace=True)
        report = report[["Date","SessionCode","SubjectName","ClassName","RollNumber"]]
        st.dataframe(report, use_container_width=True)
        st.download_button(
            "⬇️ Download CSV",
            report.to_csv(index=False).encode("utf-8"),
            "attendance_report.csv",
            "text/csv"
        )

# ==================================================
# 🗂 TAB 3 – SUBJECT-WISE ATTENDANCE (Wide Report)
# ==================================================
with tab3:
    st.subheader("Subject-wise Attendance Report")
    if attendance.empty:
        st.info("No attendance recorded.")
    else:
        students_df = pd.read_excel(STUDENTS_FILE)
        # Class select
        class_options = classes["ClassName"].tolist()
        selected_class = st.selectbox("Select Class", class_options, key="admin_class")
        class_id = classes.loc[classes["ClassName"]==selected_class,"ClassID"].values[0]
        # Subject select
        subject_options = subjects[subjects["ClassID"]==class_id]["SubjectName"].tolist()
        if not subject_options:
            st.warning("No subjects mapped to this class.")
        else:
            selected_subject = st.selectbox("Select Subject", subject_options, key="admin_subject")
            subject_id = subjects.loc[subjects["SubjectName"]==selected_subject,"SubjectID"].values[0]
            # Sessions
            subject_sessions = sessions[(sessions["ClassID"]==class_id)&(sessions["SubjectID"]==subject_id)].sort_values("CreatedAt")
            if subject_sessions.empty:
                st.warning("No sessions held for this subject yet.")
            else:
                class_students = students_df[students_df["ClassID"]==class_id].copy()
                if class_students.empty:
                    st.warning("No students found for this class.")
                else:
                    # Wide report
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
                    # Total and %
                    report_df["Total Present"] = report_df[session_dates].apply(lambda x: (x=="P").sum(), axis=1)
                    report_df["% Attendance"] = (report_df["Total Present"]/len(session_dates)*100).round(2)
                    # Highlight <70%
                    def highlight_low(val):
                        return 'background-color: #f8d7da' if val < 70 else ''
                    st.dataframe(report_df.style.applymap(lambda x: 'background-color: #f8d7da' if isinstance(x,float) and x<70 else '', subset=["% Attendance"]), use_container_width=True)
                    st.download_button(
                        "⬇️ Download CSV",
                        report_df.to_csv(index=False).encode("utf-8"),
                        f"Attendance_{selected_class}_{selected_subject}.csv",
                        "text/csv"
                    )

# ==================================================
# 🎓 TAB 4 – STUDENTS
# ==================================================
with tab4:
    st.subheader("Students Master")
    if not os.path.exists(STUDENTS_FILE):
        st.error("Students.xlsx not found")
    else:
        st.data_editor(pd.read_excel(STUDENTS_FILE), num_rows="dynamic", key="students_editor")

# ==================================================
# 👨‍🏫 TAB 5 – TEACHERS
# ==================================================
with tab5:
    st.subheader("Teachers Master")
    if not os.path.exists(TEACHERS_FILE):
        st.error("teachers.csv not found")
    else:
        st.data_editor(pd.read_csv(TEACHERS_FILE), num_rows="dynamic", key="teachers_editor")
