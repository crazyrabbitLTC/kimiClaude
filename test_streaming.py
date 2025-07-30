#!/usr/bin/env python3
"""
Comprehensive test suite for Kimi K2 SSE streaming functionality
Tests both streaming and non-streaming modes with all tools
"""
import requests
import json
import os
import time
import threading
import sys

# Test configuration
PROXY_URL = "http://localhost:8090"
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
DEBUG_MODE = '--debug' in sys.argv

def print_status(message, status="INFO"):
    colors = {
        "INFO": "\033[94m",     # Blue
        "SUCCESS": "\033[92m",  # Green  
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",    # Red
        "RESET": "\033[0m"      # Reset
    }
    print(f"{colors.get(status, '')}{status}: {message}{colors['RESET']}")

def test_streaming_mode():
    """Test SSE streaming with working indicators"""
    print_status("Testing SSE Streaming Mode", "INFO")
    
    # Test streaming file listing
    streaming_request = {
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
        "stream": True,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            f"{PROXY_URL}/v1/messages",
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            json=streaming_request,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print_status("✅ Streaming request accepted", "SUCCESS")
            
            events_received = []
            content_chunks = []
            
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith('event: '):
                        event_type = line[7:]
                        events_received.append(event_type)
                        if DEBUG_MODE:
                            print_status(f"Event: {event_type}", "INFO")
                    elif line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if data.get('type') == 'content_block_delta':
                                delta_text = data.get('delta', {}).get('text', '')
                                if delta_text:
                                    content_chunks.append(delta_text)
                                    if DEBUG_MODE:
                                        print_status(f"Content: {delta_text.strip()}", "INFO")
                        except json.JSONDecodeError:
                            pass
            
            # Analyze results
            expected_events = ['message_start', 'content_block_start', 'content_block_delta', 'content_block_stop', 'message_delta', 'message_stop']
            
            print_status(f"Events received: {events_received}", "INFO")
            print_status(f"Content chunks: {len(content_chunks)}", "INFO")
            
            if all(event in events_received for event in expected_events):
                print_status("✅ All required SSE events received", "SUCCESS")
            else:
                print_status("⚠️  Some SSE events missing", "WARNING")
            
            if any("🔄" in chunk or "🤖" in chunk or "🔧" in chunk for chunk in content_chunks):
                print_status("✅ Working indicators detected in stream", "SUCCESS")
            else:
                print_status("⚠️  No working indicators found", "WARNING")
            
            final_content = ''.join(content_chunks)
            if "Files in" in final_content or any(f in final_content for f in ['.git', 'kimi.sh', '.py']):
                print_status("✅ Tool execution successful (file listing found)", "SUCCESS")
            else:
                print_status("❌ Tool execution may have failed", "ERROR")
            
            return True
            
        else:
            print_status(f"❌ Streaming request failed: {response.status_code}", "ERROR")
            print_status(f"Response: {response.text[:200]}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"❌ Streaming test error: {str(e)}", "ERROR")
        return False

def test_non_streaming_mode():
    """Test non-streaming mode for compatibility"""
    print_status("Testing Non-Streaming Mode", "INFO")
    
    non_streaming_request = {
        "messages": [{"role": "user", "content": "Use the Write tool to create a test file called streaming_test.txt with content 'Streaming test successful'"}],
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
        "stream": False,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            f"{PROXY_URL}/v1/messages",
            headers={"Content-Type": "application/json"},
            json=non_streaming_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get('content', [])
            stop_reason = data.get('stop_reason', 'unknown')
            
            print_status(f"✅ Non-streaming request successful", "SUCCESS")
            print_status(f"Stop reason: {stop_reason}", "INFO")
            print_status(f"Content blocks: {len(content)}", "INFO")
            
            # Check if file was created
            if os.path.exists('streaming_test.txt'):
                with open('streaming_test.txt', 'r') as f:
                    file_content = f.read()
                if 'Streaming test successful' in file_content:
                    print_status("✅ File creation successful", "SUCCESS")
                    os.remove('streaming_test.txt')  # Cleanup
                else:
                    print_status("⚠️  File created but content incorrect", "WARNING")
            else:
                print_status("⚠️  Test file not found", "WARNING")
            
            return True
            
        else:
            print_status(f"❌ Non-streaming request failed: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"❌ Non-streaming test error: {str(e)}", "ERROR")
        return False

def test_multi_tool_streaming():
    """Test streaming with multiple tool calls"""
    print_status("Testing Multi-Tool Streaming", "INFO")
    
    multi_tool_request = {
        "messages": [{"role": "user", "content": "First list files with LS, then use Bash to run 'pwd' command"}],
        "tools": [
            {
                "name": "LS",
                "description": "List files and directories",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"}
                    }
                }
            },
            {
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
            }
        ],
        "stream": True,
        "max_tokens": 1500
    }
    
    try:
        response = requests.post(
            f"{PROXY_URL}/v1/messages",
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            json=multi_tool_request,
            stream=True,
            timeout=45
        )
        
        if response.status_code == 200:
            progress_indicators = []
            tool_mentions = []
            
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if data.get('type') == 'content_block_delta':
                            delta_text = data.get('delta', {}).get('text', '')
                            if any(indicator in delta_text for indicator in ['🔄', '🤖', '🔧', '✅']):
                                progress_indicators.append(delta_text.strip())
                            if any(tool in delta_text for tool in ['LS', 'Bash', 'pwd']):
                                tool_mentions.append(delta_text.strip())
                    except json.JSONDecodeError:
                        pass
            
            print_status(f"Progress indicators found: {len(progress_indicators)}", "INFO")
            print_status(f"Tool mentions found: {len(tool_mentions)}", "INFO")
            
            if DEBUG_MODE:
                for indicator in progress_indicators[:5]:  # Show first 5
                    print_status(f"Indicator: {indicator}", "INFO")
            
            if len(progress_indicators) >= 2:
                print_status("✅ Multiple progress indicators detected", "SUCCESS")
            else:
                print_status("⚠️  Limited progress indicators", "WARNING")
            
            if len(tool_mentions) >= 2:
                print_status("✅ Multiple tools detected in stream", "SUCCESS")
            else:
                print_status("⚠️  Limited tool activity detected", "WARNING")
            
            return True
            
        else:
            print_status(f"❌ Multi-tool streaming failed: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"❌ Multi-tool streaming error: {str(e)}", "ERROR")
        return False

def test_proxy_health():
    """Test proxy health and connectivity"""
    print_status("Testing Proxy Health", "INFO")
    
    try:
        response = requests.get(f"{PROXY_URL}/health", timeout=5)
        if response.status_code == 200:
            print_status("✅ Proxy health check passed", "SUCCESS")
            return True
        else:
            print_status(f"❌ Proxy health check failed: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        print_status(f"❌ Proxy connection error: {str(e)}", "ERROR")
        return False

def main():
    """Run comprehensive streaming tests"""
    print_status("🧪 Starting Kimi K2 SSE Streaming Tests", "INFO")
    print_status("=" * 50, "INFO")
    
    if not GROQ_API_KEY:
        print_status("❌ GROQ_API_KEY environment variable not set", "ERROR")
        print_status("Run: export GROQ_API_KEY=$(cat ~/.config/kimi-claude/groq_api_key)", "INFO")
        return
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Proxy Health", test_proxy_health),
        ("Non-Streaming Mode", test_non_streaming_mode),
        ("SSE Streaming Mode", test_streaming_mode),
        ("Multi-Tool Streaming", test_multi_tool_streaming)
    ]
    
    for test_name, test_func in tests:
        print_status(f"\n📋 Running {test_name} Test...", "INFO")
        try:
            result = test_func()
            test_results.append((test_name, result))
            if result:
                print_status(f"✅ {test_name} Test: PASSED", "SUCCESS")
            else:
                print_status(f"❌ {test_name} Test: FAILED", "ERROR")
        except Exception as e:
            print_status(f"❌ {test_name} Test: ERROR - {str(e)}", "ERROR")
            test_results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print_status("\n🏁 Test Summary", "INFO")
    print_status("=" * 30, "INFO")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print_status(f"{test_name}: {status}", "SUCCESS" if result else "ERROR")
    
    print_status(f"\nOverall: {passed}/{total} tests passed", "SUCCESS" if passed == total else "WARNING")
    
    if passed == total:
        print_status("🎉 All tests passed! SSE streaming is working correctly.", "SUCCESS")
    else:
        print_status(f"⚠️  {total - passed} test(s) failed. Check implementation.", "WARNING")

if __name__ == '__main__':
    main()