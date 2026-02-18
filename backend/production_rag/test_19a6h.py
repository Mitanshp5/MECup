"""
Quick test for error code 19A6H retrieval
"""

from agent import get_agent, classify_query, expand_query

def test_error_code():
    query = "What is 19A6H error"
    
    print("=" * 70)
    print("TESTING ERROR CODE 19A6H RETRIEVAL")
    print("=" * 70)
    
    # Test classification
    query_type = classify_query(query)
    print(f"\nQuery: {query}")
    print(f"Classified as: {query_type}")
    
    # Test query expansion
    variations = expand_query(query, query_type)
    print(f"\nQuery variations generated:")
    for i, var in enumerate(variations, 1):
        print(f"  {i}. {var}")
    
    # Initialize agent
    print("\nInitializing agent...")
    agent = get_agent()
    
    # Test retrieval
    print("\nQuerying agent...")
    response = agent.query(query)
    
    print("\n" + "=" * 70)
    print("RESPONSE:")
    print("=" * 70)
    print(response)
    print("\n" + "=" * 70)
    
    # Check if response contains error code
    if "19a6h" in response.lower() or "19A6H" in response:
        print("\n✓ SUCCESS: Error code found in response")
    else:
        print("\n✗ WARNING: Error code not explicitly mentioned")
        print("  This might be okay if the description is accurate")
    
    # Check HTML formatting
    if "<div class=\"troubleshoot-response\">" in response:
        print("✓ HTML formatting correct")
    else:
        print("✗ HTML formatting issue")

if __name__ == "__main__":
    test_error_code()
