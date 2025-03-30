from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
import mysql.connector

# 使用 Qwen2:7b 模型
ollama_llm = "qwen2:7b"
llm = ChatOllama(model=ollama_llm)

# MySQL 数据库连接设置
def create_db_connection():
    return mysql.connector.connect(
        host="119.45.93.228",
        user="jjdd",
        password="123456",
        database="jjdd"
    )

# 查询数据库中的所有表名
def get_all_table_names():
    db = create_db_connection()
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    cursor.close()
    db.close()
    table_name = {table[0]: table[0] for table in tables}
    return table_name

# 生成与用户问题相关的表名
def get_related_tables(question, table_name):
    template = """根据下面的表名，判断用户的问题应该和哪些表有关，并返回相关表的名称:
{table_name}

Question: {question}

Related Tables:"""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Identify relevant tables based on the user's question."),
            ("human", template),
        ]
    )
    
    memory = ConversationBufferMemory(return_messages=True)
    related_table_chain = (
        RunnablePassthrough.assign(
            table_name=table_name,
            question=question,
            history=RunnableLambda(lambda x: memory.load_memory_variables(x)["history"]),
        )
        | prompt
        | llm.bind(stop=["\nRelated Tables:"])
        | StrOutputParser()
    )

    related_tables_response = related_table_chain.invoke({
        "table_name": table_name,
        "question": question,
        "history": []
    })
    
    related_tables = {table.strip() for table in related_tables_response.split(',')}
    return related_tables

# 获取相关表的全部记录
def get_records_from_related_tables(related_table):
    db = create_db_connection()
    cursor = db.cursor()
    records = {}
    
    for table in related_table:
        cursor.execute(f"SELECT * FROM {table}")
        results = cursor.fetchall()
        records[table] = results
    
    cursor.close()
    db.close()
    return records

# 主程序
if __name__ == "__main__":
    question = "用户提供的问题"  # 替换为实际的用户问题
    table_name = get_all_table_names()
    related_table = get_related_tables(question, table_name)
    records = get_records_from_related_tables(related_table)
    
    # 打印相关表的全部记录
    for table, data in records.items():
        print(f"Table: {table}")
        for row in data:
            print(row)
