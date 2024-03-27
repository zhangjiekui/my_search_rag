from langserve import RemoteRunnable
# import xml.etree.ElementTree as ET
# print(ET)
remote_chain = RemoteRunnable("http://localhost:8001/agent/")
r = remote_chain.invoke({
    "input": "请回答问题如何使用Function Call，或者Agent?一定要使用提供的工具检索回答我,并明确告诉我是否使用了工具。",
    "chat_history": []  # Providing an empty list as this is the first call
})

print(r)