import os
from PIL import Image, ImageDraw, ImageFont

def create_icon(size, filename):
    # 背景が暗いグレーの画像を作成
    image = Image.new('RGBA', (size, size), (19, 19, 20, 255))
    draw = ImageDraw.Draw(image)
    
    # 真ん中にアクセントカラー（青）の円を描く
    margin = size // 10
    draw.ellipse([margin, margin, size - margin, size - margin], 
                 outline=(138, 180, 248, 255), width=size // 20)
    
    # 「L」の文字を入れる（フォントがなくても動くように円だけで構成）
    # 中央にコアを描画
    core_margin = size // 3
    draw.ellipse([core_margin, core_margin, size - core_margin, size - core_margin], 
                 fill=(138, 180, 248, 255))

    # 保存先が static フォルダ内になるように調整
    filepath = os.path.join('static', filename)
    image.save(filepath, 'PNG')
    print(f"✅ {filepath} を作成しました！ (サイズ: {size}x{size})")

if __name__ == "__main__":
    # static フォルダがない場合は作成
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # PWAに必要な2つのサイズを生成
    create_icon(192, 'icon-192.png')
    create_icon(512, 'icon-512.png')
    print("\n🚀 全てのアイコンが実体化しました。もう一度デバッグ画面を確認してみてね！")