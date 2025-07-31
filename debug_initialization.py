#!/usr/bin/env python3
"""Debug MCP server initialization issues"""

import subprocess
import time
import json

def test_basic_startup():
    print("🔍 Testing basic MCP server startup...")
    
    # Start server with timeout
    process = subprocess.Popen(
        ["timeout", "60", "./start_enhanced_fixed.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        print("⏳ Waiting 15 seconds for startup...")
        time.sleep(15)
        
        # Try to send a simple request
        print("📤 Sending test request...")
        test_request = '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}\n'
        
        process.stdin.write(test_request)
        process.stdin.flush()
        
        # Try to read response with timeout
        print("📥 Waiting for response...")
        
        # Read with timeout
        import select
        import sys
        
        if select.select([process.stdout], [], [], 10):
            response = process.stdout.readline()
            print(f"✅ Response received: {response[:100]}...")
            
            try:
                parsed = json.loads(response)
                print("✅ Valid JSON response")
                return True
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON: {response}")
                return False
        else:
            print("❌ No response within timeout")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        process.terminate()
        process.wait()
        
        # Print stderr for debugging
        stderr = process.stderr.read()
        if stderr:
            print(f"\n📝 Stderr output:\n{stderr}")

def test_components_individually():
    print("\n🔍 Testing components individually...")
    
    # Test msf_init.py
    print("1. Testing msf_init.py...")
    result = subprocess.run(["python3", "msf_init.py"], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        print("✅ msf_init.py works")
    else:
        print(f"❌ msf_init.py failed: {result.stderr}")
    
    # Test import of enhanced MCP
    print("2. Testing MCP imports...")
    test_import = """
import sys
sys.path.append('.')
try:
    from msfconsole_mcp_enhanced import VERSION
    print(f"MCP Version: {VERSION}")
except Exception as e:
    print(f"Import error: {e}")
    """
    
    result = subprocess.run(["python3", "-c", test_import], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print(f"✅ MCP imports work: {result.stdout.strip()}")
    else:
        print(f"❌ MCP import failed: {result.stderr}")

if __name__ == "__main__":
    print("🧪 MCP Initialization Debug Test")
    print("=" * 50)
    
    # Test individual components first
    test_components_individually()
    
    # Test basic startup
    success = test_basic_startup()
    
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")