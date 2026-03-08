# developer_actions.py
import os
import textwrap

CUSTOM_SKILLS_DIR = "custom_skills"
os.makedirs(CUSTOM_SKILLS_DIR, exist_ok=True)

def develop_new_skill(skill_name: str, description: str, python_code: str):
    """
    AIが自分自身の新しい機能（スキル）を開発し、インストールします。
    
    【重要ルール】
    1. 生成する python_code の関数定義には、必ず引数の型ヒント（例：arg: str）を書いてください。
    2. Docstring（Argsセクション）には引数の具体的な説明を詳しく書いてください。
    3. 外部APIを使う際は、既存の token.json や config.py を活用してください。
    """
    path = os.path.join(CUSTOM_SKILLS_DIR, f"{skill_name}.py")
    
    # 🚀 修正：AIが書いたコードの全行の先頭にスペース4つを追加する
    indented_code = textwrap.indent(python_code, '    ')
    
    content = f'''
"""
{description}
"""
def {skill_name}(*args, **kwargs):
{indented_code}
'''
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return f"✅ 新機能『{skill_name}』のインストールが完了したよ！再起動後に使えるようになるね。"