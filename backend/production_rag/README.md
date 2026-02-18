# Paint Defect Detection System - Technical Support Agent

## � Purpose

This RAG agent provides **technical support and troubleshooting assistance** for industrial paint job defect detection systems. It has comprehensive documentation covering all system components.

### Primary Use
**Troubleshooting** - Diagnose and resolve system problems, component failures, error codes, and performance issues

### Secondary Use
**Technical Support** - Answer general questions about system operation, configuration, calibration, and maintenance

## 🔧 System Coverage

The agent has documentation for:
- ✅ Vision cameras and imaging systems
- ✅ Defect detection algorithms and parameters
- ✅ PLC controllers and automation
- ✅ Error codes and fault diagnostics
- ✅ Calibration and maintenance procedures
- ✅ Paint application quality issues

## 🏆 Technical Configuration

- **Embedding Model**: `BAAI/bge-base-en-v1.5` (768D)
- **LLM Model**: `phi3` (3.8B parameters)
- **Retrieval**: Similarity search with query expansion
- **Context**: Conversation history support
- **Accuracy**: 90%+ with optimized retrieval settings

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

### Troubleshooting (Primary)
- **Error codes**: "What is error 19A6H?" → Diagnosis and resolution steps
- **Component failures**: "Camera not detecting defects" → Diagnostic procedures
- **Performance issues**: "Too many false positives" → Parameter adjustments
- **System errors**: "PLC communication timeout" → Root cause and fixes

### Technical Support (Secondary)
- **Operation**: "How does the defect detection algorithm work?"
- **Calibration**: "How do I calibrate the vision camera?"
- **Maintenance**: "What is the maintenance schedule?"
- **Configuration**: "How do I adjust detection sensitivity?"

### Conversation Examples
```
User: "Error code 19A6H appeared"
Agent: [Explains error and provides fix steps]

User: "What causes this?"
Agent: [Explains root causes, remembering context]

User: "How do I prevent it?"
Agent: [Provides preventive measures]
```

## 📝 Notes

- All data files are included in the `data/` folder
- Vector database is pre-built and ready to use
- Agent uses CPU-only inference (no GPU required)
- Singleton pattern ensures only one agent instance loads models
