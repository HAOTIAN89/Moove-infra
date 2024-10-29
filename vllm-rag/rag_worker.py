from fastapi import FastAPI
from pydantic import BaseModel
from pymilvus import (
    connections, Collection, FieldSchema, CollectionSchema, DataType, utility
)
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
from typing import List
from contextlib import asynccontextmanager
import os
import json


MARKDOWN_SEPARATORS = [
    "\n#{1,6} ",
    "```\n",
    "\n\\*\\*\\*+\n",
    "\n---+\n",
    "\n___+\n",
    "\n\n",
    "\n",
    " ",
    "",
]

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('omw-1.4')

# global database information
GROUPS_FILE = "./database/groups.json"

@asynccontextmanager
async def lifespan(app: FastAPI):
    global groups
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as file:
            groups = json.load(file)
    else:
        groups = {}
        
    yield

    with open(GROUPS_FILE, "w") as file:
        json.dump(groups, file)

app = FastAPI(lifespan=lifespan)

# client = MilvusClient("./database/milvus_demo.db")
connections.connect(
    alias='default',
    host='localhost',
    port='19530'
)

model = SentenceTransformer(
    "dunzhang/stella_en_400M_v5",
    trust_remote_code=True
).cuda()

class GroupNameInput(BaseModel):
    group_name: str

class DocumentInput(BaseModel):
    group_name: str
    document_name: str
    document: str
    chunk_size: int = 10

class DeleteDocumentInput(BaseModel):
    group_name: str
    document_name: str

class SearchInput(BaseModel):
    group_name: str
    query: str
    top_k: int = 3

def create_index_if_not_exists(collection: Collection, field_name: str = "embedding"):
    # Define the index parameters
    index_params = {
        "metric_type": "IP",
        "index_type": "IVF_FLAT", 
        "params": {"nlist": 128}
    }
    
    # Check existing indexes
    existing_indexes = collection.indexes
    if not any(idx.field_name == field_name for idx in existing_indexes):
        collection.create_index(field_name, index_params)
        print(f"Index created on field '{field_name}'.")
    else:
        print(f"Index already exists on field '{field_name}'.")
    
def create_collection(group_name: str, embedding_dim: int = 1024):
    if utility.has_collection(group_name):
        return Collection(name=group_name)
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=embedding_dim),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="document_name", dtype=DataType.VARCHAR, max_length=256)
    ]
    schema = CollectionSchema(fields, description=f"Collection for group {group_name}")
    collection = Collection(name=group_name, schema=schema)
    return collection

@app.post("/add_group/")
def add_group(input_data: GroupNameInput):
    group_name = input_data.group_name
    try:
        create_collection(group_name)
        return {"message": f"Group {group_name} created."}
    except Exception as e:
        return {"error": str(e)}
    
@app.delete("/delete_group/")
def delete_group(input_data: GroupNameInput):
    group_name = input_data.group_name
    try:
        if not utility.has_collection(group_name):
            return {"warning": f"Group {group_name} does not exist."}
        collection = Collection(name=group_name)
        collection.drop()
        # Remove group from groups dictionary
        if group_name in groups:
            del groups[group_name]
        return {"message": f"Group {group_name} deleted."}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/add_document/")
def add_document(input_data: DocumentInput):
    group_name = input_data.group_name
    document = input_data.document
    chunk_size = input_data.chunk_size
    document_name = input_data.document_name
    try:
        if not utility.has_collection(group_name):
            create_collection(group_name)
        collection = Collection(name=group_name)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=int(chunk_size / 10),
            add_start_index=True,
            strip_whitespace=True,
            separators=MARKDOWN_SEPARATORS,
        )
        texts = splitter.split_text(document)

        stop_words = set(stopwords.words('english'))
        cleaned_texts = []
        for text in texts:
            tokens = word_tokenize(text)
            tokens = [w for w in tokens if not w.lower() in stop_words]
            cleaned_text = ' '.join(tokens)
            cleaned_texts.append(cleaned_text)

        doc_embeddings = model.encode(cleaned_texts).tolist()
        
        number_chunks = len(cleaned_texts)
        data = [
            doc_embeddings,
            cleaned_texts,
            [document_name]*number_chunks
        ]

        collection.insert(data)
        
        # Create index if it doesn't exist
        create_index_if_not_exists(collection)
        
        # Load the collection to make the index effective
        collection.load()
        
        # Update groups dictionary
        if group_name not in groups:
            groups[group_name] = []
        if document_name not in groups[group_name]:
            groups[group_name].append(document_name)
        
        return {"message": f"Document added to group {group_name}. Totally {number_chunks} chuncks are stored."}
    except Exception as e:
        return {"error": str(e)}
    
@app.delete("/delete_document/")
def delete_document(input_data: DeleteDocumentInput):
    group_name = input_data.group_name
    document_name = input_data.document_name
    try:
        if not utility.has_collection(group_name):
            return {"warning": f"Group {group_name} does not exist."}
        collection = Collection(name=group_name)
        expr = f'document_name == "{document_name}"'
        collection.delete(expr)
        # Update groups dictionary
        if group_name in groups and document_name in groups[group_name]:
            groups[group_name].remove(document_name)
            if not groups[group_name]:
                del groups[group_name]
        return {"message": f"Document '{document_name}' deleted from group '{group_name}'."}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/search/")
def search(input_data: SearchInput):
    group_name = input_data.group_name
    query = input_data.query
    top_k = input_data.top_k

    try:
        if not utility.has_collection(group_name):
            return {"error": f"Group {group_name} does not exist."}

        collection = Collection(name=group_name)
        
        # Load the collection into memory
        collection.load()

        tokens = word_tokenize(query)
        stop_words = set(stopwords.words('english'))
        tokens = [w for w in tokens if not w.lower() in stop_words]
        cleaned_query = ' '.join(tokens)

        query_embedding = model.encode(
            [cleaned_query],
            prompt_name="s2p_query"
        ).tolist()

        search_params = {"metric_type": "IP", "params": {"nprobe": 10}}

        results = collection.search(
            data=query_embedding,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "document_name"]
        )

        search_results = []
        for hits in results:
            for hit in hits:
                search_results.append({
                    "id": hit.id,
                    "distance": hit.distance,
                    "text": hit.entity.get('text'),
                    "document_name": hit.entity.get('document_name')
                })

        return {"results": search_results}

    except Exception as e:
        return {"error": str(e)}
    
@app.get("/get_groups/")
def get_groups(input_data: GroupNameInput):
    try:
        return {"groups": groups}
    except Exception as e:
        return {"error": str(e)}
    
