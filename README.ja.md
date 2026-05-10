# Paradox Script MCP Server

トークン効率の良いAIアシスタント向けParadoxスクリプトの探索ツール

## これはなに？

Paradoxのゲームスクリプトはプレインテキストで書かれており、ClaudeCodeなどのコーディングボットなどに読み込ませ探索させることでイベントの発生条件などを自動で調べさせることができます。

しかしながら、ゲームスクリプトは一つ一つのファイルサイズが長めなのでそのままコーディングボットに入れてしまうとコンテキスト量があっというまに爆発してしまいます。(そして多くのParadoxゲームのようにリソース不足は死を意味します)

そこでこのMCPでは、Paradoxのスクリプトからシンボル(イベントIDとか)のみを抽出したり、そのシンボルが示すブロックのみで読み込むことができます。

これはClaude、ClaudeCode、gemini-cli(試してないです)などのMCPを使用できるクライアントから使用することができます。

## 使用例: 実績の調査

<details>
<summary>HOI4実績「No One Crosses the Finnish Line」の調査例</summary>

このMCPを使用してHOI4の実績「[No One Crosses the Finnish Line](https://hoi4.paradoxwikis.com/No_one_crosses_the_finnish_line)」を調査する実際の会話例です。

---

> \>「No One Crosses the Finnish Line」の達成方法を調べてください。

> ● ゲームディレクトリを初期化し、実績ファイルから該当する実績を探します。

```
init_game("/path/to/Hearts of Iron IV")
→ "Initialized: /path/to/Hearts of Iron IV"

list_symbols("common/achievements.txt")
→ block: no_one_crosses_the_finnish_line (id=185)
  block: finnish_him (id=114)
  ...
```

> ● 実績 `no_one_crosses_the_finnish_line` を見つけました。詳細を確認します。

```
get_structure("common/achievements.txt", "no_one_crosses_the_finnish_line")
→ no_one_crosses_the_finnish_line:
    possible: [block] (4 keys)
    id: 185
    happened: [block] (2 keys)
```

> ● `possible`（解除可能条件）と`happened`（達成条件）のブロックがあります。それぞれを調査します。

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

> ● NOT条件とtagブロックをさらに深掘りします。

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

> ● **実績「No One Crosses the Finnish Line」の達成条件:**
>
>**解除可能条件:**
>- **フィンランド（FIN）** でプレイ
>- **アイアンマンモード**有効
>- カスタム難易度設定なし
>- 実績許可ゲームルール
>
>**達成条件:**
> 1. **開始時の中核州を一つも失わない**（グローバルフラグ`achievement_fin_has_lost_one_starting_core` が立っていないこと）
> 2. **1944年9月19日以降まで生き残る**（この日付は歴史上のモスクワ休戦協定（継続戦争終結）にちなんでいます）
> 3. **以下のフォーカスを完了していないこと**（制限ルート）:
>   - `FIN_right_wing_policies`（右翼政策）
>   - `FIN_suomalainen_sosialismi`（フィンランド式社会主義）
>   - ソ連が `SOV_beaten_but_not_defeated`（敗北するも屈せず）を完了していない

---

> \> `achievement_fin_has_lost_one_starting_core` はどのように立ちますか？

> ● このフラグが全スクリプトファイルのどこで設定されるか検索します。

```
search_references("achievement_fin_has_lost_one_starting_core", include_lines=True)
→ Found in 2 file(s):
  common/achievements.txt
    L4693: NOT = { has_global_flag = achievement_fin_has_lost_one_starting_core }
  common/on_actions/09_aat_on_actions.txt
    L1699: set_global_flag = achievement_fin_has_lost_one_starting_core
```

> ● `09_aat_on_actions.txt` の1699行目で設定されています。その行がどのシンボルに属するか確認します。

```
find_symbol_at_line("common/on_actions/09_aat_on_actions.txt", 1699)
→ symbol: on_actions
    type: on_actions
    lines: L2-L4046
    use: get_structure(file_path, "on_actions")

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

> ● **フラグの設定条件:**
>
> フラグ `achievement_fin_has_lost_one_starting_core` は `on_state_control_changed`（州の支配権変更時）に以下の条件で設定されます：
>
>- **`FIN.core_states_at_game_start`** = フィンランドのゲーム開始時の中核州リスト
>- **`FROM.FROM`** = 支配権が変わった州
>
>つまり、**フィンランドの開始時中核州のいずれかが他国の支配下に入った瞬間**にこのフラグが立ちます。
>
>**実績への影響:**
>
>一度でもフィンランドの開始時中核州（本土やカレリアなど）を敵に占領されると、たとえ奪還してもフラグは消えないため、**実績達成が不可能**になります。
>
>ソ連の侵攻時に一切の領土を失わない完璧な防衛が必要です。

</details>

## 対応ゲーム

| ゲーム | game_type |
|--------|-----------|
| 🪖 Hearts of Iron IV | `hoi4` |
| 🌠 Stellaris | `stellaris` |
| 🧭 Europa Universalis V | `eu5` |
| 🚂 Victoria 3 | `vic3` |
| 👑 Crusader Kings 3 | `ck3` |

## 利用方法

### 利用者向け

#### 1. uv をインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 2. Claude / Claude Code に設定する

使用するクライアントの `.mcp.json` に追加します：

```json
{
  "mcpServers": {
    "paradox-script": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/106-/paradox-script-mcp",
        "paradox-script-mcp"
      ]
    }
  }
}
```

クライアントを再起動すると、`uvx` が自動でサーバーを起動します。インストール作業は不要です。

> **Note:** paradox-script-parserは自作のパーサーであり、Paradoxスクリプトの全ての構文に対応しているわけではありません。一部のスクリプトが正しくパースされない可能性があります。

### 開発者向け

```bash
# 開発用インストール
uv pip install -e .

# ホットリロードで実行（streamable-http、ポート8000）
make serve

# テスト実行
make test
```

`make serve` で起動した場合は、`.mcp.json` に以下の設定を使います：

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

## MCPツール

### init_game

ゲームディレクトリパスで初期化します。最初に呼び出す必要があります。

```
init_game("/path/to/Hearts of Iron IV")
→ "Initialized: /path/to/Hearts of Iron IV"
```

### list_directories

スクリプトディレクトリとその用途を一覧表示します。

```
list_directories()
→ common/national_focus/ -> 国家方針ツリー
   common/decisions/ -> ディシジョン
   common/ideas/ -> 国民精神、閣僚、企業
   events/ -> イベント
   ...
```

### list_files

ディレクトリ内の `.txt` ファイルを一覧表示します。`list_symbols` や `get_structure` を呼ぶ前にファイル名を調べるのに使います。

```
list_files("common/national_focus")
→ afghanistan.txt
   argentina.txt
   australia.txt
   austria.txt
   ...
```

### search_references

全スクリプトファイルを横断して文字列を検索します。フラグ名やイベントIDがどのファイルで参照されているかを調べるのに使います。

```
search_references("achievement_fin_has_lost_one_starting_core")
→ Found in 2 file(s):
   common/achievements.txt
   common/on_actions/09_aat_on_actions.txt
```

`include_lines=True` にすると行番号と内容も返します：

```
search_references("CZE_capitulated_germany", include_lines=True)
→ Found in 2 file(s):
   common/achievements.txt
     L7784: has_country_flag = CZE_capitulated_germany
   common/on_actions/15_mun_on_actions.txt
     L114: CZE = { set_country_flag = CZE_capitulated_germany }
```

### find_symbol_at_line

指定した行番号を含むシンボルを返します。`search_references` で行番号を得た後、どのシンボルに属するかを調べるのに使います。

指定行がコメント行や空行などブロック外だった場合は、最も近いシンボルをフォールバックとして返します（`note:` フィールドで通知）。

```
find_symbol_at_line("common/on_actions/15_mun_on_actions.txt", 114)
→ symbol: on_actions
    type: on_actions
    lines: L1-L466
    use: get_structure(file_path, "on_actions")
```

```
find_symbol_at_line("events/MUN_Czechoslovakia.txt", 3030)
→ symbol: MUN_czech.1034
    container: country_event
    lines: L2928-L3192
    use: get_structure(file_path, "MUN_czech.1034")
```

```
# コメント行を指定した場合 — 最近傍シンボルにフォールバック
find_symbol_at_line("events/shroud_events.txt", 8213)
→ symbol: shroud.4135
    container: country_event
    lines: L8214-L8325
    note: nearest symbol (line 8213 is outside any block)
    use: get_structure(file_path, "shroud.4135")
```

### list_symbols

ファイル内のシンボルを一覧表示します（トップレベルのみ）。
子要素を表示するには `get_structure` を使用してください。

```
list_symbols("common/national_focus/japan.txt")
→ focus: JAP_the_unthinkable_option (x=12, y=0)
  focus: JAP_approach_the_young_officers (y=1)
  ...
  focus_tree: japan_wtt_focus
```

### get_structure

シンボルの構造を表示します（キーのみ、フルコンテンツなし）。

```
get_structure("common/national_focus/japan.txt", "JAP_the_unthinkable_option")
→ JAP_the_unthinkable_option:
     id: "JAP_the_unthinkable_option"
     icon: "GFX_goal_generic_political_reform"
     prerequisite: [block] (1 keys)
     completion_reward: [block] (8 keys)
```

### get_structure（ネストされたブロックへのナビゲーション）

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

### get_structure_by_id

ファイルパスを指定せず、IDだけでシンボルの構造を直接取得します。`country_event = { id = shroud.4135 }` のような参照を見つけたとき、定義元にすぐジャンプするのに便利です。

内部ではテキスト検索（候補ファイルの絞り込み）とパース（定義の確認）を組み合わせており、Stellarisのような大規模ゲームでも効率的に動作します。

```
get_structure_by_id("shroud.4135")
→ # found in: events/shroud_events.txt
  shroud.4135:
    is_triggered_only: "yes"
    picture_event_data: [block] (2 keys)
    desc: "shroud.4135.desc"
    ...
```

`get_structure` と同様に `key_path` もサポート：

```
get_structure_by_id("shroud.4135", key_path="option.0")
→ # found in: events/shroud_events.txt
  shroud.4135.option.0:
    name: "shroud.4135.a"
    accept_end_of_the_cycle: "yes"
    ...
```

`glob_pattern` で検索範囲を絞ることでさらに高速化できます：

```
get_structure_by_id("shroud.4135", glob_pattern="events/**/*.txt")
```

## 各ゲームへの対応方法

新しいゲームに対応するには、`src/paradox_script_mcp/knowledge/{game_type}/directories.yml` にスクリプトディレクトリの一覧と用途を記述したYAMLを置く必要があります。

### `/generate-knowledge` スキルを使う（Claude Code）

Claude Codeを使っている場合、組み込みの `/generate-knowledge` スキルでゲームディレクトリを自動スキャンしてYAMLを生成できます。

```
/generate-knowledge <game_type> <game_path>
```

例：

```
/generate-knowledge eu4 "/path/to/Europa Universalis IV"
/generate-knowledge ck3 "/path/to/Crusader Kings III"
```

スキルはゲームディレクトリ内の各サブディレクトリにある `.txt` ファイルをサンプリングし、`src/paradox_script_mcp/knowledge/{game_type}/directories.yml` に一行の説明付きで書き出します。`gfx`・`interface`・`music` などの非スクリプトディレクトリは自動的にスキップされます。

### 手動で作成する

`src/paradox_script_mcp/knowledge/{game_type}/directories.yml` を手動で作成することもできます：

```yaml
# {game_type} Directory Knowledge

directories:
  some/path:
    description: Brief purpose in English

  another/path:
    description: Brief purpose in English
```

## プロジェクト構成

```
paradox-script-mcp/
├── pyproject.toml
└── src/paradox_script_mcp/
    ├── __init__.py
    ├── server.py              # MCPサーバーエントリポイント
    ├── core/
    │   └── game.py            # ゲームパス管理
    ├── knowledge/
    │   └── directory_map.py   # HOI4ディレクトリ知識ベース
    └── tools/
        ├── explore.py         # list_directories, list_files
        ├── search.py          # search_references
        ├── symbols.py         # list_symbols, find_symbol_at_line
        └── structure.py       # get_structure, get_structure_by_id
```

