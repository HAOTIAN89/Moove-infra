# Moove-infra

Moove-infra provides the infrastructure for the models used on the Moove platform, comprising a model launcher, RAG (Retrieval-Augmented Generation) worker, and infrastructure controller. The setup utilizes `vllm serve` as the model launcher, [Milvus](https://github.com/milvus-io/milvus) as the vector database, and the `FastAPI` framework to build the RAG worker and infrastructure controller.

## How to start it
To start Moove-infra, you should first set up the environment by running:
```sh
./setup.sh
```
Next, install and start the `Milvus` open-source vector database using either [docker or docker compose](https://milvus.io/docs/install_standalone-docker.md).

If you prefer to use Docker Compose, the configuration file and necessary commands are available in the `vllm-rag/milvus` directory.

After starting Milvus, initiate the model launcher by running: 
```sh
./model_launch.sh
```
from within the `vllm-serve` folder.

Then, start the RAG worker and infrastructure controller by running:
```sh
./rag_worker_launch.sh
```
in the `vllm-rag` folder and 
```sh
./app_launch.sh
```
in the `vllm-serve` folder.

## How to use it
Moove-infra currently supports direct operations on vector databases and LLM (Large Language Model) answer generation with RAG enhancements. For detailed usage, please refer to the following test cases

- `test/add_group.sh`: creates one group/organization in the vector database if it doesn't already exist.
- `test/delete_group.sh`: deletes one existing group/organization from the vector databse.
- `test/add_document.sh`: adds chunks of a specified document to a specific group/organization in the vector database, provided that the group/organization exists.
- `test/add_document.sh`: deletes all chunks of a specified document from a group/organization in the vector database if the document exists in that group/organization.
- `test/get_information.sh`: retrieves information about all groups/organizations in a dictionary format.
- `test/search.sh`: searches for and retrieves targeted chunks, which will be added to the user prompt in the llm_call_with_rag.sh.
- `test/llm_call_without_rag.sh`: get the llm response without RAG enhancement。
- `test/llm_call_with_rag.sh`: get the llm response with RAG enhancement.
