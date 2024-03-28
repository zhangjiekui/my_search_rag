# from c0_env_config_models import es_connection,es_vectorstore,get_es_vectorstore_from_documents,index_documents_to_es_vectorstore,index_name,chat_model,embeddings
from c0_env_config_models import *
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

template = """Answer the question based only on the following context:

{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

retriever = es_vectorstore.as_retriever()
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | chat_model
    | StrOutputParser()
)

print(chain.input_schema.schema())
print(chain.output_schema.schema())

pass

print('r = chain.invoke("What did the president say about technology?")的结果：')
r = chain.invoke("What did the president say about technology?")
print(r)

print('==================================')
print('异步 ar = await chain.ainvoke("What did the president say about technology?")的结果：')




import asyncio
async def async_function_wrapper(question:str = "What did the president say about technology?"):
    ar = await chain.ainvoke(question)
    print(ar)
    

    print('async + stream 【chain.astream】')
    async for ar in chain.astream(question):
        print(ar,end='',flush=True)
    
    print('异步执行结束并已打印结果！')

asyncio.run(async_function_wrapper())


print('==================================')
print('&&&&&&&&&&&&&&下面是两个参数的&&&&&&&&&&&&&&')




prompt = ChatPromptTemplate.from_template(
    "Tell me a short joke about {topic} in {language}"
)

chain = (
    {"topic": RunnablePassthrough(),'language':RunnablePassthrough()} 
    | prompt
    | chat_model
    | StrOutputParser()
)

r2params = chain.invoke({"topic":"ice cream","language":"中文"})
print(f'中文的结果：\n {r2params}')

r2params = chain.invoke({"topic":"ice cream","language":"English"})
print(f'English的结果：\n {r2params}')

print(f'stream的结果：\n')
for chunk in chain.stream({"topic":"ice cream","language":"中文"}):
    print(chunk, end="", flush=True)

print(f'batch的结果：\n')
r_batch = chain.batch([{"topic":"ice cream","language":"英文"},{"topic":"cat","language":"中文"}])
print(f'r_batch = {r_batch}')
