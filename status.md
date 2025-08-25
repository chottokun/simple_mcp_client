# System Verification Checklist

This document tracks the detailed steps for verifying the end-to-end functionality of the Intelligent RAG Chat System.

## 1. System Startup

- [ ] Start all services using `docker compose up -d`.
- [ ] Check `backend` container logs for successful startup and model loading.
- [ ] Check `playwright` container logs for successful startup.
- [ ] Check `chroma` and `frontend` container logs for any errors.

## 2. Data Ingestion

- [ ] Run `pip install -r requirements.txt` to ensure CLI dependencies are met.
- [ ] Execute `python cli.py ingest data/test_document.txt`.
- [ ] Verify that the output shows a success message for the ingestion.

## 3. Tool Verification

### 3.1. Internal Document Search (`local_document_search`)

- [ ] Send a POST request to `/api/chat` with a question about the content of `data/test_document.txt`.
- [ ] Verify the response is 200 OK.
- [ ] Verify the answer in the response JSON is correct.
- [ ] Verify the `sources` in the response JSON point to `test_document.txt`.
- [ ] Check `backend` logs to confirm the `local_document_search` tool was used.

### 3.2. GitHub Repository Search

- [ ] Send a POST request to `/api/chat` with a question like "Find a langchain repository on GitHub".
- [ ] Verify the response is 200 OK.
- [ ] Verify the answer contains information about a GitHub repository.
- [ ] Check `backend` logs to confirm a tool from the `github` MCP client was used (e.g., `search_repositories`).

### 3.3. Website Browsing (Playwright)

- [ ] Send a POST request to `/api/chat` with a question like "What is the title of the website at https://example.com?".
- [ ] Verify the response is 200 OK.
- [ ] Verify the answer contains the title of the example website.
- [ ] Check `backend` logs to confirm a tool from the `playwright` MCP client was used (e.g., `browser_snapshot`).

## 4. Final Cleanup

- [ ] Stop all services using `docker compose down`.
