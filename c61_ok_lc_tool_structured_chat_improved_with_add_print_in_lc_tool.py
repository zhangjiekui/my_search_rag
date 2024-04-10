# https://python.langchain.com/docs/modules/agents/agent_types/structured_chat
#!/usr/bin/env python
from langchain_community.chat_message_histories import ElasticsearchChatMessageHistory
import warnings
warnings.filterwarnings("ignore")
import langchain
langchain.debug = False  

import os
# 为了忽略 Python REPL can execute arbitrary code. Use with caution.
# 看看能否纠正下面的错误
'''
    Python REPL can execute arbitrary code. Use with caution.
    Could not parse LLM output: 
'''
# os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
# 先调用一次就ok了

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import WebBaseLoader,SeleniumURLLoader

from langchain_community.document_transformers import Html2TextTransformer
html2text = Html2TextTransformer()

from langchain_openai import OpenAIEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain import hub
from langchain.agents import create_openai_functions_agent,create_structured_chat_agent
from langchain.agents import AgentExecutor
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.messages import BaseMessage,ChatMessage
# from zh_search_tool import get_web_search_documents


from c0_env_config_models import chat_model,embeddings,es_vectorstore,index_documents_to_es_vectorstore,get_es_vectorstore_from_documents,api_base,api_key
# llm = chat_model.bind(response_format={"type": "json_object"})
llm = chat_model

# 1. Load Retriever
url = ["http://www.jqsoft.net/webinfo/gyjq/gsjj/"]
# loader1 = WebBaseLoader(url,autoset_encoding=True,requests_kwargs ={'verify':False},verify_ssl=False,requests_per_second=1,continue_on_failure=True)
# docs1 = loader1.load()
# loader2 = SeleniumURLLoader(url)
# docs2 = loader2.load()

# docs = html2text.transform_documents(docs1+docs2)
# text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500,chunk_overlap = 100)
# documents = text_splitter.split_documents(docs)
# results = index_documents_to_es_vectorstore(documents,index_name='jqsoft',clear_before_add_index=False)
# print(f"Add indices result:{results}")



# 2. Create Tools
# 2.1  两个检索工具retriever tools

es_vectorstore.index_name='jqsoft'
retriever1 = es_vectorstore.as_retriever(k=1)
# d1=retriever1.get_relevant_documents("安徽晶奇网络科技股份有限公司总机电话号码")[0]
retriever_tool1 = create_retriever_tool(
    retriever1,
    "jqgs_search",
    "任何关于晶奇网络科技股份有限公司的问题, 你必须使用这个工具来获取答案",
)
# es_vectorstore.index_name='langsmith'
# retriever2 = es_vectorstore.as_retriever()
# d2=retriever2.get_relevant_documents("what is langsmith and how can langsmith help with testing?")[0]

# retriever_tool2 = create_retriever_tool(
#     retriever2,
#     "search_langchain_smith",
#     "Search for information about LangSmith. For any questions about LangSmith, you must use this tool!",
# )

# 2.2  自定义工具
from langchain.agents import tool,Tool
from datetime import date
@tool
def get_flight_number(dep:str,des:str,date:date) -> str:
    """根据输入的出发地(dep),目的地(des),日期(date),返回航班号。重要:日期(date)只接受python datetime.date类型输入，如果日期是不确定的描述，如明天、后天等，可以先使用工具'python_repl_tool'进行计算，并且返回python datetime.date类型结果，具体格式示例如下：2024-04-03。"""
    return f"晶奇航空666[{date}]"

# @tool
# def web_search(query:str) -> str:
#     """根据输入的搜索关键词(query)，使用搜索引擎进行搜索，返回搜索结果。重要:当你自身的知识无法回答用户问题时，可以尝试进行网络搜索。关键词(query)必须是联系的，直接不能出现空格等分割符"""
#     from zh_search_tool import get_web_search_documents
#     docs = get_web_search_documents(query)
#     res = [doc.page_content.strip() for doc in docs]
#     res = '\\n'.join(res)
#     return res

from c62_create_websearch_agenttool import create_web_retriever_tool
web_search= create_web_retriever_tool(es_vectorstore = es_vectorstore,
                                      name='web_search', 
                                      description='根据输入的搜索关键词(query)，使用搜索引擎进行搜索，返回搜索结果。重要:当你自身的知识无法回答用户问题时，可以尝试进行网络搜索'
                                    )


# 2.3  使用load_tools直接载入工具
from langchain.agents import load_tools,get_all_tool_names
from langchain_community.tools import HumanInputRun
print('\nall_tool_names:\n',','.join(get_all_tool_names()))
# loaded_tools = load_tools(["llm-math"],llm=llm)
# loaded_tools = load_tools(["human","llm-math","stackexchange"],llm=llm)
# loaded_tools = load_tools(["human","stackexchange","dalle-image-generator"],llm=llm,openai_api_base=api_base,openai_api_key=api_key)
loaded_tools = load_tools(["human","stackexchange"],llm=llm)

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

# 2.4  使用Shell (bash)工具 【操作系统层面】
# from langchain_community.tools import ShellTool
# shell_tool = ShellTool()
# print(shell_tool.run({"commands": ["echo 'Hello World!'", "time"]}))
# shell_tool.description = shell_tool.description + f"args {shell_tool.args}".replace(
#     "{", "{{"
# ).replace("}", "}}")

# 2.5  使用python_repl并包装成Agent工具 【代码执行层面】
from langchain_experimental.tools import PythonREPLTool
python_repl = PythonREPLTool()
print(python_repl.run("print(1+1)")) #先运行一遍，后面似乎就不再会输出警告信息: Python REPL can execute arbitrary code. Use with caution.

def python_repl_run_with_print(query:str,python_repl=python_repl) -> str:

    print('...调用执行Python_REPL......结果如下：')
    return python_repl.run(query)


python_repl_tool = Tool(
    name="python_repl_tool",
    # from https://python.langchain.com/docs/integrations/toolkits/python
    description ="""牢记：请生成Python代码,代码内容必须是全英文字符，代码行之间必须用换行号符'\n'分割,千万不要使用';'来分割！
                You are an agent designed to write and execute python code to answer questions.
                You have access to a python REPL, which you can use to execute python code.Input should be a valid python command.
  
                If you get an error, debug your code and try again.
                Only use the output of your code to answer the question.
                You might know the answer without running any code, but you should still run the code to get the answer.
                If it does not seem like you can write code to answer the question, just return "I don't know" as the answer.
                """,
    # https://python.langchain.com/docs/integrations/tools/python
    # description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
    func=python_repl_run_with_print
    # func=python_repl.run
)

# 2.6 AI工具层面
# "dalle-image-generator"  #https://python.langchain.com/docs/integrations/tools/dalle_image_generator/
#   ASR and TTS : https://python.langchain.com/docs/integrations/tools/nvidia_riva/
#  https://python.langchain.com/docs/integrations/text_embedding/nvidia_ai_endpoints/

# https://python.langchain.com/docs/integrations/tools/gradio_tools/

# NVIDIA AI Foundation End: https://python.langchain.com/docs/integrations/text_embedding/nvidia_ai_endpoints/
# https://build.nvidia.com/explore/visual-design
import requests
import base64

@tool
def sd_image_gen(query:str= "A steampunk dragon soaring over a Victorian cityscape, with gears and smoke billowing from its wings.") -> str:
    """根据输入的请求(query),生成一张图片，并返回保存的地址。"""
    invoke_url = "https://ai.api.nvidia.com/v1/genai/stabilityai/sdxl-turbo"
    headers = {
        "Authorization": "Bearer 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",
        "Accept": "application/json",
    }

    payload = {
    "text_prompts": [
        {
        "text":query,
        "weight": 1
        }
    ],
    "sampler": "K_EULER_ANCESTRAL",
    "steps": 2,
    "seed": 0
    }

    # re-use connections
    session = requests.Session()

    response = session.post(invoke_url, headers=headers, json=payload)

    response.raise_for_status()
    response_body = response.json()
    print(response_body)
    request_base64 = response_body['artifacts'][0]['base64']
    imgdata = base64.b64decode(request_base64)
    fp = "SavedImage.png"
    with open(fp,"wb") as fh:
        fh.write(imgdata)
    print(f"Image saved to {fp}")
    return fp


# 2.7  所有可用的工具列表
# tools = [retriever_tool1,retriever_tool2,get_flight_number,python_repl_tool,shell_tool,input_tool] + loaded_tools
tools = [retriever_tool1,web_search,get_flight_number,sd_image_gen,python_repl_tool] + loaded_tools
tool_names = ','.join([tool.name for tool in tools])
print(f'\n本次程序中提供的所有可用的工具列表:\n {tool_names}')




from langchain.memory import ConversationSummaryBufferMemory,ConversationBufferMemory,ConversationBufferWindowMemory

# 放到这里使用
# agent_executor = AgentExecutor(...,memory=memory)
# https://github.com/ThreeRiversAINexus/sample-langchain-agents/blob/main/structured_chat.py
# 加载chat_model模型时需指定tiktoken_model_name='r50k_base'
    # chat_model = ChatOpenAI(
    #     model_name='qwen1.5-chat',
    #     openai_api_base='http://10.1.150.105:9997/v1',
    #     openai_api_key='EMPTY',
    #     streaming=True,
    #     tiktoken_model_name='r50k_base',
    #     temperature=0
    # )
# 但还是失败
# memory = ConversationSummaryBufferMemory(
#     llm = llm, # 这里的llm的作用是总结
#     # max_token_limit=4096,#NotImplementedError: get_num_tokens_from_messages() is not presently implemented for model cl100k_base
#     memory_key="chat_history",
#     return_messages=True
# )
# chat_history=[]

memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True,k=3)
chat_history = memory.buffer_as_messages
# memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
# chat_history = memory.buffer_as_messages


# 3. Create Agent/Agent_executor
# prompt = hub.pull("hwchase17/openai-functions-agent") #qwen api无法成功运行
# agent = create_openai_functions_agent(llm, tools, prompt)#qwen api无法成功运行

prompt = hub.pull("hwchase17/structured-chat-agent")
# 修改、丰富提示词
prompt.messages[0].prompt.template = prompt.messages[0].prompt.template.replace("Use tools if necessary.", "Use tools if necessary, or even ask for more specific information from user (but leave this as the last option) ." )


agent = create_structured_chat_agent(llm, tools, prompt)

prompt.pretty_print()

def _handle_error(error) -> str:
    # print(error)
    # python_repl_tool.run(error.args)
    return "Check your output and make sure it conforms, use the Action/Action Input syntax." + "This is error message:" + str(error)

# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True,return_intermediate_steps=True)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True,return_intermediate_steps=True)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=_handle_error,
                               return_intermediate_steps=False,#似乎与memory冲突
                               memory=memory,
                               max_iterations=100,
                               )

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
    # "请记住：Use a json blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).Provide only ONE action per $JSON_BLOB, as shown:\n\n```\n{\n  \"action\": $TOOL_NAME,\n  \"action_input\": $INPUT\n}\n```\n\nFollow this format:\n\nQuestion: input question to answer\nThought: consider previous and subsequent steps\nAction:\n```\n$JSON_BLOB\n```\nObservation: action result\n... (repeat Thought/Action/Observation N times)\nThought: I know what to respond\nAction:\n```\n{\n  \"action\": \"Final Answer\",\n  \"action_input\": \"Final response to human\"\n}\n\nBegin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary, or even ask for more specific information from user (please leave this as the last option) . Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation\n",
    '请查询和输出今天的日期',
    "请查询今天从合肥到上海的航班",
    "请查询后天从合肥到上海的航班",    
    "请查询2024年3月29日从合肥到上海的航班",
    "安徽晶奇网络科技股份有限公司总机电话号码?",
    # "what did the president say about ketanji brown jackson in the most recent state of the union?",
     "100的3倍等于多少?",
     "'100的3倍等于多少'包含多少个字符?",
    "What is the 10th fibonacci number?",
    "请帮我生成一张天安门升旗仪式的图片",
    '帮我写一个python程序，计算1到100的和，并运行得到正确的结果',
    # '请使用stackexchange工具检索和回答:What parts does a JUnit4 unit test case consist of?',
    f"请告诉我安徽晶奇网络科技股份有限公司2024年的预期营收是多少?可以调用工具Human向用户提问或请求更多信息，以得到正确答案" 
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


# for query in querys:
#     print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'*3)
#     print(query)
#     result = agent_executor.invoke({"input": query,"chat_history": chat_history},include_run_info=True)
#     print_nested_dict(result)
    
#     print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'*3)

def q(user_inputs=querys,verbose_info=True):
    user_inputs=[user_inputs] if isinstance(user_inputs,str) else user_inputs
    agent_executor.verbose=verbose_info
    for query in user_inputs:
        result = agent_executor.invoke({"input": query,"chat_history": chat_history},include_run_info=verbose_info)
        print_nested_dict(result)

if __name__ == '__main__':
    # q(user_inputs='帮我生成一张大气漂亮的黄山迎客松为近景风景照')
    # q(user_inputs="安徽晶奇网络科技股份有限公司总机电话号码?")
    # q('what is langchain smith?')
    # q('搜索中国科学技术大学的新闻，并对结果进行综述')
    # q('请搜索中国科学技术大学是985吗')
    q('合肥八中有几个校区？')
    

    




    # # 测试
    # # 测试1
    # print(q("请帮我写一个python程序，计算1到100的和，并运行得到正确的结果"))

    # # 测试2
    # print(q("请告诉我安徽晶奇网络科技股份有限公司2024年的预期营收是多少?可以调用工具Human向用户提问或请求更多信息，以得到正确答案"))

    # # Could not parse LLM output
    #     # C:\Users\zjk\.conda\envs\test\Lib\site-packages\langchain\agents\agent.py#L624
    #     # C:\Users\zjk\.conda\envs\test\Lib\site-packages\langchain\agents\agent.py#L1165
        
    # # Invalid or incomplete response
    #     # C:\Users\zjk\.conda\envs\test\Lib\site-packages\langchain\agents\agent.py#L1189  

    # # 修改Agent的1274行：
    #             # if isinstance(output, AgentAction):
    #             # actions = [output]
        

    #     # C:\Users\zjk\.conda\envs\test\Lib\site-packages\langchain\agents\output_parsers\json.py # JSONAgentOutputParser