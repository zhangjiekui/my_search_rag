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
from langchain.agents import create_openai_functions_agent
from langchain.agents import AgentExecutor
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.messages import BaseMessage,ChatMessage
from langserve import add_routes

from c0_env_config_models import chat_model,embeddings
llm = chat_model

#0 document_chain 
#0 设置一个链，该链将接收一个问题和检索到的文档，并生成一个答案。
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
 
prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:
<context>
{context}
</context>
Question: {input}""")
 
document_chain = create_stuff_documents_chain(llm, prompt)
from langchain_core.documents import Document
 
r=document_chain.invoke({
    "input": "how can langsmith help with testing?",
    "context": [Document(page_content="langsmith can let you visualize test results")]
})

print(r)


# 1. Load Retriever
loader = WebBaseLoader("https://docs.smith.langchain.com/user_guide")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)
print(documents)
# embeddings = OpenAIEmbeddings()
vector = FAISS.from_documents(documents, embeddings)
retriever = vector.as_retriever()
# 1.1 retrieval_chain
from langchain.chains import create_retrieval_chain
retrieval_chain = create_retrieval_chain(retriever, document_chain)
response = retrieval_chain.invoke({"input": "how can langsmith help with testing?"})
print(response["answer"])
# 1.2 对话历史和更新检索
from langchain.chains import create_history_aware_retriever
from langchain.prompts import MessagesPlaceholder

prompt_with_history = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="chat_history"),
    ('user','{input}'),
    ('user','根据上面的对话，生成一个搜索查询以获取与对话相关的信息')
])

retriever_chain = create_history_aware_retriever(llm, retriever, prompt_with_history)

from langchain_core.messages import HumanMessage, AIMessage
 
chat_history = [HumanMessage(content="LangSmith是否可以帮助测试我的LLM应用？"), AIMessage(content="是的！")]
r=retriever_chain.invoke({
    "chat_history": chat_history,
    "input": "告诉我怎么做"
})

print(r)

whole_promt = ChatPromptTemplate.from_messages([
    ('system','根据提供的上下文(context)回答用户的问题：\n\n<context>{context}</context>'),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
])

document_chain = create_stuff_documents_chain(llm, whole_promt)
retrieval_chain = create_retrieval_chain(retriever_chain, document_chain)
chat_history = [HumanMessage(content="LangSmith是否可以帮助测试我的LLM应用？"), AIMessage(content="是的！")]

print('\n\n==========================================================================')
r=retrieval_chain.invoke({
    "chat_history": chat_history,
    "input": "告诉我怎么做"
})
print(r)





# 2. Create Tools
retriever_tool = create_retriever_tool(
    retriever,
    "langsmith_search",
    "Search for information about LangSmith. For any questions about LangSmith, you must use this tool!",
)
# search = TavilySearchResults()
# tools = [retriever_tool, search]

tools = [retriever_tool]


# 3. Create Agent
prompt = hub.pull("hwchase17/openai-functions-agent")
print(prompt)

print('\n\n===================Agent=======================================================')
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True,return_intermediate_steps=True)
agent_executor.invoke({"input": "how can langsmith help with testing?"},include_run_info=True)


# 4. App definition
app = FastAPI(
  title="LangChain Server",
  version="1.0",
  description="A simple API server using LangChain's Runnable interfaces",
)

# 5. Adding chain route

# We need to add these input/output schemas because the current AgentExecutor
# is lacking in schemas.

class Input(BaseModel):
    input: str
    chat_history: List[BaseMessage] = Field(
        ...,
        extra={"widget": {"type": "chat", "input": "location"}},
    )


class Output(BaseModel):
    output: str

add_routes(
    app,
    agent_executor.with_types(input_type=Input, output_type=Output),
    path="/agent",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8001)
