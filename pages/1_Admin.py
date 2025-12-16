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

# ---------------- ADMIN LOGIN ----------------
ADMIN_PASSWORD = "admin123"

pwd = st.text_input("Enter Admin Password", type="password")
if pwd != ADMIN_PASSWORD:
    st.stop()

st.success("✅ Logged in as Admin")

# ---------------- SAFE LOADERS ----------------
def load_csv(path, columns):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns)

sessions = load_csv(
    SESSIONS_FILE,
    ["SessionID","ClassID","SubjectID","SessionCode","CreatedAt","ExpiryMinutes","Active"]
)

attendance = load_csv(
    ATTENDANCE_FILE,
    ["Date","SessionID","RollNumber"]
)

classes = load_csv(CLASSES_FILE, ["ClassID","ClassName"])
subjects = load_csv(SUBJECTS_FILE, ["SubjectID","SubjectName","ClassID"])

# ---------------- AUTO-EXPIRE SESSIONS ----------------
now = datetime.now()

if not sessions.empty:
    def check_active(row):
        created = datetime.fromisoformat(row["CreatedAt"])
        return now <= created + timedelta(minutes=int(row["ExpiryMinutes"]))

    sessions["Active"] = sessions.apply(check_active, axis=1)
    sessions.to_csv(SESSIONS_FILE, index=False)

# ===================== TABS =====================
tab1, tab2, tab3 = st.tabs([
    "📌 Sessions",
    "📊 Attendance Reports",
    "🎓 Students"
])

# ==================================================
# 📌 TAB 1 – SESSIONS (IMPROVED)
# ==================================================
with tab1:
    st.subheader("All Sessions")

    if sessions.empty:
        st.info("No sessions found.")
        st.stop()

    # Merge for display
    view = sessions.merge(subjects, on="SubjectID", how="left")
    view = view.merge(classes, on="ClassID", how="left")

    # Reorder columns (SessionCode FIRST)
    view = view[[
        "SessionCode",
        "SubjectName",
        "ClassName",
        "SessionID",
        "CreatedAt",
        "ExpiryMinutes",
        "Active"
    ]]

    st.dataframe(view, use_container_width=True)

    st.divider()
    st.subheader("⛔ Deactivate Session")

    active_sessions = view[view["Active"] == True]

    if active_sessions.empty:
        st.info("No active sessions to deactivate.")
        st.stop()

    selected_code = st.selectbox(
        "Select Session Code to Deactivate",
        active_sessions["SessionCode"]
    )

    if st.button("Deactivate Selected Session"):
        sessions.loc[
            sessions["SessionCode"] == selected_code, "Active"
        ] = False

        sessions.to_csv(SESSIONS_FILE, index=False)
        st.success(f"Session `{selected_code}` deactivated")
        st.rerun()

# ==================================================
# 📊 TAB 2 – ATTENDANCE REPORTS
# ==================================================
with tab2:
    st.subheader("Attendance Reports")

    if attendance.empty:
        st.info("No attendance data available.")
        st.stop()

    report = attendance.merge(sessions, on="SessionID", how="left")
    report = report.merge(subjects, on="SubjectID", how="left")
    report = report.merge(classes, on="ClassID", how="left")

    report = report[[
        "Date",
        "SessionCode",
        "SubjectName",
        "ClassName",
        "RollNumber"
    ]]

    st.dataframe(report, use_container_width=True)

    csv = report.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Attendance CSV",
        csv,
        "attendance_report.csv",
        "text/csv"
    )

# ==================================================
# 🎓 TAB 3 – STUDENTS
# ==================================================
with tab3:
    st.subheader("Students Master Data")

    if not os.path.exists(STUDENTS_FILE):
        st.error("Students.xlsx not found")
    else:
        students = pd.read_excel(STUDENTS_FILE)
        st.dataframe(students, use_container_width=True)

        st.info("✏️ Edit students via Excel file")
