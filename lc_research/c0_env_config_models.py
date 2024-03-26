from langchain_openai import ChatOpenAI

chat_model = ChatOpenAI(
    model_name='qwen1.5-chat',
    openai_api_base='http://10.1.150.105:9997/v1',
    openai_api_key='EMPTY',
    streaming=True,
)
print(f'当前使用的Langchain ChatOpenAI模型为:{chat_model.model_name},API_URL为{chat_model.openai_api_base}')

# 直接使用OpenAI
from openai import OpenAI
client_openai = OpenAI(base_url='http://10.1.150.105:9997/v1',api_key='EMPTY')
print(f'当前使用的OpenAI模型base_url为:{client_openai.base_url}')


from os.path import join
model_base = fr"D:\biaoshu\localmodels"
model_name = join(model_base,"m3e-base") 
print(f'当前使用的Embedding模型为:{model_name}')

if 'bge' in model_name: # 有query_instruction https://github.com/langchain-ai/langchain/blob/ee94ef55ee6ab064da08340817955f821dfa6261/libs/langchain/langchain/embeddings/huggingface.py#L187
    from langchain_community.embeddings import HuggingFaceBgeEmbeddings as HuggingFaceEmbeddings
else:
    from langchain_community.embeddings import HuggingFaceEmbeddings
model_kwargs = {'device': 'cuda'}
encode_kwargs = {'normalize_embeddings': True}
embeddings = HuggingFaceEmbeddings(model_name=model_name,model_kwargs=model_kwargs,encode_kwargs =encode_kwargs)

# r_chat_model = chat_model.invoke("how can langsmith help with testing?")
# print(r_chat_model)


from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchStore
from langchain.indexes import SQLRecordManager, index
llm = chat_model
ELASTIC_PASSWORD='Is3Evsr9t-JZi9STRILV'
CERT_FINGERPRINT='f3fdb3f509e00bf88fe45779426102abc1a1eb87bd5d3cefeed3cdc6b3845986'
ES_URL ="https://localhost:9200"
index_name="test_index"

es_connection = Elasticsearch(
    ES_URL,
    # ca_certs=f"d:\JqkjKB\http_ca.crt",
    ssl_assert_fingerprint=CERT_FINGERPRINT,
    basic_auth=("elastic", ELASTIC_PASSWORD),
    request_timeout=600 #这个设置很重要  elastic_transport.ConnectionTimeout: Connection timed out
)

print(f'当前使用的Elasticsearch URL为{ES_URL},详细信息如下:')
print('-------Elasticsearch Connection详细信息-------')
print(es_connection.info())
print('-------Elasticsearch Connection详细信息-------')




# 方式一：常见的在教程中见到的
def get_es_store_from_documents(documents, es_connection=es_connection,index_name=index_name,embedding=embeddings,strategy=ElasticsearchStore.ApproxRetrievalStrategy(hybrid=False)):
    elastic_vector_search = ElasticsearchStore.from_documents(documents=documents,es_connection=es_connection,index_name=index_name,embedding=embedding,strategy=strategy)
    return elastic_vector_search

# 方式二，使用LangChain indexing API，防止重复插入
# https://python.langchain.com/docs/modules/data_connection/indexing 

namespace = f"elasticsearch/{index_name}"
record_manager = SQLRecordManager(namespace, db_url="sqlite:///record_manager_cache.sql")
record_manager.create_schema()
es_vectorstore = ElasticsearchStore(es_connection=es_connection, index_name=index_name, embedding=embeddings)

def _clear():
    """Hacky helper method to clear content. See the `full` mode section to to understand why it works."""
    clear_result = index([], record_manager, es_vectorstore, cleanup="full", source_id_key="source")
    print(f'Clear_Result report of "index_documents_to_es_vectorstore":{clear_result}')

def index_documents_to_es_vectorstore(documents,cleanup="incremental",clear_before_add_index=False):
    if clear_before_add_index:
        _clear()

    result=index(documents, record_manager, es_vectorstore, cleanup=cleanup, source_id_key="source")
    return result




# print(elastic_vector_search)


if __name__ == '__main__':

    print('******************'*5)
    print('下面是main函数中的输出：')
    # 直接使用OpenAI
    # from openai import OpenAI
    # client = OpenAI(base_url='http://10.1.150.105:9997/v1',api_key='EMPTY')

    completion = client_openai.chat.completions.create(
      model="qwen1.5-chat",
      messages=[
        {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
        {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
      ]
    )
    print(completion.choices[0].message)

    print('=========='*10)

    completion2 = client_openai.completions.create(
      model="qwen1.5-chat",
      prompt= "Compose a poem that explains the concept of recursion in programming."
    )
    print(completion2)

    embeddings_result = embeddings.embed_documents(
    [
        "Hi there!",
        "Oh, hello!",
        "What's your name?",
        "My friends call me World",
        "Hello World!"
    ])
    print(len(embeddings_result), len(embeddings_result[0]))
    print('******************'*5)
