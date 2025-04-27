# EAG-V7

## Overview

EAG-V7 is a document search and web capture system featuring:
- A FastAPI backend for searching indexed documents and saving new web content
- A browser extension (plugin) that lets users search for information and highlights the exact query on the destination web page
- Automatic highlighting of user queries with a red rectangle in the opened tab

---

## Backend (FastAPI) Setup

### Requirements
- Python 3.8+
- FastAPI
- Uvicorn
- Other dependencies as required (see your requirements.txt if present)

### Running the Backend
1. Install dependencies:
   ```bash
   pip install fastapi uvicorn
   # plus any others needed
   ```
2. Start the server:
   ```bash
   uvicorn app.web_capture_api:router --reload
   ```
   Or, if using a main app file:
   ```bash
   uvicorn app.main:app --reload
   ```
3. The API will be available at `http://localhost:8000/`

### Key Endpoints
- `GET /search_documents?query=...` — Search for documents matching the query
- `POST /save_web_content` — Save new web content (expects JSON with `url` and `content`)

---

## Plugin (Browser Extension) Setup

### Features
- User enters a query in the popup
- The plugin calls the backend `/search_documents` endpoint
- If a result is found with a weblink, the plugin opens it in a new tab and highlights every occurrence of the query with a red rectangle
- If no weblink is found, the result is shown in the popup

### Installation
1. Open your browser's extensions page (e.g., `chrome://extensions/`)
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `plugin/` directory
4. Ensure permissions in `manifest.json` allow access to tabs and scripting

### Usage
- Click the extension icon
- Enter your search query (e.g., `Bill Gates`)
- If a matching document is found, a new tab opens and your query is highlighted with a red rectangle

---

## How Search and Highlighting Work

1. **User enters a query** in the plugin popup
2. **Plugin sends the query** to the backend (`/search_documents?query=...`)
3. **Backend returns**:
   - `weblink`: URL to open (if found)
   - `text`: relevant chunk from the document
   - `highlight_text`: always the original user query (e.g., `Bill Gates`)
   - `highlight`: true/false (whether to highlight in opened tab)
4. **Plugin opens the link** and injects a script that:
   - Finds all occurrences of the query (case-insensitive)
   - Wraps each with a `<span>` styled with a red outline (rectangle)

---

## Troubleshooting & Tips

- **500 or 404 errors**: Check the backend logs for missing files, malformed results, or exceptions.
- **No highlights appearing**: Ensure the backend returns the correct `highlight_text` (should match the user's original query, not URL-encoded).
- **Plugin not working**: Check browser console for extension errors, and verify permissions in `manifest.json`.
- **Backend changes**: Restart the backend server after making code changes.

---

## Contributing
Feel free to open issues or PRs for improvements!

---

## License
Specify your license here.