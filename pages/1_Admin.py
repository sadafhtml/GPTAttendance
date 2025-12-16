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

# Ensure IDs are strings
for df, col in [(sessions, "ClassID"), (sessions, "SubjectID")]:
    df[col] = df[col].astype(str)

for df, col in [(classes, "ClassID"), (subjects, "SubjectID"), (subjects, "ClassID")]:
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

    # Merge with subjects and classes
    view = pd.merge(view, subjects[["SubjectID","SubjectName"]], on="SubjectID", how="left")
    view = pd.merge(view, classes[["ClassID","ClassName"]], on="ClassID", how="left")

    view["SubjectName"].fillna("—", inplace=True)
    view["ClassName"].fillna("—", inplace=True)

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
        sessions.loc[sessions["SessionCode"] == selected_code, "Active"] = False
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

    report = attendance.merge(sessions, on="SessionID", how="left")
    report = report.merge(subjects[["SubjectID","SubjectName"]], on="SubjectID", how="left")
    report = report.merge(classes[["ClassID","ClassName"]], on="ClassID", how="left")

    report["SubjectName"].fillna("—", inplace=True)
    report["ClassName"].fillna("—", inplace=True)

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
