"""Test script to verify dynamic formatting across all query types."""

from agent import get_agent, classify_query

def test_agent():
    print("Loading agent...")
    agent = get_agent()

    test_cases = [
        ("greeting",        "hi"),
        ("vague",           "help?"),
        ("error_code",      "What is error code 1A68H [FX5-SSC-S]?"),
        ("troubleshooting", "Camera is not detecting defects properly"),
        ("how_to",          "How to calibrate the vision system?"),
        ("info",            "What does the light intensity parameter do?"),
        ("general",         "Tell me about the paint inspection process"),
    ]

    print("\n" + "=" * 70)
    print("TESTING DYNAMIC RESPONSE FORMATTING")
    print("=" * 70 + "\n")

    for expected_type, query in test_cases:
        detected = classify_query(query)
        match = "OK" if detected == expected_type else f"MISMATCH (expected {expected_type})"
        print(f"Query: {query}")
        print(f"Type:  {detected} [{match}]")
        print("-" * 70)
        try:
            response = agent.query(query)
            print(response)
        except Exception as e:
            print(f"ERROR: {e}")
        print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    test_agent()
