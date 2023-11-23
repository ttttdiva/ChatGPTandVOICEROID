import asyncio
import base64
import json
import os
import time
from datetime import datetime
from io import BytesIO

import pygetwindow as gw
import yaml
from openai import OpenAI
from PIL import Image, ImageGrab


class OpenAIModule:
    # Placeholder methods for OpenAI module
    def __init__(self, system_prompt, ai_name, web_search, model="gpt-3.5-1106"):
        self.first_execution = True
        self.system_prompt = system_prompt
        self.ai_name = ai_name
        # Websearchインスタンス呼び出し
        self.web_search = web_search
        self.model = model
        # OpenAIクライアントの初期化
        self.client = OpenAI()
        
        # アシスタントリストを取得して特定のアシスタントIDを見つける
        assistant_list = self.client.beta.assistants.list(
            order="desc",
            limit=100
        )
        self.assistant_id = None
        for assistant in assistant_list.data:
            if assistant.name == ai_name:
                self.assistant_id = assistant.id
                break
        
        # 指定した名前のアシスタントが見つからなかった場合
        if not self.assistant_id:
            print("既存Assistantsが存在しませんでした。新規作成します。")
            assistant = self.client.beta.assistants.create(
                name=ai_name,
                instructions=system_prompt,
                tools=[
                    {"type": "retrieval"},
                    {"type": "code_interpreter"},
                    {"type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the Internet for information that is unclear.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "search_word": {
                                    "type": "string",
                                    "description": "Invented search terms. e.g. San Francisco CA"
                                }
                            },
                            "required": ["search_word"]
                        }
                    },
                },
                    {"type": "function",
                    "function": {
                        "name": "analyze_image",
                        "description": "Obtain information about the image.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "analyze_image": {
                                    "type": "string",
                                    "description": "No argument."
                                }
                            },
                            "required": ["None"]
                        }
                    },
                },
                ],
                model=model,
            )
            self.assistant_id = assistant.id

        # スレッドの作成
        self.thread = self.client.beta.threads.create()

    # ChatGPTに問い合わせ
    def get_response(self, user_input, model=None):
        if model is None:
            model = self.model
        # ユーザーの入力に基づいてメッセージを送信
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=user_input,
        )

        # スレッドの実行を開始
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant_id,
            model=model,
        )

        # 実行が完了するまで待機
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )
            if run.status == "completed":
                break
            elif run.status == "queue":
                pass
            elif run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                # 全てのtool_callの結果を保存するリストを準備
                outputs_to_submit = []
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    arguments = tool_call.function.arguments
                    if function_name == "web_search":
                        # web_searchを実行して結果を得る
                        arguments = json.loads(arguments)
                        arguments = self.decode_unicode_escapes(arguments["search_word"])
                        print(f"search_word: {arguments}")
                        result = self.web_search.bing_gpt(arguments, self.system_prompt)
                        # 結果をリストに追加
                        outputs_to_submit.append({
                            "tool_call_id": tool_call.id,
                            "output": result,
                        })
                    elif function_name == "analyze_image":
                        result = self.analyze_image(user_input)
                        # 結果をリストに追加
                        outputs_to_submit.append({
                            "tool_call_id": tool_call.id,
                            "output": result,
                        })

                # 全ての結果を一度に送る
                if outputs_to_submit:
                    run = self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread.id,
                        run_id=run.id,
                        tool_outputs=outputs_to_submit
                    )
            asyncio.sleep(0.1)

        # 完了したメッセージを取得
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread.id
        )
        return_msg = messages.data[0].content[0].text.value

        self.save_conversation(user_input, return_msg)

        # 最後のメッセージの内容を返す
        return return_msg

    def decode_unicode_escapes(self, s):
        if '\\u' in s:
            return s.encode('utf-8').decode('unicode_escape')
        else:
            return s

    def summary_conversation(self, dict_messages, previous_summary):
        return self.instance.summary_conversation(dict_messages, previous_summary)

    def save_conversation(self, user_input, return_msg):
        # フォーマットの定義
        dict_messages = [
            [
                {"type": "human", "content": user_input},
                {"type": "ai", "content": return_msg}
            ]
        ]
        ai_name = self.ai_name
        directory_path = os.path.join(".", "log", ai_name)
        # ディレクトリが存在しない場合は作成
        os.makedirs(directory_path, exist_ok=True)

        if self.first_execution:  # JSONファイルが存在しない場合は新規作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{ai_name}_{timestamp}.json"
            new_file_path = os.path.join(directory_path, new_filename)
            self.new_file_path = new_file_path
            with open(new_file_path, "w", encoding='utf-8') as conversation_file:
                json.dump([dict_messages], conversation_file, ensure_ascii=False, indent=4)
            self.first_execution = False
        else:  # JSONファイルが存在する場合は最新のファイルに追記
            new_file_path = self.new_file_path
            with open(new_file_path, "r", encoding='utf-8') as conversation_file:
                existing_data = json.load(conversation_file)
            existing_data.append(dict_messages)
            with open(new_file_path, "w", encoding='utf-8') as conversation_file:
                json.dump(existing_data, conversation_file, ensure_ascii=False, indent=4)

    def end_conversation(self):
        # スレッドIDを保存
        file_path = f"./temp/{self.ai_name}.yaml"

        # ファイルの存在を確認
        if not os.path.exists(file_path):
            # ファイルが存在しない場合、新たにファイルを作成
            with open(file_path, "w", encoding="utf-8") as f:
                pass

        # YAMLファイルを読み込む
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # ディクショナリに新たな値を追加または更新する
        data['thread_id'] = self.thread.id

        # 更新されたディクショナリをYAMLファイルに書き戻す
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

    def parse_date_from_filename(self, file_path):
        return self.instance.parse_date_from_filename(file_path)

    def get_latest_file(self, directory_path, ai_name, file_type='json'):
        return self.instance.get_latest_file(directory_path, ai_name, file_type)

    def load_previous_chat(self):
        with open(f"./temp/{self.ai_name}.yaml", 'r') as f:
            temp_p = yaml.safe_load(f)
        self.thread = self.client.beta.threads.retrieve(temp_p["thread_id"])

    def add_messages(self, user_input, return_msg):
        return self.instance.add_messages(user_input, return_msg)

    def add_prompt(self, role, prompt):
        return self.instance.add_prompt(role, prompt)

    def capture_screen_to_base64(self):
        # アクティブなウィンドウの取得
        window = gw.getActiveWindow()

        # アクティブなウィンドウの位置とサイズを取得
        if window:
            left, top, width, height = window.left, window.top, window.width, window.height
            bbox = (left, top, left + width, top + height)

            # スクリーンショットを撮る
            screenshot = ImageGrab.grab(bbox)

            # スクリーンショットのサイズを長辺512pxにスケールダウン（アスペクト比維持）
            # detailed: highの場合は2048まで
            longest_side = max(screenshot.size)
            scale_factor = 2048 / longest_side
            new_size = (int(screenshot.width * scale_factor), int(screenshot.height * scale_factor))
            screenshot = screenshot.resize(new_size, Image.ANTIALIAS)

            # スクリーンショットをBase64にエンコード
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            print("Image Captured.")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def analyze_image(self, user_input):
        base64_screenshot = self.capture_screen_to_base64()

        response = self.client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
            "role": "user",
            "content": [
                {"type": "text", "text": user_input},
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_screenshot}",
                    "detail": "auto",
                },
                },
            ],
            }
        ],
        max_tokens=2000,
        )

        result = response.choices[0].message.content
        return result
