# Moove-infra

Moove-infra is the infrastructure of the models used on the Moove platform, and consists of model launcher, rag worker and infrastructure controller. 
We use native `vllm serve` as model launcher, use [milvus-io/milvus](https://github.com/milvus-io/milvus) as the vector database, 
and use `fastapi` framework to build the rag worker and infrastructure controller.

## How to start it
