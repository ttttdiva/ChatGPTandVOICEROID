import os
from datetime import datetime

import yaml
from googleapiclient.discovery import build

from character_manager import CharacterManager
from llm_manager import LLMManager


class WebSearch:
    def __init__(self, google_api_key, cx, ai_name):
        # 設定ファイルを読み込み
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)
        self.java_home = os.path.expandvars(config['java_settings']['java_home'])
        # JAVA環境変数の設定
        os.environ['JAVA_HOME'] = self.java_home
        os.environ['PATH'] = f"{self.java_home}\\bin;" + os.environ['PATH']

        self.google_api_key = google_api_key
        self.cx = cx
        self.ai_name = ai_name
        # 他の初期化コード

    # メイン処理
    def bing_gpt(self, ai_character, ai_dialogues, question):
        # question = re.sub(r"(を|で)?検索して", "", question)
        search_word = self.generate_search_word(question)
        search_result = self.get_search_results(search_word, 3)

        if search_result is None:
            return "検索失敗"

        links = []
        links = self.get_links(search_result)
        print(links)
        contents = self.get_contents(links)
        summary = self.summarize_contents(contents, search_word)
        prompt = ai_character + ai_dialogues
        summary_prompt = f"""
以下の文章を参考に、「{question}」という質問に回答してください。
全く分からない場合はそのように伝えてください。
また、今回に限り必要であれば200文字程度で回答してください。
"""
        gpt_chat = LLMManager(prompt, summary_prompt, model="gpt-3.5-turbo", ai_name=self.ai_name[0])
        
        # キャラプロンプト＋要約
        m = gpt_chat.get_response(summary, model="gpt-4")

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./log/search/{search_word}_{current_time}.log"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(m)
        except:
            filename = f"./log/search/incorrect_search_word_{current_time}.log"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(m)
        return m

    # 検索ワード生成
    def generate_search_word(self, question):
        names_formatted = "」「".join(f'"{name}"' for name in self.ai_name)
        search_word = LLMManager.oneshot_get_response(f"""
以下の質問に基づいて、最も関連性が高く、検索結果を最適に絞り込むことができるキーワードを生成してください。
質問の主題、必要とされる情報、およびその独特なコンテキストを考慮した上で、キーワードを選定してください。
質問の情報から不要な詳細を取り除き、検索に最も有用な要素を抽出することを心掛けてください。

「{names_formatted}」等は{self.ai_name[0]}というキャラクターのことを指します。

回答は必ず1行だけ出力してください。
""", question)
        return search_word

    # Google検索
    def get_search_results(self, query, num, start_index = 0):
        # Google Custom Search API
        result = None
        service = build("customsearch",
                        "v1",	
                        cache_discovery=False,
                        developerKey=self.google_api_key)
        # CSEの検索結果を取得
        error_occurred = False
        for i in range(2):
            try:
                result = service.cse().list(q=query,
                                        cx=self.cx,
                                        num=num,
                                        start=start_index).execute()
                break  # エラーが発生しなければループを抜ける
            except Exception as e:
                if error_occurred:
                    # 2回目のエラーであれば終了
                    print(f"エラーが2回発生しました: {e}")
                    break
                else:
                    # 1回目のエラーであればもう一度試す
                    print(f"エラーが発生しましたが、再試行します: {e}")
                    error_occurred = True
        # 検索結果(JSON形式)
        return result

    # 検索結果からリンクを抽出する関数
    def get_links(self, search_result):
        if 'items' in search_result:
            return [item['link'] for item in search_result['items']]
        return []

    # content抽出
    def get_contents(self, links):
        from boilerpipe.extract import Extractor
        contents = []
        for link in links:
            try:
                extractor = Extractor(extractor='DefaultExtractor', url=link)
                contents.append(extractor.getText())
            except:
                continue
        return contents

    # 検索結果を要約
    def summarize_contents(self, contents, search_word):
        extract_texts = ""
        for con in contents:
            print("contents: ")
            print(con)
            if len(con) > 500:
                try:
                    m = LLMManager.oneshot_get_response(f"以下の文章にかんして、「{search_word}」に関連する文章を抽出してください",con[:1500])
                    extract_texts += m
                except:
                    print("error")
            else:
                extract_texts += str(con)
        return extract_texts[:4000]




