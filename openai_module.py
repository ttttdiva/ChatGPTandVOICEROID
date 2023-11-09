import json
import os
import time
from datetime import datetime

import yaml
from openai import OpenAI


class OpenAIModule:
    # Placeholder methods for OpenAI module
    def __init__(self, system_prompt, model, ai_name):
        self.first_execution = True
        self.model = model
        self.system_prompt = system_prompt
        self.ai_name = ai_name
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
        
        # エラーハンドリング: 指定した名前のアシスタントが見つからなかった場合
        if not self.assistant_id:
            print("既存Assistantsが存在しませんでした。新規作成します。")
            assistant = self.client.beta.assistants.create(
                name=ai_name,
                instructions=system_prompt,
                tools=[{"type": "retrieval"}],
                model=model,
            )
            self.assistant_id = assistant.id

        # スレッドの作成
        self.thread = self.client.beta.threads.create()

        # スレッドIDを保存
        file_path = f"./temp/{ai_name}.yaml"

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
        )

        # 実行が完了するまで待機
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )
            if run.status == "completed":
                break
            time.sleep(1)

        # 完了したメッセージを取得
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread.id
        )
        return_msg = messages.data[0].content[0].text.value

        self.save_conversation(user_input, return_msg)

        # 最後のメッセージの内容を返す
        return return_msg

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

    def save_summary_conversation(self):
        return self.instance.save_summary_conversation()

    def parse_date_from_filename(self, file_path):
        return self.instance.parse_date_from_filename(file_path)

    def get_latest_file(self, directory_path, ai_name, file_type='json'):
        return self.instance.get_latest_file(directory_path, ai_name, file_type)

    def load_previous_chat(self):
        return self.instance.load_previous_chat()

    def add_messages(self, user_input, return_msg):
        return self.instance.add_messages(user_input, return_msg)

    def add_prompt(self, role, prompt):
        return self.instance.add_prompt(role, prompt)