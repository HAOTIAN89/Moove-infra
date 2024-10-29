# stop the milvus standalone
# sudo docker compose down
# delete the data in the milvus standalone
# sudo rm -rf volumes
# start the milvus standalone again
# sudo docker compose up -d

# if showing error "network milvus was found but has incorrect label com.docker.compose.network set to "milvus""
# then execute the following commands
# use "docker network ls" list all network
# use "docker network rm milvus" delete milvus network
# run "docker compose up" again will work