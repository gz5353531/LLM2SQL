from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
import mysql.connector
from paddlespeech.cli.asr.infer import ASRExecutor
from paddlespeech.cli.tts.infer import TTSExecutor
import os
import re
from datetime import datetime

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

def filter_chinese_and_numbers(text):
    # 正则表达式：匹配中文字符、常见的中文标点符号和数字
    pattern = re.compile(r'[\u4e00-\u9fa5，。！？、；：0-9]')
    # 使用正则表达式过滤文本
    filtered_text = ''.join(pattern.findall(text))
    return filtered_text

def get_schema(_):

    print("========================")
    print("获取数据库表模式")

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

    print("========================")
    print("根据下面的表模式，编写一个SQL查询来回答用户的问题:")
    print(f"表模式: {schema_info}")

    return schema_info

def run_query(query):
    # 清理查询语句，去掉前面的自然语言部分
    query_start = query.lower().find("select")
    if query_start != -1:
        cleaned_query = query[query_start:]
    else:
        cleaned_query = query

    print("========================")
    print(f"执行的查询: {cleaned_query}")

    db = create_db_connection()
    cursor = db.cursor()
    cursor.execute(cleaned_query)
    results = cursor.fetchall()
    cursor.close()
    db.close()

    print("========================")
    print(f"查询结果: {results}")

    return results

# Prompt 模板
template_query = """根据下面的表模式，编写一个SQL查询来回答用户的问题:
{schema}

请确保SQL查询遵循以下示例格式:

如果问的是会议，请类比以下查询：

SELECT * 
FROM 日程表
WHERE 日期 = '2024-07-01' AND 事件 = '会议';

如果问的是值班，请类比以下查询：

SELECT * 
FROM 日程表
WHERE 日期 = '2024-07-01' AND 事件 = '值班';

如果问的是警情，请类比以下查询：

SELECT 地点, 案件
FROM 案情表
WHERE 日期 = '2024-07-01';

如果问的是考核，请类比以下查询：

SELECT 人员账号, 人员姓名, 考核项目, 日期
FROM 考核表
WHERE 完成情况 = '未完成';

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
SQL Response: {response}"""

prompt_response = ChatPromptTemplate.from_messages(
    [
        (
            "system", "Given an input question and SQL response, convert it to a natural language answer. No pre-amble.",
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

# 语音识别
def recognize_speech_from_file(file_path):
    try:
        asr = ASRExecutor()
        result = asr(audio_file=file_path, lang='zh')
        print("\n========================")
        print(f"识别结果: {result}")
        return result
    except Exception as e:
        print(f"请求错误: {str(e)}")
    return None

# 文本转换为语音
def text_to_speech(text, output_path="response.mp3"):
    try:
        tts = TTSExecutor()
        tts(text=text, output=output_path, lang='zh')
        print("\n========================")
        print(f"语音输出: {output_path}")
    except Exception as e:
        print(f"语音合成错误: {str(e)}")

# 主函数
def main():
    while True:
        print("\n========================")
        print("开始新的对话，输入 'q' 退出")
        print("========================")
        file_path = input("请说话/输入音频文件（或输入 'q' 退出）：").strip()
        print("========================\n")
        if file_path.lower() == 'q':
            break

        # 识别音频文件中的语音
        user_input = recognize_speech_from_file(file_path)
        if user_input is None:
            print("========================")
            print("未能识别音频中的语音内容，请重试。")
            print("========================")
            continue

        # 使用链处理用户输入
        input_data = {"question": user_input}
        response_text = chain.invoke(input_data)
        
        # 输出响应文本到终端
        print("========================")
        print(f"响应: {response_text.content}")

        # 提取 content 字段的值作为 response_text
        # 提取 content 属性的值作为 response_text
        response_text = response_text.content

        # 检查 response_text 是否为字符串类型
        if isinstance(response_text, str):
            filtered_response_text = filter_chinese_and_numbers(response_text)
            print("========================")
            print(f"过滤响应: {filtered_response_text}")
            print("========================\n")

            # 获取当前时间，并格式化为字符串
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 将响应文本转换为语音并保存为文件
            output_file_path = f"/root/temp/responses/response_{current_time}.mp3"
            text_to_speech(filtered_response_text, output_file_path)
        else:
            print("错误: 回答不是字符类型。")

if __name__ == "__main__":
    main()
