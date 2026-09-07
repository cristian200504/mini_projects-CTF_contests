#!/bin/bash
export MONGODB_ADMIN_PW=$(head -c $((64*10)) /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
export MONGO_INITDB_ROOT_USERNAME=admin
export MONGO_INITDB_ROOT_PASSWORD=$MONGODB_ADMIN_PW
echo -e "\n\n[entrypoint] MongoDB Admin Password: $MONGODB_ADMIN_PW\n\n"

docker-entrypoint.sh mongod -f /etc/mongod.conf &

echo -e "\n\n[entrypoint] Waiting 10s to give MongoDB time before probing...\n\n"
sleep 2

until mongosh "mongodb://admin:$MONGODB_ADMIN_PW@127.0.0.1:27017?authSource=admin" --quiet --eval "db.adminCommand('ping')" &>/dev/null; do
  echo -e "\n\n[entrypoint] Waiting for MongoDB to be ready..\n\n."
  sleep 1
done

echo -e "\n\n[entrypoint] Seemingly ready, waiting 5s to be sure...\n\n"
sleep 5 && echo -e "\n\n[entrypoint] Starting bun.js backend\n\n" && /backend
