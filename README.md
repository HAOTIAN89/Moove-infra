# Moove-infra

Moove-infra is the infrastructure of the models used on the Moove platform, and consists of model launcher, rag worker and infrastructure controller. 
We use native `vllm serve` as model launcher, use [milvus-io/milvus](https://github.com/milvus-io/milvus) as the vector database, 
and use `fastapi` framework to build the rag worker and infrastructure controller.

## How to start it
To start the Moove-infra, you should first set up the environment by running
```sh
./setup.sh
```
Then install and start the `milvus` open-source vector database by [docker or docker compose](https://milvus.io/docs/install_standalone-docker.md)

If you want to use docker compose to install, the config file and commands are already in the `vllm-rag/milvus`.

