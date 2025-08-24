import requests
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

# The URL for our tool server
TOOL_SERVER_URL = "http://backend:8000/tools"


def search_api(query: str) -> str:
    """
    Function that calls our backend's search tool endpoint.
    """
    try:
        response = requests.post(f"{TOOL_SERVER_URL}/search", json={"query": query})
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json().get("results", "No results found.")
    except requests.exceptions.RequestException as e:
        return f"Error calling search API: {e}"


def get_tools():
    """
    Initializes the tools for the agent.
    """
    search_tool = Tool(
        name="search",
        func=search_api,
        description="Searches the company's documents for information about a query. Use this to answer any question about internal company knowledge.",
    )
    return [search_tool]


def create_agent_executor():
    """
    Creates the LangChain agent, including its prompt, LLM, and tools.
    """
    prompt_template = """
    You are a helpful assistant for a corporate knowledge base.
    Answer the following questions as best you can. You have access to the following tools:

    {tools}

    When you use the 'search' tool, it will return a JSON object with two keys: 'content_for_llm' and 'sources'.
    Use the 'content_for_llm' to formulate your answer.
    Your final answer MUST be a JSON object with two keys: 'answer' and 'sources'.
    The 'sources' key must contain the exact list of source objects that the search tool provided.

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
    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=True, handle_parsing_errors=True
    )

    return agent_executor
