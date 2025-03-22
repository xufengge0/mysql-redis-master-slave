## MySQL 主从复制启动流程

按照以下步骤设置并启动 `mysql-master-slave` 文件夹中的 MySQL 主从复制配置。

1. **启动 Docker Compose 服务**：
-
  ```
  docker compose up -d
  ```
2. **连接主库，创建复制用户**：
- 连接到主节点（例如 `mysql-master`）。
- 执行以下 SQL 命令创建复制用户并授予权限：
  ```sql
  CREATE USER 'repl'@'%' IDENTIFIED WITH 'mysql_native_password' BY 'replpassword';
  GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
  FLUSH PRIVILEGES;
  ```
- 记录主库的二进制日志文件和位置，用于从库配置：
  ```sql
  SHOW MASTER STATUS;
  ```
  记录输出的 `File`（如 `mysql-bin.000001`）和 `Position`（如 `154`），后续从库配置时需要。

3. **连接从库，填入主库的信息、启动、检查**：
- 连接到从节点（例如 `mysql-slave`）。
- 配置从库以从主库复制，使用记录的 `File` 和 `Position`：
  ```sql
  CHANGE MASTER TO MASTER_HOST='mysql-master', MASTER_USER='repl', MASTER_PASSWORD='replpassword', MASTER_LOG_FILE='mysql-bin.000001', MASTER_LOG_POS=544;
  ```
- 启动复制进程：
  ```sql
  START SLAVE;
  ```
- 检查复制状态：
  ```sql
  SHOW SLAVE STATUS\G;
  ```
  检查 `Slave_IO_Running` 和 `Slave_SQL_Running` 是否都为 `Yes`，表示复制正常。
4. **测试，主库写、从库查**：
   - 在主库中创建测试数据库和表，并插入数据：
     ```sql
     USE testdb;
     CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50));
     INSERT INTO users (name) VALUES ('Alice');
     ```
   - 在从库中查询数据，验证复制是否正常：
     ```sql
     SELECT * FROM testdb.users;
     ```

5. **配置 ProxySQL**：
   - 连接到 ProxySQL 管理接口：
     ```
     mysql -uadmin -padmin -h 127.0.0.1 -P 6032
     ```
   - 添加 MySQL 服务器：
     ```sql
     -- 添加主库（写组，hostgroup_id=1）
     INSERT INTO mysql_servers (hostgroup_id, hostname, port) VALUES (1, 'mysql-master', 3306);
     -- 添加从库（读组，hostgroup_id=2）
     INSERT INTO mysql_servers (hostgroup_id, hostname, port) VALUES (2, 'mysql-slave', 3306);
     ```
   - 配置读写分离规则：
     ```sql
     DELETE FROM mysql_query_rules;
     INSERT INTO mysql_query_rules (rule_id, active, match_digest, destination_hostgroup, apply) VALUES
     (1, 1, '^SELECT.*FOR UPDATE', 1, 1),  -- 带锁的 SELECT 到主节点
     (2, 1, '^SELECT.*', 2, 1),            -- 普通 SELECT 到从节点
     (3, 1, '.*', 1, 1);                   -- 其他操作（写）到主节点
     LOAD MYSQL QUERY RULES TO RUNTIME;
     SAVE MYSQL QUERY RULES TO DISK;
     ```
   - 添加 MySQL 用户：
     ```sql
     INSERT INTO mysql_users (username, password, default_hostgroup) VALUES ('root', 'rootpassword', 1);
     ```
   - 应用配置：
     ```sql
     LOAD MYSQL SERVERS TO RUNTIME;
     LOAD MYSQL QUERY RULES TO RUNTIME;
     LOAD MYSQL USERS TO RUNTIME;
     SAVE MYSQL SERVERS TO DISK;
     SAVE MYSQL QUERY RULES TO DISK;
     SAVE MYSQL USERS TO DISK;
     ```
   - 检查数据库状态：
     ```sql
     SELECT * FROM runtime_mysql_servers;
     ```
   - 检查主从分离配置：
     ```sql
     SELECT * FROM mysql_replication_hostgroups;
     ```
   - 查看读写请求配置信息：
     ```sql
     SELECT rule_id, active, match_digest, destination_hostgroup, apply FROM runtime_mysql_query_rules ORDER BY rule_id;
     ```
   - 查看读写请求代理情况：
     ```sql
     SELECT hostgroup, digest_text, count_star FROM stats.stats_mysql_query_digest ORDER BY count_star DESC;
     ```
   - 在主库添加用户用于 ProxySQL 监视：
     ```sql
     CREATE USER 'monitor'@'%' IDENTIFIED BY 'monitor';
     GRANT REPLICATION CLIENT ON *.* TO 'monitor'@'%';
     GRANT SELECT ON mysql.* TO 'monitor'@'%';
     FLUSH PRIVILEGES;
     ```

6. **可能的报错及解决方法**：
   - **挂载文件权限太大，挂载后被忽略**：
     ```
     mysql: [Warning] World-writable config file '/etc/mysql/conf.d/master.cnf' is ignored.
     ```
     **解决方法**：在宿主机上修改 `master.cnf` 和 `slave.cnf` 的文件权限为 0644：
     ```
     chmod 0644 master.cnf slave.cnf
     ```
   - **认证插件报错**：
     ```
     Last_IO_Errno: 2061
     Last_IO_Error: Error connecting to source 'repl@mysql-master:3306'. This was attempt 1/86400, with a delay of 60 seconds between attempts. Message: Authentication plugin 'caching_sha2_password' reported error: Authentication requires secure connection.
     ```
     **原因**：MySQL 8.0 默认使用 `caching_sha2_password` 作为认证插件，它要求连接使用 SSL 加密。如果未配置 SSL（当前 `Master_SSL_Allowed: No`），就会报错。
     **解决方法**：将主库的 `repl` 用户认证插件改为 `mysql_native_password`，以避免 SSL 要求，然后重新启动从库复制：
     - 连接到主库：
       ```
       docker exec -it mysql-master mysql -uroot -prootpassword
       ```
     - 检查用户认证插件：
       ```sql
       SELECT user, host, plugin FROM mysql.user WHERE user = 'repl' AND host = '%';
       ```
     - 修改认证插件：
       ```sql
       ALTER USER 'repl'@'%' IDENTIFIED WITH 'mysql_native_password' BY 'replpassword';
       FLUSH PRIVILEGES;
       ```
     - 重新检查主库状态：
       ```sql
       SHOW MASTER STATUS;
       ```
