import os
from google.adk.agents import Agent
from .config import MODEL
from .prompts import SYSTEM_INSTRUCTION
from .tools.case_file import open_case, update_case
from .tools.evidence import search_habitability_evidence
from .tools.statutes import match_statutes
from .tools.funds import match_relief_funds
from .tools.brief import finalize_brief
from .tools.tract import get_tract_context, find_tract_for_block

tools = [
    open_case,
    update_case,
    search_habitability_evidence,
    match_statutes,
    match_relief_funds,
    finalize_brief,
    get_tract_context,
    find_tract_for_block,
]

# If TOOLBOX_URL is set, connect via MCPToolset
toolbox_url = os.environ.get("TOOLBOX_URL")
if toolbox_url:
    try:
        from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams
        toolbox = MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=toolbox_url + "/mcp",
                headers={"Authorization": f"Bearer {os.environ.get('TOOLBOX_ID_TOKEN', '')}"},
            ),
            tool_filter=["get_tract_context", "find_tract_for_block", "list_relief_programs"],
        )
        tools.append(toolbox)
    except Exception as e:
        print(f"Warning: could not attach MCPToolset: {e}")

root_agent = Agent(
    name="stabilization_navigator",
    model=MODEL,
    description="Eviction-prevention intake navigator for NYC legal-aid paralegals.",
    instruction=SYSTEM_INSTRUCTION,
    tools=tools,
)
