"""
Production RAG Agent - Page-Indexed Retrieval with Dynamic HTML Formatting
Uses similarity search with relevance scores for fast, precise answers.
"""

from typing import TypedDict, List, Dict, Tuple
import os
import re
import time

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VECTORDB_DIR = os.path.join(SCRIPT_DIR, "vectordb")
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
LLM_MODEL = "phi3"

# Retrieval settings
TOP_K = 4
RELEVANCE_THRESHOLD = 0.25


class AgentState(TypedDict):
    query: str
    query_type: str
    context: List[str]
    sources: List[Dict]
    response: str


# ── Query type detection ────────────────────────────────────────────

QUERY_PATTERNS = {
    "error_code": re.compile(
        r'(error\s*(code)?|fault|alarm|code)\s*[:.]?\s*[A-Z0-9]{2,}',
        re.IGNORECASE,
    ),
    "troubleshooting": re.compile(
        r'(not working|fail|issue|problem|broken|stuck|won\'t|doesn\'t|can\'t|unable'
        r'|malfunction|defect|noise|vibrat|overheat|leak|jam|slow|stop)',
        re.IGNORECASE,
    ),
    "how_to": re.compile(
        r'(how\s+(to|do|can)|steps?\s+to|procedure|instructions?|guide|setup|configure|calibrat)',
        re.IGNORECASE,
    ),
    "info": re.compile(
        r'(what\s+(is|are|does)|explain|describe|tell\s+me|meaning|definition|specification|parameter)',
        re.IGNORECASE,
    ),
    "greeting": re.compile(
        r'^(hi|hello|hey|help|assist|what can you|capabilities)',
        re.IGNORECASE,
    ),
}


def classify_query(query: str) -> str:
    """Classify the query into a response type."""
    q = query.strip()
    if len(q.split()) < 3 and not QUERY_PATTERNS["error_code"].search(q):
        if QUERY_PATTERNS["greeting"].search(q):
            return "greeting"
        return "vague"
    for qtype in ("error_code", "troubleshooting", "how_to", "info"):
        if QUERY_PATTERNS[qtype].search(q):
            return qtype
    return "general"


# ── Dynamic HTML prompt templates ───────────────────────────────────

PROMPT_TEMPLATES = {
    "greeting": """You are an industrial machine troubleshooting assistant for a paint defect detection system.
User said: {query}
Reply in 2 sentences. Introduce yourself briefly and ask what specific issue they need help with. ONLY return plain text, no HTML.""",

    "vague": """You are an industrial machine troubleshooting assistant.
User said: "{query}"
Reply in 2 sentences. Ask them to describe their specific issue or provide an error code. ONLY return plain text, no HTML.""",

    "error_code": """You are an industrial machine troubleshooting assistant.

User query: {query}

Reference documentation:
{context}

Return ONLY this HTML (no other text):
<div class="response-card error-code-card">
  <div class="section">
    <strong>Error Code Details:</strong>
    <p>[error code and its meaning from documentation]</p>
  </div>
  <div class="section">
    <strong>Probable Cause:</strong>
    <p>[what causes this error, 1-2 sentences]</p>
  </div>
  <div class="section">
    <strong>Recommended Action:</strong>
    <ol>
      <li>[action step]</li>
      <li>[action step]</li>
      <li>[action step if needed]</li>
    </ol>
  </div>
  <div class="source-ref">Source: {sources}</div>
</div>""",

    "troubleshooting": """You are an industrial machine troubleshooting assistant.

User issue: {query}

Reference documentation:
{context}

Return ONLY this HTML (no other text):
<div class="response-card troubleshoot-card">
  <div class="section">
    <strong>Issue Identified:</strong>
    <p>[brief description of the problem]</p>
  </div>
  <div class="section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>[step - one sentence]</li>
      <li>[step - one sentence]</li>
      <li>[step - one sentence]</li>
    </ol>
  </div>
  <div class="source-ref">Source: {sources}</div>
</div>""",

    "how_to": """You are an industrial machine troubleshooting assistant.

User question: {query}

Reference documentation:
{context}

Return ONLY this HTML (no other text):
<div class="response-card howto-card">
  <div class="section">
    <strong>Procedure:</strong>
    <ol>
      <li>[step]</li>
      <li>[step]</li>
      <li>[step]</li>
    </ol>
  </div>
  <div class="section">
    <strong>Notes:</strong>
    <p>[any important warnings or tips, 1-2 sentences]</p>
  </div>
  <div class="source-ref">Source: {sources}</div>
</div>""",

    "info": """You are an industrial machine troubleshooting assistant.

User question: {query}

Reference documentation:
{context}

Return ONLY this HTML (no other text):
<div class="response-card info-card">
  <div class="section">
    <strong>Answer:</strong>
    <p>[clear, concise answer based on documentation, 2-4 sentences]</p>
  </div>
  <div class="source-ref">Source: {sources}</div>
</div>""",

    "general": """You are an industrial machine troubleshooting assistant.

User question: {query}

Reference documentation:
{context}

Return ONLY this HTML (no other text):
<div class="response-card general-card">
  <div class="section">
    <p>[answer the question concisely using the reference documentation, 2-5 sentences]</p>
  </div>
  <div class="source-ref">Source: {sources}</div>
</div>""",
}


class ProductionRAGAgent:
    """Page-indexed RAG agent with dynamic response formatting."""

    def __init__(self):
        print("[*] Initializing Production RAG Agent...")
        print(f"    Embedding: {EMBEDDING_MODEL}")
        print(f"    LLM: {LLM_MODEL}")

        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 16},
        )

        self.vectorstore = Chroma(
            persist_directory=VECTORDB_DIR,
            embedding_function=self.embeddings,
        )

        self.llm = OllamaLLM(
            model=LLM_MODEL,
            temperature=0.1,
            num_predict=400,
            top_k=10,
            top_p=0.9,
        )

        self._build_graph()
        print("[OK] Agent ready!\n")

    # ── Retrieval with page-indexed scoring ──────────────────────────

    def _retrieve_with_scores(self, query: str) -> Tuple[List[str], List[Dict]]:
        """Similarity search with relevance scores and page metadata."""
        results = self.vectorstore.similarity_search_with_relevance_scores(
            query, k=TOP_K
        )

        contexts = []
        sources = []
        for doc, score in results:
            if score < RELEVANCE_THRESHOLD:
                continue
            contexts.append(doc.page_content)
            sources.append({
                "page": doc.metadata.get("page_number", "?"),
                "file": doc.metadata.get("source_file", "unknown"),
                "section": doc.metadata.get("section", ""),
                "score": round(score, 3),
            })

        return contexts, sources

    def _format_sources(self, sources: List[Dict]) -> str:
        """Format source references for display."""
        if not sources:
            return "No matching documentation found"
        seen = set()
        parts = []
        for s in sources:
            key = f"{s['file']} p{s['page']}"
            if key not in seen:
                seen.add(key)
                parts.append(key)
        return ", ".join(parts)

    # ── Graph ────────────────────────────────────────────────────────

    def _build_graph(self):
        """Build LangGraph workflow."""

        def retrieve(state: AgentState):
            query = state["query"]
            query_type = classify_query(query)
            contexts, sources = self._retrieve_with_scores(query)
            return {
                "query_type": query_type,
                "context": contexts,
                "sources": sources,
            }

        def respond(state: AgentState):
            qtype = state["query_type"]
            template = PROMPT_TEMPLATES.get(qtype, PROMPT_TEMPLATES["general"])

            context_text = "\n\n".join(state["context"][:3]) if state["context"] else "No relevant documentation found."
            source_text = self._format_sources(state.get("sources", []))

            prompt = template.format(
                query=state["query"],
                context=context_text,
                sources=source_text,
            )

            response = self.llm.invoke(prompt)
            return {"response": response}

        graph = StateGraph(AgentState)
        graph.add_node("retrieve", retrieve)
        graph.add_node("respond", respond)
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "respond")
        self.agent = graph.compile()

    # ── Public API ───────────────────────────────────────────────────

    @staticmethod
    def _clean_response(response: str) -> str:
        """Strip markdown fences from LLM output."""
        r = response.strip()
        if r.startswith("```html"):
            r = r[7:]
        elif r.startswith("```"):
            r = r[3:]
        if r.endswith("```"):
            r = r[:-3]
        return r.strip()

    def query(self, question: str) -> str:
        """Run a query and return the formatted response."""
        t0 = time.time()
        result = self.agent.invoke({"query": question})
        elapsed = time.time() - t0
        print(f"    [{elapsed:.2f}s] type={result.get('query_type','?')}")
        return self._clean_response(result["response"])


# ── Singleton ────────────────────────────────────────────────────────

_agent_instance = None


def get_agent():
    """Get or create the singleton agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ProductionRAGAgent()
    return _agent_instance


if __name__ == "__main__":
    agent = get_agent()

    test_queries = [
        "What is error code 1A68H?",
        "Camera is not detecting defects properly",
        "How to calibrate the vision system?",
        "What does the light intensity parameter do?",
        "hi",
    ]

    print("=" * 60)
    print("TESTING PRODUCTION AGENT")
    print("=" * 60 + "\n")

    for q in test_queries:
        print(f"Query: {q}")
        print(f"Type:  {classify_query(q)}")
        print("-" * 60)
        resp = agent.query(q)
        print(resp)
        print("\n" + "=" * 60 + "\n")
