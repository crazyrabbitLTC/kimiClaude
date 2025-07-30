# SSE Streaming Implementation Guide for Claude Code Proxy

## Overview

This guide provides expert implementation details for adding Server-Sent Events (SSE) streaming to your Claude Code proxy while maintaining reliable tool calling functionality.

## Key Implementation Features

### ✅ **What the Optimized Streaming Proxy Provides**

1. **Real-time Working Indicators**: Shows progress during tool execution phases
2. **Proper Anthropic SSE Format**: Compatible with Claude Code's expected event structure
3. **Multi-iteration Tool Support**: Handles complex tool calling cycles with streaming updates
4. **Dual Mode Operation**: Supports both streaming and non-streaming requests
5. **Enhanced Error Handling**: Robust error recovery and logging
6. **Performance Optimized**: Minimal latency with natural typing effects

### 🔧 **Technical Architecture**

```
Claude Code Request (stream: true)
    ↓
Optimized Streaming Proxy
    ↓
1. Send message_start event
2. Send content_block_start event  
3. Send progress updates during tool execution
4. Execute tool calling loop with Groq API
5. Stream final response with typing effect
6. Send completion events
```

## Implementation Details

### **1. SSE Event Structure**

The proxy implements the complete Anthropic streaming format:

```javascript
// Message start
event: message_start
data: {"type": "message_start", "message": {...}}

// Content block start  
event: content_block_start
data: {"type": "content_block_start", "index": 0, "content_block": {...}}

// Progress updates during tool execution
event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "🔄 Working..."}}

// Final response streaming
event: content_block_delta  
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "word "}}

// Completion events
event: content_block_stop
data: {"type": "content_block_stop", "index": 0}

event: message_delta
data: {"type": "message_delta", "delta": {"stop_reason": "end_turn"}}

event: message_stop
data: {"type": "message_stop"}
```

### **2. Tool Execution with Streaming**

```python
def _process_conversation_with_streaming(self, anthropic_request, message_id):
    """Process conversation with real-time progress updates"""
    
    # Send initial progress
    self._send_progress_update("🔄 Starting...", replace_previous=True)
    
    # Convert messages and tools
    conversation_messages = self._convert_messages_to_openai(initial_messages)
    openai_tools = self._convert_tools_to_openai(tools)
    
    # Execute conversation loop with streaming updates
    iteration = 0
    while iteration < MAX_TOOL_ITERATIONS:
        iteration += 1
        
        # Show thinking progress
        self._send_progress_update(f"🤔 Thinking (step {iteration})...")
        
        # Call Groq API
        response = self._call_groq_api(conversation_messages, openai_tools, anthropic_request)
        
        # Check for tool calls
        if message.get('tool_calls'):
            tool_names = [tc['function']['name'] for tc in message['tool_calls']]
            self._send_progress_update(f"🔧 Executing {', '.join(tool_names)}...")
            
            # Execute each tool with progress updates
            for tool_call in message['tool_calls']:
                tool_result = execute_tool_locally(tool_name, tool_args)
                # Add to conversation and continue
        else:
            # Final response ready
            break
    
    return final_response
```

### **3. Progress Indicator Strategy**

The proxy uses a multi-phase progress system:

1. **🔄 Starting...** - Initial processing
2. **🤔 Thinking (step N)...** - LLM reasoning phases  
3. **🔧 Executing tool1, tool2...** - Tool execution phase
4. **⚙️ tool_name (1/3)...** - Individual tool progress (if multiple)
5. **Final response streaming** - Natural typing effect

### **4. Error Handling & Recovery**

```python
def _send_error_event(self, error_message: str):
    """Send error event in streaming format"""
    self._send_event("error", {
        "type": "error", 
        "error": {
            "type": "api_error",
            "message": error_message
        }
    })
```

## Usage Instructions

### **1. Start the Optimized Proxy**

```bash
# The proxy is automatically used by kimi.sh
./kimi.sh

# Or start manually for testing
python3 optimized_streaming_proxy.py
```

### **2. Test Streaming Functionality**

```bash
# Test the streaming implementation
python3 test_streaming.py
```

### **3. Claude Code Integration**

The proxy automatically detects streaming requests:

```json
{
  "model": "claude-3-sonnet-20240229",
  "messages": [...],
  "tools": [...],
  "stream": true  // Triggers streaming mode
}
```

## Advanced Configuration

### **Environment Variables**

```bash
export GROQ_API_KEY="your-key"
export KIMI_PROXY_PORT="8090"
export KIMI_WORKING_DIR="/path/to/project"
```

### **Streaming Parameters**

```python
STREAM_DELAY = 0.01          # Delay between progress updates
MAX_TOOL_ITERATIONS = 15     # Maximum tool calling cycles
```

### **Debug Logging**

Monitor streaming behavior:

```bash
tail -f /tmp/kimi_streaming_debug.log
```

## Performance Considerations

### **Optimizations Applied**

1. **Minimal Latency**: 10ms delays for smooth streaming without lag
2. **Efficient Tool Execution**: Local tool execution eliminates API round-trips
3. **Smart Progress Updates**: Context-aware progress messages
4. **Connection Management**: Proper HTTP keep-alive and buffering control
5. **Memory Efficient**: Streaming prevents large response buffering

### **Claude Code Compatibility**

- ✅ Proper SSE event format
- ✅ Correct content-type headers (`text/event-stream`)
- ✅ CORS support for browser clients
- ✅ Event-driven progress updates
- ✅ Graceful error handling

## Troubleshooting

### **Common Issues**

1. **No Working Indicator**: Check if `stream: true` in request
2. **Tools Not Executing**: Verify tool schema format
3. **Connection Timeout**: Increase timeout values
4. **Progress Updates Missing**: Check SSE event format

### **Debug Commands**

```bash
# Test proxy health
curl http://localhost:8090/health

# Test streaming with curl
curl -N -H "Content-Type: application/json" \
     -d '{"messages":[{"role":"user","content":"test"}],"stream":true}' \
     http://localhost:8090/v1/messages

# Check proxy logs
tail -f /tmp/kimi_streaming_debug.log
```

## Best Practices

### **For Proxy Development**

1. **Always test both streaming and non-streaming modes**
2. **Use proper event-driven architecture for real-time updates**
3. **Implement comprehensive error handling**
4. **Log extensively for debugging complex tool calling scenarios**
5. **Optimize for low latency while maintaining reliability**

### **For Claude Code Integration**

1. **Set appropriate timeouts for tool-heavy operations**
2. **Monitor proxy health before making requests**
3. **Handle streaming errors gracefully**
4. **Test with various tool combinations**

## Advanced Features

### **Multi-Tool Progress Tracking**

When multiple tools are called in sequence:

```
🔧 Executing LS, Read, Write...
⚙️ LS (1/3)...
⚙️ Read (2/3)...  
⚙️ Write (3/3)...
```

### **Natural Typing Effect**

Final responses stream word by word with realistic timing:

```python
def _stream_text_naturally(self, text: str):
    words = text.split()
    for word in words:
        # Send delta with natural timing
        time.sleep(max(0.01, min(0.05, len(word) * 0.01)))
```

### **Connection Health Monitoring**

The proxy includes built-in health checks and connection monitoring to ensure reliable streaming even with long-running tool operations.

---

## Conclusion

This implementation provides a production-ready streaming solution that:

- ✅ Shows working indicators during tool execution
- ✅ Maintains reliable tool calling functionality  
- ✅ Follows proper SSE format for Claude Code
- ✅ Handles multi-iteration tool execution cycles
- ✅ Provides real-time progress feedback
- ✅ Offers excellent performance and error handling

The hybrid approach ensures both streaming responsiveness and conversation reliability, making it ideal for Claude Code's requirements.