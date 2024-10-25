"""
# bluetooth-server.py
Bluetooth通信関係のモジュール。
ブラウザからのjanコードを受け取り、そのjanコードをbluetoothで送信する…とか
"""

import serial

from incomings.variables import EnvVariables

ENVVAL = EnvVariables()
SERIAL_PORT = ENVVAL.SERIAL_PORT


def send_jan_code(jan_code):
    """
    コマンドライン入力から取得したJANコードをESP32に送信する関数
    """
    # シリアル通信を設定 (ポート名とボーレートは環境に応じて変更してください)
    ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)  # ボーレートをESP32側と合わせる

    if ser.is_open:
        # コマンドラインで入力されたJANコードを送信
        command = f"{jan_code}\n"
        ser.write(command.encode("utf-8"))  # ESP32にJANコードを送信
        print(f"Sent JAN code: {jan_code}")

    ser.close()

###############################################
##               会計確定時の処理              ##
###############################################
# 確定メニューを処理してJANコードと共に返すエンドポイント
# TODO ここは無くなって、ブラウザからbluetooth-serverに送信するようになる感じ？？
# @app.route('/confirm_order', methods=['POST'])
# def confirm_order():
#     confirmed_menus = request.json.get('confirmed_menus', [])
#     if not confirmed_menus:
#         return jsonify({'error': 'No confirmed menus provided'}), 400

#     # 料理マスタを読み込む
#     menu = menu_all.menu

#     # 確定メニューに対応するJANコードとメニュー情報を収集
#     confirmed_items = []
    
#     for menu_name in confirmed_menus:
#         # menuの中でdisplay_nameが一致するJANコードを探す
#         found = False
#         """"
#         menuの形式: 
#         [
#             menu_code: {'jan_code':jan_code, 'display_name': display_name, 'price': price},
#         ]
#         """
        
#         for menu_code, item in menu.items(): # このforで、確定したメニューと、メニューデータ(CSV)を照合している
#             # itemの形式: {'jan_code':jan_code, 'display_name': display_name, 'price': price}
#             if item['display_name'] == menu_name:
#                 # itemからJANコードと価格を取得
#                 jan_code=item['jan_code']
#                 price = item['price']
                
#                 confirmed_items.append({
#                     'jan_code': jan_code,
#                     'price': price,
#                 })
                
#                 # 入力されたJANコードをESP32に送信
#                 send_jan_code(jan_code)
#                 print(f"\33[36m[confirm_order] jan_code: {jan_code}\33[0m")
#                 print("jancode", jan_code)
#                 print("confirmed_items", confirmed_items)

#                 found = True
#                 break

#         if not found:
#             confirmed_items.append({
#                 'display_name': menu_name,
#                 'jan_code': None,
#                 'price': 0
#             })
#     return jsonify({'confirmed_items': confirmed_items})