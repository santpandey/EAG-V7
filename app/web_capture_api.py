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
from example3 import search_documents
import re

@router.get("/search_documents")
async def search_documents_api(query: str = Query(...)):
    try:
        results = search_documents(query)
        if not results or not isinstance(results, list):
            return JSONResponse(status_code=404, content={"error": "No results found"})
        # Find the first result that looks like it has a [Source: ...] annotation
        for result in results:
            match = re.search(r"\[Source: ([^,\]]+)", result)
            if match:
                docname = match.group(1)
                chunk_text = result.split("[Source:")[0].strip()
                # Try to extract the weblink from the .doc file
                doc_path = DOCUMENTS_DIR / docname
                if doc_path.exists():
                    with open(doc_path, encoding="utf-8") as f:
                        first_line = f.readline().strip()
                        if first_line.startswith("URL: "):
                            url = first_line[5:].strip()
                            return {"weblink": url, "text": chunk_text}
                # If no URL found, still return text
                return {"weblink": None, "text": chunk_text}
        # If no valid result found
        return JSONResponse(status_code=404, content={"error": "No relevant document found"})
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

    return {"status": "success", "file": str(file_path)}
