# Paradox Script MCP Server

トークン効率の良いAIアシスタント向けParadoxスクリプトの探索ツール

## これはなに？

Paradoxのゲームスクリプトはプレインテキストで書かれており、ClaudeCodeなどのコーディングボットなどに読み込ませ探索させることでイベントの発生条件などを自動で調べさせることができます。

しかしながら、ゲームスクリプトは一つ一つのファイルサイズが長めなのでそのままコーディングボットに入れてしまうとコンテキスト量があっというまに爆発してしまいます。(そして多くのParadoxゲームのようにリソース不足は死を意味します)

そこでこのMCPでは、Paradoxのスクリプトからシンボル(イベントIDとか)のみを抽出したり、そのシンボルが示すブロックのみで読み込むことができます。

これはClaude、ClaudeCode、gemini-cli(試してないです)などのMCPを使用できるクライアントから使用することができます。

## 使用例: 実績の調査

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

> ● このフラグがどこで設定されるか検索します。on_actionsファイルにあるはずです。

```
list_symbols("common/on_actions/09_aat_on_actions.txt")
→ block: on_actions

get_structure("common/on_actions/09_aat_on_actions.txt", "on_actions")
→ on_actions:
    on_state_control_changed: [block] (1 keys)
    ...
```

> ● `on_state_control_changed` フックが関連していそうです。その内容を確認します。

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

## インストール

```bash
# uvを使用（推奨）
uv pip install -e .

# またはpip
pip install -e .
```

### 依存関係

- Python >= 3.11
- [mcp](https://github.com/modelcontextprotocol/python-sdk) >= 1.0.0
- [paradox-script-parser](https://github.com/106-/paradox-script-parser) - 自作のParadoxスクリプトパーサー

> **Note:** paradox-script-parserは自作のパーサーであり、Paradoxスクリプトの全ての構文に対応しているわけではありません。一部のスクリプトが正しくパースされない可能性があります。

## 使い方

### サーバー起動

```bash
# ホットリロード付き（開発用）
make serve

# または直接実行
uv run paradox-script-mcp
```

### Claude Code設定

`.mcp.json` に追加:

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

## 各ゲームへの対応方法

`src/paradox_script_mcp/knowledge/` 以下にディレクトリやファイルの知識をいれたyamlを置くことで対応できます。現在はHoI4の知識のみ備わっています。

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
        ├── explore.py         # list_directories
        ├── symbols.py         # list_symbols
        └── structure.py       # get_structure
```

## 開発

```bash
# 開発用インストール
uv pip install -e .

# ホットリロードで実行
make serve

# テスト実行
make test
```
