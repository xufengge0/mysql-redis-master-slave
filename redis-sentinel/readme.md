## Redis 主从同步并配置哨兵

按照以下步骤设置并启动 `redis-sentinel` 文件夹中的 Redis 主从复制和 Sentinel 高可用性配置。

1. **部署 Redis 主从复制**：
   - **启动 Docker Compose 服务**：
     ```
     docker compose up -d
     ```
   - **主节点 (redis-master)**：
     - 运行在 `redis-master:6379`，映射到主机 `localhost:6379`，提供读写服务。
   - **从节点 (redis-slave1 和 redis-slave2)**：
     - 通过 `--slaveof redis-master 6379` 配置为从节点，同步主节点数据。
     - 分别映射到主机 `localhost:6380` 和 `localhost:6381`，提供只读服务。
   - **作用**：
     - 读写分离：主节点处理写操作，从节点处理读操作，提升读性能。

2. **通过 Sentinel 实现高可用性**：
   - **Sentinel 节点**：
     - 3 个 Sentinel 节点（`sentinel1`、`sentinel2`、`sentinel3`）分别运行在 26379 端口，映射到主机 26379、26380、26381 端口。
     - 使用 `sentinel1.conf` 配置文件，内容如下：
       ```
       port 26379
       dir /tmp
       sentinel monitor mymaster redis-master 6379 2
       sentinel down-after-milliseconds mymaster 5000
       sentinel parallel-syncs mymaster 1
       sentinel failover-timeout mymaster 15000
       sentinel announce-port 26379
       ```
   - **作用**：
     - 监控主节点和从节点的状态。
     - 如果主节点宕机，Sentinel 会选举一个从节点（例如 `redis-slave1`）为主节点，并重新配置其他从节点指向新主节点，主节点恢复后自动成为新主节点（例如 `redis-slave1`）的从节点。
   - **验证 Sentinel 状态**：
     - 连接到 Sentinel 节点（例如 `sentinel1`）：
       ```
       redis-cli -h localhost -p 26379
       ```
     - 检查主节点地址：
       ```
       SENTINEL get-master-addr-by-name mymaster
       ```
     - 预期输出为主节点的 IP 和端口（例如 `172.18.0.2 6379`）。
