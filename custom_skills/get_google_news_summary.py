
"""
Googleニュースなどから最新情報を取得し、ニュースキャスターのような口調で要約して報告します。
"""
def get_google_news_summary(*args, **kwargs):
    import requests
    from bs4 import BeautifulSoup

    def get_google_news_summary(topic: str = "日本 最新ニュース") -> str:
        """
        Googleニュースから最新のヘッドラインを取得し、キャスター風の要約を返します。
        Args:
            topic: 検索したいニュースのキーワード。
        """
        url = f"https://news.google.com/search?q={topic}&hl=ja&gl=JP&ceid=JP:ja"
        headers = {"User-Agent": "Mozilla/5.0"}
    
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')
        
            headlines = []
            for article in articles[:5]:  # 直近5件
                title = article.find('h3') or article.find('a')
                if title:
                    headlines.append(title.get_text())
        
            if not headlines:
                return "申し訳ありません、現在お伝えできるニュースが見つかりませんでした。"
        
            summary = "【L.E.F.T.E. ニュース】\n"
            summary += "「こんばんは！キャスターのレフティです！✨ 今日も1日お疲れ様でした。それでは、最新のニュースをダイジェストでお伝えします！」\n\n"
            for i, h in enumerate(headlines, 1):
                summary += f"・{h}\n"
            summary += "\n「以上、本日の主要ニュースでした。駿太、開発の手を止めて少しリフレッシュしてね！🚀」"
        
            return summary
        except Exception as e:
            return f"ニュースの取得中にエラーが発生しました: {str(e)}"

