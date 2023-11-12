import os
import time

import openai
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

_ = load_dotenv(find_dotenv())

openai.api_key = os.environ['OPENAI_API_KEY']
client_openai = OpenAI()

# アシスタントリストを取得して特定のアシスタントIDを見つける
assistant_list = client_openai.beta.assistants.list(
    order="desc",
    limit=100
)
assistant_id = None
for assistant in assistant_list.data:
    if assistant.name == "琴葉葵":
        assistant_id = assistant.id
        break

thread = client_openai.beta.threads.create()

def main():
    message = client_openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=input("user: "),
    )

    run = client_openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    while True:
        run = client_openai.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        print(run.status)
        if run.status == "completed":
            break
        time.sleep(1)

    messages = client_openai.beta.threads.messages.list(
        thread_id=thread.id
    )

    return_msg = messages.data[0].content[0].text.value
    return return_msg

while True:
    return_msg = main()
    print(return_msg)