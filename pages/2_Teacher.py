import streamlit as st
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="Teacher Panel", layout="centered")
st.title("👨‍🏫 Teacher Attendance Control")

# Load data
classes = pd.read_csv("classes.csv")
subjects = pd.read_csv("subjects.csv")

# Select class
class_name = st.selectbox("Select Class", classes["ClassName"])
class_id = classes[classes["ClassName"] == class_name]["ClassID"].values[0]

# Filter subjects by class
filtered_subjects = subjects[subjects["ClassID"] == class_id]
subject_name = st.selectbox("Select Subject", filtered_subjects["SubjectName"])
subject_id = filtered_subjects[filtered_subjects["SubjectName"] == subject_name]["SubjectID"].values[0]

# Session code input
session_code = st.text_input("Enter Session Code (announce to students)")

if st.button("🚀 Activate Session"):
    session_data = {
        "session_code": session_code,
        "class_id": class_id,
        "subject_id": subject_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "created_at": datetime.now().isoformat()
    }

    with open("session.json", "w") as f:
        json.dump(session_data, f)

    st.success("✅ Session activated (valid for 30 minutes)")

st.info("After activation, share link + session code with students")
