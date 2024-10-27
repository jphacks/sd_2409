"""
# Types.py
各種データクラスを定義するモジュール。

MenuObject, OsaraShohinResultBox, OsaraShohinResultの3つのデータクラスを定義する。
"""

from typing import Literal, Tuple, TypedDict
import numpy as np


# ----------
# ---メニューのデータクラス
# ----------
class Nutrition(TypedDict):
    """栄養成分を格納するデータクラス。

    Example:
    下のような形で保存される
    ```json
    {
        "energy": float,  # エネルギー(kcal)
        "protein": float,  # たんぱく質(g)
        "fat": float,  # 脂質(g)
        "carbohydrates": float,  # 炭水化物(g)
        "fiber": float,  # 食物繊維(g)
        "vegetables": float,  # 野菜(g)
    }
    ```
    """

    energy: float  # エネルギー(kcal)
    protein: float  # たんぱく質(g)
    fat: float  # 脂質(g)
    carbohydrates: float  # 炭水化物(g)
    fiber: float  # 食物繊維(g)
    vegetables: float  # 野菜(g)


class MenuObject(TypedDict):
    """メニューの情報を格納するデータクラス。

    Example:
    下のような形で保存される
    ```json
    {
        "menu_code": str,  # メニューコード。「212080」
        "display_name": str,  # 表示名。「自家製カレー」
        "romaji": str,  # ローマ字。「JIKASEI KARE」
        "yolo_name": str,  # YOLOモデルの学習名。「homemade_curry」
        "jan_code": str,  # JANコード「2121052120800」
        "price": int,  # 価格。「341」
        "nutrition": {
            "energy": float,  # エネルギー(kcal)
            "protein": float,  # たんぱく質(g)
            "fat": float,  # 脂質(g)
            "carbohydrates": float,  # 炭水化物(g)
            "fiber": float,  # 食物繊維(g)
            "vegetables": float,  # 野菜(g)
        }
    }

    """

    menu_code: str  # メニューコード。「212080」
    display_name: str  # 表示名。「自家製カレー」
    romaji: str  # ローマ字。「JIKASEI KARE」
    yolo_name: str  # YOLOモデルの学習名。「homemade_curry」
    jan_code: str  # JANコード「2121052120800」
    price: int  # 価格。「341」
    nutrition: Nutrition  # 栄養成分


# ----------
# ---推論→補正結果のデータクラス
# ----------
class OsaraShohinResultBox(TypedDict):
    """お皿と商品(料理)のペアを意識して推論→補正した結果の、各商品を格納するデータクラス。

    Example:
    下のような形で保存される
    ```json
    {
        "label": str,  # ラベル
        "osara_type": Literal["DON", "CURRY", "RICE"]| None,  # お皿の種類
        "confidence": float,  # 確信度
        "xyxy": Tuple[float, float, float, float],  # bboxの座標(0-1)
        "menu_object": MenuObject  # メニューオブジェクト
    }
    ```
    """

    label: str  # ラベル
    osara_type: Literal["DON", "CURRY", "RICE"] | None  # お皿の種類
    confidence: float  # 確信度
    xyxy: Tuple[float, float, float, float]  # bboxの座標(0-1)
    menu_object: MenuObject  # メニューオブジェクト

    def __repr__(self):
        return f"OsaraShohinResultBox(label={self.label}, osara_type={self.osara_type}, confidence={self.confidence}, bbox={self.xyxy})"


class OsaraShohinResult(TypedDict):
    """お皿と商品(料理)のペアを意識して推論→補正した結果を格納するデータクラス。

    Example:
    下のような形で保存される
    ```json
    {
        "image": np.ndarray,  # bboxの画像
        "path": str|None,  # 画像のパス。numpyの場合はNone
        "boxes": [
            {
                "label": str,  # ラベル
                "osara_type": Literal["DON", "CURRY", "RICE"]| None,  # お皿の種類
                "confidence": float,  # 確信度
                "xyxy": Tuple[float, float, float, float],  # bboxの座標(0-1)
                "menu_object": {
                    "menu_code": str,  # メニューコード。「212080」
                    "display_name": str,  # 表示名。「自家製カレー」
                    "romaji": str,  # ローマ字。「JIKASEI KARE」
                    "yolo_name": str,  # YOLOモデルの学習名。「homemade_curry」
                    "jan_code": str,  # JANコード「2121052120800」
                    "price": int,  # 価格。「341」
                }
            }
        ],
    }
    ```

    """

    image: np.ndarray  # bboxの画像
    path: str  # 画像のパス
    boxes: list[OsaraShohinResultBox]  # bboxのリスト

    def __repr__(self):
        return f"OsaraShohinResult(image={self.image}, path={self.path}, boxes={self.boxes})"
