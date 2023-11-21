py -m venv venv
call venv\Scripts\activate

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

setlocal

:: Git Bashのパスを指定
set GIT_BASH_PATH=C:\Program Files\Git\bin\bash.exe

:: patchコマンドを実行
"%GIT_BASH_PATH%" -c "patch ./venv/Lib/site-packages/discord/voice_client.py < ./patch/voice_client.py.patch"

endlocal

pause