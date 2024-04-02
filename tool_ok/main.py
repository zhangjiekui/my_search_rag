# https://python.langchain.com/docs/modules/agents/agent_types/structured_chat
#!/usr/bin/env python

import os
# 为了忽略 Python REPL can execute arbitrary code. Use with caution.
# 看看能否纠正下面的错误
'''
    ObservPython REPL can execute arbitrary code. Use with caution.
    Could not parse LLM output: 
'''
# os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
# 先调用一次就ok了

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain import hub
from langchain.agents import create_openai_functions_agent,create_structured_chat_agent
from langchain.agents import AgentExecutor
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.messages import BaseMessage,ChatMessage


from c0_env_config_models import chat_model,embeddings,es_vectorstore,index_documents_to_es_vectorstore,get_es_vectorstore_from_documents
# llm = chat_model.bind(response_format={"type": "json_object"})
llm = chat_model

# 1. Load Retriever
loader = WebBaseLoader("https://docs.smith.langchain.com/")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)
vector = get_es_vectorstore_from_documents(documents,index_name='langsmith')

# 2. Create Tools
# 2.1  两个retriever tools

retriever1 = vector.as_retriever()
d1=retriever1.get_relevant_documents("how to upload a dataset")[0]
retriever_tool1 = create_retriever_tool(
    retriever1,
    "langsmith_search",
    "Search for information about LangSmith. For any questions about LangSmith, you must use this tool!",
)

retriever2 = es_vectorstore.as_retriever()
d2=retriever2.get_relevant_documents("What did the president say about technology?")[0]

retriever_tool2 = create_retriever_tool(
    retriever2,
    "search_state_of_union",
    "Searches american president,state and political related, returns excerpts from the 2022 State of the Union.",
)

# 2.2  自定义工具
from langchain.agents import tool,Tool
@tool
def get_flight_number(dep:str,des:str,date:str) -> str:
    """根据输入的出发地(dep),目的地(des),日期(date),返回航班号，如果日期是不确定的描述，如明天、后天等，可以先使用工具'python_repl_tool'进行计算"""
    return [f"晶奇航空666[{date}]"]


# 2.3  使用load_tools直接载入工具
from langchain.agents import load_tools,get_all_tool_names
from langchain_community.tools import HumanInputRun
print('\nall_tool_names:\n',','.join(get_all_tool_names()))
# loaded_tools = load_tools(["llm-math"],llm=llm)
loaded_tools = load_tools(["human","llm-math"],llm=llm)

def get_input() -> str:
    print("Insert your text. Enter 'q' or press Ctrl-D (or Ctrl-Z on Windows) to end.")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "q":
            break
        contents.append(line)
    return "\n".join(contents)

# 也是humun工具，但是自定义了接收输入的函数
input_tool = HumanInputRun(name='multi_line_humun_input',input_func=get_input)


# 2.4  使用python_repl并包装成Agent工具
from langchain_experimental.tools import PythonREPLTool
python_repl = PythonREPLTool()
print(python_repl.run("print(1+1)")) #先运行一遍，后面似乎就不再会输出警告信息: Python REPL can execute arbitrary code. Use with caution.

def python_repl_run_with_print(query:str,python_repl=python_repl) -> str:

    print('...调用执行Python_REPL......结果如下：')
    return python_repl.run(query)


python_repl_tool = Tool(
    name="python_repl_tool",
    # from https://python.langchain.com/docs/integrations/toolkits/python
    description ="""牢记：代码最后一行必须使用print($result)打印输出结果$result（result是结果变量名称）,并且必须是全英文的，否则后续程序处理就会出错！
                You are an agent designed to write and execute python code to answer questions.
                You have access to a python REPL, which you can use to execute python code.Input should be a valid python command, and Input of python code MUST in English.
                If  you want to see the output of a value and get the observation, you MUST print it out with `print(...)`.
                If you get an error, debug your code and try again,especially checking if you using ‘print($result)’, rather than ‘$result’    .
                Only use the output of your code to answer the question.
                You might know the answer without running any code, but you should still run the code to get the answer.
                If it does not seem like you can write code to answer the question, just return "I don't know" as the answer.
                """,
    # https://python.langchain.com/docs/integrations/tools/python
    # description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
    func=python_repl_run_with_print
    # func=python_repl.run
)

# 2.5  所有可用的工具列表
# tools = [retriever_tool1,retriever_tool2,get_flight_number,python_repl_tool,input_tool] + loaded_tools
tools = [retriever_tool1,retriever_tool2,get_flight_number,python_repl_tool] + loaded_tools
tool_names = ','.join([tool.name for tool in tools])
print(f'\n本次程序中提供的所有可用的工具列表:\n {tool_names}')



# 3. Create Agent/Agent_executor
# prompt = hub.pull("hwchase17/openai-functions-agent") #qwen api无法成功运行
# agent = create_openai_functions_agent(llm, tools, prompt)#qwen api无法成功运行

prompt = hub.pull("hwchase17/structured-chat-agent")
# 修改、丰富提示词
prompt.messages[0].prompt.template = prompt.messages[0].prompt.template.replace("Use tools if necessary.", "Use tools if necessary, or even ask for more specific information from user (please leave this as the last option) ." )


agent = create_structured_chat_agent(llm, tools, prompt)

prompt.pretty_print()

def _handle_error(error) -> str:
    # print(error)
    # python_repl_tool.run(error.args)
    return "Check your output and make sure it conforms, use the Action/Action Input syntax." + "This error message:" + str(error)

# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True,return_intermediate_steps=True)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True,return_intermediate_steps=True)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=_handle_error,return_intermediate_steps=True)

# 4. 执行Agent
print('\n\n==============================执行Agent=======================================================')

# querys = [
#     "你好",
#     "后天从合肥到上海的航班，如果你不知道后天的具体日期，请使用提供的工具来查询",
#     "帮我查询今天的日期",
#     "今天从合肥到上海的航班",
#     "2024年3月29日从合肥到上海的航班",
#     # "what is langsmith and how can langsmith help with testing?",
#     # "what did the president say about ketanji brown jackson in the most recent state of the union?",
#      "100的3倍等于多少?",
#      "'100的3倍等于多少'包含多少个字符?",
#     "What is the 10th fibonacci number?",
#     '帮我写一个python程序，计算1到100的和，并运行得到正确的结果',
#     "What's my friend Eric's surname?" 
# ]  

querys = [
    "请使用python print'输出你好，千问大模型'",
    '请查询和输出今天的日期',
    "请查询今天从合肥到上海的航班",
    "请查询后天从合肥到上海的航班",    
    "请查询2024年3月29日从合肥到上海的航班",
    "what is langsmith and how can langsmith help with testing?",
    "what did the president say about ketanji brown jackson in the most recent state of the union?",
     "100的3倍等于多少?",
     "'100的3倍等于多少'包含多少个字符?",
    "What is the 10th fibonacci number?",
    '帮我写一个python程序，计算1到100的和，并运行得到正确的结果',
    f"What's my friend Eric's surname?可以调用工具Human向用户提问或请求更多信息，以得到正确答案" 
]  


def print_nested_dict(nested_dict, indent=2):
    for key, value in nested_dict.items():
        if isinstance(value, dict):
            print(' ' * indent + str(key) + ":")
            print_nested_dict(value, indent+2)
        elif isinstance(value, list):
            print(' ' * indent + str(key) + f"(共{len(value)}步):")
            for i,item in enumerate(value):                
                print(f"{'-' * indent} ({i+1}): {item}")
        else:
            print(' ' * indent + str(key) + ": " + str(value))


for query in querys:
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'*3)
    print(query)
    result = agent_executor.invoke({"input": query},include_run_info=True)
    print_nested_dict(result)
    
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'*3)


# Could not parse LLM output
    # C:\Users\zjk\.conda\envs\test\Lib\site-packages\langchain\agents\agent.py#L624
    # C:\Users\zjk\.conda\envs\test\Lib\site-packages\langchain\agents\agent.py#L1165
    
# Invalid or incomplete response
    # C:\Users\zjk\.conda\envs\test\Lib\site-packages\langchain\agents\agent.py#L1189  

# 修改Agent的1274行：
            # if isinstance(output, AgentAction):
            # actions = [output]
    

    # C:\Users\zjk\.conda\envs\test\Lib\site-packages\langchain\agents\output_parsers\json.py # JSONAgentOutputParser
