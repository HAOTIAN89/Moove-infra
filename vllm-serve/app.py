from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from starlette.middleware.cors import CORSMiddleware
from typing import AsyncGenerator
import logging

# log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Backend server URLs
VLLM_SERVER_URL = "http://0.0.0.0:8080"
RAG_SERVER_URL = "http://127.0.0.1:8001"

# Default system prompt
DEFAULT_SYSTEM_PROMPT = """## Guiding Principles

- Respectful, polite interaction: You must always engage in a respectful, polite, and courteous manner, maintaining professionalism in all interactions
- Honest, evidence-based information: All responses should be meticulously detail-oriented and based on the latest medical evidence and guidelines
- Ethical and safe content: Under no circumstances should you provide fake, harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. If a question is unclear or factually incorrect, you should explain why rather than attempting to answer it inaccurately. Start and end with a warning that this content must be verified

You should always follw the following template : 

- Introduction

    - Begin with a polite introduction, you are a medical AI assistant

- Acknowledge the question

    - Summarize the user’s question succinctly
    - Use empathy when appropriate, especially if the question involves sensitive or urgent issues
    - Determine if the user is a medical professional or a layperson based on the question and adapt the response accordingly

- Critical content filter

    - Ensure all content is appropriate and safe, adhering to ethical guidelines.
    - If emergent care is needed, advise the user to seek immediate medical attention.

- Structured, prioritized information

    - Headings and subheadings: Break down the response into clear sections with headings and subheadings in markdown format
    - Lists and bullet points: Use bulleted or numbered lists to organize information logically and clearly

- Contextual Adaptation

    - Tailor responses to the geographical context, resource setting, level of care, seasonality/epidemiology, and medical specialty as relevant

## Specific Scenarios

- Diagnosis queries

    - Provide a list of possible diagnoses in order of probability
    - **Rationale**: Briefly explain the reasoning behind each diagnosis
    - **Diagnostic** steps: Detail the main steps needed to confirm the diagnosis and be nuanced

- Treatment advice

    - Provide a list of possible treatments for the most likely diagnoses
    - Rationale: Explain the rationale for each treatment option
    - Interactions and contraindications: Detail possible interactions or contraindications relevant to the context (e.g. pregnancy/age/comorbidity considerations)
    - Dosage: Provide a ballpark estimate of the dosage but always provide a concise warning that this should be checked in the form of “(dosages should be verified)”

- Summary of recommendations

    - Conclude with a concise summary of recommendations, ensuring clarity and actionable advice.
    
ALWAYS FOLLOW THE NICE MARKDOWN FORMAT"""

client = httpx.AsyncClient()

# Define RAG server paths
RAG_PATHS = {
    "POST": ["/add_group/", "/add_document/", "/search/"],
    "DELETE": ["/delete_group/", "/delete_document/"],
    "GET": ["/get_groups/"],
}

def is_rag_path(method: str, path: str) -> bool:
    """Determine if the request should be routed to the RAG server."""
    paths = RAG_PATHS.get(method.upper(), [])
    for rag_path in paths:
        if path.startswith(rag_path.strip("/")):
            return True
    return False

@app.api_route("/{path:path}", methods=["GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS"])
async def proxy(request: Request, path: str):
    method = request.method
    logger.info(f"Incoming request: {method} {path}")

    if is_rag_path(method, path):
        target_url = f"{RAG_SERVER_URL}/{path}"
        logger.info(f"Routing to RAG server: {target_url}")
        modify_body = False
    else:
        target_url = f"{VLLM_SERVER_URL}/{path}"
        logger.info(f"Routing to VLLM server: {target_url}")
        modify_body = True

    # Prepare headers, excluding 'host', 'content-length', and 'transfer-encoding'
    excluded_headers = {"host", "content-length", "transfer-encoding"}
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in excluded_headers
    }

    # Read the body if present
    try:
        if request.headers.get("content-type", "").startswith("application/json"):
            body = await request.json()
        else:
            body = await request.body()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid request body") from e
    
    logger.info(f"modfiy body: {modify_body}")

    # Modify the body for VLLM requests
    if modify_body and method.upper() == "POST":
        try:
            if path.endswith("/chat/completions") or path.endswith("/completions"):
                body = await add_default_system_prompt(path, body)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error modifying request body") from e

    # Forward the request to the appropriate backend
    try:
        resp = await client.request(
            method=method,
            url=target_url,
            headers=headers,
            json=body if isinstance(body, dict) else None,
            content=body if not isinstance(body, dict) else None,
            timeout=None if modify_body and method.upper() == "POST" and body.get("stream", False) else 120.0
        )
    except httpx.RequestError as e:
        logger.error(f"Request forwarding error: {e}")
        raise HTTPException(status_code=502, detail=f"Error forwarding request: {e}") from e

    # Handle streaming responses for VLLM
    if modify_body and method.upper() == "POST" and body.get("stream", False):
        response_headers = dict(resp.headers)
        response_headers.pop("Content-Length", None)
        response_headers.pop("Transfer-Encoding", None)

        async def event_generator(resp: httpx.Response) -> AsyncGenerator[bytes, None]:
            async for chunk in resp.aiter_bytes():
                yield chunk

        return StreamingResponse(event_generator(resp), status_code=resp.status_code, headers=response_headers)

    # For non-streaming responses or RAG server responses
    response_headers = dict(resp.headers)
    excluded_response_headers = {"content-length", "transfer-encoding", "content-encoding", "connection"}
    response_headers = {k: v for k, v in response_headers.items() if k.lower() not in excluded_response_headers}

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers
    )

async def add_default_system_prompt(path: str, body: dict) -> dict:
    """
    Add the default system prompt to the request body for VLLM server.
    """
    logger.info(f"Original body: {body}")
    
    with_rag = body.get("with_rag", False)
    group_name = body.get("group_name", "")
    top_k = body.get("top_k", 0)
    
    if with_rag and group_name and top_k:
        try:
            if path.endswith("/chat/completions"):
                messages = body.get("messages", [])
                # Find the index of the last user message
                for idx in reversed(range(len(messages))):
                    if messages[idx].get("role") == "user":
                        query = messages[idx].get("content", "")
                        last_user_idx = idx
                        break
                else:
                    query = ""
                    last_user_idx = None
            elif path.endswith("/completions"):
                query = body.get("prompt", "")
            else:
                query = ""
                
            if len(query) == 0:
                pass
            
            # build the request to the RAG system if query is valid
            print("begin to prepare the search payload: ")
            search_payload = {
                "group_name": group_name,
                "query": query,
                "top_k": top_k
            }
            print(search_payload)
            
            # send the request to the /search/ endpoint of the RAG system
            rag_response = await client.post(f"{RAG_SERVER_URL}/search/", json=search_payload)
            if rag_response.status_code == 200:
                rag_results = rag_response.json()
                texts = [result.get('text', '') for result in rag_results.get('results', [])]
                combined_text = "\nDocument: " + "\nDocument: ".join(texts)
                print("combined_text: ", combined_text)
                # add the combined_text reference into the user prompt
                if path.endswith("/chat/completions") and last_user_idx is not None:
                    messages[last_user_idx]['content'] += f"\n\nReference:\n{combined_text}"
                elif path.endswith("/completions"):
                    body['prompt'] += f"\n\nReference:\n{combined_text}"
            else:
                logger.error(f"RAG search failed with status code {rag_response.status_code}")
        except Exception as e:
            logger.error(f"Error during RAG search: {e}")
            pass
    else:
        # no need for RAG system
        pass
    
    # remove these arguments before sending to the vllm serve
    body.pop('with_rag', None)
    body.pop('group_name', None)
    body.pop('top_k', None)
    
    if path.endswith("/chat/completions"):
        messages = body.get("messages", [])
        if not any(msg.get("role") == "system" for msg in messages):
            messages.insert(0, {"role": "system", "content": DEFAULT_SYSTEM_PROMPT})
            body["messages"] = messages
    elif path.endswith("/completions"):
        prompt = body.get("prompt", "")
        if not isinstance(prompt, str) or DEFAULT_SYSTEM_PROMPT not in prompt:
            if isinstance(prompt, str):
                body["prompt"] = f"{DEFAULT_SYSTEM_PROMPT}\n{prompt}"
            elif isinstance(prompt, list):
                body["prompt"] = [DEFAULT_SYSTEM_PROMPT] + prompt
            else:
                body["prompt"] = DEFAULT_SYSTEM_PROMPT
    
    logger.info(f"Modified body: {body}")
    return body

@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()
    logger.info("HTTP client closed.")