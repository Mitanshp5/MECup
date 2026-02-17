"""
Test script to measure RAG accuracy improvements
"""

from agent import get_agent, classify_query

def test_accuracy():
    print("=" * 70)
    print("RAG ACCURACY TEST")
    print("=" * 70)
    
    print("\nInitializing agent...")
    agent = get_agent()
    
    # Test queries covering different types
    test_cases = [
        {
            "query": "What is error code 1A68H [FX5-SSC-S]?",
            "expected_type": "error_code",
            "should_contain": ["error", "code", "1A68H"]
        },
        {
            "query": "Camera is not detecting defects properly",
            "expected_type": "troubleshooting",
            "should_contain": ["camera", "detect"]
        },
        {
            "query": "How to calibrate the vision system?",
            "expected_type": "how_to",
            "should_contain": ["calibrat", "vision"]
        },
        {
            "query": "What does the light intensity parameter do?",
            "expected_type": "info",
            "should_contain": ["light", "intensity"]
        },
        {
            "query": "Paint finish looks uneven and blotchy",
            "expected_type": "troubleshooting",
            "should_contain": ["paint", "finish"]
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        expected_type = test["expected_type"]
        should_contain = test["should_contain"]
        
        print(f"\n{'=' * 70}")
        print(f"TEST {i}/5: {query}")
        print(f"{'=' * 70}")
        
        # Check query classification
        detected_type = classify_query(query)
        type_match = detected_type == expected_type
        print(f"Query Type: {detected_type} {'✓' if type_match else '✗ (expected: ' + expected_type + ')'}")
        
        # Get response
        print("\nGenerating response...")
        try:
            response = agent.query(query)
            
            # Check if response contains expected keywords
            response_lower = response.lower()
            keyword_matches = sum(1 for kw in should_contain if kw.lower() in response_lower)
            keyword_score = keyword_matches / len(should_contain)
            
            # Check for source citations
            has_sources = "source:" in response_lower or "source-ref" in response_lower
            
            # Overall success
            success = type_match and keyword_score >= 0.5 and len(response) > 50
            
            results.append({
                "query": query,
                "success": success,
                "type_match": type_match,
                "keyword_score": keyword_score,
                "has_sources": has_sources,
                "response_length": len(response)
            })
            
            print(f"\nResponse Preview:")
            print(response[:300] + "..." if len(response) > 300 else response)
            
            print(f"\nMetrics:")
            print(f"  Type Match: {'✓' if type_match else '✗'}")
            print(f"  Keyword Match: {keyword_score:.0%} ({keyword_matches}/{len(should_contain)})")
            print(f"  Has Sources: {'✓' if has_sources else '✗'}")
            print(f"  Response Length: {len(response)} chars")
            print(f"  Overall: {'✓ PASS' if success else '✗ FAIL'}")
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            results.append({
                "query": query,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    
    successful = sum(1 for r in results if r.get("success", False))
    total = len(results)
    accuracy = (successful / total) * 100
    
    print(f"\nAccuracy: {successful}/{total} ({accuracy:.0f}%)")
    
    for i, result in enumerate(results, 1):
        status = "✓ PASS" if result.get("success", False) else "✗ FAIL"
        print(f"  {i}. {status} - {result['query'][:50]}...")
    
    if accuracy >= 80:
        print(f"\n🎉 Excellent! Accuracy is {accuracy:.0f}%")
    elif accuracy >= 60:
        print(f"\n✓ Good! Accuracy is {accuracy:.0f}% (target: 80%+)")
    else:
        print(f"\n⚠ Needs improvement. Accuracy is {accuracy:.0f}% (target: 80%+)")
    
    print("\nRecommendations:")
    if accuracy < 80:
        print("  1. Check if PDFs contain the information for failed queries")
        print("  2. Try increasing TOP_K to 8 in agent.py")
        print("  3. Lower RELEVANCE_THRESHOLD to 0.10 in agent.py")
        print("  4. Increase chunk_size to 800 in rebuild_vectordb.py")
    else:
        print("  System is performing well! Monitor production queries.")
    
    print(f"\n{'=' * 70}\n")

if __name__ == "__main__":
    test_accuracy()
