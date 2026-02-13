# Production RAG Agent - Page-Indexed Architecture

## 🚀 Auto-Runs with `npm run dev`

**The RAG agent now automatically starts when you run `npm run dev`!** It's integrated into the main FastAPI backend and accessible at:

- **Troubleshoot Endpoint**: `POST http://localhost:5001/api/troubleshoot`
- **Health Check**: `GET http://localhost:5001/api/health`

## 🏆 Optimized Configuration

- **Embedding Model**: `BAAI/bge-base-en-v1.5` (768D)
- **LLM Model**: `phi3` (3.8B parameters)
- **Search Strategy**: Similarity search with relevance scores (faster than MMR)
- **Architecture**: Page-indexed chunks with metadata for precise citations

## ⚡ Key Optimizations

1. **Page-Indexed Chunking** - Every chunk stores `page_number`, `source_file`, `section` metadata
2. **Dynamic HTML Formatting** - 7 query types with tailored response formats:
   - `error_code` → Error details + cause + action steps
   - `troubleshooting` → Issue + troubleshooting steps
   - `how_to` → Numbered procedure + notes
   - `info` → Concise answer
   - `general` → General answer
   - `greeting` → Plain text intro
   - `vague` → Clarification request
3. **Smaller Chunks** (400 chars) for more precise retrieval
4. **Relevance Filtering** (threshold 0.25) to skip low-quality matches
5. **Reduced Token Generation** (400 tokens) for faster responses

## 📁 Folder Structure

```
production_rag/
├── agent.py              # Main agent with dynamic formatting
├── rebuild_vectordb.py   # Page-indexed chunking system
├── fastapi_server.py     # FastAPI router (integrated into main.py)
├── data/                 # Source PDFs (error_codes.pdf, manuals, etc.)
├── vectordb/             # Page-indexed vector database
├── requirements.txt      # Python dependencies
├── config.json           # Configuration details
└── README.md            # This file
```

## 🔧 Setup (First Time Only)

### 1. Install Dependencies

```bash
cd backend/production_rag
pip install -r requirements.txt
```

### 2. Install Ollama & phi3

```bash
ollama pull phi3
```

### 3. Rebuild Vector Database (if needed)

```bash
python rebuild_vectordb.py
```

This creates page-indexed chunks from all PDFs in `data/`.

### 4. Verify Setup

```bash
python setup.py
```

## 🎯 Usage

### Via API (Automatic with `npm run dev`)

```bash
curl -X POST http://localhost:5001/api/troubleshoot \
  -H "Content-Type: application/json" \
  -d '{"query": "What is error code 1A68H?"}'
```

### Direct Python Import

```python
from production_rag import get_agent

agent = get_agent()
response = agent.query("Camera is not detecting defects")
print(response)
```

### Test All Query Types

```bash
python test_conversation.py
```

## 📊 Query Type Examples

| Type | Example Query | Response Format |
|------|---------------|-----------------|
| **error_code** | "What is error code 1A68H?" | Error details + cause + action steps |
| **troubleshooting** | "Camera not detecting defects" | Issue identified + troubleshooting steps |
| **how_to** | "How to calibrate the vision system?" | Numbered procedure + notes |
| **info** | "What is the light intensity parameter?" | Concise answer paragraph |
| **general** | "Tell me about paint inspection" | General answer |
| **greeting** | "hi" | Plain text intro (no HTML) |
| **vague** | "help?" | Clarification request |

## 🔍 Source Citations

Every response includes source references like:
```html
<div class="source-ref">Source: error_codes.pdf p42, ib0300253engm.pdf p128</div>
```

## 📝 Notes

- **Auto-starts** with main backend (`npm run dev`)
- **CPU-only** inference (no GPU required)
- **Singleton pattern** ensures models load once
- **Page metadata** enables precise document citations
- **Dynamic formatting** adapts to query type (not just troubleshooting)
