from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes
from sql_ollama import chain as sql_ollama_chain

# 创建 FastAPI 实例
app = FastAPI()

# 添加路由
add_routes(app, sql_ollama_chain, path="/sql-ollama")

# 重定向根路径到 /docs
@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
