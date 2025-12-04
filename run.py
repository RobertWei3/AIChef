import uvicorn
import os
import sys

# 【可选】将当前目录加入系统路径
# 这行代码可以防止 Python 报错说 "ModuleNotFoundError: No module named 'core'"
# 它可以确保 app 文件夹里的代码能顺利引用到 core 文件夹里的代码
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 正在启动 AIChef RAG 服务...")
    print("📡 接口文档地址: http://127.0.0.1:8000/docs")
    
    # 启动 Uvicorn 服务器
    # 参数解析:
    # "app.main:app" -> 指向 app 文件夹下的 main.py 文件里的 app 对象
    # host="0.0.0.0" -> 允许局域网访问 (如果你只想本机访问可以用 127.0.0.1)
    # port=8000      -> 服务端口号
    # reload=True    -> 【开发模式】当你修改代码保存时，服务器会自动重启，不用手动关掉再开
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)