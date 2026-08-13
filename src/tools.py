"""Tool implementations for the university course catalog MCP server.

Each function validates its input with the corresponding Pydantic model before
touching the database. Business-logic failures return structured dicts rather
than raising exceptions, so the MCP client always gets a usable response.

Tools are registered onto the `mcp` instance imported from src.main. The import
of this module in main.py is what triggers registration (decorator side-effects).
"""



import networkx as nx
from sqlalchemy import func

from src.database import SessionLocal
from src.models import Course, Department, Instructor, Prerequisite
from src.schemas import (
    CourseResult,
    GetPrerequisiteGraphInput,
    GetPrerequisitesInput,
    GraphEdge,
    GraphNode,
    InstructorResult,
    LookupInstructorInput,
    PrerequisiteGraphResult,
    PrerequisiteItem,
    PrerequisitesResult,
    SearchCoursesInput,
)


def _get_mcp():
    # Deferred import to avoid circular: tools.py is imported by main.py,
    # which defines `mcp`. Importing main here would recurse.
    from src.main import mcp
    return mcp


def register_tools(mcp) -> None:
    """Attach all tool functions to the given FastMCP instance."""

    @mcp.tool()
    def search_courses(query: str, department_code: str | None = None) -> list[dict]:
        """Search courses by title/description substring, optionally filtered by department code."""
        validated = SearchCoursesInput(query=query, department_code=department_code)

        session = SessionLocal()
        try:
            q = session.query(Course)

            if validated.department_code:
                q = q.join(Department).filter(
                    func.upper(Department.code) == validated.department_code.upper()
                )

            pattern = f"%{validated.query}%"
            q = q.filter(
                func.lower(Course.title).contains(validated.query.lower())
                | func.lower(Course.description).contains(validated.query.lower())
            )

            results = q.all()
            return [
                CourseResult(
                    course_code=c.course_code,
                    title=c.title,
                    credits=c.credits,
                ).model_dump()
                for c in results
            ]
        finally:
            session.close()

    @mcp.tool()
    def get_prerequisites(course_code: str) -> PrerequisitesResult:
        """Return the direct prerequisites for a course.

        Returns a PrerequisitesResult with an error field set if the course_code is not found.
        Returns an empty prerequisites list for courses with no prerequisites.
        """
        validated = GetPrerequisitesInput(course_code=course_code)

        session = SessionLocal()
        try:
            course = (
                session.query(Course)
                .filter(
                    func.upper(Course.course_code)
                    == validated.course_code.upper()
                )
                .first()
            )
            if course is None:
                return PrerequisitesResult(error="Course not found")

            prereq_rows = (
                session.query(Prerequisite)
                .filter(Prerequisite.course_id == course.id)
                .all()
            )

            prereq_items = []
            for row in prereq_rows:
                prereq_course = (
                    session.query(Course).filter(Course.id == row.prerequisite_id).first()
                )
                if prereq_course:
                    prereq_items.append(
                        PrerequisiteItem(
                            course_code=prereq_course.course_code,
                            title=prereq_course.title,
                        )
                    )

            return PrerequisitesResult(
                course_code=course.course_code,
                prerequisites=prereq_items,
            )
        finally:
            session.close()

    @mcp.tool()
    def lookup_instructor(instructor_name: str) -> InstructorResult:
        """Return contact and department info for an instructor by name (case-insensitive).

        Returns an InstructorResult with error field set if no instructor matches.
        """
        validated = LookupInstructorInput(instructor_name=instructor_name)

        session = SessionLocal()
        try:
            instructor = (
                session.query(Instructor)
                .filter(
                    func.lower(Instructor.name).contains(
                        validated.instructor_name.lower()
                    )
                )
                .first()
            )
            if instructor is None:
                return InstructorResult(error="Instructor not found")

            dept = session.query(Department).filter(
                Department.id == instructor.department_id
            ).first()

            return InstructorResult(
                name=instructor.name,
                email=instructor.email,
                department_name=dept.name if dept else "",
            )
        finally:
            session.close()

    @mcp.tool()
    def get_prerequisite_graph(course_code: str) -> PrerequisiteGraphResult:
        """Build and return the full transitive prerequisite graph for a course.

        Uses NetworkX to compute ancestors. Edges run source→target where source
        is a prerequisite of target. Returns a PrerequisiteGraphResult with error
        field set for unknown courses.
        """
        validated = GetPrerequisiteGraphInput(course_code=course_code)

        session = SessionLocal()
        try:
            root = (
                session.query(Course)
                .filter(
                    func.upper(Course.course_code)
                    == validated.course_code.upper()
                )
                .first()
            )
            if root is None:
                return PrerequisiteGraphResult(error="Course not found")

            # Load all prerequisite edges from the DB into a directed graph.
            # Edge direction: prerequisite_id → course_id  (prereq is required for course)
            all_prereqs = session.query(Prerequisite).all()

            # Map course id → course_code for labelling
            all_courses = session.query(Course).all()
            id_to_code: dict[int, str] = {c.id: c.course_code for c in all_courses}

            G = nx.DiGraph()
            for p in all_prereqs:
                src = id_to_code[p.prerequisite_id]
                tgt = id_to_code[p.course_id]
                G.add_edge(src, tgt)

            # Ensure the root node exists even if it has no prerequisites
            if root.course_code not in G:
                G.add_node(root.course_code)

            ancestor_codes = nx.ancestors(G, root.course_code)
            relevant_nodes = ancestor_codes | {root.course_code}

            # Subgraph restricted to relevant nodes
            sub = G.subgraph(relevant_nodes)

            nodes = [GraphNode(id=n) for n in sub.nodes()]
            edges = [
                GraphEdge(source=u, target=v)
                for u, v in sub.edges()
            ]

            return PrerequisiteGraphResult(nodes=nodes, edges=edges)
        finally:
            session.close()
