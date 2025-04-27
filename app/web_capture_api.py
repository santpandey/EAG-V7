from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os
from pathlib import Path
from datetime import datetime
import hashlib

router = APIRouter()

DOCUMENTS_DIR = Path(__file__).parent / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)

from fastapi import Query
from fastapi.responses import JSONResponse
from app.example3 import search_documents, process_documents
import re

@router.get("/search_documents")
async def search_documents_api(query: str = Query(...)):
    try:
        import urllib.parse
        original_query = query
        # If the query seems URL-encoded, decode it
        if '%' in query:
            query = urllib.parse.unquote(query)
        print(f"[DEBUG] User query received: '{original_query}', decoded for highlight: '{query}'")
        results = search_documents(query)
        if not results or not isinstance(results, list):
            return JSONResponse(status_code=404, content={"error": "No results found"})
        # Find the first result that looks like it has a [Source: ...] annotation
        for idx, result in enumerate(results):
            match = re.search(r"\[Source: ([^,\]]+)", result)
            if not match:
                continue  # Skip results without a source annotation
            docname = match.group(1)
            chunk_text = result.split("[Source:")[0].strip()
            doc_path = DOCUMENTS_DIR / docname
            if not doc_path.exists():
                # Log missing file for debugging
                print(f"[ERROR] Document file not found: {doc_path}")
                continue
            try:
                with open(doc_path, encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if first_line.startswith("URL: "):
                        url = first_line[5:].strip()
                        return {"weblink": url, "text": chunk_text, "highlight_text": query, "highlight": True}
            except Exception as file_err:
                print(f"[ERROR] Failed to open/read {doc_path}: {file_err}")
                continue
            # If no URL found, still return text
            return {"weblink": None, "text": chunk_text, "highlight_text": query, "highlight": False}
        # If no valid result found
        print(f"[INFO] No valid result found for query: {query}")
        return JSONResponse(status_code=404, content={"error": "No relevant document found or document file missing."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/save_web_content")
async def save_web_content(request: Request):
    data = await request.json()
    url = data.get("url")
    content = data.get("content")
    if not url or not content:
        return JSONResponse(status_code=400, content={"error": "Missing url or content"})

    # Generate unique filename based on timestamp and hash of url
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    filename = f"web_{now}_{url_hash}.doc"
    file_path = DOCUMENTS_DIR / filename

    # Save URL and content to file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n\n{content}")

    # Update FAISS index
    try:
        process_documents()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Saved file but failed to update index: {e}"})

    return {"status": "success", "file": str(file_path)}
