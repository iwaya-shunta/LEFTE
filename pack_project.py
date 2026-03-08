import os

# --- 設定：除外したいフォルダやファイル ---
EXCLUDE_DIRS = {
    'static/uploads', 
    'static/wav_files', 
    '__pycache__', 
    '.venv', 
    '.git', 
    '.idea', 
    'voice_cache'
}
EXCLUDE_FILES = {
    '.env', 
    'chat_history.db', 
    'project_bundle.txt', # 出力ファイル自身
    'pack_project.py'     # このスクリプト自身
}

OUTPUT_FILE = 'project_bundle.txt'

def should_exclude(path):
    for ex_dir in EXCLUDE_DIRS:
        if path.startswith(ex_dir) or f"/{ex_dir}/" in f"/{path}/":
            return True
    if os.path.basename(path) in EXCLUDE_FILES:
        return True
    # 拡張子で除外（画像や音声、証明書など）
    if path.endswith(('.png', '.jpg', '.wav', '.crt', '.key', '.ico', '.pyc')):
        return True
    return False

def main():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk('.'):
            # 相対パスを取得
            rel_root = os.path.relpath(root, '.')
            if rel_root == '.':
                rel_root = ''

            for file in files:
                full_path = os.path.join(rel_root, file)
                if should_exclude(full_path):
                    continue

                try:
                    with open(full_path, 'r', encoding='utf-8') as infile:
                        outfile.write(f"\n{'='*50}\n")
                        outfile.write(f"FILE: {full_path}\n")
                        outfile.write(f"{'='*50}\n\n")
                        outfile.write(infile.read())
                        outfile.write("\n")
                    print(f"Packed: {full_path}")
                except Exception as e:
                    print(f"Skipped (Error): {full_path} - {e}")

    print(f"\n完了！ {OUTPUT_FILE} が作成されました。")

if __name__ == "__main__":
    main()