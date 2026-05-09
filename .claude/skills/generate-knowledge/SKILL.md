---
name: generate-knowledge
description: Generate knowledge YAML for a Paradox game directory. Use this skill when the user wants to create or regenerate `src/paradox_script_mcp/knowledge/{game_type}/directories.yml`, gives a game directory path and asks to scan or analyze it, or wants to add support for a new Paradox game (EU4, CK3, Stellaris, etc.).
---

# generate-knowledge

Explore a Paradox game directory and generate `knowledge/{game_type}/directories.yml` automatically.

## Usage

```
/generate-knowledge <game_type> <game_path>
```

Examples:
```
/generate-knowledge hoi4 /path/to/Hearts of Iron IV
/generate-knowledge eu4 "/path/to/Europa Universalis IV"
```

## Steps

### 1. Parse arguments

Read `game_type` (e.g. `hoi4`) and `game_path` (absolute path to the game directory) from the user's message. If either is missing, ask for it before proceeding.

### 2. Enumerate directories

List the top-level entries of `game_path`. Then, if a `common/` subdirectory exists, also list its immediate children. Collect all unique directory paths relative to `game_path`.

### 3. Sample each directory

For each candidate directory, check whether it contains `.txt` files (look at direct children only — no need to recurse).

**Skip the directory entirely** if any of these apply:
- No `.txt` files exist in it
- The directory name strongly suggests non-script content: `gfx`, `interface`, `music`, `fonts`, `sound`, `icons`, `portraits`, `flags`, `map`, `pdx_browser`

For directories that pass the check:
- List up to 5 `.txt` file names
- Read the first ~20 lines of one file to get a sense of the top-level block types and IDs

From the file names and top-level block structure, write a concise English description of the directory's purpose (one line, no trailing period).

### 4. Write the YAML

Output path: `src/paradox_script_mcp/knowledge/{game_type}/directories.yml` relative to this repository root (not inside the game directory).

**Never include the absolute game path anywhere in the YAML.**

Use this template:

```yaml
# {game_type} Directory Knowledge
# Auto-generated — review and correct descriptions as needed.

directories:
  some/path:
    description: Brief purpose in English

  another/path:
    description: Brief purpose in English
```

- Use forward slashes for paths
- Sort entries alphabetically
- If an existing file is present, confirm with the user before overwriting

### 5. Report

Tell the user:
- How many directories were added
- How many were skipped (non-text) and why (one-line summary)
- Which entries you're least confident about so the user knows where to double-check
