"""
Flask API Server for Production RAG Agent
Provides REST API endpoint for troubleshooting queries
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append('./production_rag')

from agent import get_agent

app = Flask(__name__)
CORS(app)

agent = None

@app.before_request
def initialize_agent():
    global agent
    if agent is None:
        print("Initializing RAG agent...")
        agent = get_agent()
        print("Agent ready!")

@app.route('/api/troubleshoot', methods=['POST'])
def troubleshoot():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        print(f"\n[Query] {query}")
        response = agent.query(query)
        print(f"[Response] {response[:100]}...")
        
        return jsonify({'response': response})
    
    except Exception as e:
        print(f"[Error] {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'agent_loaded': agent is not None
    })

if __name__ == '__main__':
    print("="*60)
    print("Starting Troubleshooting Agent API Server")
    print("="*60)
    print("Server will run on: http://localhost:5000")
    print("API endpoint: POST /api/troubleshoot")
    print("Health check: GET /api/health")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
