from datetime import datetime
from typing import TypedDict
import random
import base64
from modules.Types import MenuObject


voice_data = {
    "random": [
        {
            "voice": "いらっしゃいませなのだ",
            "voice_path": "jph/voices/01_いらっしゃいませなのだ.wav",
        },
        {
            "voice": "箸とかスプーンとか、忘れずにもっていくのだ",
            "voice_path": "jph/voices/06_箸とかスプーンとか、忘れずにもっていくのだ.wav",
        },
    ],
    "menu": [
        {
            "condition": "display_name",
            "value": "自家製カレー",
            "voice": "自家製カレーのご注文、ありがとうなのだ",
            "voice_path": "jph/voices/02_自家製カレーのご注文、ありがとうなのだ.wav",
        }
    ],
    "time": [
        {
            "condition": "time",
            "value": "12",
            "voice": "授業お疲れ様なのだ",
            "voice_path": "jph/voices/04_授業お疲れ様なのだ.wav",
        },
    ],
}


class VoiceData(TypedDict):
    voice: str
    voice_path: str


def choose_voice(menu_objects: list[MenuObject]) -> VoiceData:
    # 時間、メニュー、ランダムから、条件に合う音声を選択する

    # ---メニューから音声候補を選ぶ
    menu_voice_candidates: list[VoiceData] = []
    if len(menu_objects) == 0:
        return {"voice": "うまく見えなかったのだ。もう一度撮影してみてほしいのだ", "voice_path": "jph/voices/07_見えない.wav"}
    # ---各音声候補に対して、forで見ていく
    for menu_voice in voice_data["menu"]:
        condition = menu_voice["condition"]
        value = menu_voice["value"]
        voice = menu_voice["voice"]
        voice_path = menu_voice["voice_path"]

        # ---入力されたメニュー情報から判定する
        for menu_object in menu_objects:
            # そのmenu_objectのcondition属性が、valueに部分一致するか？
            if menu_object is None:
                continue
            if value in menu_object[condition]:
                menu_voice_candidates.append({"voice": voice, "voice_path": voice_path})
                break
    print(f"\x1b[32m{menu_voice_candidates}\x1b[0m")

    # ---ランダムから音声候補を選ぶ
    random_voice_candidates: list[VoiceData] = []

    choice = random.choice(voice_data["random"])
    random_voice_candidates.append(
        {"voice": choice["voice"], "voice_path": choice["voice_path"]}
    )
    print(f"\x1b[32m{random_voice_candidates}\x1b[0m")

    # ---時間から音声候補を選ぶ
    time_voice_candidates: list[VoiceData] = []
    current_time = datetime.now().strftime("%H")
    for time_voice in voice_data["time"]:
        condition = time_voice["condition"]
        value = time_voice["value"]
        voice = time_voice["voice"]
        voice_path = time_voice["voice_path"]

        if current_time == value:
            time_voice_candidates.append({"voice": voice, "voice_path": voice_path})
    print(f"\x1b[32m{time_voice_candidates}\x1b[0m")

    # ---音声候補を統合する
    voice_candidates = (
        menu_voice_candidates + random_voice_candidates + time_voice_candidates
    )
    # ---音声候補からランダムに選ぶ
    choice = random.choice(voice_candidates)
    print(f"\x1b[32m{choice}\x1b[0m")

    # ---選ばれた音声を返す
    return choice


def encode_voice_data(voice_data: VoiceData) -> str:
    # VoiceDataを、base64でエンコードして返す
    with open(voice_data["voice_path"], "rb") as f:
        voice_binary = f.read()
    voice_base64 = base64.b64encode(voice_binary).decode("utf-8")
    return voice_base64
