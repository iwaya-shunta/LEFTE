import os
import logging
from voicevox_core.blocking import Synthesizer, Onnxruntime, OpenJtalk, VoiceModelFile

def generate_voice_parts():
    DICT_DIR = "/home/iwaya/LEFTE/open_jtalk_dic_utf_8-1.11"
    MODEL_PATH = "/home/iwaya/LEFTE/voicevox_core_runtime/voicevox_core/models/vvms/0.vvm"
    SAVE_PATH = "/home/iwaya/LEFTE/static/voices/library/"
    SPEAKER_ID = 8  # 春日部つむぎ

    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)

    try:
        onnx = Onnxruntime.load_once()
        jt = OpenJtalk(DICT_DIR)
        syn = Synthesizer(onnx, jt)
        model = VoiceModelFile.open(MODEL_PATH)
        syn.load_voice_model(model)
        
        # 🚀 確実にエラーを回避するため、単体で発音できない文字を除去
        # 🚀 list() を外して、[]（リスト）として直接繋ぎます
        # 1. 基本のカタカナセット
        seion = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
        dakuon = "ガギグゲゴザジズゼゾダヂヅデドバビブベボ"
        handakuon = "パピプペポ"
        
        # 2. 拗音（小さい文字）セット
        youon_base = ["キャ", "キュ", "キョ", "シャ", "シュ", "ショ", "チャ", "チュ", "チョ", "ニャ", "ニュ", "ニョ", "ヒャ", "ヒュ", "ヒョ", "ミャ", "ミュ", "ミョ", "リャ", "リュ", "リョ", "ギャ", "ギュ", "ギョ", "ジャ", "ジュ", "ジョ", "ビャ", "ビュ", "ビョ", "ピャ", "ピュ", "ピョ"]

        # 🚀 すべての音に対して「ッ」をつけたコンボを自動生成
        # (例: アッ, ガッ, キャッ ...)
        all_base_sounds = list(seion + dakuon + handakuon) + youon_base
        sokuon_combos = [s + "ッ" for s in all_base_sounds]

        # 3. 最終的なターゲットリストを合体
        targets = (
            all_base_sounds +    # 通常音
            sokuon_combos +      # 促音（ッ）付き音 🚀
            ["ダヨ", "ダネ", "カナ", "ボク", "レフティ", "シュンタ", "オツカレサマ", "エヘヘ", "ワーイ"] # 特殊フレーズ
        )

        print(f"🚀 生成開始: {len(targets)}個のパーツに挑戦します")
        count = 0
        for text in targets:
            try:
                # クエリ作成
                query = syn.create_audio_query(text, SPEAKER_ID)
                query.pre_phoneme_length = 0.0
                query.post_phoneme_length = 0.0
                
                # 音声合成
                wav_data = syn.synthesis(query, SPEAKER_ID)

                # 保存（ファイル名として安全な名前に）
                with open(os.path.join(SAVE_PATH, f"{text}.wav"), "wb") as f:
                    f.write(wav_data)
                
                count += 1
                if count % 10 == 0:
                    print(f"進捗: {count}/{len(targets)} 完了...")
            except Exception as e:
                # 🚀 エラーが出た文字は飛ばして次へ進む
                print(f"⏩ スキップ: '{text}' は単体で発音できないため飛ばします。")
                continue

        return f"✨ 完了！ {count}個のWAVファイルを {SAVE_PATH} に作成したよ！"

    except Exception as e:
        import traceback
        return f"❌ 致命的なエラー: {e}\n{traceback.format_exc()}"

if __name__ == "__main__":
    print(generate_voice_parts())