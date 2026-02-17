# Production RAG Agent

## 🏆 Optimized Configuration

Based on comprehensive benchmarking, this production agent uses:

- **Embedding Model**: `BAAI/bge-base-en-v1.5` (768D)
- **LLM Model**: `phi3` (3.8B parameters)
- **Search Strategy**: MMR (Maximal Marginal Relevance)
- **Performance Score**: 3.71 (best among all tested configurations)

## 📊 Performance Metrics

- **Load Time**: 3.84s
- **Average Query Time**: 3.68s
- **Success Rate**: 100%
- **Throughput**: Optimized for CPU-only systems

## 📁 Folder Structure

```
production_rag/
├── agent.py              # Main production agent
├── data/                 # Source documents
│   ├── camera_system_troubleshooting.txt
│   ├── machine_error_codes.docx
│   ├── paint_defects_reffrence.md
│   ├── paint_defects_troubleshooting.txt
│   └── paint_machine_user_manual.txt
├── vectordb/             # Pre-built vector database (768D)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Quick Start

### 1. Install Dependencies

```bash
cd production_rag
pip install -r requirements.txt
```

### 2. Ensure Ollama Model is Available

```bash
ollama pull phi3
```

### 3. Test the Agent

```bash
python agent.py
```

### 4. Use in Your Application

```python
from agent import get_agent

# Get agent instance (singleton)
agent = get_agent()

# Query the agent
response = agent.query("Camera is not detecting defects properly")
print(response)
```

## 🔧 Integration with Console App

The console app can import and use this agent:

```python
import sys
sys.path.append('c:/Users/Priyanshu/OneDrive/Desktop/me_app/production_rag')

from agent import get_agent

agent = get_agent()
response = agent.query(user_question)
```

## 📈 Why This Configuration?

This configuration was selected after testing 24 different combinations:

1. **bge-base embeddings**: Better quality than bge-small (768D vs 384D)
2. **phi3 LLM**: Fastest generation time while maintaining quality
3. **No hybrid search**: Simpler, faster, and sufficient for this use case
4. **MMR retrieval**: Balances relevance with diversity

## 🎯 Use Cases

- Industrial paint defect detection troubleshooting
- Error code resolution
- Vision system calibration guidance
- Machine operation support

## 📝 Notes

- All data files are included in the `data/` folder
- Vector database is pre-built and ready to use
- Agent uses CPU-only inference (no GPU required)
- Singleton pattern ensures only one agent instance loads models
