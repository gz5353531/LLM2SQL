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

# 获取所有表的名字
def list_all_tables():
    db = create_db_connection()
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    db.close()
    return tables

# 确定与问题相关的表
def identify_relevant_tables(question, all_tables):
    # 使用LLM分析问题与表的关系
    prompt = "Given the question: '{}', which of the following tables are relevant? {}".format(question, ', '.join(all_tables))
    relevant_tables = llm.ask(prompt).split(", ")
    return relevant_tables

# 获取表结构
def get_schema(_):
    db = create_db_connection()
    cursor = db.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    schema_info = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        schema_info[table_name] = [column[0] for column in columns]
    cursor.close()
    db.close()
    return schema_info

# 获取相关表的完整记录
def get_full_records(tables):
    db = create_db_connection()
    cursor = db.cursor()
    records = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        records[table] = cursor.fetchall()
    cursor.close()
    db.close()
    return records

# 执行SQL查询
def run_query(query):
    query_start = query.lower().find("select")
    cleaned_query = query[query_start:] if query_start != -1 else query
    print(f"Executing Query: {cleaned_query}")
    db = create_db_connection()
    cursor = db.cursor()
    cursor.execute(cleaned_query)
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return results

# Prompt 模板
template_query = """根据下面的表模式，编写一个SQL查询来回答用户的问题:
{schema}

请确保SQL查询适用于这个数据库;

Question: {question}
SQL Query:"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Given an input question, convert it to a SQL query. No pre-amble."),
        MessagesPlaceholder(variable_name="history"),
        ("human", template_query),
    ]
)

memory = ConversationBufferMemory(return_messages=True)

# 提供提示的输入类型
class InputType(BaseModel):
    question: str

# 回答链模板
template_response = """根据下面提供的表模式、问题、sql查询和sql响应，用中文编写一个自然语言响应：
{schema}

Question: {question}
SQL Query: {query}
SQL Response: {response}"""

prompt_response = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given an input question and SQL response, convert it to a natural "
            "language answer. No pre-amble."
        ),
        ("human", template_response),
    ]
)

# 构建查询和回答链
chain = (
    RunnablePassthrough.assign(
        tables=lambda _: list_all_tables(),
        question=lambda x: x.input.question
    )
    | RunnableLambda(lambda x: identify_relevant_tables(x.question, x.tables))
    | RunnablePassthrough.assign(
        full_records=lambda x: get_full_records(x.output)
    )
    | RunnablePassthrough.assign(
        schema=get_schema
    )
    | prompt
    | llm.bind(stop=["\nSQLResult:"])
    | StrOutputParser()
    | RunnablePassthrough.assign(
        response=lambda x: run_query(x.output)
    )
    | prompt_response
    | llm
)
