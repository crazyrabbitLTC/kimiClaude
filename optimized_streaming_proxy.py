#!/usr/bin/env python3
"""
Optimized Streaming Proxy for Kimi K2 - Expert SSE Implementation
Provides real-time working indicators during tool execution while maintaining reliability

Key Features:
- Proper Anthropic SSE format for Claude Code compatibility
- Real-time progress indicators during tool execution
- Multi-iteration tool calling with streaming updates
- Reliable conversation state management
- Performance optimized for responsiveness
"""

import json
import os
import sys
import requests
import datetime
import time
import threading
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List, Any, Optional

# Configuration
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
PROXY_PORT = int(os.environ.get('KIMI_PROXY_PORT', '8090'))
WORKING_DIR = os.environ.get('KIMI_WORKING_DIR', os.getcwd())
DEBUG_FILE = '/tmp/kimi_streaming_debug.log'
MAX_TOOL_ITERATIONS = 15
STREAM_DELAY = 0.01  # Minimal delay for smooth streaming

def log_debug(message: str):
    """Thread-safe debug logging"""
    with open(DEBUG_FILE, 'a') as f:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        f.write(f"[{timestamp}] {message}\n")

def execute_tool_locally(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Execute Claude Code tools locally with enhanced error handling"""
    try:
        if tool_name == 'LS':
            import os
            path = tool_input.get('path', WORKING_DIR)
            ignore_patterns = tool_input.get('ignore', [])
            
            # Handle home directory redirection
            home_dir = os.path.expanduser('~')
            if path == home_dir:
                log_debug(f"TOOL_LS: Redirecting home dir to working dir {WORKING_DIR}")
                path = WORKING_DIR
            
            # Convert relative to absolute paths
            if not os.path.isabs(path):
                path = os.path.join(WORKING_DIR, path)
                
            try:
                files = os.listdir(path)
                
                # Apply ignore patterns if specified
                if ignore_patterns:
                    import fnmatch
                    filtered_files = []
                    for file in files:
                        should_ignore = False
                        for pattern in ignore_patterns:
                            if fnmatch.fnmatch(file, pattern):
                                should_ignore = True
                                break
                        if not should_ignore:
                            filtered_files.append(file)
                    files = filtered_files
                
                abs_path = os.path.abspath(path)
                file_list = []
                for f in sorted(files):
                    full_path = os.path.join(abs_path, f)
                    if os.path.isdir(full_path):
                        file_list.append(f"- {f}/")
                    else:
                        file_list.append(f"- {f}")
                
                return f"- {abs_path}/\n" + "\n".join(file_list)
            except PermissionError:
                return f"Permission denied accessing {path}"
            except Exception as e:
                return f"Error listing {path}: {str(e)}"
        
        elif tool_name == 'Read':
            import os
            file_path = tool_input.get('file_path', '')
            offset = tool_input.get('offset', 0)
            limit = tool_input.get('limit', None)
            
            # Convert relative to absolute paths
            if not os.path.isabs(file_path):
                file_path = os.path.join(WORKING_DIR, file_path)
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    # Handle offset and limit for large files
                    if offset > 0:
                        for _ in range(offset):
                            f.readline()
                    
                    lines = []
                    line_count = 0
                    for line in f:
                        if limit and line_count >= limit:
                            break
                        lines.append(f"{offset + line_count + 1:>6}→{line.rstrip()}")
                        line_count += 1
                    
                    if not lines:
                        return f"File {file_path} is empty or offset beyond file length"
                    
                    return "\n".join(lines)
            except FileNotFoundError:
                return f"File not found: {file_path}"
            except PermissionError:
                return f"Permission denied reading {file_path}"
            except Exception as e:
                return f"Error reading {file_path}: {str(e)}"
        
        elif tool_name == 'Write':
            import os
            file_path = tool_input.get('file_path', '')
            content = tool_input.get('content', '')
            
            # Convert relative to absolute paths
            if not os.path.isabs(file_path):
                file_path = os.path.join(WORKING_DIR, file_path)
                
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully wrote {len(content)} characters to {file_path}"
            except PermissionError:
                return f"Permission denied writing to {file_path}"
            except Exception as e:
                return f"Error writing to {file_path}: {str(e)}"
        
        elif tool_name == 'Edit':
            import os
            file_path = tool_input.get('file_path', '')
            old_string = tool_input.get('old_string', '')
            new_string = tool_input.get('new_string', '')
            replace_all = tool_input.get('replace_all', False)
            
            # Convert relative to absolute paths
            if not os.path.isabs(file_path):
                file_path = os.path.join(WORKING_DIR, file_path)
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if old_string not in content:
                    return f"String not found in {file_path}: {old_string[:50]}..."
                
                if replace_all:
                    new_content = content.replace(old_string, new_string)
                    replacements = content.count(old_string)
                else:
                    new_content = content.replace(old_string, new_string, 1)
                    replacements = 1
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                return f"Successfully replaced {replacements} occurrence(s) in {file_path}"
            except Exception as e:
                return f"Error editing {file_path}: {str(e)}"
        
        elif tool_name == 'Bash':
            import os
            import subprocess
            command = tool_input.get('command', '')
            description = tool_input.get('description', 'Execute command')
            timeout = tool_input.get('timeout', 30)
            
            try:
                log_debug(f"TOOL_BASH: Executing '{command}' in {WORKING_DIR}")
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=min(timeout, 60),  # Max 60 seconds
                    cwd=WORKING_DIR,
                    env=os.environ.copy()
                )
                
                output = ""
                if result.stdout:
                    output += result.stdout
                if result.stderr:
                    if output:
                        output += "\n" + result.stderr
                    else:
                        output = result.stderr
                
                if not output:
                    output = f"Command completed with exit code {result.returncode}"
                
                return f"Command: {command}\nExit code: {result.returncode}\nOutput:\n{output}"
            except subprocess.TimeoutExpired:
                return f"Command timed out after {timeout} seconds: {command}"
            except Exception as e:
                return f"Error executing command '{command}': {str(e)}"
        
        elif tool_name == 'Glob':
            import os
            import glob
            pattern = tool_input.get('pattern', '*')
            path = tool_input.get('path', WORKING_DIR)
            
            # Convert relative to absolute paths
            if not os.path.isabs(path):
                path = os.path.join(WORKING_DIR, path)
            
            try:
                full_pattern = os.path.join(path, pattern)
                matches = glob.glob(full_pattern, recursive=True)
                
                # Sort by modification time (newest first)
                matches.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)
                
                if not matches:
                    return f"No files found matching pattern '{pattern}' in {path}"
                
                return "\n".join(matches)
            except Exception as e:
                return f"Error globbing pattern '{pattern}' in {path}: {str(e)}"
        
        else:
            return f"Tool '{tool_name}' is not implemented in local execution"
            
    except Exception as e:
        log_debug(f"TOOL_ERROR: {tool_name} failed with {str(e)}")
        return f"Error executing tool {tool_name}: {str(e)}"

class OptimizedStreamingProxy(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-api-key')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        path = self.path.split('?')[0]
        
        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok", 
                "service": "kimi-streaming-proxy",
                "version": "1.0.0",
                "features": ["streaming", "tool_calling", "claude_code_compatible"]
            }).encode())
        else:
            self.send_error(404, f"Path {path} not found")
    
    def do_POST(self):
        """Handle POST requests"""
        path = self.path.split('?')[0]
        
        if path in ['/v1/messages', '/messages']:
            self.handle_messages()
        else:
            self.send_error(404, f"Path {path} not found")
    
    def handle_messages(self):
        """Main message handling with streaming support"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            anthropic_request = json.loads(post_data)
            
            # Extract request parameters
            initial_messages = anthropic_request.get('messages', [])
            tools = anthropic_request.get('tools', [])
            stream = anthropic_request.get('stream', False)
            
            log_debug(f"REQUEST: {len(initial_messages)} messages, {len(tools)} tools, stream={stream}")
            
            if stream:
                self.handle_streaming_conversation(anthropic_request)
            else:
                self.handle_complete_conversation(anthropic_request)
                
        except json.JSONDecodeError as e:
            log_debug(f"JSON_ERROR: {str(e)}")
            self.send_error(400, f"Invalid JSON: {str(e)}")
        except Exception as e:
            log_debug(f"HANDLER_ERROR: {str(e)}")
            self.send_error(500, str(e))
    
    def handle_streaming_conversation(self, anthropic_request: Dict[str, Any]):
        """Handle streaming conversation with real-time progress updates"""
        log_debug("STREAMING: Starting streaming conversation")
        
        # Set up streaming headers
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('X-Accel-Buffering', 'no')  # Disable nginx buffering
        self.end_headers()
        
        try:
            # Generate unique message ID
            message_id = f"msg_{uuid.uuid4().hex[:8]}"
            
            # Send message_start event
            self._send_event("message_start", {
                "type": "message_start",
                "message": {
                    "id": message_id,
                    "type": "message",
                    "role": "assistant",
                    "content": [],
                    "model": "moonshotai/kimi-k2-instruct",
                    "stop_reason": None,
                    "usage": {"input_tokens": 0, "output_tokens": 0}
                }
            })
            
            # Send content_block_start event
            self._send_event("content_block_start", {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""}
            })
            
            # Process conversation with streaming updates
            final_response = self._process_conversation_with_streaming(
                anthropic_request, message_id
            )
            
            # Stream the final response text
            final_text = self._extract_text_from_response(final_response)
            self._stream_text_naturally(final_text)
            
            # Send completion events
            self._send_completion_events(final_response)
            
            log_debug("STREAMING: Successfully completed streaming conversation")
            
        except Exception as e:
            log_debug(f"STREAMING_ERROR: {str(e)}")
            self._send_error_event(str(e))
    
    def handle_complete_conversation(self, anthropic_request: Dict[str, Any]):
        """Handle complete (non-streaming) conversation"""
        log_debug("COMPLETE: Starting complete conversation")
        
        try:
            final_response = self._execute_complete_conversation(anthropic_request)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(final_response).encode())
            
            log_debug("COMPLETE: Successfully completed conversation")
            
        except Exception as e:
            log_debug(f"COMPLETE_ERROR: {str(e)}")
            self.send_error(500, str(e))
    
    def _send_event(self, event_type: str, data: Dict[str, Any]):
        """Send a Server-Sent Event"""
        try:
            if event_type != "message_start":  # Don't add event type for message_start
                self.wfile.write(f"event: {event_type}\n".encode())
            self.wfile.write(f"data: {json.dumps(data)}\n\n".encode())
            self.wfile.flush()
        except Exception as e:
            log_debug(f"EVENT_SEND_ERROR: {str(e)}")
    
    def _process_conversation_with_streaming(
        self, 
        anthropic_request: Dict[str, Any], 
        message_id: str
    ) -> Dict[str, Any]:
        """Process conversation with tool execution and streaming progress updates"""
        
        initial_messages = anthropic_request.get('messages', [])
        tools = anthropic_request.get('tools', [])
        
        # Send initial working indicator
        self._send_progress_update("🔄 Starting...", replace_previous=True)
        time.sleep(STREAM_DELAY)
        
        # Convert messages and tools to OpenAI format
        conversation_messages = self._convert_messages_to_openai(initial_messages)
        openai_tools = self._convert_tools_to_openai(tools)
        
        log_debug(f"CONVERSATION: Starting with {len(conversation_messages)} messages, {len(openai_tools)} tools")
        
        # Execute conversation loop with streaming updates
        iteration = 0
        total_tool_calls = 0
        
        while iteration < MAX_TOOL_ITERATIONS:
            iteration += 1
            
            # Send iteration progress
            self._send_progress_update(f"🤔 Thinking (step {iteration})...", replace_previous=True)
            time.sleep(STREAM_DELAY)
            
            # Call Groq API
            response = self._call_groq_api(conversation_messages, openai_tools, anthropic_request)
            if not response:
                log_debug(f"ITERATION_{iteration}: Groq API call failed")
                break
            
            message = response['choices'][0]['message']
            
            # Add assistant response to conversation
            conversation_messages.append({
                'role': 'assistant',
                'content': message.get('content', ''),
                'tool_calls': message.get('tool_calls')
            })
            
            # Check for tool calls
            if message.get('tool_calls'):
                tool_calls = message['tool_calls']
                total_tool_calls += len(tool_calls)
                
                tool_names = [tc['function']['name'] for tc in tool_calls]
                log_debug(f"ITERATION_{iteration}: Executing tools: {', '.join(tool_names)}")
                
                # Send tool execution progress
                tool_list = ', '.join(tool_names)
                self._send_progress_update(f"🔧 Executing {tool_list}...", replace_previous=True)
                time.sleep(STREAM_DELAY)
                
                # Execute each tool call
                for i, tool_call in enumerate(tool_calls):
                    tool_name = tool_call['function']['name']
                    tool_args = json.loads(tool_call['function']['arguments'])
                    tool_id = tool_call['id']
                    
                    # Send individual tool progress
                    if len(tool_calls) > 1:
                        self._send_progress_update(
                            f"⚙️ {tool_name} ({i+1}/{len(tool_calls)})...", 
                            replace_previous=True
                        )
                        time.sleep(STREAM_DELAY)
                    
                    # Execute tool locally
                    tool_result = execute_tool_locally(tool_name, tool_args)
                    
                    log_debug(f"TOOL_{tool_name}: Result length: {len(tool_result)} chars")
                    
                    # Add tool result to conversation
                    conversation_messages.append({
                        'role': 'tool',
                        'tool_call_id': tool_id,
                        'content': tool_result
                    })
                
                # Continue to next iteration
                continue
            else:
                # No more tools needed, we have the final response
                log_debug(f"FINAL: No tools called, conversation complete after {iteration} iterations")
                break
        
        # Build final response
        final_message = conversation_messages[-1]  # Last assistant message
        final_response = {
            'id': message_id,
            'type': 'message',
            'role': 'assistant',
            'content': [{'type': 'text', 'text': final_message.get('content', '')}],
            'model': 'moonshotai/kimi-k2-instruct',
            'stop_reason': 'end_turn',
            'usage': {
                'input_tokens': response.get('usage', {}).get('prompt_tokens', 100),
                'output_tokens': response.get('usage', {}).get('completion_tokens', 50)
            }
        }
        
        log_debug(f"CONVERSATION_COMPLETE: {iteration} iterations, {total_tool_calls} tool calls")
        return final_response
    
    def _execute_complete_conversation(self, anthropic_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete conversation without streaming (reuse streaming logic)"""
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        return self._process_conversation_with_streaming(anthropic_request, message_id)
    
    def _convert_messages_to_openai(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Anthropic messages to OpenAI format"""
        openai_messages = []
        
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if isinstance(content, list):
                # Handle complex content (tool results, etc.)
                text_parts = []
                for item in content:
                    if item.get('type') == 'text':
                        text_parts.append(item['text'])
                    elif item.get('type') == 'tool_result':
                        # Convert tool result to text
                        result_content = item.get('content', '')
                        if isinstance(result_content, list):
                            result_text = ' '.join([str(c.get('text', c)) for c in result_content])
                        else:
                            result_text = str(result_content)
                        text_parts.append(f"Tool result: {result_text}")
                
                if text_parts:
                    openai_messages.append({
                        'role': 'user' if role == 'user' else role,
                        'content': ' '.join(text_parts)
                    })
            else:
                openai_messages.append({'role': role, 'content': content})
        
        return openai_messages
    
    def _convert_tools_to_openai(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Anthropic tools to OpenAI format"""
        openai_tools = []
        
        for tool in tools:
            if 'name' in tool and 'input_schema' in tool:
                openai_tools.append({
                    'type': 'function',
                    'function': {
                        'name': tool['name'],
                        'description': tool.get('description', ''),
                        'parameters': tool.get('input_schema', {})
                    }
                })
        
        return openai_tools
    
    def _call_groq_api(
        self, 
        messages: List[Dict[str, Any]], 
        tools: List[Dict[str, Any]], 
        anthropic_request: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make API call to Groq"""
        payload = {
            'model': 'moonshotai/kimi-k2-instruct',
            'messages': messages,
            'max_tokens': min(anthropic_request.get('max_tokens', 4096), 16384),
            'temperature': anthropic_request.get('temperature', 0.7)
        }
        
        if tools:
            payload['tools'] = tools
        
        try:
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {GROQ_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=45  # Increased timeout for better reliability
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                log_debug(f"GROQ_API_ERROR: {response.status_code} - {response.text[:300]}")
                return None
                
        except requests.exceptions.Timeout:
            log_debug("GROQ_API_TIMEOUT: Request timed out")
            return None
        except Exception as e:
            log_debug(f"GROQ_API_EXCEPTION: {str(e)}")
            return None
    
    def _send_progress_update(self, text: str, replace_previous: bool = False):
        """Send a progress update via streaming"""
        try:
            if replace_previous:
                # This simulates replacing previous text, though SSE doesn't directly support it
                # Claude Code will append, so we send the new status
                pass
            
            self._send_event("content_block_delta", {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": text}
            })
        except Exception as e:
            log_debug(f"PROGRESS_UPDATE_ERROR: {str(e)}")
    
    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """Extract text content from response"""
        for content_block in response.get('content', []):
            if content_block.get('type') == 'text':
                return content_block.get('text', '')
        return ""
    
    def _stream_text_naturally(self, text: str):
        """Stream text with natural typing effect"""
        if not text:
            return
        
        # Clear the progress indicator and start fresh content
        self._send_event("content_block_delta", {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "text_delta", "text": "\n\n"}
        })
        
        # Stream text word by word for natural effect
        words = text.split()
        for i, word in enumerate(words):
            word_with_space = word + (" " if i < len(words) - 1 else "")
            
            self._send_event("content_block_delta", {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": word_with_space}
            })
            
            # Small delay for natural typing effect
            time.sleep(max(0.01, min(0.05, len(word) * 0.01)))
    
    def _send_completion_events(self, response: Dict[str, Any]):
        """Send completion events"""
        try:
            # Content block stop
            self._send_event("content_block_stop", {
                "type": "content_block_stop",
                "index": 0
            })
            
            # Message delta
            self._send_event("message_delta", {
                "type": "message_delta",
                "delta": {
                    "stop_reason": response.get('stop_reason', 'end_turn'),
                    "stop_sequence": None
                },
                "usage": response.get('usage', {})
            })
            
            # Message stop
            self._send_event("message_stop", {
                "type": "message_stop"
            })
            
        except Exception as e:
            log_debug(f"COMPLETION_EVENTS_ERROR: {str(e)}")
    
    def _send_error_event(self, error_message: str):
        """Send error event in streaming"""
        try:
            self._send_event("error", {
                "type": "error",
                "error": {
                    "type": "api_error",
                    "message": error_message
                }
            })
        except Exception as e:
            log_debug(f"ERROR_EVENT_ERROR: {str(e)}")
    
    def log_message(self, format, *args):
        """Override to control logging"""
        # Only log errors to avoid cluttering
        if "error" in format.lower():
            log_debug(f"HTTP: {format % args}")

def main():
    """Main function to start the optimized streaming proxy"""
    
    # Initialize debug log
    with open(DEBUG_FILE, 'w') as f:
        f.write(f"=== Optimized Streaming Proxy Started ===\n")
        f.write(f"Working Directory: {WORKING_DIR}\n")
        f.write(f"Proxy Port: {PROXY_PORT}\n")
        f.write(f"Groq API Key: {'***' if GROQ_API_KEY else 'NOT SET'}\n")
        f.write("=" * 50 + "\n")
    
    log_debug("STARTUP: Starting optimized streaming proxy with enhanced tool support")
    
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        server = HTTPServer(('localhost', PROXY_PORT), OptimizedStreamingProxy)
        log_debug(f"STARTUP: Server bound to localhost:{PROXY_PORT}")
        
        print(f"🚀 Optimized Streaming Proxy running on http://localhost:{PROXY_PORT}", file=sys.stderr)
        print(f"📁 Working directory: {WORKING_DIR}", file=sys.stderr)
        print(f"📝 Debug log: {DEBUG_FILE}", file=sys.stderr)
        print("✅ Ready for Claude Code streaming requests!", file=sys.stderr)
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        log_debug("SHUTDOWN: Received keyboard interrupt")
        print("\n🛑 Proxy shutting down...", file=sys.stderr)
    except Exception as e:
        log_debug(f"STARTUP_ERROR: {str(e)}")
        print(f"❌ Error starting proxy: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()