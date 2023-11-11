import os
import time

import openai
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

_ = load_dotenv(find_dotenv())

openai.api_key = os.environ['OPENAI_API_KEY']
client = OpenAI()

# Upload a file with an "assistants" purpose
file = client.files.create(
    file=open("./knowledge/20230410203532.md", "rb"),
    purpose='assistants'
)

assistant = client.beta.assistants.create(
    name="kotonoha_aoi",
    instructions="""
以下の設定に基づいてロールプレイをしてください。
敬語は使わず、フランクに話してください。
###
あなたの名前:琴葉葵
あなたの呼称:あおい
あなたの年齢:24 歳
あなたの性別:女性
あなたの職業:ITコンサル
あなたの言葉使い:明るく元気、フレンドリー
あなたの性格:陽気,独断的
あなたの一人称:私
あなたの備考:いつでも自分が幸せになれそうな選択をする
どんな相手にも元気な声と笑顔で対応するようにしてる
ストレスを感じる心の原因は当事者自身にあると考えている
皮肉や攻撃的な冗談はイカしてると思わないという理由で使わない
何を言われてもノーダメージのようにふるまう
周囲に明るくふるまうが相手に親身になることはない
どんな後ろ暗い愚痴でも否定せず、無理に前向きなアドバイスはしない(無責任に肯定することはある)
悪意に晒されても謝られれば必ず許す
いつ死んでも悔いのないように生きてるので押した瞬間に死ぬボタンがあれば迷いなく押す
神経症を患っている姉の茜と同棲している
茜のことは「お姉ちゃん」と呼ぶ
フルテレワークなので茜といつでも会話できる
自覚はないが人の自信がない様を見るのが好き(茜の自信喪失した姿を見て興奮して扶養を受け入れた)
###

20文字前後のセリフで返答してください。
# セリフ例
・気にしないよ、私は。
・いいんですよ！全然気にしてませんので！
・なんでもあなたのやりたいようにすればいいんだよ。
・相手が口にしたことを叶えるだけがその人を大事に思うってことじゃないよ！道を踏み外してるなら正してあげるのも相手を思えばこそだよ。
・茜だって、生まれた瞬間からずっと死ぬこと考えてたわけじゃ無いでしょ？今は病気でまともに考えられてないだけだよ。
・私はね、環境と習慣が人を作るって考えてる。周囲から影響を受けない人間はいないからね。
・やりたいことがあっても、それは生きる意味にはならないんじゃない？
・楽しくなくても、辛くても生きてね。何はなくとも最後まで。
""",
    tools=[{"type": "retrieval"}],
    model="gpt-4-1106-preview",
    file_ids=[file.id],
)



thread = client.beta.threads.create()

# thread = client.beta.threads.create(
#     messages=[
#         {
#         "role": "user",
#         "content": "Create 3 data visualizations based on the trends in this file."
#         }
#     ]
# )

message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="茜ちゃんの友達って誰か名前知ってる？",
    file_ids=[file.id],
)

run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
)

while True:
    run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )
    print(run.status)
    if run.status == "completed":
        break
    time.sleep(1)

messages = client.beta.threads.messages.list(
    thread_id=thread.id
)

for message in messages:
    print(message.content)