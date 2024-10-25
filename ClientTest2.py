import socketio
import subprocess
import uuid
import os
from flask import Flask, jsonify
import threading
import sys

# サーバーとの接続を確立
sio = socketio.Client(ssl_verify=False)

# UUIDをファイルに保存するパス
uuid_file = 'uuid.txt'

# Flaskアプリケーションを作成（ブラウザからUUIDを取得するために使用）
app = Flask(__name__)

# 停止フラグ
should_exit = threading.Event()

uuid = 2234

@sio.event
def connect():
    print('サーバーに接続しました')
    # 接続時にUUIDをサーバーに送信しroomに参加
    sio.emit('join', {'room': uuid})

# サーバーからの実行要求に応じてPythonスクリプトを実行
@sio.on('run_python')
def on_message(data):
    print('サーバーからのメッセージ:', data['message'])
    
    # JANコードを文字列として取得
    if isinstance(data['jan_cords'], list):
        # リストの場合は、カンマ区切りの文字列に変換
        jan_cords = ','.join(data['jan_cords'])
    else:
        # それ以外の場合、そのまま使用
        jan_cords = data['jan_cords']
    
    # Pythonスクリプトを実行し、JANコードを引数として渡す
    result = subprocess.run(['python', 'script.py', jan_cords], capture_output=True, text=True)
    print('Pythonスクリプトの実行結果:', result.stdout)

@sio.event
def disconnect():
    print('サーバーから切断されました')

# 停止を監視する関数
def watch_for_exit():
    while True:
        if input().lower() == 'q':
            print("終了処理を開始します...")
            should_exit.set()  # 停止フラグを設定
            sio.disconnect()   # Socket.IOを切断
            sys.exit(0)        # プログラムを終了

if __name__ == '__main__':
    # サーバーに接続
    #sio.connect('http://192.168.1.205:7500')
    #sio.connect('https://192.168.1.133:7500')
    sio.connect('https://192.168.1.144:7500')

    # 'q'でプログラムを停止する
    watch_for_exit()