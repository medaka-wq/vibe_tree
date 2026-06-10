import os
import argparse
import fnmatch
import unicodedata  # 日本語の表示幅を正しく計算するために追加

# Python 3.11以降なら標準、それ未満なら pip install tomli が必要

# --- 設定定数 ---
# Markdown貼り付け時の推奨幅（全角2/半角1換算）
MAX_MD_WIDTH = 80 
PADDING_MARGIN = 2

try:
    import tomllib
except ImportError:
    import tomli as tomllib

def load_config():
    filename = "vibe_tree_config.toml"
    
    # 1. まず「今いるフォルダ（カレントディレクトリ）」を探す
    config_path = os.path.join(os.getcwd(), filename)
    
    # 2. カレントに無ければ「スクリプト本体があるフォルダ」を探す
    if not os.path.exists(config_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, filename)

    # デフォルト設定値
    default_config = {
        "hide_dirs": {".git", "__pycache__", ".vscode", "node_modules"},
        "exclude_dirs": {"venv", ".venv"},
        "exclude_exts": {".pyc"},
        "default_depth": 3,
        "max_depth_limit": 5,
        "comments": {}
    }

    # 設定ファイルが存在すれば読み込む
    if os.path.exists(config_path):
        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
            settings = data.get("settings", {})
            # 【追加】設定値の検証
            if settings.get("default_depth", 0) > settings.get("max_depth_limit", 0):
                print(f"[Warning] default_depth is greater than max_depth_limit in {config_path}")
            return {
                "hide_dirs": set(settings.get("hide_dirs", default_config["hide_dirs"])),
                "exclude_dirs": set(settings.get("exclude_dirs", default_config["exclude_dirs"])),
                "exclude_exts": set(settings.get("exclude_exts", default_config["exclude_exts"])),
                "default_depth": settings.get("default_depth", 3),
                "max_depth_limit": settings.get("max_depth_limit", 5),
                "comments": data.get("comments", {})
            }
        except Exception as e:
            print(f"[Warning] Failed to load config ({config_path}): {e}")
            print("Falling back to default settings.\n")

    return default_config

CONFIG = load_config()

def get_display_width(text):
    """
    全角文字を2、半角文字を1として、画面上の見た目の文字幅（カウント）を計算する
    """
    width = 0
    for char in text:
        status = unicodedata.east_asian_width(char)
        # 'W' (Wide), 'F' (Fullwidth), 'A' (Ambiguous) は全角扱い（2幅）
        if status in ('W', 'F', 'A'):
            width += 2
        else:
            width += 1
    return width

def is_ignored(item, full_path):
    """
    除外判定ロジック
    """
    if os.path.isdir(full_path) and item in CONFIG["hide_dirs"]:
        return True
    
    if os.path.isfile(full_path):
        for pat in CONFIG["exclude_exts"]:
            pattern = pat if pat.startswith("*") else "*" + pat
            if fnmatch.fnmatch(item, pattern):
                return True
    return False

def build_tree_data(root_path, target_depth, show_files, show_comments):
    """
    ツリーの構造を解析し、リストを返す
    """
    tree_lines = []

    def _build(path, indent="", is_last=True, is_root=True, depth=1):
        # 階層制限チェック
        if depth > target_depth:
            return

        name = os.path.basename(path)
        is_dir = os.path.isdir(path)
        display_name = f"{name}/" if is_dir else name
        
        # 1. 現在の行を記録
        if is_root:
            tree_lines.append({"tree_part": display_name, "comment": ""})
        else:
            branch = "└── " if is_last else "├── "
            tree_part = f"{indent}{branch}{display_name}"
            
            comment = ""
            if show_comments:
                comment = CONFIG["comments"].get(name, "")
            
            tree_lines.append({"tree_part": tree_part, "comment": comment})

        # 2. フォルダなら中身を探索
        if is_dir and (name not in CONFIG["exclude_dirs"] or is_root):
            try:
                items = os.listdir(path)
            except PermissionError:
                return

            # 除外判定などのフィルタリング
            filtered_items = []
            for item in items:
                full_path = os.path.join(path, item)
                
                # --- 1. 除外ルールに引っかかるなら無視する ---
                if is_ignored(item, full_path):
                    continue
                
                # --- 2. ファイル非表示モードなら無視する ---
                if not show_files and os.path.isfile(full_path):
                    continue
                filtered_items.append(item)

            # ソート
            filtered_items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

            # 再帰呼び出し
            next_indent = indent + ("    " if is_last else "│   ")
            for i, item in enumerate(filtered_items):
                _build(os.path.join(path, item), next_indent, is_last=(i == len(filtered_items) - 1), is_root=False, depth=depth + 1)

    # 最初の呼び出し
    _build(os.path.abspath(root_path))
    return tree_lines

def main():
    parser = argparse.ArgumentParser(description="vibe-tree: A smart tree command with depth control and comments.")
    parser.add_argument("path", nargs="?", default=".", help="Target root directory")
    parser.add_argument("-d", "--depth", type=int, default=None, help="Maximum depth to display")
    parser.add_argument("-f", "--files", action="store_true", help="Include files in the tree")
    parser.add_argument("-nc", "--no-comment", action="store_true", help="Hide comments even if defined in TOML")
    
    args = parser.parse_args()
    
    # 階層数の決定
    target_depth = args.depth if args.depth is not None else CONFIG["default_depth"]
    
    # 安全ブレーキ
    if target_depth > CONFIG["max_depth_limit"]:
        print(f"[Warning] Depth {target_depth} exceeds limit. Capped at {CONFIG['max_depth_limit']}.\n")
        target_depth = CONFIG["max_depth_limit"]
        
    if os.path.exists(args.path):
        show_comments = not args.no_comment
        
        # 1パス目：画面出力はせず、すべての行のデータをツリー部とコメント部に分けて回収
        lines_data = build_tree_data(args.path, target_depth, args.files, show_comments)
        
        # コメントがある行の、ツリー部分の「見た目の最大幅」を割り出す
        max_tree_width = 0
        for line in lines_data:
            if line["comment"]:  # コメントが存在する行だけを対象にする
                width = get_display_width(line["tree_part"])
                if width > max_tree_width:
                    max_tree_width = width
        
        # 2パス目：幅を綺麗に揃えながら画面に出力
        # 【重要】ここで行を追加して、有効な最大幅を決定する
        effective_max_width = min(max_tree_width, MAX_MD_WIDTH)
        
        for line in lines_data:
            if line["comment"]:
                current_width = get_display_width(line["tree_part"])
                
                if current_width > effective_max_width:
                    # 制限を超えたら、揃えずに最低限の空白だけ空けてコメントを書く
                    print(f"{line['tree_part']}{' ' * PADDING_MARGIN}# {line['comment']}")
                else:
                    # 制限内なら、綺麗に揃える
                    space_count = (effective_max_width - current_width) + PADDING_MARGIN
                    print(f"{line['tree_part']}{' ' * space_count}# {line['comment']}")
            else:
                # コメントがない行はそのまま出力
                print(line["tree_part"])
    else:
        print(f"Error: {args.path} not found.")

if __name__ == "__main__":
    main()
