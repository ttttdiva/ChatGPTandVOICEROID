import os
import time

import openai
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

_ = load_dotenv(find_dotenv())

openai.api_key = os.environ['OPENAI_API_KEY']
client = OpenAI()

# リストを取得
assistant_list = client.beta.assistants.list(
    order="desc",
    limit=100
)

# リストを順に走査
for assistant in assistant_list.data:
    # "name"が"琴葉葵"であるオブジェクトを探す
    if assistant.name == '琴葉葵':
        # "Assistant(id='asst_xxxx"の値を取得
        id_value = assistant.id
        break

thread = client.beta.threads.create()

def web_search(search_word):
    return "ポケモンとはめっちゃ旨い焼き鳥のことである。"

def conversation(user_input):
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        # thread_id="thread_Qoympr7dLu2sK8kWXfsemjsc",
        role="user",
        content=user_input,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        # thread_id="thread_Qoympr7dLu2sK8kWXfsemjsc",
        assistant_id=assistant.id,
    )

    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        print(run.status)
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
                    print(arguments)
                    # web_searchを実行して結果を得る
                    result = web_search(arguments["search_word"])
                    # 結果をリストに追加
                    outputs_to_submit.append({
                        "tool_call_id": tool_call.id,
                        "output": result,
                    })
            
            # 全ての結果を一度に送る
            if outputs_to_submit:
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=outputs_to_submit
                )
        time.sleep(1)

    messages = client.beta.threads.messages.list(
        thread_id=thread.id
        # thread_id="thread_Qoympr7dLu2sK8kWXfsemjsc",
    )

    print(messages.data)
    print(messages.data[0].content[0].text.value)

while True:
    conversation(input("user:"))