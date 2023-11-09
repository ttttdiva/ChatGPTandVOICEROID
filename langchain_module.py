import json
import os
import re
from datetime import datetime

from langchain.callbacks import get_openai_callback
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts.chat import (AIMessagePromptTemplate,
                                    ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    MessagesPlaceholder,
                                    SystemMessagePromptTemplate)
from langchain.schema import messages_from_dict, messages_to_dict


class LangChainModule:
    def __init__(self, system_prompt, model, ai_name):
        self.first_execution = True
        self.model = model
        self.system_prompt = system_prompt
        self.ai_name = ai_name
        
        self.chat = ChatOpenAI(model_name=model, temperature=0.5)

        # memoryを定義
        self.memory = ConversationSummaryBufferMemory(
            llm=self.chat,
            max_token_limit=100000,
            return_messages=True,
            ai_prefix=ai_name,
            human_prefix="User",
        )

        # chainを定義
        self.conversation = ConversationChain(
            llm=self.chat, memory=self.memory, verbose=True
        )
        # 固定プロンプトを入力
        self.conversation.prompt = self.create_prompt_template(system_prompt)
        self.previous_summary = ""

    def create_prompt_template(self, system_prompt):
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
        ])

    def get_response(self, user_input, model=None):
        if model is None:
            model = self.model
        self.chat.model_name = model
        with get_openai_callback() as cb:
            # LLMに問い合わせ
            return_msg = self.conversation.predict(input=user_input)
            # 会話履歴保存
            messages = self.memory.chat_memory.messages
            dict_messages = messages_to_dict(messages)
            self.save_conversation(dict_messages[-2:])
            print(f"total_tokens: {cb.total_tokens}")
            
            # 2000トークンを超えたら会話要約
            if cb.total_tokens >= 2000:
                self.previous_summary = self.memory.predict_new_summary(messages, self.previous_summary)
                self.summary_conversation(dict_messages, self.previous_summary)
            return return_msg

    def summary_conversation(self, dict_messages, previous_summary):
        # 会話の要約を更新し、要約を含む新しいSystemテンプレートを挿入
        dict_messages = dict_messages[-2:]
        self.memory.chat_memory.messages = messages_from_dict(dict_messages)
        if previous_summary:
            character_with_summary = f"{self.system_prompt}\nまた、前回までの会話を要約した文章を提供します。\n###\n{previous_summary}"
        else:
            character_with_summary = self.system_prompt
        self.conversation.prompt = self.create_prompt_template(character_with_summary)

    def save_conversation(self, dict_messages):
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
        ai_name = self.ai_name
        directory_path = f"./log/{ai_name}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        messages = self.memory.chat_memory.messages
        summary_msg = self.memory.predict_new_summary(messages, self.previous_summary)
        
        summary_filename = f"{directory_path}/{ai_name}_{timestamp}_summary.txt"
        with open(summary_filename, "w", encoding='utf-8') as summary_file:
            summary_file.write(summary_msg)

    # ファイル名から日付を解析する関数
    def parse_date_from_filename(self, file_path):
        pattern = r'(\d{8}_\d{6})'
        match = re.search(pattern, file_path)
        return match.group(1) if match else None

    # ai_nameにマッチする最新のファイルのパスを取得する関数
    def get_latest_file(self, directory_path, ai_name, file_type='json'):
        # 指定されたディレクトリ内の全ファイルをリストアップ
        files = os.listdir(directory_path)
        # ai_nameを含み、指定された拡張子のファイルを抽出
        if file_type == 'json':
            extension = '.json'
        elif file_type == 'summary':
            extension = 'summary.txt'
        else:
            raise ValueError("Unsupported file type. Use 'json' or 'summary'.")

        filtered_files = [f for f in files if ai_name in f and f.endswith(extension)]
        if not filtered_files:
            return None
        # タイムスタンプが最新のファイルを見つける
        latest_file = max(filtered_files, key=lambda x: datetime.strptime(self.parse_date_from_filename(x), '%Y%m%d_%H%M%S'))
        return os.path.join(directory_path, latest_file)

    # ai_nameに基づいて最新のsummary.txtファイルを読み込む関数
    def load_previous_chat(self):
        # ai_nameに基づいたフォルダのパスを構築し、そのフォルダ内のファイルのみを取得
        ai_name = self.ai_name
        directory_path = os.path.join(".", "log", ai_name)
        
        latest_summary_file = self.get_latest_file(directory_path, ai_name, file_type='summary')
        if latest_summary_file is None:
            print("Summary file not found for the AI name provided.")
            self.conversation.prompt = self.create_prompt_template(f"{self.system_prompt}\n前回の会話履歴は見つかりませんでした。")

        with open(latest_summary_file, "r", encoding='utf-8') as file:
            file_content = file.read()
            # 必要に応じて文字列を適切な形式に変換してからsave_contextに渡す
            previous_chat = f"{self.system_prompt}\nまた、前回までの会話を要約した文章を提供します。Aoi, Aoi-chanはあなたで、userは私です。\n###\n{file_content}"
            self.conversation.prompt = self.create_prompt_template(previous_chat)

    def add_messages(self, user_input, return_msg):
        self.memory.save_context({"input": user_input}, {"ouput": return_msg})
        # 会話履歴保存
        messages = self.memory.chat_memory.messages
        dict_messages = messages_to_dict(messages)
        self.save_conversation(dict_messages[-2:])
        self.first_execution = False

    def add_prompt(self, role, prompt):
        if role == "system":
            self.conversation.prompt.append(SystemMessagePromptTemplate.from_template(prompt))
        elif role == "user":
            self.conversation.prompt.append(HumanMessagePromptTemplate.from_template(prompt))
        elif role == "ai":
            self.conversation.prompt.append(AIMessagePromptTemplate.from_template(prompt))

    @classmethod
    def oneshot_get_response(cls, system_prompt, user_input):
        # 新しいインスタンスを作成しキャラプロンプトではないSystemプロンプトを設定
        manager = cls(system_prompt, "")
        # 応答を取得
        return_msg = manager.get_response(user_input)
        print("oneshot_get_response:")
        print(return_msg)
        return return_msg