#!/bin/bash

# Kimi Launcher for Claude Code - macOS Version
# Supports both Moonshot AI and Groq APIs with automatic proxy for Groq
# This script temporarily sets environment variables to use Kimi K2 with Claude Code
# without affecting your permanent system settings

# Color codes for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_DIR="$HOME/.config/kimi-claude"
MOONSHOT_KEY_FILE="$CONFIG_DIR/moonshot_api_key"
GROQ_KEY_FILE="$CONFIG_DIR/groq_api_key"
CONFIG_FILE="$CONFIG_DIR/config"
PROVIDER_FILE="$CONFIG_DIR/provider"

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Function to display header
show_header() {
    echo -e "${CYAN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}Kimi K2 Launcher for Claude Code${NC}        ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BLUE}macOS Edition${NC} | ${MAGENTA}Groq + Moonshot${NC}        ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════╝${NC}"
    echo
}

# Function to display usage
usage() {
    show_header
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  ${BOLD}kimi${NC} [claude-args...]         Launch Claude Code with Kimi K2"
    echo -e "  ${BOLD}kimi setup${NC}                  Initial setup wizard"
    echo -e "  ${BOLD}kimi provider${NC} <groq|moonshot> Switch between Groq and Moonshot"
    echo -e "  ${BOLD}kimi set-key${NC} <provider> <KEY> Set API key for provider"
    echo -e "  ${BOLD}kimi check${NC}                  Check current configuration"
    echo -e "  ${BOLD}kimi reset${NC}                  Reset all settings"
    echo -e "  ${BOLD}kimi help${NC}                   Show this help message"
    echo
    echo -e "${CYAN}Examples:${NC}"
    echo -e "  kimi provider groq          # Switch to Groq (fast!)"
    echo -e "  kimi set-key groq YOUR_KEY  # Set Groq API key"
    echo -e "  kimi                        # Launch with current provider"
    echo -e "  kimi --print \"your prompt\"   # Get response and exit (non-interactive)"
    echo -e "  kimi --help                 # Show Claude Code help"
}

# Function to get current provider
get_current_provider() {
    if [ -f "$PROVIDER_FILE" ]; then
        cat "$PROVIDER_FILE"
    else
        echo "moonshot"  # Default provider
    fi
}

# Function to set provider
set_provider() {
    local provider="$1"
    
    case "$provider" in
        groq|moonshot)
            echo "$provider" > "$PROVIDER_FILE"
            echo -e "${GREEN}✓ Provider switched to: ${BOLD}$provider${NC}"
            
            # Show provider-specific info
            if [ "$provider" = "groq" ]; then
                echo -e "${CYAN}Groq benefits:${NC}"
                echo -e "  • ${GREEN}~200 tokens/second${NC} (blazing fast!)"
                echo -e "  • Same Kimi K2 model"
                echo -e "  • 131K context window"
                echo -e "  • Lower cost ($1 input, $3 output per 1M tokens)"
                
                if [ ! -f "$GROQ_KEY_FILE" ]; then
                    echo -e "\n${YELLOW}Note: You need to set your Groq API key${NC}"
                    echo -e "Get one at: ${CYAN}https://console.groq.com/keys${NC}"
                    echo -e "Then run: ${BOLD}kimi set-key groq YOUR_KEY${NC}"
                fi
            else
                echo -e "${CYAN}Moonshot benefits:${NC}"
                echo -e "  • Official Kimi K2 provider"
                echo -e "  • Direct support from Moonshot AI"
            fi
            ;;
        *)
            echo -e "${RED}Error: Invalid provider. Choose 'groq' or 'moonshot'${NC}"
            return 1
            ;;
    esac
}

# Function to check if API key is stored
check_api_key() {
    local provider="${1:-$(get_current_provider)}"
    local key_file
    
    if [ "$provider" = "groq" ]; then
        key_file="$GROQ_KEY_FILE"
    else
        key_file="$MOONSHOT_KEY_FILE"
    fi
    
    [ -f "$key_file" ] && [ -s "$key_file" ]
}

# Function for initial setup
setup_wizard() {
    show_header
    echo -e "${BLUE}Welcome to Kimi K2 Setup Wizard!${NC}\n"
    
    # Check if Claude Code is installed
    echo -e "${YELLOW}Step 1: Checking Claude Code installation...${NC}"
    
    # Check for 'claude' command (Claude Code uses this)
    if command -v claude &> /dev/null; then
        echo -e "${GREEN}✓ Claude Code found in PATH (as 'claude')${NC}"
        CLAUDE_CMD="claude"
    # Check for 'claude-code' command
    elif command -v claude-code &> /dev/null; then
        echo -e "${GREEN}✓ Claude Code found in PATH${NC}"
        CLAUDE_CMD="claude-code"
    # Check for macOS app
    elif [ -d "/Applications/Claude Code.app" ]; then
        echo -e "${GREEN}✓ Claude Code app found${NC}"
        CLAUDE_CMD="open -a 'Claude Code'"
    # Check for Homebrew installation
    elif [ -f "/opt/homebrew/bin/claude" ]; then
        echo -e "${GREEN}✓ Claude Code found (Homebrew)${NC}"
        CLAUDE_CMD="/opt/homebrew/bin/claude"
    elif [ -f "/usr/local/bin/claude" ]; then
        echo -e "${GREEN}✓ Claude Code found (usr/local)${NC}"
        CLAUDE_CMD="/usr/local/bin/claude"
    # Check for npx
    elif command -v npx &> /dev/null && npx claude --version &> /dev/null 2>&1; then
        echo -e "${GREEN}✓ Claude Code available via npx${NC}"
        CLAUDE_CMD="npx claude"
    else
        echo -e "${RED}✗ Claude Code not found${NC}"
        echo -e "${YELLOW}Please install Claude Code first${NC}"
        echo -e "${CYAN}Options:${NC}"
        echo -e "  • Download: https://claude.ai/download"
        echo -e "  • The command is 'claude' not 'claude-code'"
        return 1
    fi
    
    # Save Claude Code command
    echo "CLAUDE_CMD=\"$CLAUDE_CMD\"" > "$CONFIG_FILE"
    
    # Choose provider
    echo -e "\n${YELLOW}Step 2: Choose Provider${NC}"
    echo -e "${CYAN}1) Groq${NC} - Lightning fast (~200 TPS), lower cost"
    echo -e "${CYAN}2) Moonshot${NC} - Official provider"
    echo
    read -p "Select provider (1 or 2): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[1]$ ]]; then
        set_provider "groq" > /dev/null
        provider="groq"
        api_prompt="Enter your Groq API key"
        api_url="https://console.groq.com/keys"
        api_prefix="gsk"
    else
        set_provider "moonshot" > /dev/null
        provider="moonshot"
        api_prompt="Enter your Moonshot API key"
        api_url="https://platform.moonshot.ai/"
        api_prefix="sk"
    fi
    
    # Get API key
    echo -e "\n${YELLOW}Step 3: API Key Setup${NC}"
    echo -e "${CYAN}Get your API key from: $api_url${NC}"
    read -p "$api_prompt: " api_key
    
    if [[ ! "$api_key" =~ ^$api_prefix ]]; then
        echo -e "${RED}Error: API key should start with '$api_prefix'${NC}"
        return 1
    fi
    
    set_api_key "$provider" "$api_key" silent
    
    # Create alias suggestion
    echo -e "\n${YELLOW}Step 4: Shell Integration${NC}"
    echo -e "Add this line to your ~/.zshrc for easy access:"
    echo -e "${BOLD}alias kimi='$SCRIPT_DIR/$(basename $0)'${NC}"
    
    echo -e "\n${GREEN}✅ Setup complete!${NC}"
    echo -e "Provider: ${BOLD}$provider${NC}"
    echo -e "Run ${BOLD}kimi${NC} to launch Claude Code with Kimi K2"
}

# Function to set API key
set_api_key() {
    local provider="$1"
    local key="$2"
    local silent="$3"
    
    if [ -z "$provider" ]; then
        echo -e "${RED}Error: Please specify provider (groq or moonshot)${NC}"
        echo -e "Usage: kimi set-key <provider> <key>"
        return 1
    fi
    
    if [ -z "$key" ]; then
        if [ "$provider" = "groq" ]; then
            read -p "Enter your Groq API key: " key
        else
            read -p "Enter your Moonshot API key: " key
        fi
    fi
    
    # Validate key prefix
    if [ "$provider" = "groq" ]; then
        if [[ ! "$key" =~ ^gsk ]]; then
            echo -e "${RED}Error: Groq API key should start with 'gsk'${NC}"
            return 1
        fi
        echo "$key" > "$GROQ_KEY_FILE"
        chmod 600 "$GROQ_KEY_FILE"
    else
        if [[ ! "$key" =~ ^sk- ]]; then
            echo -e "${RED}Error: Moonshot API key should start with 'sk-'${NC}"
            return 1
        fi
        echo "$key" > "$MOONSHOT_KEY_FILE"
        chmod 600 "$MOONSHOT_KEY_FILE"
    fi
    
    if [ "$silent" != "silent" ]; then
        echo -e "${GREEN}✓ $provider API key saved securely${NC}"
    fi
}

# Function to check configuration
check_config() {
    show_header
    echo -e "${BLUE}Configuration Status:${NC}"
    echo -e "─────────────────────────────────────"
    
    # Current provider
    local provider=$(get_current_provider)
    echo -e "${CYAN}Current Provider:${NC} ${BOLD}$provider${NC}"
    
    # Check Groq API key
    if [ -f "$GROQ_KEY_FILE" ]; then
        echo -e "${GREEN}✓ Groq API Key:${NC} Configured"
        GROQ_KEY=$(cat "$GROQ_KEY_FILE")
        echo -e "  ${CYAN}Key:${NC} gsk${GROQ_KEY:3:4}...${GROQ_KEY: -4} (masked)"
    else
        echo -e "${YELLOW}○ Groq API Key:${NC} Not configured"
    fi
    
    # Check Moonshot API key
    if [ -f "$MOONSHOT_KEY_FILE" ]; then
        echo -e "${GREEN}✓ Moonshot API Key:${NC} Configured"
        MOONSHOT_KEY=$(cat "$MOONSHOT_KEY_FILE")
        echo -e "  ${CYAN}Key:${NC} sk-${MOONSHOT_KEY:3:4}...${MOONSHOT_KEY: -4} (masked)"
    else
        echo -e "${YELLOW}○ Moonshot API Key:${NC} Not configured"
    fi
    
    # Check Claude Code
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
        if [ -n "$CLAUDE_CMD" ]; then
            echo -e "${GREEN}✓ Claude Code:${NC} $CLAUDE_CMD"
        fi
    else
        echo -e "${YELLOW}! Claude Code:${NC} Not configured (run 'kimi setup')"
    fi
    
    # Show endpoints
    echo -e "\n${BLUE}API Endpoints:${NC}"
    echo -e "  ${CYAN}Groq:${NC} https://api.groq.com/openai/v1"
    echo -e "  ${CYAN}Moonshot:${NC} https://api.moonshot.ai/anthropic"
    echo -e "\n${BLUE}Config Location:${NC} $CONFIG_DIR"
    echo -e "─────────────────────────────────────"
}

# Function to reset configuration
reset_config() {
    read -p "Are you sure you want to reset all Kimi settings? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        echo -e "${GREEN}✓ All settings have been reset${NC}"
    else
        echo -e "${YELLOW}Reset cancelled${NC}"
    fi
}

# Function to launch Claude Code with Kimi
launch_kimi() {
    local claude_args="$@"
    # Check if setup has been run
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${YELLOW}First time setup required!${NC}"
        setup_wizard
        return
    fi
    
    # Load configuration
    source "$CONFIG_FILE"
    
    # Get current provider
    local provider=$(get_current_provider)
    
    # Check if API key exists for current provider
    if ! check_api_key "$provider"; then
        echo -e "${RED}Error: No API key found for $provider!${NC}"
        echo -e "${YELLOW}Run: kimi set-key $provider YOUR_KEY${NC}"
        return 1
    fi
    
    # Set up environment based on provider
    if [ "$provider" = "groq" ]; then
        API_KEY=$(cat "$GROQ_KEY_FILE")
        NEEDS_PROXY=true
        PROXY_PORT=8090
        MODEL_NAME="moonshotai/kimi-k2-instruct"
        SPEED_INFO="~200 tokens/second"
    else
        API_KEY=$(cat "$MOONSHOT_KEY_FILE")
        NEEDS_PROXY=false
        API_URL="https://api.moonshot.ai/anthropic"
        MODEL_NAME="Kimi K2"
        SPEED_INFO="Standard speed"
    fi
    
    # Display launch info
    clear
    show_header
    echo -e "${GREEN}✓ Model:${NC} Kimi K2 (1 Trillion Parameters)"
    echo -e "${GREEN}✓ Provider:${NC} ${BOLD}$provider${NC} ($SPEED_INFO)"
    
    if [ "$NEEDS_PROXY" = true ]; then
        echo -e "${GREEN}✓ Proxy:${NC} Enabled (Anthropic ↔ OpenAI)"
        echo -e "${GREEN}✓ Endpoint:${NC} http://localhost:$PROXY_PORT"
    else
        echo -e "${GREEN}✓ Endpoint:${NC} $API_URL"
    fi
    
    echo -e "${GREEN}✓ Interface:${NC} Claude Code"
    
    if [ "$provider" = "groq" ]; then
        echo -e "${MAGENTA}✓ Speed Mode:${NC} ${BOLD}TURBO${NC} 🚀"
    fi
    
    # Start proxy if needed for Groq
    if [ "$NEEDS_PROXY" = true ]; then
        # Check if Python proxy exists
        PROXY_SCRIPT="$CONFIG_DIR/kimi_proxy.py"
        
        if [ ! -f "$PROXY_SCRIPT" ]; then
            echo -e "\n${YELLOW}Creating proxy script...${NC}"
            # Create the proxy script
            cat > "$PROXY_SCRIPT" << 'PROXY_EOF'
#!/usr/bin/env python3
"""
Kimi Proxy - Translates between Anthropic API (Claude Code) and OpenAI API (Groq)
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from urllib.parse import urlparse
import signal
import threading

# Configuration
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_BASE_URL = 'https://api.groq.com/openai/v1'
PROXY_PORT = int(os.environ.get('KIMI_PROXY_PORT', '8090'))
MODEL_NAME = 'moonshotai/kimi-k2-instruct'

class AnthropicToOpenAIProxy(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]
        print(f"DEBUG: Received GET request to: {self.path} -> {path}", file=sys.stderr)
        
        # Health check endpoint
        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "kimi-proxy"}).encode())
        else:
            print(f"DEBUG: GET path {path} not handled, sending 404", file=sys.stderr)
            self.send_error(404, f"GET path {path} not found")
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        print(f"DEBUG: Received OPTIONS request to: {self.path}", file=sys.stderr)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_HEAD(self):
        path = self.path.split('?')[0]
        print(f"DEBUG: Received HEAD request to: {self.path} -> {path}", file=sys.stderr)
        if path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
        else:
            self.send_error(404, f"HEAD path {path} not found")
    
    def do_POST(self):
        # Strip query parameters from path
        path = self.path.split('?')[0]
        print(f"DEBUG: Received POST request to: {self.path} -> {path}", file=sys.stderr)
        if path == '/v1/messages' or path == '/messages':
            self.handle_messages()
        else:
            print(f"DEBUG: POST path {path} not handled, sending 404", file=sys.stderr)
            self.send_error(404, f"POST path {path} not found")
    
    def handle_messages(self):
        try:
            # Read the request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            anthropic_request = json.loads(post_data)
            
            # Extract Anthropic format data
            messages = anthropic_request.get('messages', [])
            max_tokens = anthropic_request.get('max_tokens', 4096)
            temperature = anthropic_request.get('temperature', 0.7)
            stream = anthropic_request.get('stream', False)
            
            # Convert messages from Anthropic to OpenAI format
            openai_messages = []
            for msg in messages:
                role = msg['role']
                content = msg['content']
                
                # Handle different content types
                if isinstance(content, list):
                    # Anthropic sometimes uses content arrays
                    text_content = ' '.join([c['text'] for c in content if c['type'] == 'text'])
                    openai_messages.append({
                        'role': role,
                        'content': text_content
                    })
                else:
                    openai_messages.append({
                        'role': role,
                        'content': content
                    })
            
            # Make request to Groq
            openai_request = {
                'model': MODEL_NAME,
                'messages': openai_messages,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'stream': stream
            }
            
            headers = {
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f'{GROQ_BASE_URL}/chat/completions',
                headers=headers,
                json=openai_request,
                stream=stream
            )
            
            if response.status_code != 200:
                self.send_error(response.status_code, response.text)
                return
            
            # Convert response from OpenAI to Anthropic format
            if stream:
                # Handle streaming response
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str == '[DONE]':
                                self.wfile.write(b'data: {"type":"message_stop"}\n\n')
                                break
                            
                            try:
                                data = json.loads(data_str)
                                choice = data['choices'][0]
                                
                                if 'delta' in choice and 'content' in choice['delta']:
                                    anthropic_event = {
                                        'type': 'content_block_delta',
                                        'delta': {
                                            'type': 'text_delta',
                                            'text': choice['delta']['content']
                                        }
                                    }
                                    self.wfile.write(f'data: {json.dumps(anthropic_event)}\n\n'.encode())
                            except:
                                pass
                        self.wfile.flush()
            else:
                # Handle non-streaming response
                openai_response = response.json()
                
                # Convert to Anthropic format
                anthropic_response = {
                    'id': openai_response.get('id', 'msg_dummy'),
                    'type': 'message',
                    'role': 'assistant',
                    'content': [{
                        'type': 'text',
                        'text': openai_response['choices'][0]['message']['content']
                    }],
                    'model': MODEL_NAME,
                    'stop_reason': 'end_turn',
                    'stop_sequence': None,
                    'usage': {
                        'input_tokens': openai_response['usage']['prompt_tokens'],
                        'output_tokens': openai_response['usage']['completion_tokens']
                    }
                }
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(anthropic_response).encode())
                
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        # Always log to help with debugging 404 issues
        sys.stderr.write(f"[Proxy] {format % args}\n")
        sys.stderr.flush()
    
    def send_response(self, code, message=None):
        # Log all responses for debugging
        print(f"DEBUG: Sending {code} response for {self.command} {self.path}", file=sys.stderr)
        super().send_response(code, message)

def run_proxy():
    print(f"Starting Kimi proxy on port {PROXY_PORT}...", file=sys.stderr)
    
    # Create server with proper error handling
    try:
        server = HTTPServer(('localhost', PROXY_PORT), AnthropicToOpenAIProxy)
    except OSError as e:
        print(f"Error: Failed to bind to localhost:{PROXY_PORT} - {e}", file=sys.stderr)
        if "Address already in use" in str(e):
            print("Another service is using this port. Kill it first or use a different port.", file=sys.stderr)
        sys.exit(1)
    
    # Verify server is actually bound and ready
    try:
        import socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(1)
        result = test_socket.connect_ex(('localhost', PROXY_PORT))
        test_socket.close()
        if result == 0:
            print(f"Error: Port {PROXY_PORT} appears to be already in use", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Warning: Could not verify port availability - {e}", file=sys.stderr)
    
    # Handle shutdown gracefully
    def shutdown_handler(signum, frame):
        print("\nShutting down proxy...", file=sys.stderr)
        server.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    print(f"Proxy ready at http://localhost:{PROXY_PORT}", file=sys.stderr)
    print(f"Health check available at http://localhost:{PROXY_PORT}/health", file=sys.stderr)
    server.serve_forever()

if __name__ == '__main__':
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    run_proxy()
PROXY_EOF
            chmod +x "$PROXY_SCRIPT"
        fi
        
        # Start proxy in background
        echo -e "\n${CYAN}Starting translation proxy...${NC}"
        
        # Kill any existing proxy on the same port
        if lsof -ti:$PROXY_PORT >/dev/null 2>&1; then
            echo -e "${YELLOW}Killing existing proxy on port $PROXY_PORT...${NC}"
            lsof -ti:$PROXY_PORT | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
        
        export GROQ_API_KEY="$API_KEY"
        export KIMI_PROXY_PORT="$PROXY_PORT"
        
        # Check which Python to use
        if command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        elif [ -f "/opt/homebrew/bin/python3" ]; then
            PYTHON_CMD="/opt/homebrew/bin/python3"
        else
            echo -e "${RED}Error: Python 3 not found${NC}"
            echo -e "${YELLOW}Please install Python 3 first${NC}"
            return 1
        fi
        
        # Use stateful proxy that handles complete tool execution cycles
        STATEFUL_PROXY="$CONFIG_DIR/stateful_proxy.py"
        if [ -f "$STATEFUL_PROXY" ]; then
            $PYTHON_CMD "$STATEFUL_PROXY" &
            PROXY_PID=$!
        elif [ -f "$CONFIG_DIR/complete_proxy.py" ]; then
            $PYTHON_CMD "$CONFIG_DIR/complete_proxy.py" &
            PROXY_PID=$!
        else
            $PYTHON_CMD "$PROXY_SCRIPT" &
            PROXY_PID=$!
        fi
        
        # Wait for proxy to be ready with proper health checking
        echo -e "${YELLOW}Waiting for proxy to be ready...${NC}"
        PROXY_READY=false
        for i in {1..15}; do
            # First check if process is still alive
            if ! kill -0 $PROXY_PID 2>/dev/null; then
                echo -e "${RED}Error: Proxy process died during startup${NC}"
                echo -e "${YELLOW}Make sure 'requests' module is installed:${NC}"
                echo -e "${CYAN}python3 -m pip install --user requests${NC}"
                return 1
            fi
            
            # Then check if HTTP server is ready
            if curl -s -f -m 2 "http://localhost:$PROXY_PORT/health" >/dev/null 2>&1; then
                echo -e "${GREEN}✓ Proxy is ready and responding${NC}"
                PROXY_READY=true
                break
            elif [ $i -eq 15 ]; then
                echo -e "${RED}Error: Proxy failed to become ready after 15 seconds${NC}"
                echo -e "${YELLOW}Check if port $PROXY_PORT is available${NC}"
                kill $PROXY_PID 2>/dev/null || true
                return 1
            else
                echo -e "${YELLOW}  Attempt $i/15 - waiting for proxy to respond...${NC}"
                sleep 1
            fi
        done
        
        if [ "$PROXY_READY" != "true" ]; then
            echo -e "${RED}Error: Proxy did not become ready${NC}"
            kill $PROXY_PID 2>/dev/null || true
            return 1
        fi
        
        # Set API URL to proxy
        API_URL="http://localhost:$PROXY_PORT"
        
        # Function to cleanup proxy on exit
        cleanup_proxy() {
            if [ -n "$PROXY_PID" ] && kill -0 $PROXY_PID 2>/dev/null; then
                echo -e "\n${YELLOW}Stopping proxy...${NC}"
                kill $PROXY_PID
            fi
        }
        
        # Set trap to cleanup proxy
        trap cleanup_proxy EXIT INT TERM
    fi
    
    echo -e "\n${CYAN}Launching Claude Code...${NC}\n"
    
    # Export environment variables only for this session
    export ANTHROPIC_AUTH_TOKEN="$API_KEY"
    export ANTHROPIC_BASE_URL="$API_URL"
    
    # Debug: Show environment variables and test connectivity
    echo -e "${CYAN}Debug: Environment variables:${NC}"
    echo -e "  ANTHROPIC_AUTH_TOKEN: ${ANTHROPIC_AUTH_TOKEN:0:10}..."
    echo -e "  ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
    
    # Test proxy connectivity before launching Claude Code
    if [ "$NEEDS_PROXY" = true ]; then
        echo -e "${CYAN}Testing proxy connectivity...${NC}"
        if curl -s -f -m 3 "$ANTHROPIC_BASE_URL/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Proxy health check passed${NC}"
        else
            echo -e "${YELLOW}⚠ Proxy health check failed, but continuing...${NC}"
        fi
    fi
    
    # Launch Claude Code with arguments
    if [ -n "$claude_args" ]; then
        # Check if this is a --print command that will exit quickly
        if [[ "$claude_args" == *"--print"* ]] || [[ "$claude_args" == *"-p"* ]]; then
            # For --print mode, don't set trap to avoid premature proxy shutdown
            trap - EXIT
            eval "$CLAUDE_CMD $claude_args"
            # Give Claude Code time to make the API call before killing proxy
            sleep 2
            cleanup_proxy
        else
            eval "$CLAUDE_CMD $claude_args"
        fi
    else
        eval "$CLAUDE_CMD"
    fi
    
    # Cleanup proxy if it was started (only for non --print commands)
    if [ "$NEEDS_PROXY" = true ] && [[ "$claude_args" != *"--print"* ]] && [[ "$claude_args" != *"-p"* ]]; then
        cleanup_proxy
    fi
}

# Main script logic
case "${1:-launch}" in
    setup)
        setup_wizard
        ;;
    provider)
        if [ -z "$2" ]; then
            echo -e "${CYAN}Current provider:${NC} ${BOLD}$(get_current_provider)${NC}"
            echo -e "To change: kimi provider <groq|moonshot>"
        else
            set_provider "$2"
        fi
        ;;
    set-key)
        set_api_key "$2" "$3"
        ;;
    check)
        check_config
        ;;
    reset)
        reset_config
        ;;
    help|-h)
        usage
        ;;
    launch|"")
        launch_kimi
        ;;
    *)
        # If the first argument doesn't match known commands, treat it as a Claude Code argument
        # and pass all arguments to launch_kimi
        launch_kimi "$@"
        ;;
esac