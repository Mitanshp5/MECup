"""Test script to verify conversational improvements"""

from agent import get_agent

def test_agent():
    print("Loading agent...")
    agent = get_agent()
    
    test_cases = [
        "What is error code : 1A68H [FX5-SSC-S]?",
    ]
    
    print("\n" + "="*70)
    print("TESTING CONVERSATIONAL IMPROVEMENTS")
    print("="*70 + "\n")
    
    for i, query in enumerate(test_cases, 1):
        print(f"Test {i}: {query}")
        print("-"*70)
        try:
            response = agent.query(query)
            print(response)
        except Exception as e:
            print(f"ERROR: {e}")
        print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    test_agent()
