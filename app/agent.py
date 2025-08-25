import json
import os
import requests
import asyncio
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_mcp_adapters.client import MultiServerMCPClient

# --- Configuration ---
LOCAL_TOOL_SERVER_URL = "http://backend:8000/tools"
PLAYWRIGHT_MCP_URL = "http://playwright:8931/mcp"
GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"


# --- Tool Implementations ---

def local_document_search(query: str) -> str:
    """
    Searches the company's internal documents.
    This tool remains a standard REST call, not an MCP tool.
    """
    try:
        response = requests.post(f"{LOCAL_TOOL_SERVER_URL}/search", json={"query": query})
        response.raise_for_status()
        return response.json().get("results", "No results found.")
    except requests.exceptions.RequestException as e:
        return f"Error calling local search API: {e}"

# --- MCP Client Setup ---

def get_mcp_client() -> MultiServerMCPClient:
    """
    Creates and configures the MultiServerMCPClient.
    """
    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat:
        print("Warning: GITHUB_PAT environment variable not set. GitHub tool will not be available.")
        return MultiServerMCPClient({"playwright": {"transport": "streamable_http", "url": PLAYWRIGHT_MCP_URL}})

    return MultiServerMCPClient({
        "github": {"transport": "streamable_http", "url": GITHUB_MCP_URL, "headers": {"Authorization": f"Bearer {github_pat}"}},
        "playwright": {"transport": "streamable_http", "url": PLAYWRIGHT_MCP_URL},
    })

mcp_client = get_mcp_client()

# --- Tool Loading ---

def get_tools() -> list[Tool]:
    """
    Initializes all tools for the agent. Synchronous wrapper for async call.
    """
    local_search_tool = Tool(
        name="local_document_search",
        func=local_document_search,
        description="Searches the company's internal documents (manuals, specs, reports)."
    )
    try:
        mcp_tools = asyncio.run(mcp_client.get_tools())
        print(f"Successfully loaded {len(mcp_tools)} tools from MCP servers.")
    except Exception as e:
        print(f"Error loading MCP tools: {e}. Proceeding with local tools only.")
        mcp_tools = []
    return [local_search_tool] + mcp_tools

# --- Agent Creation ---

def create_agent_executor() -> AgentExecutor:
    """
    Creates the LangChain agent.
    """
    print("--- Creating Agent Executor ---")
    prompt_template = """
    You are a helpful assistant. You have access to a suite of tools to find information.
    Decide which tool is most appropriate for the user's question. You can search internal documents, search GitHub, or browse a specific website.

    {tools}

    When you use a tool, it will return a JSON object with two keys: 'content_for_llm' and 'sources'.
    Use the 'content_for_llm' to formulate your answer.
    Your final answer MUST be a JSON object with two keys: 'answer' and 'sources'.
    The 'sources' key must contain the exact list of source objects that the tool provided.

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer. I will format it as a JSON object.
    Final Answer: {{"answer": "your natural language answer here", "sources": [ ... list of source objects ... ]}}

    Begin!

    Question: {input}
    Thought:{agent_scratchpad}
    """
    prompt = PromptTemplate.from_template(prompt_template)

    # Import manager here to avoid circular dependencies at startup
    from .llm_manager import llm_manager

    # Get the LLM from the central manager
    llm = llm_manager.get_llm()

    tools = get_tools()

    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    return agent_executor
