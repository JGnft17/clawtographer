# Clawtographer Skill

**Description:** Maps and documents codebases of any size using parallel LLM agents. Creates comprehensive architecture documentation.

## When to Use This Skill

Use Clawtographer when:
- User asks to "map this codebase" or "document this project"
- User wants to understand a large/complex codebase
- Building something that requires understanding existing code structure
- User mentions needing architecture documentation
- Analyzing dependencies or data flows in a project

DO NOT use for:
- Single file analysis (just read the file directly)
- Projects under 10 files (too small, not worth overhead)
- When user just wants to read specific code (use regular file viewing)

## How It Works

1. Scans codebase directory and counts tokens per file
2. Splits files into chunks that fit in LLM context windows
3. Spawns parallel LLM agents - each analyzes a chunk
4. Synthesizes all analyses into comprehensive CODEBASE_MAP.md
5. Saves to `docs/CODEBASE_MAP.md` in the target directory

## Usage
```bash
python3 ~/clawtographer/cartographer.py <codebase_path> [output_dir] [max_parallel]
```

**Examples:**
```bash
# Map current directory
python3 ~/clawtographer/cartographer.py . docs 3

# Map specific project
python3 ~/clawtographer/cartographer.py /path/to/project

# Use more parallel agents (faster but more API calls)
python3 ~/clawtographer/cartographer.py /path/to/project docs 5
```

## Configuration

Edit `~/clawtographer/config.json` to set:
- Preferred LLM model (auto-detects what's available)
- Max tokens per chunk
- Parallel agent limit
- Output format preferences

## Model Selection Strategy

Clawtographer automatically uses the best available model:

**Priority order:**
1. Local models (free): GLM, Qwen, Llama, Mistral
2. Cloud models (if configured): Claude, OpenAI, Gemini

**Cost management:**
- Estimates cost BEFORE running (if using paid APIs)
- Asks for confirmation if cost > $1
- Defaults to local models when available

## Output

Creates `docs/CODEBASE_MAP.md` containing:
- Overview and architecture summary
- Directory structure with descriptions
- Key components and responsibilities
- Data flows and dependencies
- Navigation guide for finding functionality

## Error Handling

- Respects .gitignore patterns
- Skips binary files automatically
- Handles encoding errors gracefully
- Saves progress (can resume if interrupted)
- Rate limiting for API calls

## Best Practices

- Run on clean codebases (no build artifacts)
- Use .gitignore to exclude unnecessary files
- Start with 3 parallel agents, increase if needed
- Review output and refine with follow-up questions
- Update map when codebase changes significantly

## Cost Estimation Examples

**Small project (50 files, 50K tokens):**
- Local models: FREE
- Claude Haiku: ~$0.04
- Claude Sonnet: ~$0.15

**Medium project (500 files, 500K tokens):**
- Local models: FREE
- Claude Haiku: ~$0.40
- Claude Sonnet: ~$1.50

**Large project (2000 files, 2M tokens):**
- Local models: FREE
- Claude Haiku: ~$1.60
- Claude Sonnet: ~$6.00

## Troubleshooting

**"Unknown model" error:**
- Check that Ollama is running: `ollama list`
- Or configure Claude API key in OpenClaw settings

**"Out of memory" error:**
- Reduce max_tokens_per_chunk in config.json
- Reduce max_parallel agents

**Incomplete output:**
- Check ~/clawtographer/.progress for last successful chunk
- Re-run - it will resume from last checkpoint

## Integration with OpenClaw

This skill works seamlessly with OpenClaw's model routing:
- Respects your AGENTS.md model preferences
- Uses cost optimization strategies
- Follows your autonomy boundaries
- Reports completion in your preferred format
