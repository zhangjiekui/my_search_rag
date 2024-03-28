#!/usr/bin/env python
from typing import List

from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub
from langchain.agents import create_openai_functions_agent,create_structured_chat_agent
from langchain.agents import AgentExecutor
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.messages import BaseMessage,ChatMessage
from langserve import add_routes

from c0_env_config_models import chat_model,embeddings,es_vectorstore,index_documents_to_es_vectorstore,get_es_vectorstore_from_documents
llm = chat_model

# 1. Load Retriever
loader = WebBaseLoader("https://docs.smith.langchain.com/user_guide")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)
vector = get_es_vectorstore_from_documents(documents,index_name='langsmith')
retriever1 = vector.as_retriever()

d1=retriever1.get_relevant_documents("how to upload a dataset")[0]

tool1 = create_retriever_tool(
    retriever1,
    "langsmith_search",
    "Search for information about LangSmith. For any questions about LangSmith, you must use this tool!",
)





# 2. Create Tools
retriever2 = es_vectorstore.as_retriever()
d2=retriever2.get_relevant_documents("What did the president say about technology?")[0]

tool2 = create_retriever_tool(
    retriever2,
    "search_state_of_union",
    "Searches american president,state and political related, returns excerpts from the 2022 State of the Union.",
)


# search = TavilySearchResults()
# tools = [retriever_tool, search]

from langchain.agents import tool
@tool
def get_flight_number(dep:str,des:str,date:str) -> str:
    """根据输入的出发地(dep),目的地(des),日期(date),返回航班号"""
    return ["MU584"]

tools = [tool1,tool2,get_flight_number]


# 3. Create Agent
prompt = hub.pull("hwchase17/openai-functions-agent")
prompt = hub.pull("hwchase17/structured-chat-agent")
print(prompt.messages)

print('\n\n===================Agent=======================================================')
# agent = create_openai_functions_agent(llm, tools, prompt)
agent = create_structured_chat_agent(llm, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

result = agent_executor.invoke({"input": "hi, im bob"})

res = agent_executor.invoke({"input": "明天从合肥到上海的航班"})

rr=agent_executor.invoke({"input": "what is langsmith and how can langsmith help with testing?"},include_run_info=True)

result = agent_executor.invoke(
    {
        "input": "what did the president say about ketanji brown jackson in the most recent state of the union?"
    }
)

result = agent_executor.invoke(
    {"input": "how long ago did the president nominate ketanji brown jackson?"}
)

