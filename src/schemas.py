"""Pydantic input and output models for all four MCP tools.

These are used inside tool functions to validate inputs at the boundary,
not as FastMCP parameter schemas (FastMCP reads function signatures for that).
"""

from pydantic import BaseModel



# ── search_courses ──────────────────────────────────────────────────────────


class SearchCoursesInput(BaseModel):
    query: str
    department_code: str | None = None


class CourseResult(BaseModel):
    course_code: str
    title: str
    credits: int


# ── get_prerequisites ───────────────────────────────────────────────────────


class GetPrerequisitesInput(BaseModel):
    course_code: str


class PrerequisiteItem(BaseModel):
    course_code: str
    title: str


class PrerequisitesResult(BaseModel):
    course_code: str | None = None
    prerequisites: list[PrerequisiteItem] | None = None
    error: str | None = None


# ── lookup_instructor ───────────────────────────────────────────────────────


class LookupInstructorInput(BaseModel):
    instructor_name: str


class InstructorResult(BaseModel):
    name: str | None = None
    email: str | None = None
    department_name: str | None = None
    error: str | None = None


# ── get_prerequisite_graph ──────────────────────────────────────────────────


class GetPrerequisiteGraphInput(BaseModel):
    course_code: str


class GraphNode(BaseModel):
    id: str


class GraphEdge(BaseModel):
    source: str
    target: str


class PrerequisiteGraphResult(BaseModel):
    nodes: list[GraphNode] | None = None
    edges: list[GraphEdge] | None = None
    error: str | None = None
