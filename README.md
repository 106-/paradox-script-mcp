# Paradox Script MCP Server

[日本語版はこちら](README.ja.md)

Fast, token-efficient Paradox script exploration for AI assistants

## What is this?

Paradox game scripts are written in plain text, which means you can have coding bots like Claude Code read and explore them to automatically investigate things like event trigger conditions.

However, game script files tend to be quite large, so feeding them directly to a coding bot will quickly exhaust your context. (And as in many Paradox games, resource depletion means death.)

This MCP allows you to extract only symbols (like event IDs) from Paradox scripts, or load only the block indicated by a specific symbol.

It can be used from MCP-compatible clients such as Claude, Claude Code, gemini-cli (untested), and others.

## Example: Investigating an Achievement

Here's a real conversation example of using this MCP to investigate the HOI4 achievement "[No One Crosses the Finnish Line](https://hoi4.paradoxwikis.com/No_one_crosses_the_finnish_line)".

---

> \> Please investigate how to achieve "No One Crosses the Finnish Line".

> ● I'll initialize the game directory and search for the achievement in the achievements file.

```
init_game("/path/to/Hearts of Iron IV")
→ "Initialized: /path/to/Hearts of Iron IV"

list_symbols("common/achievements.txt")
→ block: no_one_crosses_the_finnish_line (id=185)
  block: finnish_him (id=114)
  ...
```

> ● Found the achievement `no_one_crosses_the_finnish_line`. Let me check its details.

```
get_structure("common/achievements.txt", "no_one_crosses_the_finnish_line")
→ no_one_crosses_the_finnish_line:
    possible: [block] (4 keys)
    id: 185
    happened: [block] (2 keys)
```

> ● I can see there are `possible` (unlock conditions) and `happened` (completion conditions) blocks. Let me investigate each.

```
get_structure("common/achievements.txt", "no_one_crosses_the_finnish_line", "possible")
→ no_one_crosses_the_finnish_line.possible:
    is_ironman: [True, difficulty, >, ...] (7 items)
    has_any_custom_difficulty_setting: no
    game_rules_allow_achievements: yes
    tag: "FIN"

get_structure("common/achievements.txt", "no_one_crosses_the_finnish_line", "happened")
→ no_one_crosses_the_finnish_line.happened:
    NOT: [block list] (2 items)
    tag: [FIN, date, >, ...] (4 items)
```

> ● Let me dig deeper into the NOT conditions and the tag block.

```
get_structure("common/achievements.txt", "no_one_crosses_the_finnish_line", "happened.NOT")
→ no_one_crosses_the_finnish_line.happened.NOT:
    [0]:
      has_global_flag: "achievement_fin_has_lost_one_starting_core"
    [1]:
      FIN:
        has_completed_focus:
          [0]: "FIN_right_wing_policies"
          [1]: "FIN_suomalainen_sosialismi"
      SOV:
        has_completed_focus: "SOV_beaten_but_not_defeated"

get_structure("common/achievements.txt", "no_one_crosses_the_finnish_line", "happened.tag")
→ no_one_crosses_the_finnish_line.happened.tag:
    [0]: "FIN"
    [1]: "date"
    [2]: ">"
    [3]: "1944.09.19"
```

> ● **Achievement "No One Crosses the Finnish Line" Requirements:**
>
>**Unlock Conditions:**
>- Play as **Finland (FIN)**
>- **Ironman mode** enabled
>- No custom difficulty settings
>- Achievement game rules enabled
>
>**Completion Conditions:**
> 1. **Never lose any starting core states** (global flag `achievement_fin_has_lost_one_starting_core` must not be set)
> 2. **Survive until after September 19, 1944** (this date refers to the historical Moscow Armistice ending the Continuation War)
> 3. **Do not complete the following focuses** (restricted routes):
>   - `FIN_right_wing_policies` (Right Wing Policies)
>   - `FIN_suomalainen_sosialismi` (Finnish Socialism)
>   - Soviet Union must not have completed `SOV_beaten_but_not_defeated` (Beaten But Not Defeated)

---

> \> How is `achievement_fin_has_lost_one_starting_core` set?

> ● Let me search for where this flag is set. It should be in an on_actions file.

```
list_symbols("common/on_actions/09_aat_on_actions.txt")
→ block: on_actions

get_structure("common/on_actions/09_aat_on_actions.txt", "on_actions")
→ on_actions:
    on_state_control_changed: [block] (1 keys)
    ...
```

> ● The `on_state_control_changed` hook looks relevant. Let me check its contents.

```
get_structure("common/on_actions/09_aat_on_actions.txt", "on_actions", "on_state_control_changed.effect")
→ on_actions.on_state_control_changed.effect:
    [0]:
      if:
        limit:
          is_in_array:
            array: "FIN.core_states_at_game_start"
            value: "FROM.FROM"
        set_global_flag: "achievement_fin_has_lost_one_starting_core"
```

> ● **How the Flag is Set:**
>
> The flag `achievement_fin_has_lost_one_starting_core` is set on `on_state_control_changed` (when state control changes) under the following condition:
>
>- **`FIN.core_states_at_game_start`** = List of Finland's core states at game start
>- **`FROM.FROM`** = The state whose control changed
>
>This means the flag is set **the moment any of Finland's starting core states falls under enemy control**.
>
>**Impact on Achievement:**
>
>Once any of Finland's starting core states (mainland or Karelia) is occupied by the enemy, the flag remains set even if recaptured, making **achievement completion impossible**.
>
>A perfect defense that loses no territory to the Soviet invasion is required.

## Installation

```bash
# Using uv (recommended)
uv pip install -e .

# Or pip
pip install -e .
```

### Dependencies

- Python >= 3.11
- [mcp](https://github.com/modelcontextprotocol/python-sdk) >= 1.0.0
- [paradox-script-parser](https://github.com/106-/paradox-script-parser) - A custom Paradox script parser

> **Note:** paradox-script-parser is a custom parser and does not support all Paradox script syntax. Some scripts may not be parsed correctly.

## Usage

### Start Server

```bash
# With hot reload (development)
make serve

# Or directly
uv run paradox-script-mcp
```

### Claude Code Configuration

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "paradox-script": {
      "type": "streamable-http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

## MCP Tools

### init_game

Initialize with game directory path. Must be called first.

```
init_game("/path/to/Hearts of Iron IV")
→ "Initialized: /path/to/Hearts of Iron IV"
```

### list_directories

List script directories and their purposes.

```
list_directories()
→ common/national_focus/ -> National focus trees
   common/decisions/ -> Decisions
   common/ideas/ -> National spirits, ministers, companies
   events/ -> Events
   ...
```

### list_symbols

List symbols in a file (top-level only).
Use `get_structure` to view child elements.

```
list_symbols("common/national_focus/japan.txt")
→ focus: JAP_the_unthinkable_option (x=12, y=0)
  focus: JAP_approach_the_young_officers (y=1)
  ...
  focus_tree: japan_wtt_focus
```

### get_structure

Show symbol structure (keys only, no full content).

```
get_structure("common/national_focus/japan.txt", "JAP_the_unthinkable_option")
→ JAP_the_unthinkable_option:
     id: "JAP_the_unthinkable_option"
     icon: "GFX_goal_generic_political_reform"
     prerequisite: [block] (1 keys)
     completion_reward: [block] (8 keys)
```

### get_structure (navigate nested blocks)

```
get_structure(
  "common/national_focus/japan.txt",
  "JAP_the_unthinkable_option",
  "completion_reward.hidden_effect"
)
→ JAP_the_unthinkable_option.completion_reward.hidden_effect:
     add_stability: 0.05
     add_political_power: 120
```

## Adding Support for Other Games

You can add support by placing YAML files with directory and file knowledge under `src/paradox_script_mcp/knowledge/`. Currently, only HoI4 knowledge is included.

## Project Structure

```
paradox-script-mcp/
├── pyproject.toml
└── src/paradox_script_mcp/
    ├── __init__.py
    ├── server.py              # MCP server entry point
    ├── core/
    │   └── game.py            # Game path management
    ├── knowledge/
    │   └── directory_map.py   # HOI4 directory knowledge
    └── tools/
        ├── explore.py         # list_directories
        ├── symbols.py         # list_symbols
        └── structure.py       # get_structure
```

## Development

```bash
# Install for development
uv pip install -e .

# Run with hot reload
make serve

# Run tests
make test
```
