# VibeTree

A customizable directory tree generator for Markdown READMEs—a simple, Python-based alternative to the standard `tree` command.

**Features:**
- **Hide noise:** Completely exclude directories like `__pycache__` or `.venv`.
- **Filter files:** Cleanly filter out any extensions you don't want to see.
  
---

**Windowsの標準`tree`コマンドは愛しているけれど、表示したくないディレクトリ（フォルダ）の扱いが面倒、ということで、バイブスと衝動だけで作成した高機能ディレクトリ（フォルダ）ツリー生成スクリプト。**

「不要なディレクトリを弾きつつ、右側にいい感じのコメントを添えてREADME用のツリーを作りたい、もうディレクトリをよけて、戻さないで起こす事故いや！」
そんな深夜の怒りだけで実装されました。

---

Windowsの標準`tree`コマンドの出力をカスタマイズし、特定のディレクトリや拡張子を除外しながら、各ファイルへの説明（コメント）を付与してツリー構造を出力できるPython製のツールです。

ドキュメント（README等）にプロジェクトのディレクトリ構造を美しく掲載したい場合に最適です。

## 主な機能

- **フォルダの完全非表示（hide_dirs）**
  `__pycache__` や `退避` フォルダなど、ツリー上に存在自体を表示させたくないフォルダを完全に除外します。
- **下層ディレクトリの非表示（exclude_dirs）**
  `venv` や `.venv` などの仮想環境フォルダにおいて、「フォルダの存在（名前）自体はツリーに残しつつ、その配下の詳細なファイル群（下層）には潜らない」という制御が可能です。
- **フォルダ名へのスラッシュ追加**
  ディレクトリであるかファイルであるかを一目で判別できるよう、フォルダ名の末尾に自動で `/` が付与されます。
- **拡張子指定の除外（exclude_exts）**
  `.pyc` や `.DS_Store` など、不要な拡張子を持つファイルをピンポイントで除外します。
- **説明コメントの自動追記**
  設定ファイルにファイル名と説明文を登録しておくことで、ツリーの右側に「いい感じ」の間隔で補足コメントを出力します。

## 出力例

本ツールを使用して生成されたツリー構造のサンプルです。

```text
my_project/
├── venv/  <- 仮想環境（作成済み！）
├── src/
│   ├── main.py  <- メインの実行ファイル
│   └── utils.py
├── vibe_tree_config.toml  <- この設定ファイル
└── README.md  <- あなたがいま読んでいるドキュメント

```

## 使い方

### 1. 動作環境

* Python 3.11 以上（標準の `tomllib` を使用しているため、3.11以降の環境であれば追加のライブラリインストールは不要です）

### 2. 設定ファイルの準備
`vibe_tree.py` と同じディレクトリに `vibe_tree_config.toml` という名前で設定ファイルを作成し、除外したい項目やコメントを記述します。

<details>
<summary>設定ファイルのサンプル（クリックで展開）</summary>

```toml
# vibe_tree_config.toml

[settings]
# 【完全非表示】 存在すらツリーから消し去りたいフォルダ・ファイル
# 「念のためバックアップ」を緊急避難させました
hide_dirs = [
    "__pycache__", 
    "退避", 
    "念のためバックアップ", 
    ".git", 
    ".vscode", 
    ".idea", 
    ".pytest_cache", 
    "build", 
    "dist"
]

# 【下層隠し】 フォルダ名は出すけど、中身は非表示にしたいフォルダ
exclude_dirs = [
    "venv", 
    ".venv", 
    "node_modules", 
    "docs", 
    "assets"
]

# 【拡張子除外】 画面を汚す不要なファイルや、つい作ってしまう「.old」
exclude_exts = [
    ".pyc", 
    ".pyd", 
    ".pyo", 
    ".DS_Store", 
    "Thumbs.db", 
    ".log",
    ".old"
]

[comments]
# --- このツール関連 ---
"vibe_tree.py" = "<- ツリー構造生成スクリプト"
"vibe_tree_config.toml" = "<- この設定ファイル"
"README.md" = "<- あなたがいま読んでいるドキュメント"

# --- Python・環境構築関連 ---
"main.py" = "<- メインの実行ファイル"
"requirements.txt" = "<- 依存ライブラリ（pip）一覧"
"venv" = "<- Python仮想環境（作成済み）"
".venv" = "<- Python仮想環境（作成済み）"

# --- その他共通・定番ファイル ---
".gitignore" = "<- Git管理から除外するファイルの設定"
"LICENSE" = "<- ライセンス（利用規約）表記ファイル"

# --- 自分用 ---
"よく使うプロンプト.txt" = "<- AIへの指示出し用"
"memo.txt" = "<- 殴り書き用の一時ファイル"
"todo.txt" = "<- 直近でやりたいことメモ"

```
</details>

### 3. コマンドの実行

対象のフォルダ（ディレクトリ）に移動し、以下のコマンドを実行します。出力されたテキストをそのままコピーしてドキュメント等にご活用ください。

```bash
# 現在のフォルダを対象にする場合
python vibe_tree.py

# 特定のフォルダを指定して実行する場合
python vibe_tree.py C:\path\to\your\project

```

### 4. ライセンス

ソースコードの変更、利用、再配布等はご自由に行っていただいて構いません。ただし、本スクリプトの使用によって生じたあらゆる不具合や損害について、作者は一切の責任を負いません（無保証となります）。

### 5. 今後のロードマップ
- [ ] 何か追加したかったのですが忘れました。すみません。思い出し次第追記します。

