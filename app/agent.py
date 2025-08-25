import requests
import json
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

# --- Configuration ---
LOCAL_TOOL_SERVER_URL = "http://backend:8000/tools"
MS_LEARN_MCP_URL = "https://learn.microsoft.com/api/mcp"

# --- Tool Implementations ---

def local_document_search(query: str) -> str:
    """
    Function that calls the backend's search tool endpoint for internal documents.
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

def microsoft_docs_search(query: str) -> str:
    """
    Searches the official Microsoft Learn documentation.
    This function contains a commented-out real implementation and returns a realistic, hardcoded placeholder response.
    """
    # TODO: This is a placeholder implementation.
    # The commented-out code below shows a best-guess for a real implementation.
    # --- Start of Commented-Out Real Implementation ---
    # try:
    #     payload = {"tool": "microsoft_docs_search", "input": query}
    #     headers = {"Content-Type": "application/json", "Accept": "application/json"}
    #     response = requests.post(MS_LEARN_MCP_URL, json=payload, headers=headers, timeout=30)
    #     response.raise_for_status()
    #     raw_results = response.json()
    # except requests.exceptions.RequestException as e:
    #     return json.dumps({"error": f"Error calling Microsoft Learn API: {e}", "sources": []})
    # --- End of Commented-Out Real Implementation ---

    # --- Start of Placeholder Response ---
    # This is a realistic response structure based on the Zenn article.
    print(f"--- MOCK TOOL CALL: microsoft_docs_search(query='{query}') ---")
    raw_results = [
      {
        "title": "Troubleshoot Azure Backup failures caused by agent or extension issues",
        "content": "## UserErrorGuestAgentStatusUnavailable - VM agent unable to communicate with Azure Backup\n**Error code**: UserErrorGuestAgentStatusUnavailable **Error message**: VM Agent unable to communicate with Azure Backup\nThe Azure VM agent might be stopped, outdated, in an inconsistent state, or not installed.",
        "contentUrl": "https://learn.microsoft.com/en-us/azure/backup/backup-azure-troubleshoot-vm-backup-fails-snapshot-timeout#step-by-step-guide-to-troubleshoot-backup-failures"
      },
      {
        "title": "Troubleshoot Azure Windows VM Agent issues",
        "content": "## Troubleshooting checklist\nFor any VM extension to be able to run, Azure VM Guest Agent must be installed and working successfully. If you see that Guest Agent is reported as **Not ready**, or if an extension is failing and returning an error message such as `VMAgentStatusCommunicationError`, follow these steps to begin troubleshooting Guest Agent.",
        "contentUrl": "https://learn.microsoft.com/en-us/troubleshoot/azure/virtual-machines/windows/windows-azure-guest-agent#troubleshooting-checklist"
      }
    ]
    # --- End of Placeholder Response ---

    # --- Standardized Formatting Logic ---
    # This part transforms the raw API response into the standard format our agent expects.
    if not raw_results:
        return json.dumps({"content_for_llm": "No relevant documents found in Microsoft Learn.", "sources": []})

    sources_list = []
    content_list = []
    for result in raw_results:
        # The source name is the URL for this tool
        source_name = result.get('contentUrl', 'Unknown URL')
        snippet = result.get('content', '')
        title = result.get('title', 'No Title')

        sources_list.append({"document_name": source_name, "snippet": snippet})
        content_list.append(f"Title: {title}\nURL: {source_name}\nContent: {snippet}")

    return json.dumps({
        "content_for_llm": "\n\n---\n\n".join(content_list),
        "sources": sources_list
    })


def get_tools():
    """
    Initializes all tools for the agent.
    """
    local_search_tool = Tool(
        name="local_document_search",
        func=local_document_search,
        description="Searches the company's internal documents (manuals, specs, reports) for information about a query. Use this for questions about internal projects, policies, and procedures."
    )
    ms_learn_tool = Tool(
        name="microsoft_docs_search",
        func=microsoft_docs_search,
        description="Searches the official Microsoft Learn documentation. Use this for technical questions about Microsoft products like Azure, .NET, C#, etc."
    )
    return [local_search_tool, ms_learn_tool]

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
