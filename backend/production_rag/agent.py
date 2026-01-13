"""
Production RAG Agent - Optimized Configuration
Best Performance: bge-base embeddings + phi3 LLM
"""

from typing import TypedDict, List
import os

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VECTORDB_DIR = os.path.join(SCRIPT_DIR, "vectordb")
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
LLM_MODEL = "phi3"

class AgentState(TypedDict):
    query: str
    context: List[str]
    response: str

class ProductionRAGAgent:
    """Production-ready RAG agent with best configuration"""
    
    def __init__(self):
        print("[*] Initializing Production RAG Agent...")
        print(f"   Embedding Model: {EMBEDDING_MODEL}")
        print(f"   LLM Model: {LLM_MODEL}")
        
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
        
        # Setup retriever with MMR for diversity
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 3,
                "fetch_k": 6,
                "lambda_mult": 0.7
            }
        )
        
        # Load LLM
        self.llm = OllamaLLM(
            model=LLM_MODEL,
            temperature=0.1,
            num_predict=512,
            top_k=10,
            top_p=0.9
        )
        
        # Build agent graph
        self._build_graph()
        
        print("[OK] Agent initialized successfully!\n")
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        
        def retrieve(state: AgentState):
            query = state["query"]
            
            # Use original query without expansion for better relevance
            docs = self.retriever.invoke(query)
            contexts = [doc.page_content for doc in docs]
            
            return {"context": contexts}
        
        def troubleshoot(state: AgentState):
            context_text = "\n\n".join(state['context'][:3])
            query = state['query'].lower()
            
            # Detect query type
            is_general_inquiry = any(word in query for word in ['what can', 'help me', 'assist', 'what do you', 'capabilities', 'what are you'])
            is_vague = len(query.split()) < 5 and '?' in query
            
            if is_general_inquiry:
                prompt = f"""You are a Troubleshooting Agent for an industrial paint defect detection machine.

User asked: {state['query']}

Respond in 2-3 sentences maximum. Say you can help with:
- Camera and vision system issues
- Paint defect detection problems
- Error codes and system errors
- Calibration and maintenance

Ask what specific issue they're experiencing. Be brief and friendly."""
            
            elif is_vague or len(query.split()) < 4:
                prompt = f"""You are a Troubleshooting Agent for a paint defect detection machine.

The user said: "{state['query']}"

Respond in 2 sentences maximum. Ask them to describe their specific machine issue. Mention you can help with camera problems, defect detection, or error codes."""
            
            else:
                prompt = f"""You are a Troubleshooting Agent for an industrial paint defect detection machine.

User's Issue: {state['query']}

Reference Information:
{context_text}

Provide a CONCISE response (maximum 5-6 sentences).

If relevant information is found:
- Briefly identify the issue
- List 3-4 specific troubleshooting steps
- Keep each step to one short sentence

If not relevant:
- Say you don't have specific information about this issue
- Suggest consulting the manual or support

Be direct and concise. No lengthy explanations."""
            
            response = self.llm.invoke(prompt)
            return {"response": response}
        
        graph = StateGraph(AgentState)
        graph.add_node("retrieve", retrieve)
        graph.add_node("troubleshoot", troubleshoot)
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "troubleshoot")
        
        self.agent = graph.compile()
    
    def query(self, question: str) -> str:
        """Query the agent"""
        result = self.agent.invoke({"query": question})
        return result["response"]

# Singleton instance
_agent_instance = None

def get_agent():
    """Get or create agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ProductionRAGAgent()
    return _agent_instance

if __name__ == "__main__":
    # Test the agent
    agent = get_agent()
    
    test_queries = [
        "Camera is not detecting defects properly",
        "Error code E101 on the display",
        "Paint finish looks uneven"
    ]
    
    print("="*60)
    print("TESTING PRODUCTION AGENT")
    print("="*60 + "\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        print("-"*60)
        response = agent.query(query)
        print(response)
        print("\n" + "="*60 + "\n")
