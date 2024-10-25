from __future__ import annotations
from typing import TypedDict
import json


class Shape(TypedDict):
    label: str
    points: list[list[float]]
    group_id: str | None
    description: str
    shape_type: str
    flags: dict
    mask: str | None

    def __repr__(self):
        return f"Shape(label={self.label}, points={self.points})"


class LabelMeData:
    version: str
    flags: dict
    shapes: list[Shape]
    imagePath: str
    imageData: str
    imageHeight: int
    imageWidth: int

    def __init__(
        self,
        version: str,
        flags: dict,
        shapes: list[Shape],
        imagePath: str,
        imageData: str,
        imageHeight: int,
        imageWidth: int,
    ):
        self.version = version
        self.flags = flags
        self.shapes = shapes
        self.imagePath = imagePath
        self.imageData = imageData
        self.imageHeight = imageHeight
        self.imageWidth = imageWidth

    def __repr__(self):
        return f"LabelMeData(shapes={self.shapes}, imagePath={self.imagePath}, imageHeight={self.imageHeight}, imageWidth={self.imageWidth})"

    def export(self, save_path: str):
        self_object = {
            "version": self.version,
            "flags": self.flags,
            "shapes": [shape for shape in self.shapes],
            "imagePath": self.imagePath,
            "imageData": self.imageData,
            "imageHeight": self.imageHeight,
            "imageWidth": self.imageWidth,
        }
        # print(self_object)
        labelmedata_json = json.dumps(
            self_object,
            indent=4,
        )
        with open(save_path, "w") as f:
            f.write(labelmedata_json)

    @staticmethod
    def create_from_jsonfile(json_path: str) -> LabelMeData:
        new_labelmedata = LabelMeData("", {}, [], "", "", 0, 0)
        with open(json_path, "r") as f:
            labelmedata_json = json.load(f)
        new_labelmedata.version = labelmedata_json["version"]
        new_labelmedata.flags = labelmedata_json["flags"]
        new_labelmedata.shapes = [
            Shape(
                label=shape["label"],
                points=shape["points"],
                group_id=shape["group_id"],
                description=shape["description"],
                shape_type=shape["shape_type"],
                flags=shape["flags"],
                mask=shape["mask"],
            )
            for shape in labelmedata_json["shapes"]
        ]
        new_labelmedata.imagePath = labelmedata_json["imagePath"]
        new_labelmedata.imageData = labelmedata_json["imageData"]
        new_labelmedata.imageHeight = labelmedata_json["imageHeight"]
        new_labelmedata.imageWidth = labelmedata_json["imageWidth"]
        return new_labelmedata
