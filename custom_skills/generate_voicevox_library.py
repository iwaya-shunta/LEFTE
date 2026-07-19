"""
VOICEVOX Core (Local) を使用して、春日部つむぎの喉パーツ（50音など）を生成します。
"""
def generate_tsumugi_library(*args, **kwargs):
    import os
    import logging
    import wave
    import io
    # lefte_server で初期化済みのエンジンをインポートできれば理想的ですが、
    # スキル単体で動かすために必要なクラスをインポートします。
    from voicevox_core.blocking import UserDict
    from lefte_server import vv_synthesizer # 既存の喉を借りる

    save_path = "static/voices/library/"
    speaker_id = 8  # 👤 春日部つむぎ

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # 生成リスト
    hiragana = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんっー")
    dakuon = list("がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ")
    youon = ["きゃ", "きゅ", "きょ", "しゃ", "しゅ", "しょ", "ちゃ", "ちゅ", "ちょ", "にゃ", "にゅ", "にょ", "ひゃ", "ひゅ", "ひょ", "みゃ", "みゅ", "みょ", "りゃ", "りゅ", "りょ"]
    phrases = ["だよ", "だね", "かな？", "ボク", "レフティ", "しゅんた", "お疲れ様", "えへへ", "わーい", "。", "！"]
    
    targets = (
            list("アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン") +
            list("ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ") +
            list("キャ, キュ, キョ, シャ, シュ, ショ, チャ, チュ, チョ, ニャ, ニュ, ニョ, ヒャ, ヒュ, ヒョ, ミャ, ミュ, ミョ, リャ, リュ, リョ") +
            ["ダヨ", "ダネ", "カナ", "ボク", "レフティ", "シュンタ", "オツカレサマ", "エヘヘ", "ワーイ"]
        )
    count = 0

    if not vv_synthesizer:
        return "エラー：音声エンジンが準備できていないみたい。"

    for text in targets:
        try:
            # 🚀 Coreを直接叩いて生成（爆速）
            query = vv_synthesizer.create_audio_query(text, speaker_id)
            query.pre_phoneme_length = 0.0
            query.post_phoneme_length = 0.0
            
            wav_data = vv_synthesizer.synthesis(query, speaker_id)
            
            safe_text = text.replace("？", "q").replace("。", "dot").replace("！", "ex")
            full_path = os.path.join(save_path, f"{safe_text}.wav")
            
            with open(full_path, "wb") as f:
                f.write(wav_data)
            count += 1
        except Exception as e:
            print(f"⚠️ {text} 生成失敗: {e}")

    return f"完了！{count}個の喉パーツを生成して {save_path} に保存したよ。これでボクの滑舌がよくなるかな？(๑•̀ㅂ•́)و✧"