# import nltk
# nltk.download('cmudict')
# print(nltk.data.path)
# from paddlespeech.cli.asr.infer import ASRExecutor
# asr = ASRExecutor()
# result = asr(audio_file="/root/temp/my-app/packages/sql-ollama/sql_ollama/录音.wav")
# print(result)
from paddlespeech.cli.tts.infer import TTSExecutor
tts = TTSExecutor()
tts(text="今天天气十分不错。", output="output.wav")
'''
import re

def filter_chinese_and_numbers(text):
    pattern = re.compile(r'[\u4e00-\u9fa5，。！？、；：0-9]')
    filtered_text = ''.join(pattern.findall(text))
    return filtered_text

def main():
    # 模拟的响应对象
    response = {
        'content': '以下人员的考核没有完成：\n- 王某的破案任务在2024年7月2日；\n- 赵某的考勤工作安排在了2024年7月4日进行；\n- 吴某需要提交一份报告的时间为2024年7月6日；\n- 陈某需要完成的是考勤考核，计划在2024年7月10日执行。'
    }

    # 提取 content 字段的值作为 response_text
    response_text = response.get('content', '')

    # 检查 response_text 是否为字符串类型
    if isinstance(response_text, str):
        filtered_response_text = filter_chinese_and_numbers(response_text)
        print(f"响应: {filtered_response_text}")

        # 将响应文本转换为语音并保存为文件
        # text_to_speech(filtered_response_text, "/root/temp/responses/response.mp3")
    else:
        print("Error: response_text is not a string.")

if __name__ == "__main__":
    main()
'''

