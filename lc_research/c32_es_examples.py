from c0_env_config_models import elastic_client,get_es_store_from_documents

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

# lc_research\state_of_the_union.txt
loader = TextLoader("D:\JqkjKB\lc_research\state_of_the_union.txt",autodetect_encoding=True)
documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
docs = text_splitter.split_documents(documents)


elastic_client.indices.delete(
    index="rag_index",
    ignore_unavailable=True,
    allow_no_indices=True,
)
print('可在浏览器中查看Kibana: http://localhost:5601/app/enterprise_search/content/search_indices/rag_index/documents')
elastic_vector_search = get_es_store_from_documents(docs)
# elastic_vector_search.add_documents(docs) 

elastic_vector_search.client.indices.refresh(index="rag_index")
query = "What did the president say about Ketanji Brown Jackson"
# results = elastic_vector_search.similarity_search(query)
results = elastic_vector_search.similarity_search_with_score(query) #scores are currently not supported in hybrid mode
# print(results)
for r in results:
    print('~~~~~'*10)
    print(f'Score:{r[1]}')
    print(r[0].page_content.replace('\n', ''))
