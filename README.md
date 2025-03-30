# LLM2SQL

**自然语言到结构化数据的智能交互系统**

## 项目概述
LLM2SQL 是一个基于大语言模型的端到端数据交互系统，实现从自然语言指令到结构化查询的全流程自动化。通过集成主流开源大模型，将用户的口语化请求自动转换为精准的SQL查询，并将数据库结果转化为易理解的自然语言回答。

## 核心功能
🗨️ **自然语言交互**
- 支持口语化指令输入
- 自动生成结构化数据库查询
- 返回带数据解读的自然语言回答

🛠️ **智能查询转换**
- 本地部署LLaMA 2/Qwen2等大模型
- 动态Prompt优化技术自动调整查询逻辑
- 支持MySQL数据库交互

🎙️ **多模态交互**
- 集成PaddleSpeech实现语音转文本输入
- 支持文本回答转语音播报
- 命令行/GUI双模式可选

## 技术栈
```markdown
- 大语言模型: LLaMA 2 | Qwen2
- 语音处理: PaddleSpeech
- 数据库: MySQL
- 动态提示: 上下文感知Prompt引擎
- 部署: Docker | Python 3.10+
```

## 快速开始
```bash
# 克隆项目
git clone https://github.com/yourname/LLM2SQL.git

# 安装依赖
pip install -r requirements.txt

# 启动服务（示例）
python main.py --model qwen2-7b --db_config config.yaml
```

## 使用示例
```python
# 自然语言输入
用户问：显示最近三个月销量超过1000件的商品

# 自动生成SQL
SELECT * FROM products 
WHERE sales > 1000 
AND update_time >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH);

# 结构化输出
{
  "result": [...],
  "summary": "近三个月共有15款商品销量破千..."
}

# 自然语言回答
"系统找到15款热销商品，其中电子产品类占比60%..."
```

## 贡献指南
欢迎通过Issue提交建议或PR参与开发，请遵循现有代码风格并完善单元测试。

## 开源协议
本项目采用 Apache License 2.0 开源协议，使用PaddleSpeech等第三方组件时请遵守其原有协议。
