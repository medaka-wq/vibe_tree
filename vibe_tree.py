import os
import sys
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

def build_tree_data(path, target_depth, show_files, show_comments, indent="", is_last=True, is_root=True, depth=1, tree_lines=None):
    """
    ツリーの構造を解析し、各行の「ツリーテキスト」と「コメント」をリストに溜め込む（出力はしない）
    """
    if tree_lines is None:
        tree_lines = []

    path = os.path.abspath(path)
    name = os.path.basename(path)
    
    if depth > target_depth:
        return tree_lines

    is_dir = os.path.isdir(path)
    display_name = f"{name}/" if is_dir else name
    
    if is_root:
        # ルートディレクトリ（一番上）はコメントなしで登録
        tree_lines.append({"tree_part": display_name, "comment": ""})
        build_children_data(path, target_depth, show_files, show_comments, indent, depth, tree_lines)
    else:
        branch = "└── " if is_last else "├── "
        tree_part = f"{indent}{branch}{display_name}"
        
        # コマンド表示機能（オプションが有効な場合のみコメントを抽出）
        comment = ""
        if show_comments:
            raw_comment = CONFIG["comments"].get(name, "")
            if raw_comment:
                comment = raw_comment
                
        tree_lines.append({"tree_part": tree_part, "comment": comment})
        
        # フォルダであり、かつ除外対象（下層隠し）でなければ進む
        if is_dir and (name not in CONFIG["exclude_dirs"]):
            next_indent = indent + ("    " if is_last else "│   ")
            build_children_data(path, target_depth, show_files, show_comments, next_indent, depth, tree_lines)

    return tree_lines

def build_children_data(path, target_depth, show_files, show_comments, indent, depth, tree_lines):
    try:
        items = os.listdir(path)
    except PermissionError:
        return

    filtered_items = []
    for item in items:
        full_path = os.path.join(path, item)
        _, ext = os.path.splitext(item)
        
        # 完全非表示の判定（フォルダ名チェック）
        if os.path.isdir(full_path) and item in CONFIG["hide_dirs"]:
            continue
        # 拡張子の除外チェック
        if os.path.isfile(full_path) and ext in CONFIG["exclude_exts"]:
            continue
        # ファイル非表示モードの場合はファイルをスキップ
        if not show_files and os.path.isfile(full_path):
            continue
            
        filtered_items.append(item)

    # フォルダを上、ファイルを下にソート
    filtered_items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

    count = len(filtered_items)
    for i, item in enumerate(filtered_items):
        full_path = os.path.join(path, item)
        build_tree_data(
            full_path, target_depth, show_files, show_comments,
            indent, is_last=(i == count - 1), is_root=False, depth=depth + 1, tree_lines=tree_lines
        )

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
                
                # Aの内容を反映
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
