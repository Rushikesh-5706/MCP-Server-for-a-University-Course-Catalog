"""Seed script for the course catalog database.

Run directly: python data/seed.py
Or call ensure_seeded() programmatically (idempotent).
"""

import sys
import os

# Allow running as `python data/seed.py` from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.database import SessionLocal, init_db
from src.models import Course, Department, Instructor, Prerequisite


DEPARTMENTS = [
    {"name": "Computer Science", "code": "CS"},
    {"name": "Mathematics", "code": "MATH"},
    {"name": "Physics", "code": "PHYS"},
]

INSTRUCTORS = [
    {
        "name": "Dr. Sarah Chen",
        "email": "s.chen@university.edu",
        "office": "Turing Hall 204",
        "dept_code": "CS",
    },
    {
        "name": "Dr. Michael Okafor",
        "email": "m.okafor@university.edu",
        "office": "Turing Hall 310",
        "dept_code": "CS",
    },
    {
        "name": "Dr. Elena Rodriguez",
        "email": "e.rodriguez@university.edu",
        "office": "Hilbert Building 112",
        "dept_code": "MATH",
    },
    {
        "name": "Dr. Priya Nair",
        "email": "p.nair@university.edu",
        "office": "Hilbert Building 208",
        "dept_code": "MATH",
    },
    {
        "name": "Dr. James Whitfield",
        "email": "j.whitfield@university.edu",
        "office": "Faraday Labs 5B",
        "dept_code": "PHYS",
    },
]

COURSES = [
    {
        "course_code": "CS101",
        "title": "Introduction to Programming",
        "credits": 3,
        "instructor_name": "Dr. Sarah Chen",
        "dept_code": "CS",
        "description": (
            "A foundational course covering variables, control flow, functions, "
            "and basic problem-solving using Python."
        ),
    },
    {
        "course_code": "CS201",
        "title": "Data Structures and Algorithms",
        "credits": 4,
        "instructor_name": "Dr. Michael Okafor",
        "dept_code": "CS",
        "description": (
            "Covers arrays, linked lists, trees, hash tables, sorting, and "
            "algorithmic complexity analysis."
        ),
    },
    {
        "course_code": "CS301",
        "title": "Database Systems",
        "credits": 3,
        "instructor_name": "Dr. Sarah Chen",
        "dept_code": "CS",
        "description": (
            "Introduces relational database design, SQL, normalization, and "
            "transaction management."
        ),
    },
    {
        "course_code": "CS302",
        "title": "Software Engineering",
        "credits": 3,
        "instructor_name": "Dr. Michael Okafor",
        "dept_code": "CS",
        "description": (
            "Covers software design principles, version control, testing strategies, "
            "and collaborative development practices."
        ),
    },
    {
        "course_code": "CS401",
        "title": "Artificial Intelligence",
        "credits": 4,
        "instructor_name": "Dr. Sarah Chen",
        "dept_code": "CS",
        "description": (
            "Explores search algorithms, knowledge representation, machine learning "
            "fundamentals, and intelligent agent design."
        ),
    },
    {
        "course_code": "MATH101",
        "title": "Calculus I",
        "credits": 4,
        "instructor_name": "Dr. Elena Rodriguez",
        "dept_code": "MATH",
        "description": (
            "Covers limits, derivatives, and integrals of single-variable functions "
            "with applications."
        ),
    },
    {
        "course_code": "MATH201",
        "title": "Linear Algebra",
        "credits": 3,
        "instructor_name": "Dr. Priya Nair",
        "dept_code": "MATH",
        "description": (
            "Covers vector spaces, matrices, eigenvalues, and linear transformations."
        ),
    },
    {
        "course_code": "MATH301",
        "title": "Discrete Mathematics",
        "credits": 3,
        "instructor_name": "Dr. Elena Rodriguez",
        "dept_code": "MATH",
        "description": (
            "Covers logic, set theory, combinatorics, and graph theory foundational "
            "to computer science."
        ),
    },
    {
        "course_code": "PHYS101",
        "title": "Introduction to Mechanics",
        "credits": 4,
        "instructor_name": "Dr. James Whitfield",
        "dept_code": "PHYS",
        "description": (
            "Covers kinematics, Newton's laws, energy, and momentum through "
            "classical mechanics."
        ),
    },
    {
        "course_code": "PHYS201",
        "title": "Electromagnetism",
        "credits": 4,
        "instructor_name": "Dr. James Whitfield",
        "dept_code": "PHYS",
        "description": (
            "Covers electric and magnetic fields, circuits, and Maxwell's equations."
        ),
    },
]

# (course_code, prerequisite_code)
PREREQUISITES = [
    ("CS201", "CS101"),
    ("CS301", "CS201"),
    ("CS302", "CS201"),
    ("CS401", "CS301"),
    ("CS401", "MATH201"),
    ("MATH201", "MATH101"),
    ("MATH301", "MATH101"),
    ("PHYS101", "MATH101"),
    ("PHYS201", "PHYS101"),
]


def ensure_seeded() -> None:
    """Insert seed data only if the departments table is empty."""
    init_db()
    session = SessionLocal()
    try:
        if session.query(Department).count() > 0:
            return

        # Departments
        dept_map: dict[str, Department] = {}
        for d in DEPARTMENTS:
            dept = Department(name=d["name"], code=d["code"])
            session.add(dept)
            dept_map[d["code"]] = dept
        session.flush()

        # Instructors
        instructor_map: dict[str, Instructor] = {}
        for i in INSTRUCTORS:
            dept = dept_map[i["dept_code"]]
            inst = Instructor(
                name=i["name"],
                email=i["email"],
                office=i["office"],
                department_id=dept.id,
            )
            session.add(inst)
            instructor_map[i["name"]] = inst
        session.flush()

        # Courses
        course_map: dict[str, Course] = {}
        for c in COURSES:
            dept = dept_map[c["dept_code"]]
            inst = instructor_map[c["instructor_name"]]
            course = Course(
                course_code=c["course_code"],
                title=c["title"],
                description=c["description"],
                credits=c["credits"],
                instructor_id=inst.id,
                department_id=dept.id,
            )
            session.add(course)
            course_map[c["course_code"]] = course
        session.flush()

        # Prerequisites
        for course_code, prereq_code in PREREQUISITES:
            prereq_row = Prerequisite(
                course_id=course_map[course_code].id,
                prerequisite_id=course_map[prereq_code].id,
            )
            session.add(prereq_row)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    ensure_seeded()
    print("Seed complete.")
