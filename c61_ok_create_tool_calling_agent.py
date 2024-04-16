# https://python.langchain.com/docs/modules/agents/quick_start/

debug_info = False

import warnings
warnings.filterwarnings("ignore")
import langchain
langchain.debug = debug_info  

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
    "Search for information about LangSmith. For any query/questions about LangSmith, you MUST use this tool!\nIMPORTANT: Please quote the user's original query as the input.",
)
print("这句话是新加的，否则LLM可能会重写/修改传递给的retriever的query参数内容：\nIMPORTANT: Please quote the user's original query as the input.")

from langchain.agents import tool,Tool
from datetime import date
@tool
def get_flight_number(dep:str,des:str,date:date) -> str:
    """根据输入的出发地(dep),目的地(des),日期(date),返回航班号。重要:日期(date)只接受python datetime.date类型输入，如果日期是不确定的描述，如明天、后天等，可以先使用工具'python_repl_tool'进行计算，并且返回python datetime.date类型结果，具体格式示例如下：2024-04-03。"""
    return f"晶奇航空666[{date}]"

from langchain_experimental.tools import PythonREPLTool

@tool
def python_repl_tool_with_print(query:str) -> str: 
    """
    A Python shell. Use this to execute Input(query:str) python commands. And MUST print out the result value with `print(...)`.Examples:
        `print(1+1)`;

        `import datetime
         print(datetime.datetime.today() + datetime.timedelta(days=2))
        `    
    """   
    print('...调用执行Python_REPL......结果如下：')
    python_repl = PythonREPLTool()

    def _revise_query(query:str) -> str:
        print(f"===原query:\n{query}")
        lines = query.split("\n")
        for line in lines[::-1]:
            if len(line.strip())>0:
                if not line.startswith('#'): #直接跳过注释行
                    if line.startswith('print'):
                        print(f"===已经有print了，就直接返回原query:\n{query}")
                        return query #已经有print了，就直接返回原query
                    else:
                        last_line_splits = line.split("#")
                        last_line = last_line_splits[0].strip()
                        last_line = f'print({last_line})'+ '  ' +'#'.join(last_line_splits[1:])

                        lines[lines.index(line)] = last_line
                        _query = "\n".join(lines)

                        print(f"===revised_query:\n{_query}")
                        return _query
    revised_query = _revise_query(query)
    result = python_repl.run(revised_query)
    return result




tools = [retriever_tool,get_flight_number,python_repl_tool_with_print]

from langchain import hub

# Get the prompt to use - you can modify this!
prompt = hub.pull("hwchase17/openai-tools-agent")
prompt.pretty_print()


from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
# 导入错误，当前conda env test的langchain版本较老，没有create_tool_calling_agent方法。切换到conda env lcnew使用更新的langchain版本
print("\n### 可以正常使用create_tool_calling_agent方法的agent,并产生正确结果")
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=debug_info, handle_parsing_errors=True,return_intermediate_steps=debug_info)


print('==='*10)
agent_executor.invoke({"input": "hi!"})
result=agent_executor.invoke({"input": "请调用工具langsmith_search,然后回答：what's langsmith? how can langsmith help with testing?"})
print(result)
print('~~~'*10)
result=agent_executor.invoke({"input": "请查询2024-4-16日从合肥到上海的航班?"})
print(result)
print('~~~'*10)
result=agent_executor.invoke({"input": "请查询后天从合肥到上海的航班?"})
print(result)
print('~~~'*10)
result=agent_executor.invoke({"input": "请计算26527*689的结果"})
print(result)

print("\n### 无法正常使用create_openai_functions_agent方法的agent,永远不会调用工具")
# print('==='*10)
# from langchain.agents import create_openai_functions_agent
# agent = create_openai_functions_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=debug_info, handle_parsing_errors=True,return_intermediate_steps=debug_info)
# result=agent_executor.invoke({"input": "请调用工具langsmith_search,然后回答how can langsmith help with testing?"})
# print(result)
# print('~~~'*10)
# result=agent_executor.invoke({"input": "请查询2024-4-16日从合肥到上海的航班?"})
# print(result)
# pass
