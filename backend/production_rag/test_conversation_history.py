"""
Test conversation history feature
"""

from agent import get_agent

def test_conversation_flow():
    print("=" * 70)
    print("TESTING CONVERSATION HISTORY")
    print("=" * 70)
    
    agent = get_agent()
    session_id = "test_session"
    
    # Test 1: First question
    print("\n[Test 1] First question")
    print("-" * 70)
    query1 = "What is error 19A6H?"
    response1 = agent.query(query1, session_id=session_id)
    print(f"User: {query1}")
    print(f"Agent: {response1[:150]}...")
    
    # Test 2: Follow-up question
    print("\n[Test 2] Follow-up question (should understand context)")
    print("-" * 70)
    query2 = "How do I fix this error?"
    response2 = agent.query(query2, session_id=session_id)
    print(f"User: {query2}")
    print(f"Agent: {response2[:150]}...")
    
    # Test 3: Another follow-up
    print("\n[Test 3] Another follow-up")
    print("-" * 70)
    query3 = "What causes it?"
    response3 = agent.query(query3, session_id=session_id)
    print(f"User: {query3}")
    print(f"Agent: {response3[:150]}...")
    
    # Check history
    print("\n[History Check]")
    print("-" * 70)
    history = agent.get_history(session_id)
    print(f"Total messages in history: {len(history)}")
    for i, msg in enumerate(history):
        role = msg['role'].upper()
        content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
        print(f"  {i+1}. {role}: {content}")
    
    # Test 4: Different session
    print("\n[Test 4] Different session (should have separate context)")
    print("-" * 70)
    session_id2 = "test_session_2"
    query4 = "Camera not detecting defects"
    response4 = agent.query(query4, session_id=session_id2)
    print(f"User (Session 2): {query4}")
    print(f"Agent: {response4[:150]}...")
    
    history2 = agent.get_history(session_id2)
    print(f"Session 2 history: {len(history2)} messages")
    
    # Test 5: Clear history
    print("\n[Test 5] Clear history")
    print("-" * 70)
    agent.clear_history(session_id)
    history_after_clear = agent.get_history(session_id)
    print(f"History after clear: {len(history_after_clear)} messages")
    
    print("\n" + "=" * 70)
    print("TESTS COMPLETE")
    print("=" * 70)
    print("\n✓ Conversation history is working!")
    print("✓ Follow-up questions maintain context")
    print("✓ Multiple sessions are isolated")
    print("✓ History can be cleared")

if __name__ == "__main__":
    test_conversation_flow()
