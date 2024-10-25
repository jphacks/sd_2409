"""
# inference.py
推論→推論結果補正(お皿と商品のペアで)関係のモジュール。
inference_osara_shohin関数とか
"""

from typing import TypedDict
import numpy as np

from Yolov9Wrapper.Yolov9Wrapper import Yolov9, Yolov9ResultBox
from modules.Types import OsaraShohinResult, OsaraShohinResultBox


# ----------
# ---推論・補正
# ----------
class Osara_Shohin_Pair(TypedDict):
    """お皿と商品(料理)のペアを表すデータクラス。
    どのお皿にどの商品が乗っているか？
    """

    osara: Yolov9ResultBox
    shohin: Yolov9ResultBox
    osara_area: float


def inference_osara_shohin(
    frame: np.ndarray, MODEL_OSARA: Yolov9, MODEL_SHOHIN: Yolov9
) -> OsaraShohinResult:
    """お皿と商品(料理)のペアを意識して推論→補正し、質の良い結果を返す

    Args:
        frame (np.ndarray): 推論する画像
        MODEL_OSARA (Yolov9): お皿認識用のYOLOv9モデル
        MODEL_SHOHIN (Yolov9): 商品(料理)認識用のYOLOv9モデル

    Returns:
        OsaraShohinResult: お皿と商品(料理)のペアを意識して推論→補正した結果
    """
    # ----------
    # ---推論する
    # ----------
    # Yolov9Wrapperを使うようにした
    _result_osara, _ = MODEL_OSARA.predict_image(frame)
    _result_shohin, _ = MODEL_SHOHIN.predict_image(frame)
    result_osara = _result_osara[0]  # 1枚だけの推論なので、[0]を指定する
    result_shohin = _result_shohin[0]

    # ----------
    # ---お皿と料理を紐付ける(associate_dis_with_foodに対応する部分)
    # ----------
    # お皿に乗っている料理はなにか？を紐付ける
    # 料理がない場合、皿だけを返す

    # お皿と料理の組み合わせを格納するリスト
    osara_shohin_pairs: list[Osara_Shohin_Pair] = []
    # ---しきい値を設定する
    # お皿と料理の中心座標の距離が、この値以下の場合に紐づける
    OSARA_SHOHIN_DISTANCE_THRESHOLD = 0.3
    for osara in result_osara["boxes"]:  # 各お皿に対して
        print(f"\33[36m[inference_osara_shohin] result_osara:\n{osara}\33[0m")
        # ---既に紐づけられたものはスキップ
        if "associated" in osara:
            continue

        # ---お皿の座標を取得する
        osara_top_left = (osara["xyxy"][0], osara["xyxy"][1])
        osara_bottom_right = (osara["xyxy"][2], osara["xyxy"][3])

        # ---お皿の中心座標・面積を計算する
        osara_center = (
            (osara_top_left[0] + osara_bottom_right[0]) / 2,
            (osara_top_left[1] + osara_bottom_right[1]) / 2,
        )
        osara_area = (osara_bottom_right[0] - osara_top_left[0]) * (
            osara_bottom_right[1] - osara_top_left[1]
        )

        # ---指定距離内で最も信頼度が高い料理を探す
        # (料理, 皿)。料理とお皿の組み合わせの、紐づけ候補
        candidate_pair: tuple[Yolov9ResultBox, Yolov9ResultBox] = None
        max_confidence = -float("inf")
        # min_distance=float('inf')
        for shohin in result_shohin["boxes"]:  # 各料理に対して
            print(f"\33[36m[inference_osara_shohin] result_shohin:\n{shohin}\33[0m")
            # ---既に紐づけられたものはスキップ
            if "associated" in shohin:
                continue

            # ---料理の座標を取得する、中心座標・面積を計算する
            shohin_top_left = (shohin["xyxy"][0], shohin["xyxy"][1])
            shohin_bottom_right = (shohin["xyxy"][2], shohin["xyxy"][3])
            shohin_center = (
                (shohin_top_left[0] + shohin_bottom_right[0]) / 2,
                (shohin_top_left[1] + shohin_bottom_right[1]) / 2,
            )
            shohin_area = (shohin_bottom_right[0] - shohin_top_left[0]) * (
                shohin_bottom_right[1] - shohin_top_left[1]
            )

            # ---お皿と料理の距離を計算する
            distance = np.sqrt(
                (osara_center[0] - shohin_center[0]) ** 2
                + (osara_center[1] - shohin_center[1]) ** 2
            )
            print(
                f"\33[36m[inference_osara_shohin]\ndistance: {distance}\nconfidence: {shohin['confidence']}\nmax_confidence: {max_confidence}\33[0m"
            )

            # ---紐づけの判定
            # 距離がしきい値以下かつ最小、信頼度が最大の場合
            if (
                distance < OSARA_SHOHIN_DISTANCE_THRESHOLD
                and shohin["confidence"] > max_confidence
            ):
                # ---値の更新
                max_confidence = shohin["confidence"]  # 最も大きい信頼度の更新
                candidate_pair = (shohin, osara)  # お皿と料理の組み合わせを更新

        # ---紐づけ候補が見つかった場合、紐づける
        if candidate_pair is not None:
            shohin, osara = candidate_pair
            osara_shohin_pairs.append(
                {
                    "osara": osara,
                    "shohin": shohin,
                    "area": osara_area,
                }
            )

            # ---紐づけられた料理にフラグを立てる
            shohin["associated"] = True
            osara["associated"] = True
        else:
            # ---紐づけられなかった場合、お皿のみを返す
            osara_shohin_pairs.append(
                {
                    "osara": osara,
                    "shohin": None,
                    "area": osara_area,
                }
            )

    # ---associatedフラグを削除する
    for box in result_osara["boxes"]:
        if "associated" in box:
            del box["associated"]
    for box in result_shohin["boxes"]:
        if "associated" in box:
            del box["associated"]

    # ----------
    # ---お皿と料理が紐づいたもののみを描画する(process_associated_detectionsに対応する部分)
    # ----------
    annotator = result_shohin["annotator"]
    # 画像の幅・高さを取得する
    height, width, _ = result_shohin["image"].shape

    result_boxes: list[OsaraShohinResultBox] = []
    print(
        f"\33[31m[inference_osara_shohin] osara_shohin_pairs:\n{osara_shohin_pairs}\33[0m"
    )
    for pair in osara_shohin_pairs:
        if pair["shohin"] is not None:  # お皿と料理が紐づいている場合
            # ---描画用の各種パラメータを取得する
            shohin: Yolov9ResultBox = pair["shohin"]
            box = [
                int(shohin["xyxy"][0] * width),
                int(shohin["xyxy"][1] * height),
                int(shohin["xyxy"][2] * width),
                int(shohin["xyxy"][3] * height),
            ]
            label = f'{shohin["label"]} {shohin["confidence"]:.2f}' # 14395 0.96
            color = annotator.get_color(shohin["label"])

            # ---描画する
            annotator.box_label(box, label, color)

            # ---[返却用]result_boxesに追加する
            new_box: OsaraShohinResultBox = {
                "label": shohin["label"],
                "osara_type": pair["osara"]["label"],
                "confidence": shohin["confidence"],
                "xyxy": shohin["xyxy"],
                "menu_object": None,
            }
            result_boxes.append(new_box)

        else:  # お皿と料理が紐づいていない場合
            osara: Yolov9ResultBox = pair["osara"]
            box = [
                int(osara["xyxy"][0] * width),
                int(osara["xyxy"][1] * height),
                int(osara["xyxy"][2] * width),
                int(osara["xyxy"][3] * height),
            ]
            label = f'{osara["label"]} {osara["confidence"]:.2f}'
            color = annotator.get_color(osara["label"])
            color = (0, 0, 0)  # まっくろ

            # ---描画する
            annotator.box_label(box, label, color)

            # ---[返却用]result_boxesに追加する
            new_box: OsaraShohinResultBox = {
                "label": None,
                "osara_type": osara["label"],
                "confidence": osara["confidence"],
                "xyxy": osara["xyxy"],
                "menu_object": None,
            }
            result_boxes.append(new_box)

    result_image = annotator.result()

    # ---Yolov9Resultを返す
    new_shohin_result: OsaraShohinResult = {
        "image": result_image,
        "path": None,
        "boxes": result_boxes,
    }
    return new_shohin_result
