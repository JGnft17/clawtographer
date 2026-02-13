#!/usr/bin/env python3
"""
Clawtographer - Codebase Cartographer for OpenClaw
Maps codebases using LOCAL LLM agents (Ollama)
Designed for small hardware - efficient, resumable, free.
"""

import os
import json
import sys
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

try:
    import tiktoken
except ImportError:
    print("ERROR: tiktoken not installed. Run: pip3 install tiktoken --break-system-packages")
    sys.exit(1)


class Clawtographer:
    def __init__(self, codebase_path, output_dir="docs", config_path=None):
        self.codebase_path = Path(codebase_path).resolve()
        self.output_dir = Path(output_dir)
        self.script_dir = Path(__file__).parent
        self.cache_dir = self.script_dir / ".clawtographer_cache"
        
        # Validate paths
        if not self.codebase_path.exists():
            print(f"ERROR: Codebase path does not exist: {self.codebase_path}")
            sys.exit(1)
        
        if not self.codebase_path.is_dir():
            print(f"ERROR: Codebase path is not a directory: {self.codebase_path}")
            sys.exit(1)
        
        # Load config with validation
        if config_path is None:
            config_path = self.script_dir / "config.json"
        
        try:
            with open(config_path) as f:
                config = json.load(f)
            
            # Validate required keys and set defaults
            self.config = {
                "max_tokens_per_chunk": config.get("max_tokens_per_chunk", 180000),
                "max_parallel_agents": config.get("max_parallel_agents", 3),
                "ignore_patterns": config.get("ignore_patterns", [
                    ".git", "__pycache__", "node_modules", "*.pyc"
                ])
            }
            
        except Exception as e:
            print(f"ERROR: Failed to load config: {e}")
            sys.exit(1)
        
        # Initialize tokenizer
        self.encoder = tiktoken.get_encoding("cl100k_base")
        
        # Check Ollama
        self.model = self._check_ollama()
        if not self.model:
            print("ERROR: No Ollama models found. Install with: ollama pull glm-4.7-flash")
            sys.exit(1)
        
        print(f"[INFO] Using model: {self.model}")
        
        # Create directories
        try:
            self.output_dir.mkdir(exist_ok=True, parents=True)
            self.cache_dir.mkdir(exist_ok=True, parents=True)
        except Exception as e:
            print(f"ERROR: Cannot create output directories: {e}")
            sys.exit(1)
    
    def _check_ollama(self):
        """Check for Ollama and select best local model"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            # Parse available models
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            if not lines:
                return None
            
            # Priority order for local models
            priority = ["glm-4.7-flash", "qwen2.5-coder", "llama3.1", "mistral"]
            
            for preferred in priority:
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        if preferred in model_name.lower():
                            return model_name
            
            # Use first available model
            return lines[0].split()[0]
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
    
    def count_tokens(self, text):
        """Count tokens in text"""
        return len(self.encoder.encode(text))
    
    def should_ignore(self, path):
        """Check if path should be ignored"""
        path_str = str(path)
        for pattern in self.config["ignore_patterns"]:
            if pattern in path_str:
                return True
        return False
    
    def scan_codebase(self):
        """Scan codebase and return file list with token counts"""
        print(f"[INFO] Scanning {self.codebase_path}...")
        
        files = []
        total_tokens = 0
        skipped = 0
        
        for file_path in self.codebase_path.rglob('*'):
            if not file_path.is_file() or self.should_ignore(file_path):
                skipped += 1
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                tokens = self.count_tokens(content)
                
                files.append({
                    'path': str(file_path.relative_to(self.codebase_path)),
                    'full_path': str(file_path),
                    'tokens': tokens,
                    'content': content
                })
                
                total_tokens += tokens
                
            except Exception as e:
                print(f"[WARN] Skipped {file_path}: {e}")
                skipped += 1
        
        print(f"[INFO] Found {len(files)} files ({total_tokens:,} tokens), skipped {skipped}")
        return files, total_tokens
    
    def create_chunks(self, files):
        """Split files into chunks that fit in context window"""
        max_tokens = self.config["max_tokens_per_chunk"]
        print(f"[INFO] Creating chunks (max {max_tokens:,} tokens each)...")
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        # Sort by size for better packing
        files.sort(key=lambda x: x['tokens'], reverse=True)
        
        for file_info in files:
            if file_info['tokens'] > max_tokens:
                chunks.append([file_info])
                print(f"[WARN] Large file in own chunk: {file_info['path']}")
                continue
            
            if current_tokens + file_info['tokens'] > max_tokens:
                chunks.append(current_chunk)
                current_chunk = [file_info]
                current_tokens = file_info['tokens']
            else:
                current_chunk.append(file_info)
                current_tokens += file_info['tokens']
        
        if current_chunk:
            chunks.append(current_chunk)
        
        print(f"[INFO] Created {len(chunks)} chunks")
        return chunks
    
    def analyze_chunk(self, chunk_id, chunk):
        """Analyze chunk using Ollama - with caching"""
        cache_file = self.cache_dir / f"chunk_{chunk_id:03d}.md"
        
        # Check cache
        if cache_file.exists():
            print(f"[INFO] Using cached analysis for chunk {chunk_id + 1}")
            return chunk_id, cache_file.read_text(), True  # True = from cache
        
        # Build prompt
        file_list = "\n".join([f"- {f['path']}" for f in chunk])
        files_content = "\n\n".join([
            f"=== {f['path']} ===\n{f['content']}"
            for f in chunk
        ])
        
        prompt = f"""Analyze these code files:

{file_list}

For each file, describe:
1. Purpose and main responsibility
2. Key functions, classes, or exports
3. Dependencies (what it imports/requires)
4. Important patterns or logic

Files:
{files_content}

Provide clear, concise analysis in markdown format."""
        
        try:
            print(f"[INFO] Analyzing chunk {chunk_id + 1} ({len(chunk)} files)...")
            
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                analysis = result.stdout.strip()
                
                # Validate output is not empty
                if not analysis:
                    error = "ERROR: Ollama returned empty response"
                    print(f"[ERROR] {error}")
                    return chunk_id, error, False
                
                # Cache the result
                cache_file.write_text(analysis)
                return chunk_id, analysis, False  # False = newly analyzed
            else:
                error = f"ERROR: Ollama failed - {result.stderr}"
                print(f"[ERROR] {error}")
                return chunk_id, error, False
                
        except subprocess.TimeoutExpired:
            error = "ERROR: Analysis timed out (>5 min)"
            print(f"[ERROR] {error}")
            return chunk_id, error, False
        except Exception as e:
            error = f"ERROR: {e}"
            print(f"[ERROR] {error}")
            return chunk_id, error, False
    
    def analyze_chunks(self, chunks):
        """Analyze all chunks in parallel"""
        max_parallel = self.config["max_parallel_agents"]
        print(f"[INFO] Analyzing {len(chunks)} chunks ({max_parallel} parallel)...")
        
        analyses = []
        
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            futures = {
                executor.submit(self.analyze_chunk, i, chunk): i
                for i, chunk in enumerate(chunks)
            }
            
            for future in as_completed(futures):
                chunk_id, analysis, from_cache = future.result()
                analyses.append((chunk_id, analysis, from_cache))
                print(f"[PROGRESS] Completed {len(analyses)}/{len(chunks)}")
        
        return analyses
    
    def synthesize_map(self, analyses):
        """Use Ollama to synthesize final coherent map - with smart truncation"""
        print("[INFO] Synthesizing final map...")
        
        # Sort by chunk ID
        analyses.sort(key=lambda x: x[0])
        
        # Create summaries of each chunk for synthesis (avoid context overflow)
        chunk_summaries = []
        for cid, analysis, _ in analyses:
            # Take first 2000 chars of each analysis as summary
            summary = analysis[:2000]
            if len(analysis) > 2000:
                summary += "\n... (truncated)"
            chunk_summaries.append(f"## Chunk {cid + 1}\n{summary}")
        
        combined_summaries = "\n\n".join(chunk_summaries)
        
        # Check if combined summaries fit in reasonable context
        summary_tokens = self.count_tokens(combined_summaries)
        
        if summary_tokens > 100000:
            # Too large even with summaries - skip synthesis
            print(f"[WARN] Codebase too large for synthesis ({summary_tokens:,} tokens)")
            print("[INFO] Saving concatenated analyses without synthesis")
            
            # Just concatenate full analyses
            combined_full = "\n\n---\n\n".join([
                f"## Analysis Block {cid + 1}\n\n{analysis}"
                for cid, analysis, _ in analyses
            ])
            
            return self._create_final_map(combined_full, synthesized=False)
        
        # Synthesis prompt using summaries
        synthesis_prompt = f"""You are creating a comprehensive CODEBASE MAP from multiple code analyses.

Here are summaries from different parts of the codebase:

{combined_summaries}

Create a well-organized codebase map with:

1. **Overview** - What this codebase does (high-level purpose)
2. **Architecture** - Main components and how they relate
3. **Directory Structure** - Key directories and their purposes
4. **Important Files** - Critical files and what they do
5. **Data Flow** - How information moves through the system
6. **Entry Points** - Where execution begins
7. **Dependencies** - External libraries and internal dependencies

Make it clear, organized, and useful for someone learning this codebase.
Use markdown formatting with headers and lists."""
        
        try:
            print("[INFO] Running synthesis (this may take 1-3 minutes)...")
            
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=synthesis_prompt,
                capture_output=True,
                text=True,
                timeout=240  # Increased timeout
            )
            
            if result.returncode == 0:
                synthesized = result.stdout
                return self._create_final_map(synthesized, synthesized=True)
            else:
                print("[WARN] Synthesis failed, using combined analyses")
                combined_full = "\n\n---\n\n".join([
                    f"## Analysis Block {cid + 1}\n\n{analysis}"
                    for cid, analysis, _ in analyses
                ])
                return self._create_final_map(combined_full, synthesized=False)
                
        except subprocess.TimeoutExpired:
            print("[WARN] Synthesis timed out, using combined analyses")
            combined_full = "\n\n---\n\n".join([
                f"## Analysis Block {cid + 1}\n\n{analysis}"
                for cid, analysis, _ in analyses
            ])
            return self._create_final_map(combined_full, synthesized=False)
        except Exception as e:
            print(f"[WARN] Synthesis error: {e}, using combined analyses")
            combined_full = "\n\n---\n\n".join([
                f"## Analysis Block {cid + 1}\n\n{analysis}"
                for cid, analysis, _ in analyses
            ])
            return self._create_final_map(combined_full, synthesized=False)
    
    def _create_final_map(self, content, synthesized=False):
        """Create final map with metadata"""
        synthesis_note = "synthesized" if synthesized else "concatenated (too large for synthesis)"
        
        final_map = f"""# Codebase Map

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Tool:** Clawtographer (OpenClaw)
**Model:** {self.model} (local/free)
**Location:** {self.codebase_path}
**Analysis:** {synthesis_note}

---

{content}

---

*This map was automatically generated by Clawtographer using local LLM analysis.  
To update: re-run `python3 ~/clawtographer/cartographer.py {self.codebase_path}`*
"""
        
        return final_map
    
    def run(self):
        """Run the full cartographer pipeline"""
        print("[INFO] Clawtographer starting...")
        print(f"[INFO] Codebase: {self.codebase_path}")
        print(f"[INFO] Output: {self.output_dir}")
        print(f"[INFO] Cache: {self.cache_dir}")
        
        # Scan
        files, total_tokens = self.scan_codebase()
        if not files:
            print("[ERROR] No files found to analyze")
            return None
        
        # Create chunks
        chunks = self.create_chunks(files)
        
        # Analyze (with caching and resumability)
        analyses = self.analyze_chunks(chunks)
        
        # Check for errors and track successful chunks
        errors = []
        successful_chunks = []
        
        for chunk_id, analysis, from_cache in analyses:
            if analysis.startswith("ERROR:"):
                errors.append(chunk_id)
            else:
                successful_chunks.append(chunk_id)
        
        if errors:
            print(f"[WARN] {len(errors)} chunks had errors (cached for retry)")
        
        # Check if we have ANY successful analyses
        if not successful_chunks:
            print("[ERROR] All chunks failed - cannot create map")
            print("[INFO] Check cache directory for error details")
            return None
        
        # Synthesize into coherent map
        final_map = self.synthesize_map(analyses)
        
        # Save
        output_path = self.output_dir / "CODEBASE_MAP.md"
        output_path.write_text(final_map)
        print(f"[INFO] Map saved to: {output_path}")
        
        # Save timestamp
        (self.output_dir / ".clawtographer_timestamp").write_text(
            datetime.now().isoformat()
        )
        
        # Clean cache for SUCCESSFUL chunks only
        if successful_chunks:
            print(f"[INFO] Cleaning cache for {len(successful_chunks)} successful chunks...")
            for chunk_id in successful_chunks:
                cache_file = self.cache_dir / f"chunk_{chunk_id:03d}.md"
                if cache_file.exists():
                    cache_file.unlink()
        
        if errors:
            print(f"[INFO] Kept cache for {len(errors)} failed chunks - fix and re-run to retry")
        
        print("[INFO] Clawtographer complete!")
        return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 cartographer.py <codebase_path> [output_dir]")
        print("Example: python3 cartographer.py /path/to/code docs")
        print("")
        print("Clawtographer uses LOCAL Ollama models (free).")
        print("Make sure Ollama is running: ollama list")
        sys.exit(1)
    
    codebase = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "docs"
    
    carto = Clawtographer(codebase, output)
    carto.run()
