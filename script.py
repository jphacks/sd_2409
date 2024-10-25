import serial
import sys
from incomings.variables import EnvVariables

ENVVAL = EnvVariables()
SERIAL_PORT = ENVVAL.SERIAL_PORT

def send_jan_codes(jan_codes):
    """
    コマンドライン入力から取得したJANコードをESP32に一つずつ送信する関数
    """
    ser = serial.Serial(SERIAL_PORT, 115200)  # ボーレートをESP32側と合わせる

    if ser.is_open:
        print("open成功")
        for jan_code in jan_codes:
            command = f"{jan_code}\n"
            ser.write(command.encode("utf-8"))  # ESP32にJANコードを送信
            print(f"Sent JAN code: {jan_code}")
    else:
        print("open失敗")

    ser.close()

if __name__ == "__main__":
    # コマンドライン引数を取得
    if len(sys.argv) > 1:
        jan_codes = sys.argv[1].split(',')  # カンマ区切りで分割
        print(jan_codes)
        send_jan_codes(jan_codes)
    else:
        print("JANコードが指定されていません")
