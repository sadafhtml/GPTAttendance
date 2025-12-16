import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("🛠️ Admin Dashboard – Session Management")

CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
SESSIONS_FILE = "sessions.csv"

# ----------------------
# LOAD MASTER FILES
# ----------------------
for file in [CLASSES_FILE, SUBJECTS_FILE]:
    if not os.path.exists(file):
        st.error(f"❌ Missing required file: {file}")
        st.stop()

classes = pd.read_csv(CLASSES_FILE, dtype=str)
subjects = pd.read_csv(SUBJECTS_FILE, dtype=str)

# ----------------------
# CREATE SESSION (ADMIN ACTION)
# ----------------------
st.subheader("➕ Create / Activate Session")

col1, col2, col3 = st.columns(3)

with col1:
    class_name = st.selectbox("Class", classes["ClassName"])
    class_id = classes.loc[
        classes["ClassName"] == class_name, "ClassID"
    ].values[0]

with col2:
    filtered_subjects = subjects[subjects["ClassID"] == class_id]
    if filtered_subjects.empty:
        st.error("❌ No subjects mapped to this class")
        st.stop()

    subject_name = st.selectbox("Subject", filtered_subjects["SubjectName"])
    subject_id = filtered_subjects.loc[
        filtered_subjects["SubjectName"] == subject_name, "SubjectID"
    ].values[0]

with col3:
    session_code = st.text_input("Session Code")
    expiry_minutes = st.number_input(
        "Validity (minutes)", min_value=5, max_value=180, value=30
    )

if st.button("🚀 Activate Session"):
    if not session_code.strip():
        st.error("❌ Session code cannot be empty")
        st.stop()

    # Create sessions file if not exists
    if not os.path.exists(SESSIONS_FILE):
        pd.DataFrame(columns=[
            "SessionID",
            "SessionCode",
            "ClassID",
            "ClassName",
            "SubjectID",
            "SubjectName",
            "CreatedAt",
            "ExpiryMinutes",
            "Active"
        ]).to_csv(SESSIONS_FILE, index=False)

    sessions = pd.read_csv(SESSIONS_FILE, dtype=str)

    # Deactivate old active sessions with same code
    sessions.loc[
        (sessions["SessionCode"] == session_code) &
        (sessions["Active"] == "True"),
        "Active"
    ] = "False"

    new_session = {
        "SessionID": str(uuid.uuid4()),
        "SessionCode": session_code.strip(),
        "ClassID": class_id,
        "ClassName": class_name,
        "SubjectID": subject_id,
        "SubjectName": subject_name,
        "CreatedAt": datetime.now().isoformat(),
        "ExpiryMinutes": str(expiry_minutes),
        "Active": "True"
    }

    sessions = pd.concat(
        [sessions, pd.DataFrame([new_session])],
        ignore_index=True
    )

    sessions.to_csv(SESSIONS_FILE, index=False)

    st.success("✅ Session activated successfully")

# ----------------------
# VIEW & DEACTIVATE SESSIONS
# ----------------------
st.divider()
st.subheader("📋 Active Sessions")

if os.path.exists(SESSIONS_FILE):
    sessions = pd.read_csv(SESSIONS_FILE, dtype=str)

    active_sessions = sessions[sessions["Active"] == "True"]

    if active_sessions.empty:
        st.info("No active sessions")
    else:
        st.dataframe(
            active_sessions[[
                "SessionCode",
                "ClassName",
                "SubjectName",
                "CreatedAt",
                "ExpiryMinutes"
            ]],
            use_container_width=True
        )

        deactivate_code = st.selectbox(
            "Deactivate Session (by Session Code)",
            active_sessions["SessionCode"]
        )

        if st.button("🛑 Deactivate Selected Session"):
            sessions.loc[
                sessions["SessionCode"] == deactivate_code,
                "Active"
            ] = "False"

            sessions.to_csv(SESSIONS_FILE, index=False)
            st.success("✅ Session deactivated")
            st.rerun()
