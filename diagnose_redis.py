import os
import sys

# 1. 强制添加路径，确保能导入 core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
    import redis
except ImportError as e:
    print(f"❌ 环境错误: {e}")
    sys.exit(1)

print("="*40)
print("🏥 Redis 连接诊断工具")
print("="*40)

# 2. 打印当前 Python 读到的配置
print(f"1. 检查配置 (core/config.py):")
print(f"   - HOST:     {REDIS_HOST} (类型: {type(REDIS_HOST).__name__})")
print(f"   - PORT:     {REDIS_PORT} (类型: {type(REDIS_PORT).__name__})")
print(f"   - PASSWORD: {REDIS_PASSWORD} (类型: {type(REDIS_PASSWORD).__name__})")

# 检查密码类型
if isinstance(REDIS_PASSWORD, str):
    if REDIS_PASSWORD.lower() == "none":
        print("   ⚠️  警告: 密码是字符串 'None'！这会被当成真实密码。请在 config.py 里改成 Python 的 None (没有引号)。")
    elif REDIS_PASSWORD == "":
        print("   ⚠️  警告: 密码是空字符串！如果 Redis 无密码，建议设为 None。")

print("\n2. 尝试连接 Docker Redis...")
try:
    # 模拟 cache.py 的连接逻辑
    client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        socket_connect_timeout=3, # 3秒连不上就算输
        socket_timeout=3
    )
    
    # 发送 Ping
    response = client.ping()
    
    if response:
        print("   ✅ 连接成功！(PONG)")
        print("   🚀 结论: 配置没问题，是 cache.py 代码逻辑可能有误。")
        
        # 写入测试
        client.set("test_health_check", "ok", ex=10)
        val = client.get("test_health_check")
        print(f"   📝 读写测试: 写入 'ok' -> 读取 '{val.decode('utf-8')}'")

except redis.exceptions.AuthenticationError:
    print("   ❌ 认证失败 (AuthenticationError)")
    print("   👉 原因: Docker 容器没设密码，但 config.py 里填了密码；或者反之。")
    print("   👉 建议: 你当前的 Docker 是无密码模式，请确保上面的 PASSWORD 显示为 None。")

except redis.exceptions.ConnectionError:
    print("   ❌ 连接被拒 (ConnectionError)")
    print("   👉 原因: 找不到 Redis 服务。")
    print("   👉 建议: 运行 'docker ps' 确认容器名为 aichef-redis 且端口是 0.0.0.0:6379->6379")

except Exception as e:
    print(f"   ❌ 其他错误: {e}")

print("="*40)