# https://python.langchain.com/docs/modules/agents/quick_start/

import warnings
warnings.filterwarnings("ignore")
import langchain
langchain.debug = True  

from lc_research.c0_env_config_models import chat_model,embeddings,es_vectorstore,index_documents_to_es_vectorstore,get_es_vectorstore_from_documents,api_base,api_key

from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_transformers import Html2TextTransformer
html2text = Html2TextTransformer()

llm=chat_model
url=["https://docs.smith.langchain.com/overview"]
loader1 = WebBaseLoader(url,autoset_encoding=True,requests_kwargs ={'verify':False},verify_ssl=False,requests_per_second=1,continue_on_failure=True)
docs1 = loader1.load()
docs = html2text.transform_documents(docs1)
text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500,chunk_overlap = 100)
documents = text_splitter.split_documents(docs)
index_name='langsmith'
es_vectorstore.index_name=index_name
results = index_documents_to_es_vectorstore(documents,index_name=index_name,clear_before_add_index=True)
print(f"Add indices['{index_name}'] result:{results}")

retriever = es_vectorstore.as_retriever()
from langchain.tools.retriever import create_retriever_tool
retriever_tool = create_retriever_tool(
    retriever,
    "langsmith_search",
    "Search for information about LangSmith. For any query/questions about LangSmith, you must use this tool!\nIMPORTANT: Please quote the user's original query as the input.",
)
print("这句话是新加的，否则LLM可能会重写/修改传递给的retriever的query参数内容：\nIMPORTANT: Please quote the user's original query as the input.")

from langchain.agents import tool,Tool
from datetime import date
@tool
def get_flight_number(dep:str,des:str,date:date) -> str:
    """根据输入的出发地(dep),目的地(des),日期(date),返回航班号。重要:日期(date)只接受python datetime.date类型输入，如果日期是不确定的描述，如明天、后天等，可以先使用工具'python_repl_tool'进行计算，并且返回python datetime.date类型结果，具体格式示例如下：2024-04-03。"""
    return f"晶奇航空666[{date}]"

tools = [retriever_tool,get_flight_number]

from langchain import hub

# Get the prompt to use - you can modify this!
prompt = hub.pull("hwchase17/openai-functions-agent")

# prompt = hub.pull("homanp/superagent")
prompt.pretty_print()

# from langchain_core.prompts import ChatPromptTemplate
# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             "You are a helpful assistant. Make sure to use the one of [get_flight_number,langsmith_search] tools for flight information.",
#         ),
#         ("placeholder", "{chat_history}"),
#         ("human", "{input}"),
#         ("placeholder", "{agent_scratchpad}"),
#     ]
# )

from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
# 导入错误，当前conda env test的langchain版本较老，没有create_tool_calling_agent方法。切换到conda env lcnew使用更新的langchain版本
print("\n### 可以正常使用create_tool_calling_agent方法的agent,并产生正确结果")
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True,return_intermediate_steps=True)


print('==='*10)
agent_executor.invoke({"input": "hi!"})
result=agent_executor.invoke({"input": "请调用工具langsmith_search,然后回答：what's langsmith? how can langsmith help with testing?"})
print(result)
print('~~~'*10)
result=agent_executor.invoke({"input": "请查询2024-4-16日从合肥到上海的航班?"})
print(result)

print("\n### 无法正常使用create_openai_functions_agent方法的agent,永远不会调用工具")
# print('==='*10)
# from langchain.agents import create_openai_functions_agent
# agent = create_openai_functions_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True,return_intermediate_steps=True)
# result=agent_executor.invoke({"input": "请调用工具langsmith_search,然后回答how can langsmith help with testing?"})
# print(result)
# print('~~~'*10)
# result=agent_executor.invoke({"input": "请查询2024-4-16日从合肥到上海的航班?"})
# print(result)
# pass
