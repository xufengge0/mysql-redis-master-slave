import io
import redis
import time
import subprocess
import sys

# 设置标准输出和错误输出的编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
# Redis 节点配置
REDIS_MASTER_HOST = "localhost"
REDIS_MASTER_PORT = 6379
REDIS_SLAVE1_PORT = 6380
REDIS_SLAVE2_PORT = 6381
SENTINEL_PORTS = [26379, 26380, 26381]  # Sentinel 端口
MASTER_NAME = "mymaster"  # Sentinel 配置文件中定义的主节点名称（假设）

def connect_redis(host, port):
    """连接到 Redis 节点"""
    try:
        r = redis.Redis(host=host, port=port, decode_responses=True)
        r.ping()  # 测试连接
        print(f"成功连接到 Redis 节点: {host}:{port}")
        return r
    except redis.ConnectionError as e:
        print(f"连接失败: {host}:{port}, 错误: {e}")
        return None

def connect_sentinel(port):
    """连接到 Sentinel 节点"""
    try:
        s = redis.Sentinel([(REDIS_MASTER_HOST, port)], socket_timeout=0.5)
        print(f"成功连接到 Sentinel 节点: {REDIS_MASTER_HOST}:{port}")
        return s
    except redis.ConnectionError as e:
        print(f"连接 Sentinel 失败: {REDIS_MASTER_HOST}:{port}, 错误: {e}")
        return None

def test_write_and_read(redis_client, host, port):
    """测试写入和读取数据"""
    try:
        # 写入数据
        redis_client.set("test_key", "test_value")
        print(f"写入数据到 {host}:{port}: test_key = test_value")

        # 读取数据
        value = redis_client.get("test_key")
        print(f"从 {host}:{port} 读取数据: test_key = {value}")
        return value == "test_value"
    except redis.RedisError as e:
        print(f"操作失败: {host}:{port}, 错误: {e}")
        return False

def test_read_only(redis_client, host, port):
    """测试从节点只读"""
    try:
        # 尝试写入（应该失败）
        try:
            redis_client.set("slave_key", "slave_value")
            print(f"警告: 从节点 {host}:{port} 允许写入（不应该发生）")
            return False
        except redis.RedisError as e:
            print(f"从节点 {host}:{port} 写入失败（符合预期）: {e}")

        # 读取主节点写入的数据
        value = redis_client.get("test_key")
        print(f"从 {host}:{port} 读取主节点数据: test_key = {value}")
        return value == "test_value"
    except redis.RedisError as e:
        print(f"操作失败: {host}:{port}, 错误: {e}")
        return False

def get_master_from_sentinel(sentinel):
    """从 Sentinel 获取当前主节点地址"""
    try:
        master = sentinel.discover_master(MASTER_NAME)
        print(f"从 Sentinel 获取当前主节点: {master}")
        return master
    except redis.RedisError as e:
        print(f"获取主节点失败: {e}")
        return None

def simulate_master_failure():
    """模拟主节点故障（停止 redis-master 容器）"""
    print("模拟主节点故障，停止 redis-master 容器...")
    try:
        subprocess.run(["docker", "stop", "redis-master"], check=True)
        print("redis-master 已停止")
    except subprocess.CalledProcessError as e:
        print(f"停止 redis-master 失败: {e}")
        sys.exit(1)

def restart_master():
    """重启 redis-master 容器（测试后恢复）"""
    print("恢复 redis-master 容器...")
    try:
        subprocess.run(["docker", "start", "redis-master"], check=True)
        print("redis-master 已重启")
    except subprocess.CalledProcessError as e:
        print(f"重启 redis-master 失败: {e}")

def main():
    # # 1. 测试主节点读写
    # print("=== 测试主节点读写 ===")
    # master = connect_redis(REDIS_MASTER_HOST, REDIS_MASTER_PORT)
    # if not master:
    #     sys.exit(1)
    # if not test_write_and_read(master, REDIS_MASTER_HOST, REDIS_MASTER_PORT):
    #     print("主节点读写测试失败")
    #     sys.exit(1)

    # # 2. 测试从节点数据同步和只读
    # print("\n=== 测试从节点数据同步和只读 ===")
    # slave1 = connect_redis(REDIS_MASTER_HOST, REDIS_SLAVE1_PORT)
    # if slave1 and test_read_only(slave1, REDIS_MASTER_HOST, REDIS_SLAVE1_PORT):
    #     print("从节点 redis-slave1 数据同步和只读测试通过")
    # else:
    #     print("从节点 redis-slave1 测试失败")

    # slave2 = connect_redis(REDIS_MASTER_HOST, REDIS_SLAVE2_PORT)
    # if slave2 and test_read_only(slave2, REDIS_MASTER_HOST, REDIS_SLAVE2_PORT):
    #     print("从节点 redis-slave2 数据同步和只读测试通过")
    # else:
    #     print("从节点 redis-slave2 测试失败")

    # 3. 从 Sentinel 获取主节点地址
    print("\n=== 测试 Sentinel 获取主节点 ===")
    sentinel = None
    for port in SENTINEL_PORTS:
        sentinel = connect_sentinel(port)
        if sentinel:
            break
    if not sentinel:
        print("无法连接到任何 Sentinel 节点")
        sys.exit(1) 

    master_addr = get_master_from_sentinel(sentinel)
    if master_addr:
        print(f"当前主节点地址: {master_addr}")
    else:
        print("无法获取主节点地址")
        sys.exit(1)

if __name__ == "__main__":
    main()