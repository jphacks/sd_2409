"""
# menu.py
メニューの操作関係のモジュール。
Menuクラス、MenuObjectクラスとか
"""

import csv
from typing import Literal, Tuple

from modules.Types import MenuObject, OsaraShohinResult


class Menu:
    def __init__(self):
        self.menu: dict[str, MenuObject] = {}  # メニュー情報を保持する辞書

    def load_menu(
        self, csv_file_path: str, csv_encoding: str = "utf-8"
    ) -> dict[str, MenuObject]:
        """ CSVファイルからメニューを読み込み、self.menuに格納する

        Returns:
            menu: メニュー情報を保持する辞書。以下のような形式(MenuObject)で保持される。
            {
                'メニューコード': {'jan_code': 'JANコード', 'display_name': '表示名', 'romaji': 'ローマ字', 'price': 価格, 
                'energy': 'エネルギー', 'protein': 'タンパク質', 'fat': '脂質', 'carbohydrates': '炭水化物', 'fiber': '食物繊維', 'vegetables': '野菜量', 'yolo_name': 検出名, },
                ...
            }
        """
        menu: dict[str, MenuObject] = {}
        with open(csv_file_path, mode="r", encoding=csv_encoding) as csvfile:
            reader = csv.DictReader(csvfile)
            # ヘッダーから列名を特定
            for field in reader.fieldnames:
                if "料理コード" in field:
                    menu_code_column = field
                elif "JANコード" in field:
                    jan_code_column = field
                elif "お客様向け名称" in field:
                    display_name_column = field
                elif "ローマ字" in field:
                    romaji_column = field
                elif "販売価格(税込)" in field:
                    price_column = field
                elif "エネルギー" in field:
                    energy_column = field
                elif "タンパク質" in field:
                    protein_column = field
                elif "脂質" in field:
                    fat_column = field
                elif "炭水化物" in field:
                    carbohydrates_column = field
                elif "食物繊維" in field:
                    fiber_column = field
                elif "野菜量" in field:
                    vegetables_column = field
                elif "検出名" in field:
                    yoloname_column = field

            if not (
                menu_code_column
                and jan_code_column
                and display_name_column
                and romaji_column
                and price_column
                and energy_column
                and protein_column
                and fat_column
                and carbohydrates_column
            ):
                raise ValueError(
                    "必要な列が見つかりませんでした。"
                )

            for row in reader:
                menu_code = str(int(row[menu_code_column].strip()))
                display_name = row[display_name_column].strip()
                romaji = row[romaji_column].strip()
                jan_code = row[jan_code_column].strip()
                price = int(row[price_column].strip())
                energy = row[energy_column].strip()
                protein = row[protein_column].strip() 
                fat = row[fat_column].strip() 
                carbohydrates = row[carbohydrates_column].strip() 
                fiber = row[fiber_column].strip() 
                vegetables = row[vegetables_column].strip() 
                yolo_name = row[yoloname_column].strip() if yoloname_column else ""

                menu[menu_code] = {
                    "menu_code": menu_code,
                    "display_name": display_name,
                    "romaji": romaji,
                    "yolo_name": yolo_name,
                    "jan_code": jan_code,
                    "price": price,
                    "nutrition": {
                        "energy": energy,
                        "protein": protein,
                        "fat": fat,
                        "carbohydrates": carbohydrates,
                        "fiber": fiber,
                        "vegetables": vegetables,
                    }
                }

        self.menu = menu

    def find_menu_by_OsaraShohinResult(
        self, target: OsaraShohinResult
    ) -> OsaraShohinResult:
        """OsaraShohinResultからメニューを検索し、OsaraShohinResultに紐づける

        Args:
            target (OsaraShohinResult): 検索したいOsaraShohinResult。menu_objectがNoneだと思われる。
        Returns:
            OsaraShohinResult: 検索結果を紐づけたOsaraShohinResult
        """
        results: list[MenuObject] = []
        for box in target["boxes"]:  # 各商品(bbox)に対して
            # ---ラベル名で検索する
            label = box["label"]
            if label is None:
                continue
            candidate_menu_objects: list[MenuObject] = self.find_menu_by_kv(
                # "yolo_name", label
                "menu_code", label
            )
            print(
                f"\33[32m[find_menu_by_OsaraShohinResult] label: {label}, candidate counts: {len(candidate_menu_objects)}\33[0m"
            )

            if len(candidate_menu_objects) > 1:
                # ---検索した結果、候補が複数あった場合、面積で絞り込む(小・中・大があるようなやつ)
                # ---面積を計算する
                xyxy = box["xyxy"]
                area = (xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1])
                # ---面積で比較する
                osara_type = box["osara_type"]
                size: Literal["小", "中", "大"] = None
                if osara_type == "DON":
                    size = self.classify_by_size(area, (0.02441, 0.03906))
                elif osara_type == "CURRY":
                    size = self.classify_by_size(area, (0.1953, 0.2441))
                elif osara_type == "RICE":
                    size = self.classify_by_size(area, (0.01953, 0.02441))
                else:
                    size = ""
                print(
                    f"\33[32m[find_menu_by_OsaraShohinResult] osara_type: {osara_type}, size: {size}\33[0m"
                )

                # ---商品名とサイズを組み合わせて検索する
                for candidate_menu_object in candidate_menu_objects:
                    if candidate_menu_object["display_name"].startswith(size):
                        # OsaraShohinResultBoxに、メニューオブジェクトを紐づける
                        box["menu_object"] = candidate_menu_object
                        results.append(candidate_menu_object)
                        break
            elif len(candidate_menu_objects) == 1:
                # ---候補が1つだけの場合、それにする
                box["menu_object"] = candidate_menu_objects[0]
                results.append(candidate_menu_objects[0])
            else:
                # ---候補がない場合
                new_menu_object: MenuObject = {
                    "menu_code": None,
                    "display_name": "unknown",
                    "romaji": None,
                    "yolo_name": None,
                    "jan_code": None,
                    "price": 0,
                    "nutrition": {
                        "energy": None,
                        "protein": None,
                        "fat": None,
                        "carbohydrates": None,
                        "fiber": None,
                        "vegetables": None,
                    }
                }
                box["menu_object"] = new_menu_object
                results.append(new_menu_object)

            # find_menu_object=self.menu.get(label,None) # homemade_curryがサイズ分複数あるので、これは無理

        # ---渡されたOsaraShohinResultに、メニューオブジェクトを紐づけた、新規OsaraShohinResultを作成して返す
        new_osresult: OsaraShohinResult = {
            "image": target["image"],
            "path": target["path"],
            "boxes": target["boxes"],  #上で紐づいているので、そのまま渡す
        }

        return new_osresult

    def classify_by_size(
        self, area: float, thresholds: Tuple[float, float]
    ) -> Literal["小", "中", "大"]:
        """面積に応じてサイズを分類する

        Args:
            area (float): 面積
            thresholds (Tuple[float,float]): 閾値のリスト

        Returns:
            Literal["小","中","大"]: サイズ
        """
        if area < thresholds[0]:
            return "小"
        elif thresholds[0] <= area <= thresholds[1]:
            return "中"
        else:
            return "大"

    def find_menu_by_kv(
        self,
        key: Literal["menu_code", "display_name", "romaji", "yolo_name", "jan_code", "price"],
        value: str,
        search_type: Literal["exact", "partial"] = "exact",
    ) -> list[MenuObject]:
        """メニューを、キーと値で検索する

        Args:
            key (Literal["menu_code", "display_name", "romaji", "yolo_name", "jan_code", "price"]): 検索するキー
            value (str): 検索する値

        Returns:
            list[MenuObject]: 検索結果のメニューオブジェクトのリスト
        """
        if search_type == "exact":
            return [
                menu_object
                for menu_object in self.menu.values()
                if menu_object[key] == str(value)
            ]
        elif search_type == "partial":
            return [
                menu_object
                for menu_object in self.menu.values()
                if str(value) in menu_object[key]
            ]
