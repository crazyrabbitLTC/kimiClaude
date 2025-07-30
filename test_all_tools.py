#!/usr/bin/env python3
"""
Test all Claude Code tools through the Kimi proxy
"""
import requests
import json
import os

# Test configuration
PROXY_URL = "http://localhost:8090"
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

def test_tool_calling():
    """Test each tool individually"""
    
    # Test LS tool
    test_ls = {
        "messages": [{"role": "user", "content": "Use the LS tool to list files in the current directory"}],
        "tools": [{
            "name": "LS",
            "description": "List files and directories",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"}
                }
            }
        }],
        "max_tokens": 1000
    }
    
    # Test Write tool
    test_write = {
        "messages": [{"role": "user", "content": "Use the Write tool to create test.txt with content 'Hello World'"}],
        "tools": [{
            "name": "Write",
            "description": "Write content to a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["file_path", "content"]
            }
        }],
        "max_tokens": 1000
    }
    
    # Test Read tool
    test_read = {
        "messages": [{"role": "user", "content": "Use the Read tool to read the content of kimi.sh"}],
        "tools": [{
            "name": "Read",
            "description": "Read file contents",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            }
        }],
        "max_tokens": 1000
    }
    
    # Test Bash tool
    test_bash = {
        "messages": [{"role": "user", "content": "Use the Bash tool to run 'pwd' command"}],
        "tools": [{
            "name": "Bash",
            "description": "Execute bash commands",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["command"]
            }
        }],
        "max_tokens": 1000
    }
    
    tests = [
        ("LS Tool", test_ls),
        ("Write Tool", test_write), 
        ("Read Tool", test_read),
        ("Bash Tool", test_bash)
    ]
    
    print("🧪 Testing All Claude Code Tools via Kimi Proxy")
    print("=" * 50)
    
    for test_name, payload in tests:
        print(f"\n📋 Testing {test_name}...")
        
        try:
            response = requests.post(
                f"{PROXY_URL}/v1/messages",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('content', [])
                stop_reason = data.get('stop_reason', 'unknown')
                
                if stop_reason == 'tool_use':
                    tool_uses = [c for c in content if c.get('type') == 'tool_use']
                    print(f"✅ {test_name}: SUCCESS - {len(tool_uses)} tool calls made")
                    for tool_use in tool_uses:
                        print(f"   🔧 Called: {tool_use.get('name')}")
                else:
                    print(f"⚠️  {test_name}: No tools called (stop_reason: {stop_reason})")
                    text_content = [c.get('text', '') for c in content if c.get('type') == 'text']
                    if text_content:
                        print(f"   💬 Response: {text_content[0][:100]}...")
            else:
                print(f"❌ {test_name}: HTTP {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ {test_name}: Exception - {str(e)}")
    
    print(f"\n🏁 Tool testing complete!")

if __name__ == '__main__':
    if not GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY environment variable not set")
        print("Run: export GROQ_API_KEY=$(cat ~/.config/kimi-claude/groq_api_key)")
        exit(1)
    
    test_tool_calling()