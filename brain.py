import os 
import streamlit as st
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import create_retriever_tool
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate

load_dotenv()

def setup_agent(pdf_path):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 5000, chunk_overlap = 200)
    splits = text_splitter.split_documents(docs)

    embeddings = GoogleGenerativeAIEmbeddings(model = "models/text-embedding-004")
    vectorstore = Chroma.from_documents(documents = splits, embedding = embeddings)

    retriever_tool = create_retriever_tool( vectorstore.as_retriever(), "pdf_search", "Search for information within the uploaded PDF document. Use this for any questions about the file content.")
    search_tool = TavilySearchResults(max_results = 2)
    tools = [retriever_tool, search_tool]

    llm = ChatGoogleGenerativeAI(model = "gemini-flash-latest", temperature = 0, version = "v1")

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

    agent = create_react_agent(llm, tools, prompt)

    return AgentExecutor(agent = agent, tools = tools, verbose = True, handle_parsing_errors=True)

def ask_agent(agent_executor, query):
    if not agent_executor:
        return "Error: Agent not initialized."
    try:
        response = agent_executor.invoke({"input": query})
        return response["output"]
    except Exception as e:
        return f"Error when generating an answer: {str(e)}"