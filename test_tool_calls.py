#!/usr/bin/env python3
"""
Test tool calling directly with Groq API to verify if Kimi K2 can handle tools properly
"""
import json
import os
import requests

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

def test_direct_tool_call():
    """Test calling Kimi K2 directly with a simple tool"""
    
    # Simple tool definition
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
    
    # Simple request
    payload = {
        'model': 'moonshotai/kimi-k2-instruct',
        'messages': [
            {'role': 'user', 'content': 'List files in the current directory using the list_files tool'}
        ],
        'tools': tools,
        'max_tokens': 1000
    }
    
    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json'
        },
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        message = data['choices'][0]['message']
        
        print("=== Direct Kimi K2 Tool Call Test ===")
        print(f"Content: {message.get('content', 'None')}")
        print(f"Tool calls: {message.get('tool_calls', 'None')}")
        
        if message.get('tool_calls'):
            print("✅ Kimi K2 DOES call tools directly!")
            return True
        else:
            print("❌ Kimi K2 does NOT call tools - responds with text only")
            return False
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

if __name__ == '__main__':
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY environment variable not set")
        exit(1)
    
    test_direct_tool_call()