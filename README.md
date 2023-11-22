# ChatGPTandVOICEROID
ChatGPT(API)との会話をマイクで行いVOICEROIDやVOICEVOXで読み上げさせるだけのスクリプト  
run_local.batを起動した後、キャラクター名を呼びかけることで対象キャラのプロンプトを使いチャットを開始する  
Discord Botとして稼働させてメンションテキスト or ボイスチャットでも会話可能(ローカルよりも音声認識の遅延がかなり増える為注意)  
  
※初期設定ではマイク入力、音声読み上げで会話するようになっている為、テキストのみで使う場合は`config.yaml`の`Text_Only: False`をTrueに変更する  

## Install
### Local
1. `.env`ファイルにOpenAIのAPI Keyを入力する
2. `setup.bat`を実行
3. [VOICEVOX](https://voicevox.hiroshiba.jp/)をDL、インストールする(少なくともずんだもんで音声再生可能な環境にする)

### Discord Bot
1. `.env`ファイルにOpenAIのAPI Key及びBotのToken及び使用するサーバーIDを入力する
2. `setup.bat`を実行
3. [VOICEVOX](https://voicevox.hiroshiba.jp/)をDL、インストールする(少なくともずんだもんで音声再生可能な環境にする)

## Usage
### Local
1. `run_local.bat`を実行
2. 「起動しました！」のメッセージが出た後にテキストか音声でキャラクター名を入力(例：ずんだもん、葵、茜、きりたん、etc...)
3. 対象のキャラクターとの会話が開始する
  
「前回の続き」と入力することで前回のsummary.txtを読み込む  
「検索して」を含む文章を入力することでGoogle検索結果を踏まえて回答する(要Option設定)  
「エンド」と入力することでキャラクターとの会話を終了する  
再度「エンド」と入力することでbatを終了する  
  
注意：「おやすみ」「PCをシャットダウン」と入力すると会話を要約してからshutdownコマンドを実行する為注意(完全一致でのみ実行)  

### Discord Bot
1. `run_discord.bat`を実行
2. 「起動しました！」のメッセージが出た後にメンションかVCでキャラクター名を入力(例：ずんだもん、葵、茜、きりたん、etc...)
3. 対象のキャラクターとの会話が開始する
  
「前回の続き」と入力することで前回のsummary.txtを読み込む  
「検索して」を含む文章を入力することでGoogle検索結果を踏まえて回答する(要Option設定)  
「エンド」と入力することでキャラクターとの会話を終了する  
再度「エンド」と入力することでbatを終了する  
  
注意：「おやすみ」「PCをシャットダウン」と入力すると会話を要約してからshutdownコマンドを実行する為注意(完全一致でのみ実行)  

## Option
### Discord Bot Setup
1. [通常通りDiscord Botを作成](https://note.com/gx1285/n/na23072135a16)し、Botをサーバーに参加させる
2. Bot Token、Discord_Text_Channel_ID、Discord_Voice_Channel_ID、Discord_Server_IDを`.env`に記載

### VOICEROID Setup
Installの手順だけではまだVOICEROID等他読み上げソフトは実行できない  
1. [Assistant Seika](https://wiki.hgotoh.jp/documents/tools/assistantseika/assistantseika-001a)をDL、インストールする
2. `AssistantSeika.exe`と`VoiceroidEditor.exe`を起動する
3. VOICEROID2にチェックを入れる
![](attachments/2023-11-06-22-10-06.png)
1. 製品スキャンを実行
2. 話者一覧タブに移動し読み上げに使うボイスプリセットのcidを確認(画像は2158)
![](attachments/2023-11-06-22-16-01.png)
1. `./character/{キャラクター名}.yaml`の`voice_cid`を手順5で確認した値に変更する
2. `config.yaml`の`Assistant_Seika_flag`をTrueに変更する
  
CeVIOやCOEIROINK、ガイノイドTalk等AssistantSeikaが対応してるソフトであれば上記手順で設定可能  
その場合は`run_local.bat`でソフト自動起動までは行われないためあらかじめ立ち上げておく必要がある  

### GoogleSearch
必要に応じてGoogle検索を利用して検索結果を踏まえた回答をする(OpenAI API限定)  
会話中に「検索して」を含む文章を入れるとGoogle検索を利用して検索結果を踏まえた回答をする  
ただし事前にGoogle Cloud PlatformからCustom Search APIのAPI Keyを作成する必要がある  

1. Goole Custom Search APIのAPI Keyを作成する
[Custom Search APIを使ってGoogle検索結果を取得する - Qiita](https://qiita.com/zak_y/items/42ca0f1ea14f7046108c)
1. `.env`の`google_api_key`と`cx`を入力する
2. 自環境に合うJDKをインストール
[Java JDKのインストール方法（Windows &#038; Mac対応）｜Code for Fun](https://codeforfun.jp/how-to-install-java-jdk-on-windows-and-mac/)
1. `config.yaml`の`java_home`のパスをインストールしたJDKのバージョンに合わせ変更

### キャラクター追加
`./character/{キャラクター名}.yaml`を追加・修正することで可能
音声認識でキャラクター名が正常に認識されないことが多い場合は、よくご認識される文章を`ai_name`のリストに追記する  

### faster-whisper有効化
`config.yaml`の`record_model`をfaster-whisperに変更することで利用可能
聞き間違いが多くなる為非推奨  
※キャラクター名自体認識できなくなることを防ぐ為、`record_model`を変更しても起動直後の音声認識はwhisperのまま
