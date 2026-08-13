"""Smoke-test script for the University Course Catalog MCP server.

Run this against a locally running server (python src/main.py &) to verify
that all tools, resources, and the prompt template return the expected data.

Usage:
    python src/main.py &
    python scripts/verify_server.py
"""

import asyncio
import json
import sys

from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession


MCP_URL = "http://localhost:8080/mcp"
HEALTH_URL = "http://localhost:8080/health"

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

failures = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  [{PASS}] {label}")
    else:
        print(f"  [{FAIL}] {label}" + (f": {detail}" if detail else ""))
        failures.append(label)


async def verify_health() -> None:
    import urllib.request
    print("\n-- Health endpoint --")
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=5) as resp:
            status = resp.status
            body = json.loads(resp.read())
        check("/health returns 200", status == 200, str(status))
        check('/health body is {"status":"ok"}', body == {"status": "ok"}, str(body))
    except Exception as e:
        check("/health reachable", False, str(e))


async def verify_all() -> None:
    async with streamable_http_client(MCP_URL) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()

            # -- tools/list --
            print("\n-- tools/list --")
            tools = await session.list_tools()
            tool_names = {t.name for t in tools.tools}
            expected_tools = {
                "search_courses",
                "get_prerequisites",
                "lookup_instructor",
                "get_prerequisite_graph",
            }
            for name in expected_tools:
                check(f"tool '{name}' registered", name in tool_names)

            # -- resources/list --
            print("\n-- resources/list --")
            resources = await session.list_resources()
            res_names = {res.name for res in resources.resources}
            check("resource 'course_descriptions' registered", "course_descriptions" in res_names)
            check("resource 'department_directory' registered", "department_directory" in res_names)

            # -- prompts/list --
            print("\n-- prompts/list --")
            prompts = await session.list_prompts()
            prompt_names = {p.name for p in prompts.prompts}
            check("prompt 'course_comparison_template' registered", "course_comparison_template" in prompt_names)

            # -- search_courses: "Introduction" --
            print("\n-- search_courses(query='Introduction') --")
            result = await session.call_tool("search_courses", {"query": "Introduction"})
            results_data = [json.loads(c.text) for c in result.content]
            codes = {r["course_code"] for r in results_data}
            check("returns CS101", "CS101" in codes, str(codes))
            check("returns PHYS101", "PHYS101" in codes, str(codes))
            check("exactly 2 results", len(results_data) == 2, str(len(results_data)))

            # -- search_courses: nonsense query returns [] --
            print("\n-- search_courses(query='xyzzy_nonexistent') --")
            result2 = await session.call_tool("search_courses", {"query": "xyzzy_nonexistent_abc"})
            check("empty list returned (no content items)", len(result2.content) == 0, str(len(result2.content)))

            # -- get_prerequisites: CS301 -> CS201 only --
            print("\n-- get_prerequisites(course_code='CS301') --")
            result3 = await session.call_tool("get_prerequisites", {"course_code": "CS301"})
            data3 = json.loads(result3.content[0].text)
            check("course_code is CS301", data3["course_code"] == "CS301", str(data3.get("course_code")))
            prereqs3 = [p["course_code"] for p in data3["prerequisites"]]
            check("exactly 1 direct prerequisite", len(prereqs3) == 1, str(prereqs3))
            check("CS201 is the prerequisite", "CS201" in prereqs3, str(prereqs3))

            # -- get_prerequisites: CS101 -> empty list --
            print("\n-- get_prerequisites(course_code='CS101') --")
            result4 = await session.call_tool("get_prerequisites", {"course_code": "CS101"})
            data4 = json.loads(result4.content[0].text)
            check("course_code is CS101", data4["course_code"] == "CS101")
            check("prerequisites is empty list", data4["prerequisites"] == [], str(data4["prerequisites"]))

            # -- lookup_instructor: Sarah Chen --
            print("\n-- lookup_instructor(instructor_name='Sarah Chen') --")
            result5 = await session.call_tool("lookup_instructor", {"instructor_name": "Sarah Chen"})
            data5 = json.loads(result5.content[0].text)
            check("name is Dr. Sarah Chen", data5.get("name") == "Dr. Sarah Chen", str(data5.get("name")))
            check("email is s.chen@university.edu", data5.get("email") == "s.chen@university.edu", str(data5.get("email")))
            check("department_name is Computer Science", data5.get("department_name") == "Computer Science", str(data5.get("department_name")))

            # -- lookup_instructor: unknown name --
            print("\n-- lookup_instructor(instructor_name='Nobody Here') --")
            result6 = await session.call_tool("lookup_instructor", {"instructor_name": "Nobody Here"})
            data6 = json.loads(result6.content[0].text)
            check("returns error key", "error" in data6, str(data6))
            check("error is 'Instructor not found'", data6.get("error") == "Instructor not found", str(data6.get("error")))

            # -- get_prerequisite_graph: CS401 --
            print("\n-- get_prerequisite_graph(course_code='CS401') --")
            result7 = await session.call_tool("get_prerequisite_graph", {"course_code": "CS401"})
            data7 = json.loads(result7.content[0].text)
            node_ids = {n["id"] for n in data7["nodes"]}
            expected_nodes = {"CS401", "CS301", "CS201", "CS101", "MATH201", "MATH101"}
            check("6 nodes in graph", len(node_ids) == 6, str(sorted(node_ids)))
            check("all expected nodes present", node_ids == expected_nodes, str(sorted(node_ids)))
            edges_set = {(e["source"], e["target"]) for e in data7["edges"]}
            expected_edges = {
                ("CS101", "CS201"),
                ("CS201", "CS301"),
                ("CS301", "CS401"),
                ("MATH101", "MATH201"),
                ("MATH201", "CS401"),
            }
            check("5 edges in graph", len(edges_set) == 5, str(len(edges_set)))
            check("all expected edges present", expected_edges == edges_set, str(sorted(edges_set)))

            # -- course_descriptions resource --
            print("\n-- resource: course_descriptions --")
            cd = await session.read_resource("catalog://course_descriptions")
            cd_text = cd.contents[0].text
            check("[CS101] line present", "[CS101] Introduction to Programming:" in cd_text)
            check("[MATH101] line present", "[MATH101] Calculus I:" in cd_text)
            check("10 course lines", cd_text.count("\n") == 9, str(cd_text.count("\n")))

            # -- department_directory resource --
            print("\n-- resource: department_directory --")
            dd = await session.read_resource("catalog://department_directory")
            dd_text = dd.contents[0].text
            check("Computer Science (CS) present", "Computer Science (CS)" in dd_text)
            check("Mathematics (MATH) present", "Mathematics (MATH)" in dd_text)
            check("Physics (PHYS) present", "Physics (PHYS)" in dd_text)

            # -- prompt template --
            print("\n-- prompt: course_comparison_template --")
            pt = await session.get_prompt("course_comparison_template", {})
            pt_text = pt.messages[0].content.text
            check("{{course_code_1}} literal present", "{{course_code_1}}" in pt_text, repr(pt_text))
            check("{{course_code_2}} literal present", "{{course_code_2}}" in pt_text, repr(pt_text))


async def main() -> None:
    print("=" * 60)
    print("University Course Catalog MCP Server — Verification")
    print("=" * 60)

    await verify_health()

    try:
        await verify_all()
    except Exception as e:
        print(f"\n[{FAIL}] Unexpected error: {e}")
        failures.append(f"Unexpected error: {e}")
        raise

    print("\n" + "=" * 60)
    if failures:
        print(f"RESULT: {len(failures)} check(s) FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("RESULT: All checks passed.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
