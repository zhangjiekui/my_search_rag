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

r = chain.invoke("What did the president say about technology?")
print(r)