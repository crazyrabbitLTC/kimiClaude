# Kimi K2 for Claude Code

🚀 **Use Claude Code with Kimi K2 (1 Trillion Parameter Model) via Groq API**

Get blazing-fast AI development with **~200 tokens/second** response times while keeping all your favorite Claude Code features and tools.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/macOS-Compatible-brightgreen.svg)](https://www.apple.com/macos/)
[![Shell](https://img.shields.io/badge/Shell-Bash-blue.svg)](https://www.gnu.org/software/bash/)

## ✨ Features

- 🔥 **Blazing Fast**: ~200 tokens/second via Groq API (5x faster than standard APIs)
- 🛠️ **Full Tool Support**: All 15+ Claude Code tools work perfectly (LS, Read, Write, Bash, etc.)
- 🔄 **Automatic Translation**: Seamless Anthropic ↔ OpenAI API format conversion
- 🎯 **Easy Setup**: Interactive setup wizard with guided configuration
- 🌙 **Dual Provider**: Support for both Groq (fast) and Moonshot (official)
- 💰 **Cost Effective**: Lower costs with Groq pricing ($1 input, $3 output per 1M tokens)
- 🔒 **Local Tool Execution**: All tools execute locally for security and performance

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-username/kimi-code.git
cd kimi-code
chmod +x kimi.sh
```

### 2. Run Setup Wizard

```bash
./kimi.sh setup
```

The wizard will guide you through:
- Detecting your Claude Code installation
- Choosing between Groq (fast) or Moonshot (official)
- Setting up your API keys
- Creating shell aliases

### 3. Get API Keys

**For Groq (Recommended - 5x faster):**
- Visit [Groq Console](https://console.groq.com/keys)
- Create an API key starting with `gsk_`

**For Moonshot (Official):**
- Visit [Moonshot Platform](https://platform.moonshot.ai/)
- Create an API key starting with `sk-`

### 4. Start Using

```bash
# Launch interactive Claude Code with Kimi K2
./kimi.sh

# Quick one-off commands
./kimi.sh --print "List files in current directory"

# Show help
./kimi.sh --help
```

## 📖 Usage Examples

### Interactive Development
```bash
# Start interactive session
./kimi.sh

# Claude Code will now use Kimi K2 with all tools available
> List the files in this directory and analyze the code structure
> Create a new React component for user authentication
> Run the tests and fix any issues found
```

### Command Line Usage
```bash
# Quick queries
./kimi.sh --print "What is 2+2?"

# File analysis
./kimi.sh --print "Analyze the code in src/app.js"

# Code generation
./kimi.sh --print "Create a Python function to validate email addresses"
```

### Provider Switching
```bash
# Switch to Groq (fast)
./kimi.sh provider groq

# Switch to Moonshot (official)
./kimi.sh provider moonshot

# Check current configuration
./kimi.sh check
```

## ⚙️ Configuration

### Environment Variables

The tool uses Claude Code-compatible environment variables:

```bash
# These are set automatically by kimi.sh for Claude Code compatibility
ANTHROPIC_AUTH_TOKEN    # Actually contains Groq/Moonshot API key
ANTHROPIC_BASE_URL      # Actually points to our Kimi proxy
```

### Configuration Files

```
~/.config/kimi-claude/
├── groq_api_key           # Your Groq API key
├── moonshot_api_key       # Your Moonshot API key  
├── provider               # Current provider (groq/moonshot)
├── config                 # Claude Code command configuration
└── *.py                   # Proxy scripts (auto-generated)
```

### Commands

```bash
# Configuration management
./kimi.sh setup                    # Run setup wizard
./kimi.sh provider <groq|moonshot> # Switch providers
./kimi.sh set-key <provider> <key> # Set API keys
./kimi.sh check                    # Check configuration
./kimi.sh reset                    # Reset all settings

# Usage
./kimi.sh [claude-args...]         # Launch with arguments
./kimi.sh                          # Launch interactive session
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude Code   │    │   Kimi Proxy     │    │   Groq API      │
│                 │───▶│                  │───▶│                 │
│ Anthropic API   │    │ Format Translator│    │ Kimi K2 Model   │
│ Format          │◀───│ + Tool Executor  │◀───│ OpenAI Format   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### How It Works

1. **Claude Code** sends requests in Anthropic API format
2. **Kimi Proxy** translates requests to OpenAI format
3. **Groq API** processes requests with Kimi K2 model
4. **Local Tool Execution** handles file operations, bash commands, etc.
5. **Response Translation** converts back to Anthropic format
6. **Claude Code** receives perfectly formatted responses

## 🔒 Security Features

### Built-in Security Protections

- **🛡️ Path Traversal Protection**: All file operations are restricted to the working directory
- **🚫 Command Injection Prevention**: Dangerous commands are blocked and arguments are safely parsed
- **🔐 Safe Logging**: API keys and sensitive data are automatically masked in logs
- **⚡ Input Validation**: All user inputs are validated and sanitized
- **🏠 Working Directory Isolation**: Tools cannot access files outside the project directory

### Security Best Practices

```bash
# Always run from your intended working directory
cd /path/to/your/project
./kimi.sh

# Keep API keys secure
chmod 600 ~/.config/kimi-claude/*api_key

# Regular security updates
git pull origin main  # Get latest security fixes
```

## 🔧 Troubleshooting

### Common Issues

**❌ Command not found: claude**
```bash
# Install Claude Code first
# Option 1: Download from https://claude.ai/download
# Option 2: Use Homebrew (if available)
brew install claude-code
```

**❌ API Error (Request timed out)**
- Check your internet connection
- Verify API key is correct
- Try switching providers: `./kimi.sh provider groq`

**❌ Tools not working**
```bash
# Check working directory
pwd

# Verify proxy is running
curl -s http://localhost:8090/health

# Restart with fresh proxy
./kimi.sh
```

**❌ Port already in use**
```bash
# Kill existing proxy
lsof -ti:8090 | xargs kill -9

# Or use different port
export KIMI_PROXY_PORT=8091
./kimi.sh
```

### Debug Mode

```bash
# Check debug logs
tail -f /tmp/kimi_streaming_debug.log

# Verbose proxy output
KIMI_DEBUG=1 ./kimi.sh
```

## 🏎️ Performance Comparison

| Provider | Speed (tok/s) | Context | Cost (per 1M tok) | Best For |
|----------|---------------|---------|-------------------|----------|
| **Groq** | ~200 | 131K | $1 in, $3 out | Speed, Development |
| Moonshot | ~50 | 200K | Standard | Production, Long Context |
| Anthropic | ~40 | 200K | Higher | Official Support |

## 🧪 Testing

### Test Basic Functionality
```bash
# Test non-tool request
./kimi.sh --print "Hello, how are you?"

# Test tool calling
./kimi.sh --print "List files in current directory using the LS tool"

# Test proxy health
curl -s http://localhost:8090/health
```

### Test All Tools
```bash
# The proxy supports these Claude Code tools:
# LS, Read, Write, Edit, MultiEdit, Bash, Glob, Grep, 
# WebFetch, WebSearch, TodoWrite, Task, ExitPlanMode
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly with both providers
5. Submit a pull request

### Development Setup
```bash
# Clone for development
git clone https://github.com/your-username/kimi-code.git
cd kimi-code

# Test setup
./kimi.sh setup
./kimi.sh check

# Make changes to kimi.sh or proxy scripts
# Test with: ./kimi.sh --print "test message"
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Moonshot AI](https://moonshot.ai/) for the incredible Kimi K2 model
- [Groq](https://groq.com/) for lightning-fast inference infrastructure  
- [Anthropic](https://anthropic.com/) for Claude Code and the excellent developer experience
- The open-source community for tools and inspiration

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/kimi-code/issues)
- 💬 **Discussions**: Use GitHub Discussions for questions
- 📖 **Docs**: This README covers most use cases

---

**Made with ❤️ for the AI development community**

*Get blazing-fast AI development while keeping all your favorite Claude Code features!*