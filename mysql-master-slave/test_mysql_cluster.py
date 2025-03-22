import mysql.connector
import time

PROXYSQL_HOST = "127.0.0.1"
PROXYSQL_PORT = 6033
USER = "root"
PASSWORD = "rootpassword"
DATABASE = "testdb"

def write_data(name):
    conn = mysql.connector.connect(host=PROXYSQL_HOST, port=PROXYSQL_PORT, user=USER, password=PASSWORD, database=DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name) VALUES (%s)", (name,))
        conn.commit()
        print(f"Inserted '{name}' into master.")
    except mysql.connector.Error as err:
        print(f"Write error: {err}")
    finally:
        cursor.close()
        conn.close()

def read_data():
    conn = mysql.connector.connect(host=PROXYSQL_HOST, port=PROXYSQL_PORT, user=USER, password=PASSWORD, database=DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        print("Read from slave:")
        for row in rows:
            print(row)
    except mysql.connector.Error as err:
        print(f"Read error: {err}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    write_data("TestFailover")
    time.sleep(1)
    read_data()
    print("Simulating master failure...")
    
    # 手动停止 mysql-master: docker stop mysql-master
    # time.sleep(5)  # 等待 ProxySQL 检测故障
    # write_data("PostFailover")  # 若无自动切换，此处会失败
    # read_data()