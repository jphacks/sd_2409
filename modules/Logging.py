import base64
from typing import Tuple, TypedDict

import cv2
import numpy as np
from Yolov9Wrapper.LabelMeData import LabelMeData, Shape
from datetime import datetime
import os


class Box(TypedDict):
    """最終結果のbboxを表すデータクラス。"""

    label: str
    xyxy: Tuple[float, float, float, float]

    pass


def log_as_labelme(
    image_base64: str,
    boxes: list[Box],
    save_dir: str,
):
    # ---クライアント側での確認(修正)が完了した、最終結果をLabelMe形式で保存する

    # ---ログファイルの名前(拡張子なし)を作成する
    output_name = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ---ディレクトリが存在しない場合は作成する
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # ---画像を保存する
    image = base64.b64decode(image_base64)
    image_save_path = os.path.join(save_dir, f"{output_name}.jpg")
    cv2.imwrite(image_save_path, image)
    # ---画像のサイズを取得する
    nparr = np.frombuffer(image, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    height, width = img.shape[:2]

    # ---Shapeを作成する
    shapes: list[Shape] = []
    for box in boxes:
        label = box["label"]
        xyxy = box["xyxy"]
        points = [
            [xyxy[0] * width, xyxy[1] * height],
            [xyxy[2] * width, xyxy[3] * height],
        ]
        shape = Shape(
            label=label,
            points=points,
            group_id=None,
            description="",
            shape_type="rectangle",
            flags={},
            mask=None,
        )
        shapes.append(shape)

    # ---LabelMeDataを作成する
    label_me_data_path = os.path.join(save_dir, f"{output_name}.json")
    label_me_data = LabelMeData(
        version="5.5.0",
        flags={},
        shapes=shapes,
        imagePath=image_save_path,
        imageData=image_base64,
        imageHeight=height,
        imageWidth=width,
    )
    label_me_data.export(label_me_data_path)
    
    return label_me_data_path
