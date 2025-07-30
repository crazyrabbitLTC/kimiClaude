#!/usr/bin/env python3
"""
Direct test of tool calling to verify Kimi K2 can actually call tools
"""
import requests
import json
import os

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

def test_direct_kimi_tool_calling():
    """Test Kimi K2 directly with Groq API to confirm tool calling capability"""
    
    print("🧪 Testing Kimi K2 Tool Calling Directly via Groq API")
    print("=" * 55)

    # Direct Groq API call with tools
    tools = [{
        'type': 'function',
        'function': {
            'name': 'list_files',
            'description': 'List files in a directory',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {
                        'type': 'string',
                        'description': 'Directory path to list'
                    }
                },
                'required': ['path']
            }
        }
    }]
    
    payload = {
        'model': 'moonshotai/kimi-k2-instruct',
        'messages': [
            {'role': 'user', 'content': 'Please use the list_files tool to list files in the current directory'}
        ],
        'tools': tools,
        'max_tokens': 1000
    }
    
    print("📤 Sending request to Groq API...")
    print(f"   Model: {payload['model']}")
    print(f"   Tools: {len(payload['tools'])}")
    print(f"   Message: {payload['messages'][0]['content']}")
    
    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']
            
            print("📥 Response received:")
            print(f"   Status: {response.status_code} ✅")
            print(f"   Content: {message.get('content', 'None')}")
            print(f"   Tool calls: {len(message.get('tool_calls', []))}")
            
            if message.get('tool_calls'):
                print("\n🔧 Tool Calls Found:")
                for i, tool_call in enumerate(message['tool_calls']):
                    func_name = tool_call['function']['name']
                    func_args = tool_call['function']['arguments']
                    print(f"   {i+1}. {func_name}({func_args})")
                
                print("\n✅ CONFIRMED: Kimi K2 CAN call tools!")
                return True
            else:
                print("\n❌ ISSUE: Kimi K2 did not call tools")
                print("   This means the model chose to respond with text instead")
                return False
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request Error: {str(e)}")
        return False

def test_proxy_tool_forwarding():
    """Test if our proxy is properly forwarding tools"""
    
    print("\n🧪 Testing Proxy Tool Forwarding")
    print("=" * 35)
    
    # Test request with tools to our proxy
    proxy_request = {
        "messages": [{"role": "user", "content": "Use the LS tool to list files"}],
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
        "stream": False,
        "max_tokens": 1000
    }
    
    print("📤 Sending request to proxy...")
    print(f"   Tools: {len(proxy_request['tools'])}")
    print(f"   Tool name: {proxy_request['tools'][0]['name']}")
    
    try:
        response = requests.post(
            "http://localhost:8090/v1/messages",
            headers={"Content-Type": "application/json"},
            json=proxy_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get('content', [])
            
            print("📥 Proxy response received:")
            print(f"   Status: {response.status_code} ✅")
            print(f"   Content blocks: {len(content)}")
            
            # Check if response contains evidence of tool execution
            text_content = ""
            for block in content:
                if block.get('type') == 'text':
                    text_content += block.get('text', '')
            
            if any(indicator in text_content for indicator in ['Files in', 'Error listing', 'kimi.sh', '.git']):
                print("✅ CONFIRMED: Proxy executed tools successfully!")
                print(f"   Response preview: {text_content[:100]}...")
                return True
            else:
                print("❌ ISSUE: No evidence of tool execution in response")
                print(f"   Response preview: {text_content[:100]}...")
                return False
                
        else:
            print(f"❌ Proxy Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Proxy Connection Error: {str(e)}")
        return False

def main():
    if not GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY environment variable not set")
        print("Run: export GROQ_API_KEY=$(cat ~/.config/kimi-claude/groq_api_key)")
        return
    
    print("🎯 Goal: Verify Kimi K2 can call tools and proxy forwards them correctly\n")
    
    # Test 1: Direct API
    direct_test = test_direct_kimi_tool_calling()
    
    # Test 2: Through proxy
    proxy_test = test_proxy_tool_forwarding()
    
    print("\n🏁 Summary:")
    print(f"   Direct Kimi K2 tool calling: {'✅ WORKS' if direct_test else '❌ FAILED'}")
    print(f"   Proxy tool forwarding: {'✅ WORKS' if proxy_test else '❌ FAILED'}")
    
    if direct_test and proxy_test:
        print("\n🎉 Both tests passed! Tool calling should work end-to-end.")
    elif direct_test and not proxy_test:
        print("\n⚠️  Kimi can call tools, but proxy has issues.")
    elif not direct_test and proxy_test:
        print("\n⚠️  Proxy works, but Kimi isn't calling tools.")
    else:
        print("\n❌ Both tests failed. Need to investigate further.")

if __name__ == '__main__':
    main()