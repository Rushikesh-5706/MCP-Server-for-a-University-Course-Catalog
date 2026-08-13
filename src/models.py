"""SQLAlchemy ORM models matching the catalog schema exactly.

Column names, table names, and FK constraints are fixed by the spec — do not rename.
"""

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    instructors: Mapped[list["Instructor"]] = relationship(
        "Instructor", back_populates="department"
    )
    courses: Mapped[list["Course"]] = relationship(
        "Course", back_populates="department"
    )


class Instructor(Base):
    __tablename__ = "instructors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    office: Mapped[str | None] = mapped_column(Text, nullable=True)
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=False
    )

    department: Mapped["Department"] = relationship(
        "Department", back_populates="instructors"
    )
    courses: Mapped[list["Course"]] = relationship(
        "Course", back_populates="instructor"
    )


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    instructor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("instructors.id"), nullable=False
    )
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=False
    )

    instructor: Mapped["Instructor"] = relationship(
        "Instructor", back_populates="courses"
    )
    department: Mapped["Department"] = relationship(
        "Department", back_populates="courses"
    )

    # Courses this course requires (direct prerequisites)
    prerequisites: Mapped[list["Prerequisite"]] = relationship(
        "Prerequisite",
        foreign_keys="Prerequisite.course_id",
        back_populates="course",
    )
    # Courses that list this course as a prerequisite
    required_by: Mapped[list["Prerequisite"]] = relationship(
        "Prerequisite",
        foreign_keys="Prerequisite.prerequisite_id",
        back_populates="prereq_course",
    )


class Prerequisite(Base):
    __tablename__ = "prerequisites"

    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), primary_key=True
    )
    prerequisite_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), primary_key=True
    )

    course: Mapped["Course"] = relationship(
        "Course", foreign_keys=[course_id], back_populates="prerequisites"
    )
    prereq_course: Mapped["Course"] = relationship(
        "Course", foreign_keys=[prerequisite_id], back_populates="required_by"
    )
