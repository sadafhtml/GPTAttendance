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

# ---------------- SAFE LOAD FUNCTION ----------------
def load_csv(path, required_cols):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype=str)
    else:
        df = pd.DataFrame()
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
    return df[required_cols]

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

# ---------------- AUTO EXPIRE SESSIONS ----------------
now = datetime.now()
def is_active(row):
    try:
        created = datetime.fromisoformat(row["CreatedAt"])
        return now <= created + timedelta(minutes=int(row["ExpiryMinutes"]))
    except:
        return False

if not sessions.empty:
    sessions["Active"] = sessions.apply(is_active, axis=1)
    sessions.to_csv(SESSIONS_FILE, index=False)

# ===================== TABS =====================
tab1, tab2, tab3 = st.tabs([
    "📌 Sessions",
    "📊 Attendance Reports",
    "🎓 Students"
])

# ==================================================
# 📌 TAB 1 – SESSIONS
# ==================================================
with tab1:
    st.subheader("All Sessions")
    if sessions.empty:
        st.info("No sessions available.")
        st.stop()

    view = sessions.copy()

    # Merge safely with subjects and classes
    if "SubjectID" in view.columns and not subjects.empty:
        view = view.merge(subjects, on="SubjectID", how="left")
    if "ClassID" in view.columns and not classes.empty:
        view = view.merge(classes, on="ClassID", how="left")

    # Fill missing names
    if "SubjectName" not in view.columns:
        view["SubjectName"] = "—"
    if "ClassName" not in view.columns:
        view["ClassName"] = "—"

    # Reorder columns
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
        st.info("No active sessions.")
        st.stop()

    selected_code = st.selectbox(
        "Select Session Code",
        active_sessions["SessionCode"]
    )
    if st.button("Deactivate Selected Session"):
        sessions.loc[sessions["SessionCode"] == selected_code, "Active"] = "False"
        sessions.to_csv(SESSIONS_FILE, index=False)
        st.success(f"Session {selected_code} deactivated")
        st.experimental_rerun()

# ==================================================
# 📊 TAB 2 – ATTENDANCE REPORTS
# ==================================================
with tab2:
    st.subheader("Attendance Reports")
    if attendance.empty:
        st.info("No attendance recorded.")
        st.stop()

    # Safe merge for report
    report = attendance.copy()
    if "SessionID" in report.columns and not sessions.empty:
        report = report.merge(sessions, on="SessionID", how="left")
    if "SubjectID" in report.columns and not subjects.empty:
        report = report.merge(subjects, on="SubjectID", how="left")
    if "ClassID" in report.columns and not classes.empty:
        report = report.merge(classes, on="ClassID", how="left")

    # Fill missing columns
    for col in ["SessionCode","SubjectName","ClassName"]:
        if col not in report.columns:
            report[col] = "—"

    report = report[[
        "Date",
        "SessionCode",
        "SubjectName",
        "ClassName",
        "RollNumber"
    ]]
    st.dataframe(report, use_container_width=True)

    st.download_button(
        "⬇️ Download CSV",
        report.to_csv(index=False).encode("utf-8"),
        "attendance_report.csv",
        "text/csv"
    )

# ==================================================
# 🎓 TAB 3 – STUDENTS
# ==================================================
with tab3:
    st.subheader("Students Master")
    if not os.path.exists(STUDENTS_FILE):
        st.error("Students.xlsx not found")
    else:
        st.dataframe(pd.read_excel(STUDENTS_FILE), use_container_width=True)
