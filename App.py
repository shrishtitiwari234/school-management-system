import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------
st.set_page_config(page_title="School Management", page_icon="🎓", layout="wide")

st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 16px 20px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Data layer (same JSON file/format as the original console version)
# --------------------------------------------------------------------------
DATABASE = Path(__file__).resolve().parent.parent / "school_database.json"


def load_data() -> dict:
    data = {"Students": [], "Teachers": []}
    if DATABASE.exists():
        content = DATABASE.read_text()
        if content.strip():
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                st.error(
                    "school_database.json is not valid JSON. Fix or delete the file and reload."
                )
                st.stop()
    data.setdefault("Students", [])
    data.setdefault("Teachers", [])
    return data


def save_data(data: dict) -> None:
    with open(DATABASE, "w") as file:
        json.dump(data, file, indent=4)


# --------------------------------------------------------------------------
# Domain classes
# --------------------------------------------------------------------------
class Persons(ABC):
    """Base class. register() returns (success: bool, message: str)."""

    @abstractmethod
    def get_roles(self) -> str:
        pass

    @abstractmethod
    def register(self, data: dict, **fields) -> tuple[bool, str]:
        pass

    @abstractmethod
    def show_details(self, data: dict) -> pd.DataFrame:
        pass

    @staticmethod
    def validate_email(email: str) -> bool:
        return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


class Students(Persons):
    def get_roles(self) -> str:
        return "Student"

    def register(self, data, **fields):
        name = fields.get("name", "")
        age_value = fields.get("age")
        grade = fields.get("grade", "")
        email = fields.get("email", "")
        roll_number = fields.get("roll_number", "")
        name, grade, email, roll_number = (
            name.strip(),
            grade.strip(),
            email.strip(),
            roll_number.strip(),
        )
        if not all([name, grade, email, roll_number]):
            return False, "Please fill in all fields."
        if age_value is None:
            return False, "Please enter a valid age."
        try:
            age = int(age_value)
        except (TypeError, ValueError):
            return False, "Age must be a valid number."
        if age < 0:
            return False, "Age cannot be negative."
        if not self.validate_email(email):
            return False, "Invalid email format. Please try again."
        if any(s["roll_number"] == roll_number for s in data["Students"]):
            return False, "Roll number already exists. Please try again."

        data["Students"].append(
            {
                "name": name,
                "age": age,
                "grade": grade,
                "email": email,
                "roll_number": roll_number,
                "grades": {},
            }
        )
        save_data(data)
        return True, f"Student **{name}** registered successfully."

    def add_grade(self, data, roll_number, subject, grade):
        subject, grade = subject.strip(), grade.strip()
        if not subject or not grade:
            return False, "Please enter both a subject and a grade."
        for student in data["Students"]:
            if student["roll_number"] == roll_number:
                student.setdefault("grades", {})[subject] = grade
                save_data(data)
                return (
                    True,
                    f"Grade **{grade}** saved for **{subject}** ({student['name']}).",
                )
        return False, "Student not found."

    def delete(self, data, roll_number):
        data["Students"] = [
            s for s in data["Students"] if s["roll_number"] != roll_number
        ]
        save_data(data)

    def show_details(self, data):
        rows = [
            {
                "Roll No": s.get("roll_number", ""),
                "Name": s.get("name", ""),
                "Age": s.get("age", ""),
                "Class": s.get("grade", ""),
                "Email": s.get("email", ""),
                "Subjects Graded": len(s.get("grades", {})),
            }
            for s in data["Students"]
        ]
        return pd.DataFrame(rows)


class Teachers(Persons):
    def get_roles(self) -> str:
        return "Teacher"

    def register(self, data, **fields):
        name = fields.get("name", "")
        age_value = fields.get("age")
        subject = fields.get("subject", "")
        email = fields.get("email", "")
        employee_id = fields.get("employee_id", "")
        name, subject, email, employee_id = (
            name.strip(),
            subject.strip(),
            email.strip(),
            employee_id.strip(),
        )
        if not all([name, subject, email, employee_id]):
            return False, "Please fill in all fields."
        if age_value is None:
            return False, "Please enter a valid age."
        try:
            age = int(age_value)
        except (TypeError, ValueError):
            return False, "Age must be a valid number."
        if age < 0:
            return False, "Age cannot be negative."
        if not self.validate_email(email):
            return False, "Invalid email format. Please try again."
        if any(t["employee_id"] == employee_id for t in data["Teachers"]):
            return False, "Employee ID already exists. Please try again."

        data["Teachers"].append(
            {
                "name": name,
                "age": age,
                "subject": subject,
                "email": email,
                "employee_id": employee_id,
            }
        )
        save_data(data)
        return True, f"Teacher **{name}** registered successfully."

    def delete(self, data, employee_id):
        data["Teachers"] = [
            t for t in data["Teachers"] if t["employee_id"] != employee_id
        ]
        save_data(data)

    def show_details(self, data):
        rows = [
            {
                "Employee ID": t.get("employee_id", ""),
                "Name": t.get("name", ""),
                "Age": t.get("age", ""),
                "Subject": t.get("subject", ""),
                "Email": t.get("email", ""),
            }
            for t in data["Teachers"]
        ]
        return pd.DataFrame(rows)


student_mgr = Students()
teacher_mgr = Teachers()

# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------


def show_table(df: pd.DataFrame):
    """st.dataframe wrapper that works on old and new Streamlit versions."""
    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except TypeError:
        try:
            st.dataframe(df, hide_index=True)
        except TypeError:
            st.dataframe(df)


def flash(ok: bool, message: str):
    (st.success if ok else st.error)(message, icon="✅" if ok else "⚠️")


def page_dashboard(data):
    st.title("📊 Dashboard")
    st.caption("A quick overview of your school.")

    students_df = student_mgr.show_details(data)
    teachers_df = teacher_mgr.show_details(data)

    graded = sum(1 for s in data["Students"] if s.get("grades"))
    c1, c2, c3 = st.columns(3)
    c1.metric("Students", len(data["Students"]))
    c2.metric("Teachers", len(data["Teachers"]))
    c3.metric("Students with grades", graded)

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Students per class")
        if students_df.empty:
            st.info("No students registered yet.")
        else:
            st.bar_chart(students_df["Class"].value_counts())
    with right:
        st.subheader("Teachers per subject")
        if teachers_df.empty:
            st.info("No teachers registered yet.")
        else:
            st.bar_chart(teachers_df["Subject"].value_counts())


def page_register_student(data):
    st.title("🧑‍🎓 Register Student")
    with st.form("student_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name")
        roll_number = c2.text_input("Roll number")
        age = c1.number_input("Age", min_value=3, max_value=100, value=15, step=1)
        grade = c2.text_input("Class / Grade", placeholder="e.g. 10")
        email = st.text_input("Email", placeholder="student@example.com")
        submitted = st.form_submit_button("Register student", type="primary")

    if submitted:
        ok, msg = student_mgr.register(
            data,
            name=name,
            age=age,
            grade=grade,
            email=email,
            roll_number=roll_number,
        )
        flash(ok, msg)


def page_register_teacher(data):
    st.title("👩‍🏫 Register Teacher")
    with st.form("teacher_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name")
        employee_id = c2.text_input("Employee ID")
        age = c1.number_input("Age", min_value=18, max_value=100, value=30, step=1)
        subject = c2.text_input("Subject", placeholder="e.g. Mathematics")
        email = st.text_input("Email", placeholder="teacher@example.com")
        submitted = st.form_submit_button("Register teacher", type="primary")

    if submitted:
        ok, msg = teacher_mgr.register(
            data,
            name=name,
            age=age,
            subject=subject,
            email=email,
            employee_id=employee_id,
        )
        flash(ok, msg)


def page_add_grades(data):
    st.title("📝 Add Grades")
    if not data["Students"]:
        st.info("Register a student first.")
        return

    options = {
        f"{s['roll_number']} — {s['name']}": s["roll_number"] for s in data["Students"]
    }
    with st.form("grade_form", clear_on_submit=True):
        chosen = st.selectbox("Student", list(options.keys()))
        c1, c2 = st.columns(2)
        subject = c1.text_input("Subject", placeholder="e.g. Science")
        grade = c2.text_input("Grade", placeholder="e.g. A, B+, 85")
        submitted = st.form_submit_button("Save grade", type="primary")

    if submitted:
        ok, msg = student_mgr.add_grade(data, options[chosen], subject, grade)
        flash(ok, msg)


def page_student_records(data):
    st.title("📚 Student Records")
    df = student_mgr.show_details(data)
    if df.empty:
        st.info("No students registered yet.")
        return

    query = st.text_input("🔍 Search by name, roll number or class")
    if query:
        mask = df.apply(
            lambda row: query.lower() in " ".join(map(str, row)).lower(), axis=1
        )
        df = df[mask]

    show_table(df)
    st.caption(f"{len(df)} student(s) shown")

    st.divider()
    st.subheader("Student details")
    options = {f"{s['roll_number']} — {s['name']}": s for s in data["Students"]}
    chosen = st.selectbox("Select a student", list(options.keys()))
    student = options[chosen]

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"**Name:** {student['name']}")
        st.markdown(f"**Age:** {student['age']}")
        st.markdown(f"**Class:** {student['grade']}")
        st.markdown(f"**Email:** {student['email']}")
        st.markdown(f"**Roll No:** {student['roll_number']}")
    with c2:
        grades = student.get("grades", {})
        if grades:
            show_table(
                pd.DataFrame(
                    {"Subject": list(grades.keys()), "Grade": list(grades.values())}
                )
            )
        else:
            st.info("No grades added yet.")

    with st.expander("Danger zone"):
        confirm = st.checkbox(
            "Yes, I want to delete this student", key="confirm_del_student"
        )
        if st.button("Delete student", disabled=not confirm):
            student_mgr.delete(data, student["roll_number"])
            st.toast("Student deleted.", icon="🗑️")
            st.rerun()


def page_teacher_records(data):
    st.title("🍎 Teacher Records")
    df = teacher_mgr.show_details(data)
    if df.empty:
        st.info("No teachers registered yet.")
        return

    query = st.text_input("🔍 Search by name, employee ID or subject")
    if query:
        mask = df.apply(
            lambda row: query.lower() in " ".join(map(str, row)).lower(), axis=1
        )
        df = df[mask]

    show_table(df)
    st.caption(f"{len(df)} teacher(s) shown")

    with st.expander("Danger zone"):
        options = {
            f"{t['employee_id']} — {t['name']}": t["employee_id"]
            for t in data["Teachers"]
        }
        chosen = st.selectbox("Select a teacher to delete", list(options.keys()))
        confirm = st.checkbox(
            "Yes, I want to delete this teacher", key="confirm_del_teacher"
        )
        if st.button("Delete teacher", disabled=not confirm):
            teacher_mgr.delete(data, options[chosen])
            st.toast("Teacher deleted.", icon="🗑️")
            st.rerun()


# --------------------------------------------------------------------------
# Navigation
# --------------------------------------------------------------------------
PAGES = {
    "📊 Dashboard": page_dashboard,
    "🧑‍🎓 Register Student": page_register_student,
    "👩‍🏫 Register Teacher": page_register_teacher,
    "📝 Add Grades": page_add_grades,
    "📚 Student Records": page_student_records,
    "🍎 Teacher Records": page_teacher_records,
}

with st.sidebar:
    st.title("🎓 School Manager")
    selection = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
    st.divider()
    st.caption("Data is stored in `school_database.json`")

PAGES[selection](load_data())
