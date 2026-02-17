"""
Production RAG Agent for Paint Defect Detection System Troubleshooting

Purpose:
This agent provides technical support and troubleshooting assistance for industrial
paint job defect detection systems. It has access to comprehensive documentation
covering all system components including:
- Vision cameras and imaging systems
- Defect detection algorithms and parameters
- PLC controllers and automation
- Error codes and fault diagnostics
- Calibration and maintenance procedures
- Paint application quality issues

Primary Use: Troubleshooting system problems and component failures
Secondary Use: General technical questions about system operation

Implements: Query expansion, hybrid retrieval, conversation history
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

# Improved retrieval settings for large PDFs
TOP_K = 10  # Increased to 10 for better coverage of large documents
RELEVANCE_THRESHOLD = 0.10  # Lowered to 0.10 to catch more potential matches
FETCH_K = 20  # Increased candidate pool for large PDFs


def classify_query(query: str) -> str:
    """Classify query type for better prompt selection."""
    query_lower = query.lower()
    
    # Error code pattern - matches codes like 19A6H, 1A68H, E101, etc.
    if re.search(r'\b(error|fault|alarm|code)\b', query_lower, re.IGNORECASE) or \
       re.search(r'\b\d+[a-z]+\d*[a-z]*\b', query_lower, re.IGNORECASE):
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
        # Extract error code - improved pattern for codes like 19A6H
        match = re.search(r'\b(\d+[a-z]+\d*[a-z]*)\b', query, re.IGNORECASE)
        if match:
            code = match.group(1).upper()
            variations.append(f"error {code}")
            variations.append(f"code {code}")
            variations.append(f"fault {code}")
            variations.append(f"alarm {code}")
            variations.append(code)  # Just the code itself
    
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
    chat_history: List[Dict]  # Store conversation history


class ProductionRAGAgent:
    """Production-ready RAG agent with improved accuracy and conversation memory."""
    
    def __init__(self):
        print("[*] Initializing Production RAG Agent (Improved)...")
        print(f"   Embedding: {EMBEDDING_MODEL}")
        print(f"   LLM: {LLM_MODEL}")
        print(f"   Retrieval: top_k={TOP_K}, threshold={RELEVANCE_THRESHOLD}")
        
        # Initialize conversation history storage
        self.conversations = {}  # session_id -> list of messages
        
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
        for var in variations[:5]:  # Use more variations for error codes
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
                return {"response": "Hello! I'm your technical support assistant for the paint defect detection system. I specialize in troubleshooting all system components including vision cameras, defect detection algorithms, PLC controllers, error codes, and maintenance procedures. I have access to comprehensive documentation for each component. What issue can I help you resolve today?"}
            
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
                prompt = f"""You are a Technical Support Specialist for an industrial paint job defect detection system. Your role is to troubleshoot system problems using comprehensive component documentation including vision cameras, defect detection algorithms, PLC controllers, and maintenance procedures.

User's Issue: {query}

Reference Documentation from System Components:
{context_text}

IMPORTANT: Format your response as HTML with the following structure:

<div class="troubleshoot-response">
  <div class="issue-section">
    <strong>Issue Identified:</strong>
    <p>[Brief description of the error code and what it means]</p>
  </div>
  <div class="steps-section">
    <strong>Troubleshooting Steps:</strong>
    <ol>
      <li>[First step - one sentence]</li>
      <li>[Second step - one sentence]</li>
      <li>[Third step - one sentence]</li>
      <li>[Fourth step if needed]</li>
    </ol>
  </div>
</div>

Keep each step concise (one sentence). If information is not relevant, say you don't have specific information and suggest consulting the manual.

ONLY return the HTML, no other text."""
            
            elif query_type == "troubleshooting":
                prompt = f"""You are a Technical Support Specialist for an industrial paint job defect detection system. Your role is to troubleshoot system problems using comprehensive component documentation including vision cameras, defect detection algorithms, PLC controllers, and maintenance procedures.

User Issue: {query}

Reference Documentation from System Components:
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
</div>

Base your answer on the documentation. Be specific and actionable. Return ONLY the HTML, no other text."""
            
            elif query_type == "how_to":
                prompt = f"""You are a Technical Support Specialist for an industrial paint job defect detection system. Your role is to provide guidance on system operation, calibration, and maintenance procedures.

User Question: {query}

Reference Documentation from System Components:
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
</div>

Use the documentation to provide accurate steps. Return ONLY the HTML, no other text."""
            
            elif query_type == "info":
                prompt = f"""You are a Technical Support Specialist for an industrial paint job defect detection system. You provide technical information about system components and operation.

User Question: {query}

Reference Documentation from System Components:
{context_text}

Provide a clear, concise answer in HTML:

<div class="info-response">
  <div class="answer">
    <p>[Clear explanation based on documentation]</p>
  </div>
</div>

Be accurate. Return ONLY the HTML, no other text."""
            
            else:  # general
                prompt = f"""You are a Technical Support Specialist for an industrial paint job defect detection system. You assist with both troubleshooting and general technical questions about system operation.

User Question: {query}

Reference Documentation from System Components:
{context_text}

Provide a helpful answer in HTML:

<div class="general-response">
  <div class="answer">
    <p>[Comprehensive answer based on documentation]</p>
  </div>
</div>

Use the documentation to provide accurate information. Return ONLY the HTML, no other text."""
            
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
    
    def query(self, question: str, session_id: str = "default") -> str:
        """Query the agent with conversation history support."""
        # Get or create conversation history for this session
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        chat_history = self.conversations[session_id]
        
        # Invoke agent with chat history
        result = self.agent.invoke({
            "query": question,
            "chat_history": chat_history
        })
        
        raw_response = result["response"]
        cleaned = self._clean_response(raw_response)
        
        # Store this exchange in history
        self.conversations[session_id].append({
            "role": "user",
            "content": question
        })
        self.conversations[session_id].append({
            "role": "assistant",
            "content": cleaned
        })
        
        # Keep only last 10 exchanges (20 messages) to avoid context overflow
        if len(self.conversations[session_id]) > 20:
            self.conversations[session_id] = self.conversations[session_id][-20:]
        
        return cleaned
    
    def clear_history(self, session_id: str = "default"):
        """Clear conversation history for a session."""
        if session_id in self.conversations:
            self.conversations[session_id] = []
            print(f"[*] Cleared conversation history for session: {session_id}")
    
    def get_history(self, session_id: str = "default") -> List[Dict]:
        """Get conversation history for a session."""
        return self.conversations.get(session_id, [])


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
