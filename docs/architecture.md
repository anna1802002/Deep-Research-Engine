# System Architecture

## Overview
The Deep Research Engine follows a modular design:
1. **Query Processing:** Expands and vectorizes queries.
2. **Data Retrieval:** Fetches data from academic and web sources.
3. **Ranking:** Uses hybrid scoring (BERT embeddings, authority score).
4. **Extraction:** Identifies key content and metadata.
5. **Report Generation:** Compiles structured reports.

## Technology Stack
- **Backend:** Python, FastAPI
- **Machine Learning:** BERT embeddings (mxbai-embed-large)
- **Databases:** ChromaDB (vector storage), DuckDB (analytics)
- **UI:** Gradio-based interface
