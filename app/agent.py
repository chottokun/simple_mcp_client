import requests
import json
import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

# --- Configuration ---
LOCAL_TOOL_SERVER_URL = "http://backend:8000/tools"
GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"

# --- Tool Implementations ---

def local_document_search(query: str) -> str:
    """
    Searches the company's internal documents.
    """
    try:
        response = requests.post(
            f"{LOCAL_TOOL_SERVER_URL}/search",
            json={"query": query}
        )
        response.raise_for_status()
        return response.json().get("results", "No results found.")
    except requests.exceptions.RequestException as e:
        return f"Error calling local search API: {e}"

def search_github_repositories(query: str) -> str:
    """
    Searches for repositories on GitHub using the official GitHub MCP server.
    """
    github_token = os.getenv("GITHUB_PAT")
    if not github_token:
        return json.dumps({
            "error": "GITHUB_PAT environment variable not set. Please set it to a valid GitHub Personal Access Token.",
            "sources": []
        })

    try:
        payload = {
            "tool": "search_repositories",
            "input": {"query": query}
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {github_token}"
        }
        response = requests.post(GITHUB_MCP_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        raw_results = response.json()

        if not raw_results:
            return json.dumps({"content_for_llm": "No repositories found on GitHub for that query.", "sources": []})

        sources_list = []
        content_list = []
        for result in raw_results[:5]: # Limit to top 5 results for brevity
            repo_name = result.get('full_name', 'N/A')
            description = result.get('description', 'No description.')
            url = result.get('html_url', '#')

            sources_list.append({"document_name": repo_name, "snippet": description})
            content_list.append(f"Repo: {repo_name}\nURL: {url}\nDescription: {description}")

        return json.dumps({
            "content_for_llm": "\n\n---\n\n".join(content_list),
            "sources": sources_list
        })

    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"Error calling GitHub API: {e}", "sources": []})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {e}", "sources": []})


def get_tools():
    """
    Initializes all tools for the agent.
    """
    local_search_tool = Tool(
        name="local_document_search",
        func=local_document_search,
        description="Searches the company's internal documents (manuals, specs, reports). Use this for questions about internal projects, policies, and procedures."
    )
    github_tool = Tool(
        name="search_github_repositories",
        func=search_github_repositories,
        description="Searches for public repositories on GitHub. Use this to find code, projects, or libraries related to a specific topic."
    )
    return [local_search_tool, github_tool]

def create_agent_executor():
    """
    Creates the LangChain agent, including its prompt, LLM, and tools.
    """
    prompt_template = """
    You are a helpful assistant. You have access to two types of search tools.
    Decide which tool is most appropriate for the user's question.

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

    llm = Ollama(model="llama3")
    tools = get_tools()
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    return agent_executor
