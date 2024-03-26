from c0_env_config_models import chat_model as llm

from  langchain.schema import  HumanMessage,SystemMessage

instuct = '请使用中文回答问题，不要使用英文'
text = "What would be a good company name for a company that makes colorful socks?"

text = "请写一个100字的电影评论"

messages = [SystemMessage(content=instuct),HumanMessage(content=text)]

print(messages)

r = llm.invoke(messages)

print(r)


print('====chain===='*3)
from langchain_core.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ('system','You are world class technical documentation writer.'),
    'user','{input}'
])

chain = prompt | llm

r_chain = chain.invoke({'input':'how can langsmith help with testing?'})
print('type',type(r_chain))

print(r_chain)

from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseOutputParser

from langchain.output_parsers import CommaSeparatedListOutputParser
# class CommaSeparatedListOutputParser(BaseOutputParser[List[str]]):
    
#     def parse(self, text: str) -> List[str]:
#         return text.strip().split(',')

output_parser = CommaSeparatedListOutputParser()
r = output_parser.parse("hi, bye")
print(r)
# >> ['hi', 'bye']
template = "Generate a list of 5 {text}.\n\n{format_instructions}.并请使用中文回答问题"
chat_prompt = ChatPromptTemplate.from_template(template)
format_instructions=output_parser.get_format_instructions()
chat_prompt = chat_prompt.partial(format_instructions=format_instructions)
chain = chat_prompt | llm | output_parser
r = chain.invoke({"text": "colors"})
print(r)

prompt = ChatPromptTemplate.from_messages([
    ('system','You are world class technical documentation writer.'),
    'user','{input}'
])

prompt = ChatPromptTemplate.from_messages([
    ('system','，并请使用中文回答问题。'),
    'user','{input}'
])

system_chat_prompt = ChatPromptTemplate.from_messages([
    ('system',format_instructions + '.并请使用中文回答问题。'),
    ('user','{text}')
])

print(f'system_chat_prompt={system_chat_prompt}')
chain = system_chat_prompt | llm | output_parser
r = chain.invoke({"text": "5部武侠片"})  
print(r)




    

