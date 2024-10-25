"""
# Yolov9Wrapper.py
Yolov9を使うやすくするためのラッパークラス

## 使い方
- はじめに
    - yolov9のリポジトリをクローンして、requirements.txtをインストールする

```py
from Yolov9Wrapper import Yolov9

# ---モデルの読み込み
model = Yolov9(weights="./20240625.pt")

# ---1枚の画像を推論する
result, times = model.predict_image("./20240625_5690.jpg")
# 結果を表示する
boxes = result["boxes"]
for box in boxes:
    label = box["label"]
    conf = box["confidence"]
    xyxy = box["xyxy"]
    print(label, conf, xyxy)
    
cv2.imshow("result", image)
cv2.waitKey(0)
cv2.destroyAllWindows()

# ---Webカメラのストリームを推論する
# コールバック関数を用意する
def on_detect(result:Yolov9Result):
    boxes = result["boxes"]
    for box in boxes:
        print(box["label"], box["confidence"], box["xyxy"])

model.predict_stream(0, on_detect=on_detect)


```

## のこりやること
- 🙆値の返却
    - bboxの画像
    - 結果のdict
        - ラベル
        - 確信度
        - bboxの座標
- 細かいところの調整
    - 画像の保存先の指定
    - 不要なコードの削除

## 更新履歴
- 20241012
    - np.ndarrayを直接推論できるようにした
    - Yolov9Annotatorを追加した
    - Yolov9Resultに、annotatorを追加した
        - あとからbbox描画ができるようにするため
- 20240728
    - 複数枚の画像を推論できるようにした
    - LabelMeDataを追加した
        - Yolov9ResultをLabelMeDataに変換する関数で、変換できるようにした
- 20240725
    - 値の返却をするようにした
    - `detect_stream()`を追加した
- 20240713
    - がりがり削り取った
    - 「のこりやること」が残っています……
    
"""

from pathlib import Path
import platform
from typing import Tuple

import numpy as np
import torch
import sys
import base64
import json
from tqdm import tqdm

print(f"\033[36m[YoloV9Wrapper] importing yolov9...\033[0m")
sys.path.append(r"./yolov9")
from yolov9.models.common import DetectMultiBackend
from yolov9.utils.dataloaders import LoadImages, LoadStreams
from yolov9.utils.general import (
    Profile,
    check_img_size,
    check_imshow,
    cv2,
    non_max_suppression,
    scale_boxes,
    xyxy2xywh,
)
from yolov9.utils.plots import Annotator, colors, save_one_box
from yolov9.utils.torch_utils import select_device, smart_inference_mode

print(f"\033[36m[YoloV9Wrapper] imported yolov9!\033[0m")

from typing import TypedDict

from Yolov9Wrapper.LabelMeData import LabelMeData, Shape


class Yolov9Annotator:
    def __init__(
        self,
        image: np.ndarray,
        line_width: int = None,
        font_size: float = None,
        font: str = "Arial.ttf",
        pil: bool = False,
        names: dict[int, str] = {0: "label_name"},
    ) -> None:
        """Yolov9の結果を描画するためのクラス

        Args:
            image (np.ndarray): 描画する画像
            line_width (int, optional): bboxの線の太さ. Defaults to None.
            font_size (float, optional): フォントサイズ. Defaults to None.
            font (str, optional): フォント. Defaults to "Arial.ttf".
            pil (bool, optional): 不明。 Defaults to False.
            names (list[str], optional): ラベルのリスト. Defaults to None.
        """
        self.annotator = Annotator(
            image,
            line_width=line_width,
            font_size=font_size,
            font=font,
            pil=pil,
            example=str(names),
        )
        self.names = names
        self.image = image

    def box_label(
        self,
        box: tuple[float, float, float, float],
        label="",
        color=(128, 128, 128),
        txt_color=(255, 255, 255),
    ):
        """画像にbboxを描画する

        Args:
            box (tuple[float, float, float, float]): bboxの座標(0-1)
            label (str, optional): ラベル. Defaults to "".
            color (tuple, optional): bboxの色. Defaults to (128, 128, 128).
            txt_color (tuple, optional): テキストの色. Defaults to (255, 255, 255).
        """
        self.annotator.box_label(box, label, color, txt_color)

    def result(self) -> np.ndarray:
        """描画した画像を返す

        Returns:
            np.ndarray: 描画した画像
        """
        return self.annotator.result()
    
    def get_color(self, label: str) -> tuple[int, int, int]:
        """ラベルに対応する色を返す

        Args:
            label (str): ラベル

        Returns:
            tuple[int, int, int]: 色
        """
        color_index = 0
        for index, name in self.names.items():
            if name == label:
                color_index = index
                break
        return colors(index, True)


class Yolov9ResultBox(TypedDict):
    """Yolov9の推論結果のbboxを保存するクラス

    example:
    下のような形で保存される
    ```json
    {
        "label": str,  # ラベル
        "confidence": float,  # 確信度
        "xyxy": Tuple[float, float, float, float],  # bboxの座標(0-1)
    }
    ```

    """

    label: str  # ラベル
    confidence: float  # 確信度
    xyxy: Tuple[float, float, float, float]  # bboxの座標(0-1)

    def __repr__(self):
        return f"Yolov9ResultBox(label={self.label}, confidence={self.confidence}, bbox={self.xyxy})"


class Yolov9Result(TypedDict):
    """Yolov9の推論結果を保存するクラス

    example:
    下のような形で保存される
    ```json
    {
        "image": np.ndarray,  # bboxの画像
        "path": str|None,  # 画像のパス。numpyの場合はNone
        "boxes": [
            {
                "label": str,  # ラベル
                "confidence": float,  # 確信度
                "xyxy": Tuple[float, float, float, float],  # bboxの座標(0-1)
            }
        ],
        "annotator": Yolov9Annotator  # annotator
    }
    ```

    """

    image: np.ndarray  # bboxの画像
    path: str  # 画像のパス
    boxes: list[Yolov9ResultBox]  # bboxのリスト
    annotator: Yolov9Annotator  # annotator

    def __repr__(self):
        return f"Yolov9Result(image={self.image}, path={self.path}, boxes={self.boxes})"


def convert_to_labelme(yolov9_result: Yolov9Result) -> LabelMeData:
    """Yolov9ResultをLabelMeDataに変換する"""
    image_height, image_width = yolov9_result["image"].shape[:2]
    shapes: list[Shape] = []
    for box in yolov9_result["boxes"]:
        label = box["label"]
        xyxy = box["xyxy"]
        points = [
            [xyxy[0] * image_width, xyxy[1] * image_height],
            [xyxy[2] * image_width, xyxy[3] * image_height],
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

    with open(yolov9_result["path"], "rb") as f:
        base64_image_data = base64.b64encode(f.read()).decode("utf-8")

    labelme_data = LabelMeData(
        version="5.5.0",
        flags={},
        shapes=shapes,
        imagePath=yolov9_result["path"],
        imageData=base64_image_data,
        imageHeight=image_height,
        imageWidth=image_width,
    )

    return labelme_data


class Yolov9:
    def __init__(
        self,
        weights: str,  # model path
        device="",  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        data="./yolov9/data/coco.yaml",  # dataset.yaml path
        dnn=False,  # use OpenCV DNN for ONNX inference
        half=False,  # FP16 half-precision inference
    ) -> None:
        self.weights = weights
        self.device = device
        self.data = data
        self.dnn = dnn
        self.half = half
        # ---モデルの読み込み
        self.device = select_device(device)
        self.model = DetectMultiBackend(
            self.weights,
            device=self.device,
            dnn=self.dnn,
            data=self.data,
            fp16=self.half,
        )

    @smart_inference_mode()
    def predict_image(
        self,
        images: str | list[str] | np.ndarray | list[np.ndarray],  # image path
        save_dir: str | None = None,  # save image path
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
    ) -> Tuple[list[Yolov9Result], Tuple[float, float, float]]:
        """1枚の画像を推論する

        Args(主なもの):
            image (str | list[str]): 画像のパス
            save_dir (str | None): 保存先のパス

        Returns:
            Tuple[Yolov9Result, Tuple[float, float, float]]: 推論結果と処理時間
        """
        # ---モデルの読み込み
        stride, names, pt = self.model.stride, self.model.names, self.model.pt

        # ---画像の読み込み
        imgsz = check_img_size(imgsz, s=stride)  # check image size
        dataset = LoadImages(images, img_size=imgsz, stride=stride, auto=pt)

        # ---推論の実行
        self.model.warmup(imgsz=(1, 3, *imgsz))

        # Profileのdtは、時間を計測するためのやつ。
        dt = (Profile(), Profile(), Profile())

        results: list[Yolov9Result] = []
        for path, im, im0s, _, _ in tqdm(dataset, desc="Detecting objects"):
            # print("\033[31m", "="*20, "\033[0m")
            # ---画像の前処理
            with dt[0]:
                im = torch.from_numpy(im).to(self.model.device)
                im = im.half() if self.model.fp16 else im.float()  # uint8 to fp16/32
                im /= 255  # 0 - 255 to 0.0 - 1.0
                if len(im.shape) == 3:
                    im = im[None]  # expand for batch dim

            # ---実際の推論
            with dt[1]:
                pred = self.model(im, augment=augment)

            # ---NMS。推論されたbboxを整理する処理らしい。簡単に言うと、重複しているbboxを削除する処理。
            with dt[2]:
                pred = non_max_suppression(
                    pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det
                )

            # ---結果の表示
            # det = pred[0]
            result: Yolov9Result = Yolov9Result()  # 推論結果を保存するクラス
            for det in pred:  # pred、len(pred)=1確定じゃね？
                # print("\033[32m", "="*20, "\033[0m")
                p, im0, frame = path, im0s.copy(), getattr(dataset, "frame", 0)

                if type(p) == str:
                    p = Path(p)  # to Path
                elif isinstance(p, np.ndarray):
                    p = ""

                gn = torch.tensor(im0.shape)[
                    [1, 0, 1, 0]
                ]  # 幅、高さを0-1にするための値

                # ---annotatorの初期化
                # annotator = Annotator(
                #     im0, line_width=line_thickness, example=str(names)
                # )
                annotator = Yolov9Annotator(im0, line_width=line_thickness, names=names)
                im0_copy=im0.copy()
                annotator_new=Yolov9Annotator(im0_copy, line_width=line_thickness, names=names)

                box_results: list[Yolov9ResultBox] = []  # 各bboxの結果を保存するリスト
                if len(det):
                    # Rescale boxes from img_size to im0 size
                    det[:, :4] = scale_boxes(
                        im.shape[2:], det[:, :4], im0.shape
                    ).round()

                    # ---各検出bboxに対して処理する
                    for *xyxy, conf, cls in reversed(det):
                        x_sorted = sorted([xyxy[0], xyxy[2]])
                        y_sorted = sorted([xyxy[1], xyxy[3]])
                        new_xyxy = [x_sorted[0], y_sorted[0], x_sorted[1], y_sorted[1]]
                        xywh = (
                            (xyxy2xywh(torch.tensor(new_xyxy).view(1, 4)) / gn)
                            .view(-1)
                            .tolist()
                        )  # normalized xywh
                        normalized_xyxy = (
                            (torch.tensor(new_xyxy).view(1, 4) / gn).view(-1).tolist()
                        )
                        # print(f"{names[int(cls)]} {conf:.2f} {xywh}")

                        # ---bboxの描画
                        c = int(cls)
                        label = (
                            None
                            if hide_labels
                            else (names[c] if hide_conf else f"{names[c]} {conf:.2f}")
                        )
                        color=colors(c, True)
                        annotator.box_label(new_xyxy, label, color=color)

                        # ---bboxの結果を追加
                        box_results.append(
                            {
                                "label": names[int(cls)],
                                "confidence": float(conf),
                                "xyxy": normalized_xyxy,
                            }
                        )
                        # ---1つのbboxを保存する処理っぽい
                        # save_one_box(new_xyxy, imc, file=save_dir / 'crops' /
                        #              names[c] / f'{p.stem}.jpg', BGR=True)

                    # Save results (image with detections)
                    if save_dir:
                        save_path = f"{save_dir}/{p.stem}.jpg"
                        cv2.imwrite(save_path, im0)
                im0 = annotator.result()

                # ---result(1画像の結果)を用意
                result["image"] = im0
                result["path"] = str(p) if type(p) == Path else None
                result["boxes"] = box_results
                result["annotator"] = annotator_new  # 追記用にannotatorも返す

                # ---results(全画像の結果)に追加
                results.append(result)

        # ---処理時間の計測
        t = tuple(x.t * 1e3 for x in dt)  # speeds per image
        # LOGGER.info(
        #     f"Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}"
        #     % t
        # )
        return results, t

    @smart_inference_mode()
    def predict_stream(
        self,
        video_index: int,
        on_detect: callable = None,
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        vid_stride=1,  # video frame-rate stride
    ):
        # ---モデルの読み込み
        stride, names, pt = self.model.stride, self.model.names, self.model.pt

        # ---ストリームの読み込み
        view_img = check_imshow(warn=True)
        dataset = LoadStreams(
            str(video_index),
            img_size=imgsz,
            stride=stride,
            auto=pt,
            vid_stride=vid_stride,
        )
        bs = len(dataset)

        # ---推論の実行
        self.model.warmup(
            imgsz=(1 if pt or self.model.triton else bs, 3, *imgsz)
        )  # warmup

        seen, windows, dt = 0, [], (Profile(), Profile(), Profile())

        for path, im, im0s, _, _ in dataset:
            # ---画像の前処理
            with dt[0]:
                im = torch.from_numpy(im).to(self.model.device)
                im = im.half() if self.model.fp16 else im.float()  # uint8 to fp16/32
                im /= 255  # 0 - 255 to 0.0 - 1.0
                if len(im.shape) == 3:
                    im = im[None]  # expand for batch dim

            # ---実際の推論
            with dt[1]:
                pred = self.model(im, augment=augment)

            # ---NMS。推論されたbboxを整理する処理らしい。簡単に言うと、重複しているbboxを削除する処理。
            with dt[2]:
                pred = non_max_suppression(
                    pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det
                )

            # ---各bbox結果の表示
            for i, det in enumerate(pred):
                result: Yolov9Result = Yolov9Result()
                seen += 1
                p, im0, _ = path[i], im0s[i].copy(), dataset.count

                p = Path(p)  # to Path
                gn = torch.tensor(im0.shape)[
                    [1, 0, 1, 0]
                ]  # 幅、高さを0-1にするための値
                annotator = Annotator(
                    im0, line_width=line_thickness, example=str(names)
                )
                box_results: list[Yolov9ResultBox] = []  # 各bboxの結果を保存するリスト
                if len(det):
                    # Rescale boxes from img_size to im0 size
                    det[:, :4] = scale_boxes(
                        im.shape[2:], det[:, :4], im0.shape
                    ).round()

                    # ---各検出bboxに対して処理する
                    for *xyxy, conf, cls in reversed(det):
                        x_sorted = sorted([xyxy[0], xyxy[2]])
                        y_sorted = sorted([xyxy[1], xyxy[3]])
                        new_xyxy = [x_sorted[0], y_sorted[0], x_sorted[1], y_sorted[1]]
                        xywh = (
                            (xyxy2xywh(torch.tensor(new_xyxy).view(1, 4)) / gn)
                            .view(-1)
                            .tolist()
                        )  # normalized xywh
                        normalized_xyxy = (
                            (torch.tensor(new_xyxy).view(1, 4) / gn).view(-1).tolist()
                        )
                        # print(f"{names[int(cls)]} {conf:.2f} {xywh}")

                        # ---bboxの描画
                        c = int(cls)
                        label = (
                            None
                            if hide_labels
                            else (names[c] if hide_conf else f"{names[c]} {conf:.2f}")
                        )
                        annotator.box_label(new_xyxy, label, color=colors(c, True))

                        # ---bboxの結果を追加
                        box_results.append(
                            {
                                "label": names[int(cls)],
                                "confidence": float(conf),
                                "xyxy": normalized_xyxy,
                            }
                        )

                im0 = annotator.result()
                # ---映像の表示
                if view_img:
                    if platform.system() == "Linux" and p not in windows:
                        windows.append(p)
                        cv2.namedWindow(
                            str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO
                        )  # allow window resize (Linux)
                        cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
                    cv2.imshow(str(p), im0)
                    cv2.waitKey(1)  # 1 millisecond

                result["image"] = im0
                result["path"] = ""
                result["boxes"] = box_results

                if on_detect is not None and len(box_results) > 0:
                    on_detect(result)

            # ---各フレームの処理時間の表示
            t = dt[1].dt * 1e3  # ms
            print(t)

        # ---処理時間の計測
        t = tuple(x.t * 1e3 for x in dt)  # speeds per image
        # LOGGER.info(
        #     f"Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}"
        #     % t
        # )
        return result, t
