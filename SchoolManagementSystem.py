import json
from abc import ABC, abstractmethod
from pathlib import Path
from unicodedata import name

database = "school_database.json"
data = {"Students": [], "Teachers": []}

if Path(database).exists():
    with open(database, "r") as file:
        content = file.read()
        if content:
            data = json.loads(content)


def save():
    with open(database, "w") as file:
        json.dump(data, file, indent=4)


class Persons(ABC):

    @abstractmethod
    def get_roles(self) -> str:
        pass

    @abstractmethod
    def register(self):
        pass

    @abstractmethod
    def show_details(self):
        pass

    @staticmethod
    def validate_email(email):
        if "@" in email or "." in email:
            return True
        else:
            return False


class Students(Persons):

    def get_roles(self):
        return "Student"

    def register(self):
        name = input("Enter the name of the student: ")
        age = int(input("Enter the age of the student: "))
        grade = input("Enter the grade of the student: ")
        email = input("Enter the email of the student: ")
        roll_number = input("Enter the roll number of the student: ")

        if not Persons.validate_email(email):
            print("Inavlid email format. Please try again.")
            return

        for i in data["Students"]:
            if i["roll_number"] == roll_number:
                print("Roll number already exists. Please try again.")
                return

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

    def show_details(self):
        for student in data["Students"]:
            print(student)


class Teachers(Persons):

    def get_roles(self):
        return "Teacher"

    def register(self):
        name = input("Enter the name of the teacher: ")
        age = int(input("Enter the age of the teacher: "))
        subject = input("Enter the subject of the teacher: ")
        email = input("Enter the email of the teacher: ")
        employee_id = input("Enter the employee ID of the teacher: ")

        if not Persons.validate_email(email):
            print("Inavlid email format. Please try again.")
            return

        for i in data["Teachers"]:
            if i["employee_id"] == employee_id:
                print("Employee ID already exists. Please try again.")
                return

        data["Teachers"].append(
            {
                "name": name,
                "age": age,
                "subject": subject,
                "email": email,
                "employee_id": employee_id,
            }
        )

    def show_details(self):
        for teacher in data["Teachers"]:
            print(teacher)


teach = Teachers()
stud = Students()

print("Press 1 to register a student")
print("Press 2 to register a teacher")
print("Press 3 to add grades")
print("Press 4 to show details of a student")
print("Press 5 to show details of a teacher")

choice = int(input("Enter your choice: "))


if choice == 1:
    stud.register()
elif choice == 2:
    teach.register()
elif choice == 3:
    roll_number = input("Enter the roll number of the student: ")
    subject = input("Enter the subject: ")
    grade = input("Enter the grade: ")

    for student in data["Students"]:
        if student["roll_number"] == roll_number:
            student["grades"][subject] = grade
            print(f"Grade {grade} added for {subject} to student {student['name']}.")
            break
    else:
        print("Student not found.")

elif choice == 4:
    roll_number = input("Enter the roll number of the student: ")
    for student in data["Students"]:
        if student["roll_number"] == roll_number:
            print(student)
            break
    else:
        print("Student not found.")

elif choice == 5:
    employee_id = input("Enter the employee ID of the teacher: ")
    for teacher in data["Teachers"]:
        if teacher["employee_id"] == employee_id:
            print(teacher)
            break
    else:
        print("Teacher not found.")
