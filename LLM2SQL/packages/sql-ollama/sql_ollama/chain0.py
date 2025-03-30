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

def run_query(query):
    # 清理查询语句，去掉前面的自然语言部分
    query_start = query.lower().find("select")
    if query_start != -1:
        cleaned_query = query[query_start:]
    else:
        cleaned_query = query

    print(f"Executing Query: {cleaned_query}")  # 添加日志信息

    db = create_db_connection()
    cursor = db.cursor()
    cursor.execute(cleaned_query)
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return results

# Prompt 模板
# template_query = """Based on the table schema below, write a SQL query that would answer the user's question:
template_query = """根据下面的表模式，编写一个SQL查询来回答用户的问题:
{schema}

请确保SQL查询遵循以下示例格式:

SELECT CourseName 
FROM ClassSchedule 
WHERE DayOfWeek = '星期几' AND TimeOfDay = '时间段（上午，下午，晚上）';

Question: {question}
SQL Query:"""  # noqa: E501

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Given an input question, convert it to a SQL query. No pre-amble."),
        MessagesPlaceholder(variable_name="history"),
        ("human", template_query),
    ]
)

memory = ConversationBufferMemory(return_messages=True)

# 查询链
sql_chain = (
    RunnablePassthrough.assign(
        schema=get_schema,
        history=RunnableLambda(lambda x: memory.load_memory_variables(x)["history"]),
    )
    | prompt
    | llm.bind(stop=["\nSQLResult:"])
    | StrOutputParser()
)

def save(input_output):
    output = {"output": input_output.pop("output")}
    memory.save_context(input_output, output)
    return output["output"]

sql_response_memory = RunnablePassthrough.assign(output=sql_chain) | save

# 回答链
template_response = """根据下面提供的表模式、问题、sql查询和sql响应，用中文编写一个自然语言响应：
{schema}

Question: {question}
SQL Query: {query}
SQL Response: {response}"""  # noqa: E501

prompt_response = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given an input question and SQL response, convert it to a natural "
            "language answer. No pre-amble.",
        ),
        ("human", template_response),
    ]
)

# 提供提示的输入类型
class InputType(BaseModel):
    question: str

chain = (
    RunnablePassthrough.assign(query=sql_response_memory).with_types(
        input_type=InputType
    )
    | RunnablePassthrough.assign(
        schema=get_schema,
        response=lambda x: run_query(x["query"]),
    )
    | prompt_response
    | llm
)