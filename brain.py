import os 
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import create_retriever_tool
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate

# Load environment variables for secure API key management
load_dotenv()

def setup_agent(pdf_path):

    # Load the document and split it into manageable chunks for optimized context retrieval
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)
    splits = text_splitter.split_documents(docs)

    # Convert text chunks into high-dimensional vectors for semantic search
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/text-embedding-004")

    # Store vectors in ChromaDB
    vectorstore = Chroma.from_documents(documents = splits, embedding = embeddings)

    # TOOL 1: Vector-based retrieval from the uploaded PDF
    retriever_tool = create_retriever_tool( vectorstore.as_retriever(search_kwargs = {"k": 1}), "pdf_search", "Search for information within the uploaded PDF document. Use this for any questions about the file content.")

    # TOOL 2: External search tool to provide the agent with real-time web access
    search_tool = TavilySearchResults(max_results = 2)

    tools = [retriever_tool, search_tool]

    # Initialize Groq LPU for high-speed inference, using llama-3.3-70b for a balance betweem intelligence and performance
    llm = ChatGroq(model = "llama-3.3-70b-versatile", temperature = 0, groq_api_key = os.getenv("GROQ_API_KEY"))

    # ReAct Prompt: THOUGHT -> ACTION -> OBSERVATION
    prompt = PromptTemplate.from_template("""Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
(this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}""")
    
    # Initialize the ReAct agent
    agent = create_react_agent(llm, tools, prompt)

    # The AgentExecutor manages the loop and handles parsing errors
    return AgentExecutor(agent = agent, tools = tools, verbose = True, handle_parsing_errors = True)

def ask_agent(agent_executor, query):
    if not agent_executor:
        return "Error: Agent not initialized."
    try:
        # The agent invokes the necessary tools based on its own internal reasoning 
        response = agent_executor.invoke({"input": query})
        return response["output"]
    except Exception as e:
        return f"Error when generating an answer: {str(e)}"