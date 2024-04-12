import json
import requests

url = "http://127.0.0.1:5000/chat"
headers = {'Content-Type': 'application/json'}
payload = {
        "conversation": [
            {"role": "user", "content": "你好，请介绍一下你自己"},
        ],
}

# r = requests.post(url, json=payload, headers=headers)
# print(r.text)

tool_payload ={
    "conversation":[{"role": "user", "content": "Whats the biggest penguin in the world?"}],
# Define tools available for the model to use:
    "tools":[{
        "name": "internet_search",
        "description": "Returns a list of relevant document snippets for a textual query retrieved from the internet",
         "parameter_definitions": {
            "query": {
            "description": "Query to search the internet with",
            "type": 'str',
            "required": True
                    }
                }
            },
            {
                'name': "directly_answer",
                "description": "Calls a standard (un-augmented) AI chatbot to generate a response given the conversation history",
                'parameter_definitions': {}
            }
] # type: ignore
}

url = "http://127.0.0.1:5000/tool"
response = requests.post(url, json=tool_payload, headers=headers)

tools_response = response.json().get('tool_response',None)
print(tools_response)

url = "http://127.0.0.1:5000/rag"

rag_payload = {
        "conversation": [{"role": "user", "content": "请简要介绍晶奇公司和合肥工业大学，并提供联系电话"}],
        "documents": [
            { "title": "晶奇公司资料", "text": "晶奇公司是一家专注于人工智能技术研发的高科技公司，公司致力于开发先进的人工智能算法和应用，为各行各业提供智能化解决方案。" }, 
            { "title": "晶奇公司电话", "text": "晶奇公司总部位于合肥，电话是0551-88888888。" }, 
            { "title": "合肥工业大学资料", "text": "合肥工业大学是一所位于安徽省合肥市的中国重点大学，是一所以工为主，工、理、文、经、管、法、艺术等多学科协调发展的综合性大学。学校创建于1945年，前身是国立合肥工业学校。"}
        ],
        "citation_mode": "accurate" 
        #(optional, default="accurate") The citation mode ("fast" or "accurate")
    }
r = requests.post(url, json=rag_payload, headers=headers)
pass
print(r.text)
