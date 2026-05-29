import os
import sys
import tomllib  

def load_config():
    config_path = "vibe_tree_config.toml"
    default_config = {
        "hide_dirs": {"__pycache__", ".git"},
        "exclude_dirs": {"venv", ".venv"},
        "exclude_exts": {".pyc"},
        "comments": {}
    }
    
    if os.path.exists(config_path):
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
            return {
                "hide_dirs": set(data.get("settings", {}).get("hide_dirs", [])),
                "exclude_dirs": set(data.get("settings", {}).get("exclude_dirs", [])),
                "exclude_exts": set(data.get("settings", {}).get("exclude_exts", [])),
                "comments": data.get("comments", {})
            }
    return default_config

CONFIG = load_config()

def draw_tree(path, indent="", is_last=True, is_root=True):
    path = os.path.abspath(path)
    name = os.path.basename(path)
    is_dir = os.path.isdir(path)

    # フォルダ名なら後ろにスラッシュを追加
    display_name = f"{name}/" if is_dir else name

    if is_root:
        print(display_name)
        draw_children(path, indent)
    else:
        branch = "└── " if is_last else "├── "
        
        comment = CONFIG["comments"].get(name, "")
        if comment:
            comment = f"  {comment}"

        print(f"{indent}{branch}{display_name}{comment}")
        
        # 【下層隠しの判定】
        # フォルダであり、かつ exclude_dirs に入っていない場合だけさらに下に潜る
        if is_dir and (name not in CONFIG["exclude_dirs"]):
            next_indent = indent + ("    " if is_last else "│   ")
            draw_children(path, next_indent)

def draw_children(path, indent):
    try:
        items = os.listdir(path)
    except PermissionError:
        return

    filtered_items = []
    for item in items:
        full_path = os.path.join(path, item)
        _, ext = os.path.splitext(item)
        
        # 🔥【完全非表示の判定】
        # フォルダであり、かつ hide_dirs に含まれている場合はツリーの候補にすら入れない
        if os.path.isdir(full_path) and item in CONFIG["hide_dirs"]:
            continue
            
        # 拡張子の除外チェック
        if os.path.isfile(full_path) and ext in CONFIG["exclude_exts"]:
            continue
            
        filtered_items.append(item)

    # フォルダを上、ファイルを下にソート
    filtered_items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

    count = len(filtered_items)
    for i, item in enumerate(filtered_items):
        full_path = os.path.join(path, item)
        draw_tree(full_path, indent, is_last=(i == count - 1), is_root=False)

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    if os.path.exists(target_dir):
        draw_tree(target_dir)
    else:
        print(f"Error: {target_dir} not found.")
