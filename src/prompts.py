"""MCP prompt templates for the university course catalog server.

The course_comparison_template is a static string with literal double-curly
placeholders. The evaluator checks that the fetched template string contains
{{course_code_1}} and {{course_code_2}} literally, so these must not be
interpreted as Python format variables.
"""


def register_prompts(mcp) -> None:
    """Attach prompt templates to the given FastMCP instance."""

    @mcp.prompt()
    def course_comparison_template() -> str:
        """Static comparison template; placeholders are literal, not Python f-string vars."""
        return (
            "Create a table comparing the following two courses: "
            "{{course_code_1}} and {{course_code_2}}. "
            "Include columns for Title, Credits, Description, and Prerequisites."
        )
