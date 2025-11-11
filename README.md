# 🧠 Deep Research Engine

**Deep Research Engine** is an advanced AI research assistant that bridges the gap between vast academic resources and targeted research needs.  
It retrieves, analyzes, and ranks academic papers from multiple sources to deliver context-aware, citation-linked research summaries that traditionally require hours of manual effort.

---

## 🌍 Overview
Unlike traditional academic search tools that rely solely on keyword matching, Deep Research Engine comprehends the **semantic relationships** between concepts.  
By combining **natural language processing, content-aware ranking**, and **automated synthesis**, it transforms broad research problems into focused literature reviews.

---

## ✨ Key Features
- **Intelligent Query Processing:**  
  Transforms natural-language research questions into optimized, domain-specific queries using the GROQ model.
- **Multi-Source Retrieval:**  
  Connects seamlessly with **Arxiv**, **PubMed**, **Google Scholar**, and specialized repositories through a unified **Model Context Protocol (MCP)**.
- **Smart Document Management:**  
  Automatically fetches PDFs, organizes cache hierarchies, and extracts metadata for complete traceability.
- **Advanced Ranking Algorithms:**  
  Combines semantic relevance, source authority, publication recency, and content quality into a unified score.
- **Automated Report Generation:**  
  Produces academic-style reports in Markdown and HTML with proper citations and bibliographic sections.
- **Modular, Extensible Architecture:**  
  Each component—query, retrieval, ranking, and reporting—is independently replaceable and upgradable.

---

## 🧩 System Architecture
deep-research-engine/
├── config/ # System and API configurations
├── src/ # Core source modules
│ ├── query_processing/ # GROQ-based query parsing & expansion
│ ├── data_retrieval/ # Arxiv, PubMed, and Google connectors
│ ├── ranking/ # Hybrid scoring algorithms
│ ├── report_generation/ # Markdown/HTML synthesis
│ └── utils/
├── mcp-service/ # Model Context Protocol integration layer
├── scripts/ # Utilities and testing scripts
├── tests/ # Unit and integration tests
├── docs/ # Reports and documentation
│ └── Final_Report.md
└── output/ # Generated reports

---

## ⚙️ Configuration
The engine requires credentials for external APIs (stored securely in `/config/api_keys.json`, excluded from Git).  

**APIs used:**
- Google Custom Search  
- Google Scholar (restricted credentials)  
- GROQ Language Models  
- OpenAI Embeddings  

System parameters such as ranking weights, chunking behavior, and report formatting live in `/config/settings.json`.

---

## 📊 Workflow Summary
1. **Query Understanding & Expansion** → Extract and enrich core research concepts.  
2. **Multi-Source Retrieval** → Collect data via MCP connectors.  
3. **Document Processing** → Chunk, embed, and normalize text & metadata.  
4. **Ranking & Scoring** → Apply semantic and authority-based weighting.  
5. **Report Generation** → Synthesize top results with citations.  

---

## 📁 Output Organization
Each query run creates a timestamped folder with:
- `PDFs/` — downloaded source papers  
- `metadata.json` — unified citation data  
- `report.md` and `report.html` — final summarized output  

---

## 📈 Impact
- Reduced literature review time by **~80 %**  
- Maintained **100 % source traceability**  
- Processed **1000 + sources** across three repositories in < 5 minutes  
- Built foundation for real-time academic search assistants  

---

## 🧰 Tech Stack
| Category | Tools |
|-----------|-------|
| **Language** | Python |
| **Libraries** | OpenAI Embeddings, SentenceTransformers, GROQ |
| **Databases** | DuckDB, ChromaDB |
| **APIs** | Arxiv, PubMed, Google Scholar |
| **Frameworks** | FastAPI, Docker |
| **Visualization (planned)** | Streamlit, Neo4j |

---

## 🧭 Future Roadmap
- Streamlit/Gradio no-code research interface  
- PDF export and citation-graph visualization  
- Domain-specific tuning (IEEE, SSRN, JSTOR)  
- Neo4j-powered relationship mapping  

---

## 📚 Documentation
Full technical report → [`docs/Final_Report.md`](docs/Final_Report.md)

---

## 🧑‍💻 Author
**Ananya Mahesh Shetty**  
*M.S. Data Analytics Engineering | Northeastern University*  
📧 shetty.ana@northeastern.edu | [LinkedIn](https://www.linkedin.com/in/ananyashetty18)

---

![Python](https://img.shields.io/badge/Python-3.10-blue)
![AI](https://img.shields.io/badge/AI-Semantic%20Search-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
