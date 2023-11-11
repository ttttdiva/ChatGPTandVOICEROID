import os
import time

import openai
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

_ = load_dotenv(find_dotenv())

openai.api_key = os.environ['OPENAI_API_KEY']
client = OpenAI()

# ファイルをアップロード
file = client.files.create(
    file=open("./knowledge/test.txt", "rb"),
    purpose='assistants'
)

# ファイルリストを順に走査
file_list = client.files.list()
for file in file_list.data:
    # "filename"が"character_list.txt"であるオブジェクトを探す
    if file.filename == "character_list.txt":
        character_list_id = file.id

print(character_list_id)
content = client.files.retrieve_content(character_list_id)
print(content)