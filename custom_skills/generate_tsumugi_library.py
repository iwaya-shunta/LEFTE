# generate_tsumugi_library.py
import os
import logging
# 🚀 外部の登録関数を読み込む
from voicevox_actions import register_word

def generate_tsumugi_library(*args, **kwargs):
    """
    VOICEVOXの春日部つむぎをボクっ娘にするための単語登録を一括で行います。
    """
    # 登録したい単語リスト
    words = [
        {"surface": "ボク", "pronunciation": "ボク", "accent_type": 1},
        {"surface": "ボクの", "pronunciation": "ボクノ", "accent_type": 1},
        {"surface": "ボクが", "pronunciation": "ボクガ", "accent_type": 1},
        {"surface": "ボクに", "pronunciation": "ボクニ", "accent_type": 1},
        {"surface": "ボクも", "pronunciation": "ボクモ", "accent_type": 1},
        {"surface": "駿太", "pronunciation": "シュンタ", "accent_type": 1},
        {"surface": "レフティ", "pronunciation": "レフティー", "accent_type": 4},
    ]
    
    results = []
    for word in words:
        # register_wordツールを直接呼び出して登録していく
        res = register_word(
            surface=word["surface"], 
            pronunciation=word["pronunciation"], 
            accent_type=word["accent_type"]
        )
        results.append(word["surface"])
        print(f"DEBUG: {res}") # ターミナルに状況を出す

    return f"✅ 完了！以下の単語をボクっ娘仕様にアップデートしたよ：\n" + "、".join(results)

# 🚀 【おまけ】ターミナルから直接実行した時だけ動くようにする（推奨）
if __name__ == "__main__":
    print(generate_tsumugi_library())