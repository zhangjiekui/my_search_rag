from c0_env_config_models import es_connection,es_vectorstore,get_es_store_from_documents,index_documents_to_es_vectorstore,index_name

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

# lc_research\state_of_the_union.txt
loader = TextLoader("D:\JqkjKB\lc_research\state_of_the_union.txt",autodetect_encoding=True)
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
docs = text_splitter.split_documents(documents)




# 方式二，使用LangChain indexing API，防止重复插入
# https://python.langchain.com/docs/modules/data_connection/indexing 
# Do not use with a store that has been pre-populated with content independently of the indexing API, 
# as the record manager will not know that records have been inserted previously.
# 所以方式二与方式一不要混用，或者放到方式一前面

print('====='*10)
print('方式二，使用LangChain indexing API，防止重复插入。且方式二与方式一不要混用，或者放到方式一前面')
result = index_documents_to_es_vectorstore(documents = docs)
print(f'Result report of "index_documents_to_es_vectorstore":{result}')

result = index_documents_to_es_vectorstore(documents = docs,clear_before_add_index=True)
print(f'Result report of "index_documents_to_es_vectorstore":{result}')


print('====='*10)
print('方式一：常见的在教程中见到的')
# 方式一：常见的在教程中见到的
es_connection.indices.delete(
    index=index_name,
    ignore_unavailable=True,
    allow_no_indices=True,
)
print('可在浏览器中查看Kibana: http://localhost:5601/app/enterprise_search/content/search_indices/rag_index/documents')
elastic_vector_search = get_es_store_from_documents(docs)
# elastic_vector_search.add_documents(docs) 

elastic_vector_search.client.indices.refresh(index=index_name)
query = "What did the president say about Ketanji Brown Jackson"
# results = elastic_vector_search.similarity_search(query)
results = elastic_vector_search.similarity_search_with_score(query) #scores are currently not supported in hybrid mode
# print(results)
for r in results:
    print('~~~~~'*10)
    print(f'Score:{r[1]}')
    print(r[0].page_content.replace('\n', ''))
