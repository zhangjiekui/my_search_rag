import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import SeleniumURLLoader
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_loaders import NewsURLLoader #需导入结巴分词的词典，严重拖慢速度
from langchain_community.document_loaders import PlaywrightURLLoader
from playwright.sync_api import sync_playwright
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_transformers import Html2TextTransformer
html2text = Html2TextTransformer()

from c0_env_config_models import es_vectorstore,index_documents_to_es_vectorstore

from functools import partial
from typing import Optional

from langchain_core.callbacks.manager import (
    Callbacks,
)
from langchain_core.prompts import BasePromptTemplate, PromptTemplate, format_document
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.retrievers import BaseRetriever
from langchain_elasticsearch import ElasticsearchStore
from langchain.tools import Tool

index_name='temp_web_search_index'
user_agents = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.76'
class RetrieverInput(BaseModel):
    """Input to the retriever."""

    query: str = Field(description="query to look up in retriever")





class BaiduSearch:
    def __init__(self):
        # 请求头信息
        self.HEADERS = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": user_agents,
            "Referer": "https://www.baidu.com/",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }


    def search(self,query,search_url= "https://www.baidu.com/s?ie=utf-8&tn=baidu&wd="):

        if query:
            session = requests.Session()
            session.headers = self.HEADERS
            url = search_url + query
            print("百度搜索：",url)
            response = session.get(url=url)
            if response.status_code != 200:
                print(f"百度搜索失败（response.status_code != 200）: {url}")
                return []
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "lxml")

            # Finding all 'a' tags which typically contain href attribute for links
            links = [urljoin(url, a["href"]) for a in soup.find_all("a", href=True) if a["href"]]

            valid_prefix='http://www.baidu.com/link?url='
            valid_links = [link for link in links if link.startswith(valid_prefix)]

            return valid_links
        else:
            print("搜索查询(query)为空！请检查")
            return []

class BingSearch:
    def __init__(self,):
        self.HEADERS = {"User-Agent": user_agents}

    def search(self,query,language='chinese'):
        if query:
            # query = query.replace(' ','') #语言模型喜欢断成多个关键词，但Bing似乎不接受空白断开的
            if language != 'chinese' and language != 'english':
                print('不支持中英文以外的文字')
                return []
            if language == 'chinese':
                search_url = 'https://cn.bing.com/search?q='+query+'&form=ANSPH1'
            elif language == 'english':
                search_url = 'https://cn.bing.com/search?q='+query+'&FORM=BESBTB&ensearch=1'

            print("必应搜索：",search_url)

            session = requests.Session()
            session.headers = self.HEADERS
            response = session.get(search_url)
            soup = BeautifulSoup(response.text,'lxml') #"html5lib" 'html.parser'
            # print(soup.prettify())

            lis = soup.find_all('li',class_ = 'b_algo')
            links = []
            if not lis:
                for i in lis:
                    url=i.find('a',class_ = 'tilk')['href']
                    links.append(url)
            return links
        
        else:
            print("搜索查询(query)为空！请检查")
            return []
        
def get_search_result_links(query,language='chinese'):
    baidu = BaiduSearch()
    urls1 = baidu.search(query)
    print(f'Baidu搜索到 {len(urls1)} 条相关内容！')

    bing =BingSearch()
    urls2=bing.search(query,language)
    print(f'Bing搜索到 {len(urls2)} 条相关内容！')
    urls=urls1+urls2
    if urls:
        return urls
    else:
        print('没有搜索到任何相关内容！')
        return []



def get_search_result_documents(urls,query,es_vectorstore,document_loader_class=WebBaseLoader,max_doc_nums=5):

    # https://www.comet.com/site/blog/langchain-document-loaders-for-web-data/
            # 内容应该是NewsURLLoader比较适合RAG
            # 但SeleniumURLLoader似乎可以防屏蔽
    # 警告：这里不能使用loader.aload()方法，否则后面langchain agent里会报错！
    if document_loader_class==NewsURLLoader:
        loader = document_loader_class(urls,text_mode=True,nlp=True,continue_on_failure=True)
        docs = loader.load()
    elif document_loader_class==WebBaseLoader:
        loader = document_loader_class(urls,autoset_encoding=True,requests_kwargs ={'verify':False},verify_ssl=False,requests_per_second=1,continue_on_failure=True)
        docs = loader.load()
    elif document_loader_class==AsyncHtmlLoader:
        loader = document_loader_class(urls,autoset_encoding=True,requests_kwargs ={'verify':False},verify_ssl=False,requests_per_second=1,ignore_load_errors=False)
        docs = loader.load()
    elif document_loader_class==SeleniumURLLoader:
        loader = document_loader_class(urls)
        docs = loader.load()
    elif document_loader_class==PlaywrightURLLoader:
        # with sync_playwright() as p:
        loader = document_loader_class(urls,remove_selectors=["header", "footer"])
        docs = loader.load()
    else:
        print('暂时只支持Web Document Loaders：WebBaseLoader,NewsURLLoader, SeleniumURLLoader,AsyncHtmlLoader,PlaywrightURLLoader')
        print(f'但现要求使用的为{document_loader_class},请检查！')
        return []

    docs = loader.load()
    
    if docs and es_vectorstore:
        docs_transformed = html2text.transform_documents(docs)
        # 只保留page_content长度>50的
        docs_transformed = [doc for doc in docs_transformed if len(doc.page_content.strip())>50]

        if len(docs_transformed)>max_doc_nums:
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500,chunk_overlap = 100)
            documents = text_splitter.split_documents(docs_transformed)
            results = index_documents_to_es_vectorstore(documents,index_name=index_name,es_vectorstore=es_vectorstore,clear_before_add_index=True)
            
            docs_mmr = es_vectorstore.max_marginal_relevance_search(query,k=max_doc_nums)
            return docs_mmr
        else:
            return docs_transformed
    else:
        return docs

    
def get_web_search_documents(query,es_vectorstore,max_doc_nums=5):
    urls = get_search_result_links(query)
    docs = []
    if urls:
        docs = get_search_result_documents(urls,query,es_vectorstore,max_doc_nums=max_doc_nums)
    return docs

class RetrieverInput(BaseModel):
    """Input to the retriever."""

    query: str = Field(description="query to look up in retriever")


def _get_relevant_documents(
    query: str,
    es_vectorstore: ElasticsearchStore,
    document_prompt: BasePromptTemplate,
    document_separator: str,
    callbacks: Callbacks = None,

) -> str:
    docs = get_web_search_documents(query,es_vectorstore)
    return document_separator.join(
        format_document(doc, document_prompt) for doc in docs
    )

async def _aget_relevant_documents(
    query: str,
    retriever: BaseRetriever,
    document_prompt: BasePromptTemplate,
    document_separator: str,
    callbacks: Callbacks = None,
) -> str:
    print('警告：afunc是假设es_vectorstore已经建立了索引!因为我不会暂时不会async呀')
    docs = await retriever.aget_relevant_documents(query, callbacks=callbacks)
    return document_separator.join(
        format_document(doc, document_prompt) for doc in docs
    )

def create_web_retriever_tool(
    es_vectorstore: ElasticsearchStore,
    name: str,
    description: str,
    *,
    document_prompt: Optional[BasePromptTemplate] = None,
    document_separator: str = "\n\n",
) -> Tool:
    """Create a tool to do retrieval of documents.

    Args:
        retriever: The retriever to use for the retrieval
        name: The name for the tool. This will be passed to the language model,
            so should be unique and somewhat descriptive.
        description: The description for the tool. This will be passed to the language
            model, so should be descriptive.

    Returns:
        Tool class to pass to an agent
    """
    document_prompt = document_prompt or PromptTemplate.from_template("{page_content}")
    es_vectorstore.index_name = index_name
    func = partial(
        _get_relevant_documents,
        es_vectorstore=es_vectorstore,
        document_prompt=document_prompt,
        document_separator=document_separator,
    )

    afunc = partial(
        _aget_relevant_documents,
        retriever= es_vectorstore.as_retriever(),
        document_prompt=document_prompt,
        document_separator=document_separator,
    )

    return Tool(
        name=name,
        description=description,
        func=func,
        coroutine=afunc, # 注意，afunc是假设es_vectorstore已经建立了索引
        args_schema=RetrieverInput,
    )



if __name__ == "__main__":

    # urls = get_search_result_links("langchain")
    # print(urls)
    # docs = get_search_result_documents(urls)

    # query = '中国科学技术大学'

    query = '合肥八中 校区数量'
    d2 = get_web_search_documents(query)
    for doc in d2:
        print(doc.page_content)


    # 调用方法
    '''
        from c62_create_websearch_agenttool create_web_retriever_tool
        web_search= create_web_retriever_tool(es_vectorstore = es_vectorstore,
                                            name='web_search', 
                                            description='根据输入的搜索关键词(query)，使用搜索引擎进行搜索，返回搜索结果。重要:当你自身的知识无法回答用户问题时，可以尝试进行网络搜索'
                                            )
    
    '''