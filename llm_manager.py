import os
from datetime import datetime

from langchain_module import LangChainModule
from openai_module import OpenAIModule


class LLMManager:
    def __init__(self, ai_character, ai_dialogues, model="gpt-3.5-turbo", ai_name="AI"):
        self.model = model
        self.system_prompt = ai_character + ai_dialogues
        self.ai_name = ai_name
        
        # chatを定義
        if model.startswith('gpt'):
            self.instance = OpenAIModule(self.system_prompt, model, ai_name)
        else:
            self.instance = LangChainModule(self.system_prompt, model, ai_name)

    def get_response(self, user_input, model=None):
        return self.instance.get_response(user_input, model)

    def summary_conversation(self, dict_messages, previous_summary):
        return self.instance.summary_conversation(dict_messages, previous_summary)

    def save_conversation(self, dict_messages):
        return self.instance.save_conversation(dict_messages)

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