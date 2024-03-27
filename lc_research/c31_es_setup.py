# 1 安装elastic
# docker network create elastic
# docker pull docker.elastic.co/elasticsearch/elasticsearch:8.12.2
# docker run --name elasticsearch --net elastic -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -t docker.elastic.co/elasticsearch/elasticsearch:8.12.2

# elastic password：Is3Evsr9t-JZi9STRILV
# Password for the elastic user (reset with `bin/elasticsearch-reset-password -u elastic`):
#   
# Kibana enrollment token：
# eyJ2ZXIiOiI4LjEyLjIiLCJhZHIiOlsiMTcyLjE4LjAuMjo5MjAwIl0sImZnciI6ImYzZmRiM2Y1MDllMDBiZjg4ZmU0NTc3OTQyNjEwMmFiYzFhMWViODdiZDVkM2NlZmVlZDNjZGM2YjM4NDU5ODYiLCJrZXkiOiJaRjdyZUk0QlpsbFhjYkljZmZLRDpBeEV6dTc2aVRYcWh0U01WNnhFejVBIn0= 

            # ✅ Elasticsearch security features have been automatically configured!
            # ✅ Authentication is enabled and cluster connections are encrypted.

            # ℹ️  Password for the elastic user (reset with `bin/elasticsearch-reset-password -u elastic`):
            #   Is3Evsr9t-JZi9STRILV

            # ℹ️  HTTP CA certificate SHA-256 fingerprint:
            #   f3fdb3f509e00bf88fe45779426102abc1a1eb87bd5d3cefeed3cdc6b3845986

            # ℹ️  Configure Kibana to use this cluster:
            # • Run Kibana and click the configuration link in the terminal when Kibana starts.
            # • Copy the following enrollment token and paste it into Kibana in your browser (valid for the next 30 minutes):
            #   eyJ2ZXIiOiI4LjEyLjIiLCJhZHIiOlsiMTcyLjE4LjAuMjo5MjAwIl0sImZnciI6ImYzZmRiM2Y1MDllMDBiZjg4ZmU0NTc3OTQyNjEwMmFiYzFhMWViODdiZDVkM2NlZmVlZDNjZGM2YjM4NDU5ODYiLCJrZXkiOiJaRjdyZUk0QlpsbFhjYkljZmZLRDpBeEV6dTc2aVRYcWh0U01WNnhFejVBIn0=

            # ℹ️ Configure other nodes to join this cluster:
            # • Copy the following enrollment token and start new Elasticsearch nodes with `bin/elasticsearch --enrollment-token <token>` (valid for the next 30 minutes):
            #   eyJ2ZXIiOiI4LjEyLjIiLCJhZHIiOlsiMTcyLjE4LjAuMjo5MjAwIl0sImZnciI6ImYzZmRiM2Y1MDllMDBiZjg4ZmU0NTc3OTQyNjEwMmFiYzFhMWViODdiZDVkM2NlZmVlZDNjZGM2YjM4NDU5ODYiLCJrZXkiOiJZbDdyZUk0QlpsbFhjYkljZmZLQzpjeXZNTi1KOFFLMmdDQjBmQUFXU1J3In0=

            #   If you're running in Docker, copy the enrollment token and run:
            #   `docker run -e "ENROLLMENT_TOKEN=<token>" docker.elastic.co/elasticsearch/elasticsearch:8.12.2`

# 2 安装Kibana 【In a new terminal session, start Kibana and connect it to your Elasticsearch container】
# docker pull docker.elastic.co/kibana/kibana:8.12.2
# docker run --name kibana --net elastic -p 5601:5601 docker.elastic.co/kibana/kibana:8.12.2

    # Kibana URL:http://127.0.0.1:5601/?code=668873
    # elastic user：elastic
    # elastic password：Is3Evsr9t-JZi9STRILV
    # Kibana enrollment token：
    # eyJ2ZXIiOiI4LjEyLjIiLCJhZHIiOlsiMTcyLjE4LjAuMjo5MjAwIl0sImZnciI6ImYzZmRiM2Y1MDllMDBiZjg4ZmU0NTc3OTQyNjEwMmFiYzFhMWViODdiZDVkM2NlZmVlZDNjZGM2YjM4NDU5ODYiLCJrZXkiOiJaRjdyZUk0QlpsbFhjYkljZmZLRDpBeEV6dTc2aVRYcWh0U01WNnhFejVBIn0= 
 

        # To access Kibana, open the generated URL in your browser.
        # Paste the enrollment token that you copied when starting Elasticsearch and click the button to connect your Kibana instance with Elasticsearch.
        # Log in to Kibana as the elastic user with the password that was generated when you started Elasticsearch.

from langchain_elasticsearch import ElasticsearchStore
from elasticsearch import Elasticsearch
# from langchain_openai import OpenAIEmbeddings
# embedding = OpenAIEmbeddings()
from c0_env_config_models import chat_model,embeddings
llm = chat_model
embedding = embeddings
ELASTIC_PASSWORD='Is3Evsr9t-JZi9STRILV'
CERT_FINGERPRINT='f3fdb3f509e00bf88fe45779426102abc1a1eb87bd5d3cefeed3cdc6b3845986'

client = Elasticsearch(
    "https://localhost:9200",
    # ca_certs=f"d:\JqkjKB\http_ca.crt",
    ssl_assert_fingerprint=CERT_FINGERPRINT,
    basic_auth=("elastic", ELASTIC_PASSWORD),
    request_timeout=600 #这个设置很重要  elastic_transport.ConnectionTimeout: Connection timed out
)
print(client.info())


elastic_vector_search = ElasticsearchStore(
    es_connection=client,
    index_name="test_index",
    embedding=embedding,

)

print(elastic_vector_search)
