import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("🛠️ Admin Panel - Attendance System")

# ----------------------
# PASSWORD PROTECTION (Simple)
# ----------------------
PASSWORD = "admin123"  # change this
pwd = st.text_input("Enter Admin Password", type="password")

if pwd != PASSWORD:
    st.warning("❌ Incorrect password")
    st.stop()

# ----------------------
# FILE PATHS
# ----------------------
STUDENTS_FILE = "students.xlsx"
CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
ATTENDANCE_FILE = "attendance.csv"

# ----------------------
# LOAD FILES
# ----------------------
if os.path.exists(STUDENTS_FILE):
    students = pd.read_excel(STUDENTS_FILE)
else:
    students = pd.DataFrame(columns=["RollNumber","StudentName","EnrollmentNumber","ClassID"])

if os.path.exists(CLASSES_FILE):
    classes = pd.read_csv(CLASSES_FILE)
else:
    classes = pd.DataFrame(columns=["ClassID","ClassName"])

if os.path.exists(SUBJECTS_FILE):
    subjects = pd.read_csv(SUBJECTS_FILE)
else:
    subjects = pd.DataFrame(columns=["SubjectID","SubjectName","ClassID"])

# ----------------------
# TABS
# ----------------------
tab = st.tabs(["Students","Classes","Subjects","Attendance Download"])

# ----------------------
# STUDENTS TAB
# ----------------------
with tab[0]:
    st.subheader("👩‍🎓 Manage Students")
    st.dataframe(students)

    st.markdown("### Add New Student")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        new_roll = st.text_input("Roll Number", key="roll")
    with col2:
        new_name = st.text_input("Student Name", key="name")
    with col3:
        new_enroll = st.text_input("Enrollment Number", key="enroll")
    with col4:
        new_class = st.selectbox("Class", classes["ClassID"] if not classes.empty else [], key="class")

    if st.button("➕ Add Student"):
        if new_roll and new_name and new_enroll and new_class:
            new_student = {
                "RollNumber": new_roll,
                "StudentName": new_name,
                "EnrollmentNumber": new_enroll,
                "ClassID": new_class
            }
            students = pd.concat([students, pd.DataFrame([new_student])], ignore_index=True)
            students.to_excel(STUDENTS_FILE, index=False)
            st.success("✅ Student added successfully")
        else:
            st.warning("Please fill all fields")

# ----------------------
# CLASSES TAB
# ----------------------
with tab[1]:
    st.subheader("🏫 Manage Classes")
    st.dataframe(classes)

    st.markdown("### Add New Class")
    new_class_id = st.text_input("Class ID", key="classid")
    new_class_name = st.text_input("Class Name", key="classname")

    if st.button("➕ Add Class"):
        if new_class_id and new_class_name:
            classes = pd.concat([classes, pd.DataFrame([{"ClassID":new_class_id,"ClassName":new_class_name}])], ignore_index=True)
            classes.to_csv(CLASSES_FILE, index=False)
            st.success("✅ Class added successfully")
        else:
            st.warning("Please fill all fields")

# ----------------------
# SUBJECTS TAB
# ----------------------
with tab[2]:
    st.subheader("📚 Manage Subjects")
    st.dataframe(subjects)

    st.markdown("### Add New Subject")
    new_sub_id = st.text_input("Subject ID", key="subid")
    new_sub_name = st.text_input("Subject Name", key="subname")
    new_sub_class = st.selectbox("Class for Subject", classes["ClassID"] if not classes.empty else [], key="subclass")

    if st.button("➕ Add Subject"):
        if new_sub_id and new_sub_name and new_sub_class:
            subjects = pd.concat([subjects, pd.DataFrame([{"SubjectID":new_sub_id,"SubjectName":new_sub_name,"ClassID":new_sub_class}])], ignore_index=True)
            subjects.to_csv(SUBJECTS_FILE, index=False)
            st.success("✅ Subject added successfully")
        else:
            st.warning("Please fill all fields")

# ----------------------
# ATTENDANCE DOWNLOAD TAB
# ----------------------
with tab[3]:
    st.subheader("📥 Download Attendance")
    if os.path.exists(ATTENDANCE_FILE):
        attendance = pd.read_csv(ATTENDANCE_FILE)
        st.dataframe(attendance)
        csv = attendance.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Attendance CSV",
            data=csv,
            file_name=f"attendance_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime='text/csv'
        )
    else:
        st.info("No attendance data found yet")
