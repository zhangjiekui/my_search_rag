# Chain的Async Stream Events and log for Intermediate Steps

# from c0_env_config_models import es_connection,es_vectorstore,get_es_vectorstore_from_documents,index_documents_to_es_vectorstore,index_name,chat_model,embeddings
from c0_env_config_models import *
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

import jsonpatch

template = """Answer the question based only on the following context:

{context}

Question: {question}
"""


def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

#变化：定义了一个tool
from langchain_core.tools import tool
@tool
def some_tool(x: int, y: str) -> dict:
    '''Some_tool.'''
    return {"x": x, "y": y}

retriever = es_vectorstore.as_retriever()
stroutput_parser = StrOutputParser()

prompt = ChatPromptTemplate.from_template(template)
# prompt = ChatPromptTemplate.from_template(template).with_config({'run_name':'my_prompt_template','tags':['my_prompt_template']})  

# 变化：增加了with_config
run_name_with_model_name = f'my_llm({chat_model.model_name})' 
chain = (
    {
        "context": retriever.with_config(run_name="my_docs") | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt.with_config({'run_name':'my_prompt_template','tags':['my_prompt_template']})
    | chat_model.with_config(run_name=run_name_with_model_name)
    | stroutput_parser
)



async def async_function_wrapper(question:str = "What did the president say about technology?",include_names=["my_docs", run_name_with_model_name,'my_prompt_template']):
    async for event in chain.astream_events(question, version="v1", include_names=include_names):
        kind = event["event"]

        if kind == "on_prompt_start":
            print("starting prompt:")
            print('-----------------------------')
            # print(event)
            print('---question---')
            print(event["data"]['input']["question"])
            print('---context---')
            print(event["data"]['input']["context"])
            print('-----------------------------')

        elif kind == "on_prompt_end":
            print("ended prompt:")
            print(event["data"]["output"].messages)


        elif kind == "on_chat_model_stream":
            print(event["data"]["chunk"].content, end="|")
        elif kind in {"on_chat_model_start"}:
            print()
            print("Streaming LLM:")
        elif kind in {"on_chat_model_end"}:
            print()
            print("Done streaming LLM.")
        elif kind == "on_retriever_end":
            print("--")
            print("Retrieved the following documents:")
            print(event["data"]["output"]["documents"])
        elif kind == "on_tool_end":
            print(f"Ended tool: {event['name']}")
        else:
            pass
    
    # i=0
    json_doc={}
    async for chunk in chain.astream_log(question, include_names=include_names):
        # https://python-json-patch.readthedocs.io/en/latest/tutorial.html
        json_doc = jsonpatch.apply_patch(json_doc, chunk.ops)
        # if i<10 or i%10==0:
        #     print("-" * 40)
        #     print(f"[{i}]:{chunk}")
        # i+=1

    return json_doc
print('==================================')
print('&&&&&&&&&&&&&&开始&&&&&&&&&&&&&&')

import asyncio
import json
json_doc = asyncio.run(async_function_wrapper())

# TypeError: Object of type Document is not JSON serializable
# with open('log.json', 'w') as f:
#     json.dump(json_doc, f, skipkeys=True)




print('&&&&&&&&&&&&&&结束&&&&&&&&&&&&&&')
print('==================================')

print(json_doc)



