# 🦞 Clawtographer

**Codebase cartographer skill for OpenClaw** - Maps and documents codebases using local LLM agents.

Built for small hardware. Runs 100% FREE using Ollama.

## What It Does

Clawtographer analyzes your codebase in parallel using local AI models and creates comprehensive architecture documentation:

- 📁 **Scans your entire project** (respects .gitignore)
- 🧩 **Splits work across parallel agents** for speed
- 🧠 **Synthesizes analyses** into coherent documentation
- 💾 **Caches progress** - resumable if interrupted
- 💰 **Completely FREE** - uses local Ollama models

## Installation

### Prerequisites

1. **Ollama** - Install from [ollama.ai](https://ollama.ai)
2. **A local model** - Run: `ollama pull glm-4.7-flash`
3. **Python 3.8+** with pip

### Install Clawtographer
```bash
# Clone the repo
git clone https://github.com/JGnft17/clawtographer.git
cd clawtographer

# Install dependencies
pip3 install -r requirements.txt --break-system-packages

# Make executable
chmod +x cartographer.py
```

### Install as OpenClaw Skill (Optional)
```bash
# Copy to OpenClaw skills directory
mkdir -p /mnt/skills/user/clawtographer
cp -r . /mnt/skills/user/clawtographer/
```

Now OpenClaw agents can use Clawtographer automatically!

## Usage

### Basic Usage
```bash
python3 cartographer.py /path/to/your/codebase
```

This creates `docs/CODEBASE_MAP.md` in your project.

### Advanced Usage
```bash
# Specify output directory
python3 cartographer.py /path/to/code output/

# From current directory
python3 cartographer.py .
```

### Configuration

Edit `config.json` to customize:
```json
{
  "max_tokens_per_chunk": 180000,
  "max_parallel_agents": 3,
  "ignore_patterns": [".git", "node_modules", "*.pyc"]
}
```

## Output Example

Clawtographer creates a comprehensive map like this:
```markdown
# Codebase Map

## Overview
This is a web application built with React and Express...

## Architecture
- Frontend: React components in /src/components
- Backend: Express API in /server
- Database: PostgreSQL with Sequelize ORM

## Key Components
- **UserAuth.js** - Handles authentication flow
- **Dashboard.js** - Main user interface
...
```

## How It Works

1. **Scans** your codebase and counts tokens
2. **Chunks** files into groups that fit in LLM context
3. **Analyzes** each chunk in parallel using Ollama
4. **Caches** results (resumable if interrupted)
5. **Synthesizes** all analyses into coherent documentation

## Model Support

Clawtographer auto-detects and uses the best available local model:

**Recommended models:**
- `glm-4.7-flash` (fast, smart)
- `qwen2.5-coder:14b` (code-focused)
- `llama3.1:8b` (general purpose)
- `mistral` (balanced)

**Install with:** `ollama pull <model-name>`

## Performance

**Small project** (50 files, ~50K tokens):
- Time: 2-5 minutes
- Cost: FREE

**Medium project** (500 files, ~500K tokens):
- Time: 10-20 minutes
- Cost: FREE

**Large project** (2000+ files, ~2M tokens):
- Time: 30-60 minutes
- Cost: FREE

## Features

✅ **100% Local** - No API costs, complete privacy  
✅ **Resumable** - Caches progress, pick up where you left off  
✅ **Smart Chunking** - Handles projects of any size  
✅ **Parallel Processing** - Uses multiple agents for speed  
✅ **Auto-synthesis** - Creates coherent documentation  
✅ **Gitignore Aware** - Skips unnecessary files  

## Troubleshooting

**"No Ollama models found"**
```bash
# Install a model
ollama pull glm-4.7-flash

# Verify it's running
ollama list
```

**"Analysis timed out"**
- Reduce `max_parallel_agents` in config.json
- Large files may take time - this is normal

**"All chunks failed"**
- Check Ollama is running: `ollama ps`
- Check model is available: `ollama list`
- Look in `.clawtographer_cache/` for error details

## OpenClaw Integration

When installed as an OpenClaw skill, agents like Smith can use it automatically:
```
User: Map this codebase
Smith: [runs Clawtographer]
Smith: I've created a comprehensive map in docs/CODEBASE_MAP.md
```

See [SKILL.md](SKILL.md) for details on OpenClaw integration.

## Contributing

Issues and PRs welcome! This is an open-source project for the OpenClaw community.

## License

MIT License - see [LICENSE](LICENSE)

## Credits

Inspired by [kingbootoshi/cartographer](https://github.com/kingbootoshi/cartographer) for Claude Code.

Built for OpenClaw users who want powerful codebase analysis on small hardware.

---

**Made with 🦞 for the OpenClaw community**
