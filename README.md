
此存储库包含用于设置数据库集群（包括 MySQL 和 Redis）的 Docker Compose 配置。每个文件夹对应于一个特定的数据库设置，专为高可用性、可伸缩性和测试目的而设计。以下是每个文件夹及其用途的概述。

# 1. mysql-cluster
此文件夹包含用于部署 MySQL NDB 群集的 Docker Compose 配置 ，这是一种使用 NDB 存储引擎的分布式高可用性数据库解决方案。

# 2. mysql-master-slave
此文件夹包含用于部署 MySQL 主从复制设置的 Docker Compose 配置 ，这是一种用于读取可扩展性和基本容错能力的传统复制架构。

# 3. redis-cluster
此文件夹包含用于部署 Redis 集群的 Docker Compose 配置 ，Redis 集群是一个分布式键值存储，具有分片和复制功能，可实现可扩展性和高可用性。

# 4. redis-sentinel
此文件夹包含一个 Docker Compose 配置，用于使用 Redis Sentinel 部署 Redis 主从复制设置  ，以实现高可用性和自动故障转移。
