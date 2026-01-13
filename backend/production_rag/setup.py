"""
Setup script for Production RAG Agent
Verifies all dependencies and configurations
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check Python version"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (requires >= 3.8)")
        return False

def check_ollama():
    """Check if Ollama is installed and phi3 model is available"""
    print("\n🔍 Checking Ollama...")
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Ollama is installed")
            if 'phi3' in result.stdout:
                print("   ✅ phi3 model is available")
                return True
            else:
                print("   ⚠️  phi3 model not found")
                print("   Run: ollama pull phi3")
                return False
        else:
            print("   ❌ Ollama not responding")
            return False
    except FileNotFoundError:
        print("   ❌ Ollama not installed")
        print("   Install from: https://ollama.ai")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\n🔍 Checking Python dependencies...")
    required = [
        'langchain',
        'langchain_huggingface',
        'langchain_chroma',
        'langchain_ollama',
        'langgraph',
        'chromadb',
        'sentence_transformers'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    return True

def check_files():
    """Check if required files exist"""
    print("\n🔍 Checking required files...")
    base_dir = Path(__file__).parent
    
    required_files = [
        'agent.py',
        'requirements.txt',
        'data',
        'vectordb'
    ]
    
    all_exist = True
    for item in required_files:
        path = base_dir / item
        if path.exists():
            print(f"   ✅ {item}")
        else:
            print(f"   ❌ {item}")
            all_exist = False
    
    return all_exist

def test_agent():
    """Test the agent with a sample query"""
    print("\n🧪 Testing agent...")
    try:
        from agent import get_agent
        agent = get_agent()
        
        test_query = "Camera is not detecting defects properly"
        print(f"   Query: {test_query}")
        
        response = agent.query(test_query)
        print(f"   ✅ Agent responded successfully")
        print(f"   Response preview: {response[:100]}...")
        return True
    except Exception as e:
        print(f"   ❌ Agent test failed: {e}")
        return False

def main():
    """Main setup verification"""
    print("="*60)
    print("PRODUCTION RAG AGENT SETUP VERIFICATION")
    print("="*60)
    
    checks = [
        ("Python Version", check_python_version()),
        ("Ollama & phi3", check_ollama()),
        ("Python Dependencies", check_dependencies()),
        ("Required Files", check_files())
    ]
    
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60)
    
    for name, status in checks:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}")
    
    all_passed = all(status for _, status in checks)
    
    if all_passed:
        print("\n🎉 All checks passed! Testing agent...")
        if test_agent():
            print("\n✅ Setup complete! Production RAG agent is ready to use.")
            print("\nNext steps:")
            print("1. Import in your application:")
            print("   from agent import get_agent")
            print("   agent = get_agent()")
            print("   response = agent.query('your question')")
            print("\n2. Or run the console app:")
            print("   cd ../console")
            print("   python app.py")
        else:
            print("\n⚠️  Agent test failed. Please check the error above.")
    else:
        print("\n⚠️  Some checks failed. Please resolve the issues above.")
        print("\nCommon fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Install Ollama: https://ollama.ai")
        print("3. Pull phi3 model: ollama pull phi3")

if __name__ == "__main__":
    main()
