import requests

# 気象庁のAPI URL
url = "https://www.data.jma.go.jp/developer/xml/Bulletin/area/area.php"

# パラメータ設定
params = {
    "area": "1400000",  # 都道府県番号 ( Tokyo: 1400000)
    "date": "2023-02-20",  # 日付 (YYYY-MM-DD)
    "hour": "12",  # 時刻 (00-23)
}

# API リクエスト送信
response = requests.get(url, params=params)

# JSON データ取得
data = response.json()

# 天気情報取得
weather = data['weather']['description']

# 結果出力
print(weather)