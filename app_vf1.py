from datetime import datetime
from flask import Flask, render_template, redirect, url_for, session, jsonify, request 
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import os
import cv2
import numpy as np
import base64
import warnings
import random
import json
from flask import Flask, send_file, abort

from Yolov9Wrapper.Yolov9Wrapper import Yolov9
from incomings.variables import EnvVariables
from jph.Speech import choose_voice, encode_voice_data
from modules.Logging import log_as_labelme
from modules.MenuCache import MenuCache
from modules.Types import MenuObject, Nutrition
from modules.inference import inference_osara_shohin
from modules.menu import Menu

#############################################
##           初期設定(パスなど)             ##
#############################################
ENVVAL=EnvVariables()
MODEL_OSARA_WEIGHT = ENVVAL.MODEL_OSARA
MODEL_SHOHIN_WEIGHT = ENVVAL.MODEL_SHOHIN
MENU_CSV = ENVVAL.MENU_CSV
encoding = ENVVAL.CSV_ENCODING
SERIAL_PORT = ENVVAL.SERIAL_PORT

SSL_CRT=ENVVAL.SSL_CRT
SSL_KEY=ENVVAL.SSL_KEY

DEVICE="cpu" # 0:Windows GPU, mps:Mac GPU, cpu:CPU

warnings.filterwarnings("ignore", category=DeprecationWarning)

# app.pyが置かれているディレクトリに移動する
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---Flaskの初期化
app = Flask(__name__)
CORS(
    app, 
    resources={r'/*': {'origins': '*'}} # すべてのリクエストを許可
    )

# ---メニューの読み込み
menu_all=Menu()
menu_all.load_menu(MENU_CSV,encoding)

# ---最近入力されたメニューの読み込み
menu_cache=MenuCache()
if os.path.exists("menu_cache.json"):
    menu_cache.import_from_json("menu_cache.json")
else:
    # ---menu_cache.jsonが存在しない場合は空のリストを作成
    with open('menu_cache.json', 'w', encoding='utf-8') as f:
        f.write("[\n]")

# ---モデルの読み込み
MODEL_OSARA=Yolov9(MODEL_OSARA_WEIGHT,device=DEVICE)
MODEL_SHOHIN=Yolov9(MODEL_SHOHIN_WEIGHT,device=DEVICE)

# セッションのためのシークレットキー
app.secret_key = 'your_secret_key' 

socketio = SocketIO(app, cors_allowed_origins="*")

# UUIDリスト->ユーザーネームとパスワード，同一端末でのアクセスを同じUUIDでのログインにより識別する
uuid_list = {
    "1234": "a",
    "2234": "b"
}


# ---[Logging]保存先ディレクトリを用意する
# 今日の日付のディレクトリを作成
today = datetime.now().strftime("%Y%m%d")
TODAY_LOGGING_DIR = os.path.join("Logging", today)
os.makedirs(TODAY_LOGGING_DIR, exist_ok=True)

###############################################
##          loginテンプレートの読み込み        ##
###############################################
@app.route('/', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        uuid = request.form['uuid']
        password = request.form['password']

        # ユーザー認証
        if uuid in uuid_list and uuid_list[uuid] == password:
            session['uuid'] = uuid  # セッションにUUIDを保存
            return redirect(url_for('start', uuid=uuid))
        else:
            message = "UUIDまたはパスワードが間違っています。"

    return render_template('login.html', message=message)

###############################################
##          startテンプレートの読み込み        ##
###############################################
@app.route('/start/<uuid>')
def start(uuid):
    # ログインしていなかった場合，ログイン画面に誘導
    if 'uuid' not in session or session['uuid'] != uuid:
        return redirect(url_for('login'))
    
    return render_template('start.html', uuid=uuid)

###############################################
##          indexテンプレートの読み込み        ##
###############################################
@app.route('/index/<uuid>')
def index(uuid):
    # ログインしていなかった場合，ログイン画面に誘導
    if 'uuid' not in session or session['uuid'] != uuid:
        return redirect(url_for('login'))
    
    return render_template('index.html', uuid=uuid)

###############################################
##                 会計開始                   ##
###############################################
@app.route('/start_inference', methods=['POST',"OPTIONS"])
def start_inference():
    """推論を開始するAPI
    
    - リクエスト仕様
        - エンドポイント: /start_inference
        - メソッド: POST
        - パラメータ:
            - image: Base64形式の画像データ
    
    - レスポンス仕様
        - レスポンス形式: application/json
        - レスポンスデータ:
            - image: Base64形式の画像データ
            - items: 検出されたメニューアイテムのリスト
            - total: 合計金額
    """
    
    # ----------
    # ---リクエストの処理
    # ----------
    # ---プリフライト対応 
    if request.method == "OPTIONS":
        return jsonify({"success": True})
    
    # ---リクエストデータを取得
    request_data = request.json
    image_base64 = request_data.get('image')
    frame=base64str_to_ndarray(image_base64) # base64形式の画像データをNumPy配列に変換する
    
    # [デバッグ用]frameを仮で保存する
    # cv2.imwrite('output/input_image.jpg', frame)
    
    # ----------
    # ---推論・結果の取得
    # ----------
    # ---推論する
    inference_result=inference_osara_shohin(frame,MODEL_OSARA,MODEL_SHOHIN)
    
    # ---結果から、画像・メニューオブジェクト・合計金額を取得する
    annotated_image=inference_result['image']
    if annotated_image is None:
        return jsonify({'error': 'Failed to grab frame from webcam'}), 500
    # menu_objects=menu_all.find_menu_by_OsaraShohinResult(inference_result)
    new_osresult=menu_all.find_menu_by_OsaraShohinResult(inference_result)
    
    # [デバッグ用]検出画像を保存する
    cv2.imwrite('output/detected_image.jpg', annotated_image)
    
    # ----------
    # ---値の返却
    # ----------
    # ---アノテーション結果をBase64形式にエンコード
    _, buffer = cv2.imencode('.jpg', annotated_image)
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # `detected_items` がリストであることを確認し、空なら空リストにする
    # menu_objects = menu_objects if menu_objects else []
    
    menu_objects: list[MenuObject] = []
    # ---menu_objectを抽出する
    for box in new_osresult['boxes']:
        menu_object = box['menu_object']
        if not menu_object:
            continue
        menu_objects.append(menu_object)
    
    # ---合計金額を計算する
    total_price = 0
    for item in menu_objects:
        total_price += item['price']

    # ---各合計の栄養素を計算
    nutrition_totals:Nutrition = {
        'energy': 0,
        'protein': 0,
        'fat': 0,
        'carbohydrates': 0,
        'fiber': 0,
        'vegetables': 0,
    }

    for item in menu_objects:
        # 各栄養素の合計値を更新
        if item.get('energy'):
            nutrition_totals['energy'] += float(item['energy'])
        if item.get('protein'):
            nutrition_totals['protein'] += float(item['protein'])
        if item.get('fat'):
            nutrition_totals['fat'] += float(item['fat'])
        if item.get('carbohydrates'):
            nutrition_totals['carbohydrates'] += float(item['carbohydrates'])
        if item.get('fiber'):
            nutrition_totals['fiber'] += float(item['fiber'])
        if item.get('vegetables'):
            nutrition_totals['vegetables'] += float(item['vegetables'])
    
    # ---[JPHacks用]音声を選び、エンコード・返却する
    voice_data=choose_voice(menu_objects)
    voice_base64=encode_voice_data(voice_data)
    
    # ---レスポンスを返す
    # OsaraShohinResultとほぼ同じ形式で返す
    return jsonify({
        # 'image': image_base64,
        'nutrition_totals': nutrition_totals,
        "boxes": new_osresult["boxes"],
        'total': total_price,
        "voice": {
            "text": voice_data["voice"],
            "base64": voice_base64
        }
    })

###############################################
##             撮影画像補正               ##
###############################################
def base64str_to_ndarray(base64str:str)->np.ndarray:
    """
    base64形式の画像データを、cv2で使えるNumPy配列に変換する
    """

    # データURIスキームの場合、最初のコンマ以降を取り出す
    if base64str.startswith('data:image'):
        base64str = base64str.split(',')[1]
    image_bytes = base64.b64decode(base64str)
    np_array = np.frombuffer(image_bytes, np.uint8)
    cv2_image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    
    return cv2_image

# ----------
# ---メニューの検索用API
# ----------
# メニュー検索機能
@app.route('/search_menu', methods=['GET'])
def search_menu():
    """メニューを検索するAPI
    
    - リクエスト仕様
        - エンドポイント: /search_menu
        - メソッド: GET
        - パラメータ:
            - key: 検索キー。display_name, romaji, yolo_name, jan_code, priceのいずれか
            - value: 検索値
            
    - レスポンス仕様
        - レスポンス形式: application/json
        - レスポンスデータ:
            - 検索結果のリスト(list[MenuObject])
    """
    # ---検索クエリを取得する
    # クエリは小文字に変換しておく
    key=request.args.get('key', '').strip().lower()
    value=request.args.get('value', '').strip()#.lower()
    print(f"key: {key}, value: {value}")
    
    # ---クエリがない場合は空のリストを返す
    if not key or not value:
        return jsonify([])

    # ---メニューを検索する
    search_results=menu_all.find_menu_by_kv(key, value,search_type="partial")

    return jsonify(search_results)

# ----------
# ---メニューキャッシュの操作用API
# ----------
@app.route('/get_menu_cache', methods=['GET'])
def get_menu_cache():
    """メニューキャッシュを取得するAPI
    
    - リクエスト仕様
        - エンドポイント: /get_menu_cache
        - メソッド: GET
    
    - レスポンス仕様
        - レスポンス形式: application/json
        - レスポンスデータ:
            - cache: メニューキャッシュのリスト(list[MenuObject])
    """
    
    # ---メニューキャッシュを取得
    cache = menu_cache.get_cache()
    
    # ---レスポンスを返す
    return jsonify({
        'cache': cache
    })

@app.route('/add_menu_cache', methods=['POST'])
def add_menu_cache():
    """メニューキャッシュに追加するAPI
    
    - リクエスト仕様
        - エンドポイント: /add_menu_cache
        - メソッド: POST
        - パラメータ:
            - item: 追加するメニューアイテム(MenuObject)
    
    - レスポンス仕様
        - レスポンス形式: application/json
        - レスポンスデータ:
            - cache: 更新されたメニューキャッシュのリスト(list[MenuObject])
    """
    
    # ---リクエストデータを取得
    item = request.json.get('item') # MenuObjectを期待する
    
    # ---メニューキャッシュに追加
    menu_cache.add_cache(item)
    
    # ---追加後のメニューキャッシュを取得
    cache = menu_cache.get_cache()

    # ---[デバッグ用]メニューキャッシュをファイルに書き出す
    menu_cache.export_as_json("menu_cache.json")

    # ---レスポンスを返す
    return jsonify({
        'cache': cache
    })
    
@app.route('/remove_menu_cache', methods=['POST'])
def remove_menu_cache():
    """メニューキャッシュから削除するAPI
    
    - リクエスト仕様
        - エンドポイント: /remove_menu_cache
        - メソッド: POST
        - パラメータ:
            - item: 削除するメニューアイテム(MenuObject)
    
    - レスポンス仕様
        - レスポンス形式: application/json
        - レスポンスデータ:
            - cache: 更新されたメニューキャッシュのリスト(list[MenuObject])
    """
    # ---key, valueで検索し、当てはまるものを削除する
    key = request.json.get('key') # display_name, romaji, yolo_name, jan_code, priceのどれかを期待する
    value = request.json.get('value') # keyに対応する値を期待する
    print(f"key: {key}, value: {value}")
    
    searched_items = menu_cache.find_cache(key, value)
    
    # ---メニューキャッシュから削除
    for item in searched_items:
        try:
            menu_cache.remove_cache(item)
        except ValueError as e:
            print(f"Error: {e}")
            
    
    # ---削除後のメニューキャッシュを取得
    cache = menu_cache.get_cache()
    
    # ---レスポンスを返す
    return jsonify({
        'cache': cache
    })

# ----------
# ---最終的な結果をログに保存するAPI
# ----------
@app.route('/logging', methods=['POST'])
def logging():
    """最終的な結果をログに保存するAPI
    
    - リクエスト仕様
        - エンドポイント: /logging
        - メソッド: POST
        - パラメータ:
            - items: 検出されたメニューアイテムのリスト
            - total: 合計金額
    
    - レスポンス仕様
        - レスポンス形式: application/json
        - レスポンスデータ:
            - success: 成功したかどうか
    """
    """
    なにを受けるか？
    - 画像データ
    - item
        - ラベル
        - xyxy
    """
    
    # return jsonify({'success': True}) // [デバッグ用]
    
    # ---リクエストデータを取得
    request_data = request.json
    image_base64 = request_data.get('image')
    items = request_data.get('items')
    
    # ---ログに保存する処理を書く
    log_as_labelme(image_base64, items, TODAY_LOGGING_DIR)
    
    return jsonify({'success': True})

########################################################
##        　　　　　Pythonリクエスト関連　               ##
########################################################

# UUIDに対応したroomに参加
@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    emit('message', {'data': f'You have joined the room: {room}'}, room=room)

# クライアントからの実行要求を受け取る
@socketio.on('request_python_execution')
def handle_execution_request(data):
    # dataが辞書型であるため、'uuid' キーから値を取り出す
    uuid = int(data['uuid'])
    jan_cords = data['jan_codes']
    isHit=data['isHit']
    # データを1つの辞書にまとめる
    message_data = {
        'message': 'サーバーからPython実行を要求しています',
        'jan_cords': jan_cords,
        'isHit':isHit
    }
    
    # 同一のUUIDのクライアントすべてにメッセージを送信
    emit('run_python', message_data, room=uuid)
########################################################
##        　　　　　    管理ページ　               ##
########################################################
# /admin ページの表示
@app.route('/admin')
def admin():
    return render_template('admin.html')

# 正しいパスワード
ADMIN_PASSWORD = ENVVAL.ADMIN_PASSWORD

# パスワードを検証するエンドポイント
@app.route('/verify_password', methods=['POST'])
def verify_password():
    data = request.get_json()
    password = data.get('password')

    if password == ADMIN_PASSWORD:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})

# menu_cache.json をリセットする処理
@app.route('/reset_menu_cache', methods=['POST'])
def reset_menu_cache():
    try:
        # 空のオブジェクトをmenu_cache.jsonに書き込む
        with open('menu_cache.json', 'w', encoding='utf-8') as f:
            f.write("[\n]") 
        return jsonify({'success': True})
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return jsonify({'success': False})
    
########################################################
##        　　　　　    ルーレット動画　               ##
########################################################
@app.route('/get_random_video', methods=['GET'])
def get_random_video():
    video_type = request.args.get('type', 'miss')  # hit か miss を取得
    video_folder = os.path.join(app.root_path, 'static', 'videos', video_type)
    videos = [f for f in os.listdir(video_folder) if f.endswith(('.mp4', '.avi'))]

    if videos:
        random_video = random.choice(videos)
        video_url = url_for('static', filename=f'videos/{video_type}/{random_video}')
        return jsonify({'video_url': video_url})
    else:
        abort(404, description="動画が見つかりません")

@app.route('/run_hit_script', methods=['POST'])
def run_hit_script():
    try:
        # 特定のPythonファイルを実行 (例: hit_script.py)
        os.system('python3 hit_script.py')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 最後に実行する必要あり
if __name__ == '__main__':
    app.run(
        use_reloader=False,
        host='0.0.0.0', 
        port=7500, 
        ssl_context=(SSL_CRT, SSL_KEY)
    )
