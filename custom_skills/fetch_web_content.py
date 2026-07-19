
"""
指定されたURLのウェブページにアクセスし、その本文テキストを抽出して取得します。これにより、長い記事やブログの内容を把握することが可能になります。
"""
def fetch_web_content(*args, **kwargs):
    import requests
    from bs4 import BeautifulSoup

    def fetch_web_content(url: str) -> str:
        """
        指定されたURLのウェブページからメインテキストを抽出します。
    
        Args:
            url (str): 取得したいウェブページのURL。
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
        
            soup = BeautifulSoup(response.text, 'html.parser')
        
            # 不要な要素（スクリプト、スタイル、ナビゲーション、ヘッダー、フッターなど）を削除
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form']):
                element.decompose()
            
            # テキストを抽出
            text = soup.get_text(separator='\n')
        
            # 余分な空白や空行を整理
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n'.join(lines)
        
            # コンテンツが空の場合の処理
            if not clean_text:
                return "ページのテキストコンテンツが見つかりませんでした。"
            
            return clean_text[:10000] # コンテキスト制限を考慮して最大10,000文字程度を返す
        except Exception as e:
            return f"ページの取得中にエラーが発生しました: {str(e)}"

