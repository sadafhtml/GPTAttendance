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

# ---------------- PASSWORD ----------------
ADMIN_PASSWORD = "admin123"

pwd = st.text_input("Enter Admin Password", type="password")
if pwd != ADMIN_PASSWORD:
    st.stop()

st.success("✅ Logged in as Admin")

# ---------------- LOAD FILES SAFELY ----------------
def load_csv(path, columns=None):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns if columns else [])

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

if not sessions.empty:
    def is_active(row):
        created = datetime.fromisoformat(row["CreatedAt"])
        return now <= created + timedelta(minutes=int(row["ExpiryMinutes"]))

    sessions["Active"] = sessions.apply(is_active, axis=1)
    sessions.to_csv(SESSIONS_FILE, index=False)

# ===================== TABS =====================
tab1, tab2, tab3, tab4 = st.tabs([
    "📌 Active Sessions",
    "📊 Attendance Reports",
    "🎓 Students",
    "⚙️ Master Data"
])

# ==================================================
# 📌 TAB 1 – ACTIVE SESSIONS
# ==================================================
with tab1:
    st.subheader("Active & Expired Sessions")

    if sessions.empty:
        st.info("No sessions created yet.")
    else:
        st.dataframe(sessions, use_container_width=True)

        deactivate_id = st.selectbox(
            "Deactivate Session",
            ["None"] + sessions["SessionID"].tolist()
        )

        if deactivate_id != "None" and st.button("⛔ Deactivate Selected Session"):
            sessions.loc[sessions["SessionID"] == deactivate_id, "Active"] = False
            sessions.to_csv(SESSIONS_FILE, index=False)
            st.success("Session deactivated")
            st.experimental_rerun()

# ==================================================
# 📊 TAB 2 – ATTENDANCE REPORTS
# ==================================================
with tab2:
    st.subheader("Attendance Reports")

    if attendance.empty:
        st.info("No attendance recorded yet.")
    else:
        merged = attendance.merge(
            sessions,
            on="SessionID",
            how="left"
        )

        merged = merged.merge(classes, on="ClassID", how="left")
        merged = merged.merge(subjects, on="SubjectID", how="left")

        st.dataframe(merged, use_container_width=True)

        csv = merged.to_csv(index=False).encode("utf-8")
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
    st.subheader("Student Master (Read-only)")

    if not os.path.exists(STUDENTS_FILE):
        st.error("Students.xlsx not found")
    else:
        students = pd.read_excel(STUDENTS_FILE)
        st.dataframe(students, use_container_width=True)

        st.info("✏️ Student editing is Excel-based for safety")

# ==================================================
# ⚙️ TAB 4 – MASTER DATA
# ==================================================
with tab4:
    st.subheader("Classes & Subjects")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Classes")
        st.dataframe(classes, use_container_width=True)

    with col2:
        st.markdown("### Subjects")
        st.dataframe(subjects, use_container_width=True)

    st.info("✏️ Edit master data via CSV files")
