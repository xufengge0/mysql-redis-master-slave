import io
import sys
import mysql.connector
from mysql.connector import Error

# 设置标准输出和错误输出的编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
def connect_to_cluster():
    """连接到 MySQL 集群的 API 节点"""
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",  # API 节点地址
            port=13306,            # 默认 MySQL 端口
            user="root",          # 替换为你的 MySQL 用户名
            password="password",  # 替换为你的 MySQL 密码
        )
        if connection.is_connected():
            print("成功连接到 MySQL 集群，API 节点: ",connection.get_server_info())
            return connection
    except Error as e:
        print(f"连接失败: {e}")
        return None

def create_test_database(connection):
    """创建测试数据库和表"""
    try:
        cursor = connection.cursor()
        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS test_cluster_db")
        cursor.execute("USE test_cluster_db")
        
        # 创建表（使用 NDB 存储引擎）
        create_table_query = """
        CREATE TABLE IF NOT EXISTS test_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            value INT
        ) ENGINE=NDBCLUSTER
        """
        cursor.execute(create_table_query)
        print("测试数据库和表创建成功")
    except Error as e:
        print(f"创建数据库/表失败: {e}")
        return False
    return True

def insert_test_data(connection):
    """插入测试数据"""
    try:
        cursor = connection.cursor()
        insert_query = "INSERT INTO test_table (name, value) VALUES (%s, %s)"
        test_data = [
            ("Alice", 100),
            ("Bob", 200),
            ("Charlie", 300)
        ]
        cursor.executemany(insert_query, test_data)
        connection.commit()
        print(f"成功插入 {cursor.rowcount} 条数据")
    except Error as e:
        print(f"插入数据失败: {e}")
        return False
    return True

def query_test_data(connection):
    """查询测试数据"""
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM test_table")
        rows = cursor.fetchall()
        print("查询结果:")
        for row in rows:
            print(row)
    except Error as e:
        print(f"查询数据失败: {e}")
        return False
    return True

def cleanup(connection):
    """清理测试数据"""
    try:
        cursor = connection.cursor()
        cursor.execute("DROP DATABASE IF EXISTS test_cluster_db")
        connection.commit()
        print("测试数据库已清理")
    except Error as e:
        print(f"清理失败: {e}")
    finally:
        if connection.is_connected():
            connection.close()
            print("数据库连接已关闭")

def main():
    # 连接到集群
    connection = connect_to_cluster()
    if not connection:
        return

    # 创建测试数据库和表
    if not create_test_database(connection):
        cleanup(connection)
        return

    # 插入测试数据
    if not insert_test_data(connection):
        cleanup(connection)
        return

    # 查询测试数据
    if not query_test_data(connection):
        cleanup(connection)
        return

    # 清理
    cleanup(connection)

if __name__ == "__main__":
    main()