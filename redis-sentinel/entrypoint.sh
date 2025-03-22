#!/bin/sh
until ping -c 1 redis-master >/dev/null 2>&1; do
  echo "Waiting for redis-master DNS to resolve..."
  sleep 1
done
MASTER_IP=$(getent hosts redis-master | awk '{print $1}' | head -n 1)
if [ -z "$MASTER_IP" ]; then
  echo "Failed to resolve redis-master IP, exiting..."
  exit 1
fi
echo "Resolved redis-master IP: $MASTER_IP"
# 复制配置文件到临时位置
cp /usr/local/etc/redis/sentinel.conf /tmp/sentinel.conf
# 修改临时文件
sed -i "s/sentinel monitor mymaster redis-master 6379 2/sentinel monitor mymaster $MASTER_IP 6379 2/" /tmp/sentinel.conf
echo "Starting sentinel with updated config..."
exec redis-sentinel /tmp/sentinel.conf