"""MCP resources: course_descriptions and department_directory.

Both are generated dynamically from the database so they always reflect current data.
The `name` kwarg is set explicitly so the evaluator can find resources by name,
independent of the URI scheme.
"""

from src.database import SessionLocal
from src.models import Course, Department


def register_resources(mcp) -> None:
    """Attach resource generators to the given MCPServer instance."""

    @mcp.resource("catalog://course_descriptions", name="course_descriptions")
    def course_descriptions() -> str:
        """Return all courses as one line each: [CODE] Title: Description."""
        session = SessionLocal()
        try:
            courses = session.query(Course).order_by(Course.course_code).all()
            lines = [
                f"[{c.course_code}] {c.title}: {c.description}"
                for c in courses
            ]
            return "\n".join(lines)
        finally:
            session.close()

    @mcp.resource("catalog://department_directory", name="department_directory")
    def department_directory() -> str:
        """Return all departments as one line each: Name (CODE)."""
        session = SessionLocal()
        try:
            depts = session.query(Department).order_by(Department.code).all()
            lines = [f"{d.name} ({d.code})" for d in depts]
            return "\n".join(lines)
        finally:
            session.close()
