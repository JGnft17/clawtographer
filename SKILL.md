---
name: clawtographer
description: "Codebase cartographer - maps and documents codebases using parallel local LLM agents"
---

# Clawtographer Skill

## Overview
Clawtographer is a codebase mapping tool that generates comprehensive architecture documentation using parallel local LLM agents. It analyzes code structure, dependencies, and logic to create navigable codebase maps.

## When to Use Clawtographer

Use Clawtographer whenever:
- User asks to "map this codebase" or "document this project"
- Understanding large/complex codebases
- Building something requiring existing code structure knowledge
- Architecture documentation needs
- Analyzing dependencies/data flows

**Common triggers:**
- "Map this codebase"
- "Document this project's architecture"
- "Help me understand how this code works"
- "Create a codebase overview"

**DO NOT use for:**
- Single file analysis
- Projects under 10 files
- Specific code reading (use regular file viewing)

## What Clawtographer Does

1. **Scans** codebase, counts tokens per file
2. **Splits** files into chunks fitting LLM context windows
3. **Spawns** parallel LLM agents analyzing chunks
4. **Synthesizes** analyses into comprehensive CODEBASE_MAP.md
5. **Saves** to `docs/CODEBASE_MAP.md`

## How to Use Clawtographer

### Basic Usage
```bash
python3 ~/clawtographer/cartographer.py /path/to/codebase
```

This creates `docs/CODEBASE_MAP.md` in the target directory.

### Advanced Usage
```bash
# Map current directory
python3 ~/clawtographer/cartographer.py . docs 3

# Map specific project
python3 ~/clawtographer/cartographer.py /path/to/project

# More parallel agents (faster, more compute)
python3 ~/clawtographer/cartographer.py /path/to/project docs 5
```

### Configuration

Edit `~/clawtographer/config.json`:
```json
{
  "max_tokens_per_chunk": 180000,
  "max_parallel_agents": 3,
  "ignore_patterns": [".git", "node_modules", "*.pyc"]
}
```

## Model Selection Strategy

**Priority order:**
1. Local models (free): GLM, Qwen, Llama, Mistral
2. Auto-detects available models
3. Uses best available for code analysis

**Cost:** Always FREE - uses local Ollama models only.

## Output Format

Creates `docs/CODEBASE_MAP.md` containing:
- Overview and architecture summary
- Directory structure with descriptions
- Key components and responsibilities
- Data flows and dependencies
- Navigation guide for finding functionality

## Integration with OpenClaw Workflow

**Typical workflow:**
1. User uploads codebase or references project path
2. Agent runs Clawtographer to generate map
3. Agent reads CODEBASE_MAP.md
4. Agent can now navigate and work with the codebase intelligently

**Example:**
```
User: Help me add a feature to this project
Agent: [runs Clawtographer first]
Agent: [reads CODEBASE_MAP.md to understand architecture]
Agent: [makes informed changes in the right places]
```

## Error Handling

- Respects .gitignore patterns
- Skips binary files automatically
- Handles encoding errors gracefully
- Saves progress (resume if interrupted)
- Rate limiting for API calls

## Performance Estimates

**Small project (50 files, 50K tokens):**
- Time: 2-5 minutes
- Cost: FREE

**Medium project (500 files, 500K tokens):**
- Time: 10-20 minutes
- Cost: FREE

**Large project (2000+ files, 2M tokens):**
- Time: 30-60 minutes
- Cost: FREE

## Best Practices

### When to Map a Codebase
- Before making changes to unfamiliar code
- When onboarding to a new project
- Before architectural decisions
- When documenting existing systems

### How to Use the Map
- Read the overview first for context
- Use directory structure to navigate
- Reference component descriptions when editing
- Update map after major changes

### When NOT to Use
- For single-file analysis
- Very small projects (< 10 files)
- When you just need to read one specific file

## Troubleshooting

**"No Ollama models found"**
- Install Ollama: `brew install ollama`
- Pull a model: `ollama pull glm-4.7-flash`

**"Analysis timed out"**
- Reduce `max_parallel_agents` in config
- Large files take time - this is normal

**"All chunks failed"**
- Check Ollama is running: `ollama ps`
- Check model availability: `ollama list`
- Look in `.clawtographer_cache/` for errors

## Philosophy

Clawtographer embodies the "small hardware doing big things" philosophy:
- **Free:** No API costs, runs locally
- **Resumable:** Caches progress, recovers from interrupts
- **Efficient:** Parallel processing maximizes throughput
- **Smart:** Synthesizes coherent documentation

Understanding code shouldn't require expensive cloud APIs.

---

**Made with 🦞 for the OpenClaw community**
