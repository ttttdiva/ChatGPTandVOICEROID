import os

import yaml


class CharacterManager:
    def __init__(self):
        self.character_configs = {}
        self.character_dir = "./character"
        self.load_character_configs()
        self.all_char_names = self.get_all_char_names()

        # デフォルトキャラ読み込み
        with open("config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        default_character = config['default_character']
        self.get_character(default_character)

    def load_character_configs(self):
        for filename in os.listdir(self.character_dir):
            if filename.endswith(".yaml"):
                filepath = os.path.join(self.character_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as file:
                    config = yaml.safe_load(file)
                    self.character_configs[filename[:-5]] = config

    def get_all_char_names(self):
        all_char_names = []
        for config in self.character_configs.values():
            all_char_names.extend(config['ai_name'])
        return all_char_names

    def get_character(self, request_msg):
        for char_key, char_config in self.character_configs.items():
            if any(n in request_msg for n in char_config['ai_name']):
                self.ai_name = char_config['ai_name']
                self.ai_chara = char_config['ai_chara']
                self.ai_dialogues = char_config['ai_dialogues']
                self.voice_cid = char_config['voice_cid']
                self.greet = char_config['greet']
                self.tts_type = char_config['tts_type']
                return char_config['ai_name'], char_config['ai_chara'], char_config['ai_dialogues'], char_config['voice_cid'], char_config['greet'], char_config['tts_type']
        return None, None, None, None, None, None
