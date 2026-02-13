"""
Setup script for Production RAG Agent (Page-Indexed)
Verifies all dependencies and configurations.
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("[*] Checking Python version...")
    v = sys.version_info
    ok = v.major >= 3 and v.minor >= 8
    icon = "OK" if ok else "FAIL"
    print(f"    [{icon}] Python {v.major}.{v.minor}.{v.micro}")
    if not ok:
        print("    Requires >= 3.8")
    return ok


def check_ollama():
    """Check if Ollama is installed and phi3 model is available."""
    print("\n[*] Checking Ollama...")
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("    [OK] Ollama is installed")
            if 'phi3' in result.stdout:
                print("    [OK] phi3 model available")
                return True
            else:
                print("    [FAIL] phi3 model not found -> run: ollama pull phi3")
                return False
        else:
            print("    [FAIL] Ollama not responding")
            return False
    except FileNotFoundError:
        print("    [FAIL] Ollama not installed -> https://ollama.ai")
        return False


def check_dependencies():
    """Check if required packages are installed."""
    print("\n[*] Checking Python dependencies...")
    required = [
        'langchain',
        'langchain_huggingface',
        'langchain_chroma',
        'langchain_ollama',
        'langgraph',
        'chromadb',
        'sentence_transformers',
        'fastapi',
    ]

    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
            print(f"    [OK] {pkg}")
        except ImportError:
            print(f"    [FAIL] {pkg}")
            missing.append(pkg)

    if missing:
        print(f"\n    Missing: {', '.join(missing)}")
        print("    Run: pip install -r requirements.txt")
        return False
    return True


def check_files():
    """Check if required files exist."""
    print("\n[*] Checking required files...")
    base_dir = Path(__file__).parent

    required = ['agent.py', 'rebuild_vectordb.py', 'fastapi_server.py', 'data', 'vectordb']

    all_exist = True
    for item in required:
        path = base_dir / item
        exists = path.exists()
        icon = "OK" if exists else "FAIL"
        print(f"    [{icon}] {item}")
        if not exists:
            all_exist = False

    return all_exist


def test_agent():
    """Test the agent with sample queries across query types."""
    print("\n[*] Testing agent...")
    try:
        from agent import get_agent, classify_query

        agent = get_agent()

        tests = [
            ("error_code", "What is error code 1A68H?"),
            ("troubleshooting", "Camera is not detecting defects"),
            ("info", "What is the light intensity parameter?"),
        ]

        for expected_type, query in tests:
            detected = classify_query(query)
            response = agent.query(query)
            type_ok = "OK" if detected == expected_type else "MISMATCH"
            print(f"    [{type_ok}] type={detected} | {query[:40]}...")
            print(f"           Response: {response[:80]}...")

        print("    [OK] Agent responding correctly")
        return True
    except Exception as e:
        print(f"    [FAIL] Agent test failed: {e}")
        return False


def main():
    """Main setup verification."""
    print("=" * 60)
    print("PRODUCTION RAG AGENT - SETUP VERIFICATION")
    print("(Page-Indexed Architecture)")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version()),
        ("Ollama & phi3", check_ollama()),
        ("Python Dependencies", check_dependencies()),
        ("Required Files", check_files()),
    ]

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, status in checks:
        icon = "OK" if status else "FAIL"
        print(f"[{icon}] {name}")

    all_passed = all(status for _, status in checks)

    if all_passed:
        print("\nAll checks passed! Testing agent...")
        if test_agent():
            print("\nSetup complete! Agent is ready.")
            print("\nUsage:")
            print("  from agent import get_agent")
            print("  agent = get_agent()")
            print("  response = agent.query('your question')")
            print("\nTo rebuild vector DB:")
            print("  python rebuild_vectordb.py")
        else:
            print("\nAgent test failed. Check errors above.")
    else:
        print("\nSome checks failed. Common fixes:")
        print("  1. pip install -r requirements.txt")
        print("  2. Install Ollama: https://ollama.ai")
        print("  3. ollama pull phi3")
        print("  4. python rebuild_vectordb.py")


if __name__ == "__main__":
    main()
