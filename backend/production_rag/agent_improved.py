"""
Production RAG Agent - Improved Accuracy Version
Implements: Query expansion, hybrid retrieval, better chunking awareness
"""

from typing import TypedDict, List, Tuple, Dict
import os
import re

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VECTORDB_DIR = os.path.join(SCRIPT_DIR, "vectordb")
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
LLM_MODEL = "phi3"

# Improved retrieval settings
TOP_K = 6  # Increased from 3 to get more context
RELEVANCE_THRESHOLD = 0.15  # Lowered from 0.25 to be more inclusive
FETCH_K = 12  # Increased for better candidate pool


def classify_query(query: str) -> str:
    """Classify query type for better prompt selection."""
    query_lower = query.lower()
    
    # Error code pattern
    if re.search(r'\b(error|fault|alarm|code)\b.*\b[a-z0-9]{4,}\b', query_lower, re.IGNORECASE):
        return "error_code"
    
    # Troubleshooting
    if any(word in query_lower for word in [
        'not working', 'fail', 'stuck', 'issue', 'problem', 'wrong',
        'broken', 'malfunction', 'stopped', 'won\'t', 'doesn\'t', 'can\'t'
    ]):
        return "troubleshooting"
    
    # How-to
    if any(word in query_lower for word in ['how to', 'how do', 'procedure', 'steps', 'calibrate', 'setup', 'configure']):
        return "how_to"
    
    # Info request
    if any(word in query_lower for word in ['what is', 'what does', 'explain', 'describe', 'definition', 'meaning']):
        return "info"
    
    # Greeting
    if query_lower.strip() in ['hi', 'hello', 'hey', 'help']:
        return "greeting"
    
    # Vague
    if len(query.split()) < 4:
        return "vague"
    
    return "general"


def expand_query(query: str, query_type: str) -> List[str]:
    """Generate query variations to improve retrieval."""
    variations = [query]
    
    if query_type == "error_code":
        # Extract error code
        match = re.search(r'\b([a-z0-9]{4,})\b', query, re.IGNORECASE)
        if match:
            code = match.group(1)
            variations.append(f"error code {code}")
            variations.append(f"fault {code}")
            variations.append(f"alarm {code}")
    
    elif query_type == "troubleshooting":
        # Add symptom-focused variations
        variations.append(f"troubleshoot {query}")
        variations.append(f"fix {query}")
        variations.append(f"resolve {query}")
    
    elif query_type == "how_to":
        # Add procedure-focused variations
        variations.append(f"procedure {query}")
        variations.append(f"steps {query}")
    
    return variations


class AgentState(TypedDict):
    query: str
    query_type: str
    context: List[str]
    sources: List[Dict]
    response: str


class ProductionRAGAgent:
    """Production-ready RAG agent with improved accuracy."""
    
    def __init__(self):
        print("[*] Initializing Production RAG Agent (Improved)...")
        print(f"   Embedding: {EMBEDDING_MODEL}")
        print(f"   LLM: {LLM_MODEL}")
        print(f"   Retrieval: top_k={TOP_K}, threshold={RELEVANCE_THRESHOLD}")
        
        # Load embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 16}
        )
        
        # Load vector store
        self.vectorstore = Chroma(
            persist_directory=VECTORDB_DIR,
            embedding_function=self.embeddings
        )
        
        # Load LLM
        self.llm = OllamaLLM(
            model=LLM_MODEL,
            temperature=0.1,
            num_predict=600,  # Increased for more detailed answers
            top_k=10,
            top_p=0.9
        )
        
        # Build agent graph
        self._build_graph()
        
        print("[OK] Agent ready!\n")
    
    def _retrieve_with_expansion(self, query: str, query_type: str) -> Tuple[List[str], List[Dict]]:
        """Retrieve with query expansion and hybrid scoring."""
        
        # Generate query variations
        variations = expand_query(query, query_type)
        
        all_docs = []
        seen_content = set()
        
        # Retrieve for each variation
        for var in variations[:3]:  # Limit to top 3 variations
            try:
                results = self.vectorstore.similarity_search_with_relevance_scores(
                    var,
                    k=TOP_K
                )
                
                for doc, score in results:
                    # Filter by relevance threshold
                    if score >= RELEVANCE_THRESHOLD:
                        content = doc.page_content
                        # Avoid duplicates
                        if content not in seen_content:
                            seen_content.add(content)
                            all_docs.append((doc, score))
            except Exception as e:
                print(f"[Warning] Retrieval failed for '{var}': {e}")
        
        # Sort by score and take top K
        all_docs.sort(key=lambda x: x[1], reverse=True)
        top_docs = all_docs[:TOP_K]
        
        # Extract contexts and sources
        contexts = []
        sources = []
        
        for doc, score in top_docs:
            contexts.append(doc.page_content)
            
            # Extract metadata
            metadata = doc.metadata
            source_info = {
                'file': metadata.get('source', 'unknown'),
                'page': metadata.get('page', 'N/A'),
                'score': round(score, 3)
            }
            sources.append(source_info)
        
        print(f"[Retrieval] Found {len(contexts)} relevant chunks (threshold={RELEVANCE_THRESHOLD})")
        for i, src in enumerate(sources[:3]):
            print(f"   {i+1}. {src['file']} p{src['page']} (score={src['score']})")
        
        return contexts, sources
    
    def _build_graph(self):
        """Build LangGraph workflow."""
        
        def retrieve(state: AgentState):
            query = state["query"]
            query_type = classify_query(query)
            
            contexts, sources = self._retrieve_with_expansion(query, query_type)
            
            return {
                "query_type": query_type,
                "context": contexts,
                "sources": sources
            }
        
        def generate_response(state: AgentState):
            query = state['query']
            query_type = state['query_type']
            contexts = state['context']
            sources = state['sources']
            
            # Handle special cases
            if query_type == "greeting":
                return {"response": "Hello! I'm a troubleshooting assistant for industrial paint defect detection systems. I can help with error codes, camera issues, defect detection problems, and maintenance procedures. What specific issue are you facing?"}
            
            if query_type == "vague":
                return {"response": "I'd be happy to help! Could you provide more details about your specific issue? For example, are you experiencing an error code, camera problems, or defect detection issues?"}
            
            # Build context text
            if not contexts:
                context_text = "No specific documentation found for this query."
            else:
                context_text = "\n\n---\n\n".join(contexts[:4])  # Use top 4 chunks
            
            # Build source references
            source_refs = []
            for src in sources[:4]:
                source_refs.append(f"{src['file']} p{src['page']}")
            source_text = ", ".join(source_refs) if source_refs else "No sources"
            
            # Select prompt template based on query type
            if query_type == "error_code":
                prompt = f"""You are a technical troubleshooting expert for industrial paint defect detection machines.

User Query: {query}

Reference Documentation:
{context_text}

Provide a detailed response in HTML format:

<div class="error-response">
  <div class="error-details">
    <strong>Error Code:</strong>
    <p>[Error code and description]</p>
  </div>
  <div class="cause">
    <strong>Possible Cause:</strong>
    <p>[What causes this error]</p>
  </div>
  <div class="solution">
    <strong>Solution Steps:</strong>
    <ol>
      <li>[Step 1]</li>
      <li>[Step 2]</li>
      <li>[Step 3]</li>
    </ol>
  </div>
  <div class="source-ref">Source: {source_text}</div>
</div>

Use ONLY the provided documentation. If the error code is not found, say so clearly."""
            
            elif query_type == "troubleshooting":
                prompt = f"""You are a technical troubleshooting expert for industrial paint defect detection machines.

User Issue: {query}

Reference Documentation:
{context_text}

Provide a structured troubleshooting response in HTML:

<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>[Brief description]</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>[First diagnostic step]</li>
      <li>[Second step]</li>
      <li>[Third step]</li>
      <li>[Additional steps if needed]</li>
    </ol>
  </div>
  <div class="source-ref">Source: {source_text}</div>
</div>

Base your answer on the documentation. Be specific and actionable."""
            
            elif query_type == "how_to":
                prompt = f"""You are a technical expert for industrial paint defect detection machines.

User Question: {query}

Reference Documentation:
{context_text}

Provide a clear procedure in HTML:

<div class="procedure-response">
  <div class="overview">
    <strong>Procedure:</strong>
    <p>[Brief overview]</p>
  </div>
  <div class="steps">
    <strong>Steps:</strong>
    <ol>
      <li>[Step 1 with details]</li>
      <li>[Step 2 with details]</li>
      <li>[Step 3 with details]</li>
    </ol>
  </div>
  <div class="notes">
    <strong>Notes:</strong>
    <p>[Important notes or warnings]</p>
  </div>
  <div class="source-ref">Source: {source_text}</div>
</div>

Use the documentation to provide accurate steps."""
            
            elif query_type == "info":
                prompt = f"""You are a technical expert for industrial paint defect detection machines.

User Question: {query}

Reference Documentation:
{context_text}

Provide a clear, concise answer in HTML:

<div class="info-response">
  <div class="answer">
    <p>[Clear explanation based on documentation]</p>
  </div>
  <div class="source-ref">Source: {source_text}</div>
</div>

Be accurate and cite the documentation."""
            
            else:  # general
                prompt = f"""You are a technical expert for industrial paint defect detection machines.

User Question: {query}

Reference Documentation:
{context_text}

Provide a helpful answer in HTML:

<div class="general-response">
  <div class="answer">
    <p>[Comprehensive answer based on documentation]</p>
  </div>
  <div class="source-ref">Source: {source_text}</div>
</div>

Use the documentation to provide accurate information."""
            
            response = self.llm.invoke(prompt)
            return {"response": response}
        
        graph = StateGraph(AgentState)
        graph.add_node("retrieve", retrieve)
        graph.add_node("generate", generate_response)
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "generate")
        
        self.agent = graph.compile()
    
    def _clean_response(self, response: str) -> str:
        """Clean markdown artifacts from response."""
        response = response.strip()
        if response.startswith("```html"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()
    
    def query(self, question: str) -> str:
        """Query the agent."""
        result = self.agent.invoke({"query": question})
        raw_response = result["response"]
        cleaned = self._clean_response(raw_response)
        return cleaned


# Singleton instance
_agent_instance = None

def get_agent():
    """Get or create agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ProductionRAGAgent()
    return _agent_instance


# Export classify_query for testing
__all__ = ['get_agent', 'ProductionRAGAgent', 'classify_query']


if __name__ == "__main__":
    agent = get_agent()
    
    test_queries = [
        "What is error code 1A68H?",
        "Camera is not detecting defects properly",
        "How to calibrate the vision system?",
        "What does the light intensity parameter do?",
        "Paint finish looks uneven"
    ]
    
    print("=" * 70)
    print("TESTING IMPROVED AGENT")
    print("=" * 70 + "\n")
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print(f"Type: {classify_query(query)}")
        print("-" * 70)
        response = agent.query(query)
        print(response[:200] + "..." if len(response) > 200 else response)
        print("\n" + "=" * 70)
