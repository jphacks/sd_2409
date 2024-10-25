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
        """ "CSVファイルからメニューを読み込み、self.menuに格納する

        Returns:
            menu: メニュー情報を保持する辞書。以下のような形式(MenuObject)で保持される。
            {
                'メニューコード': {'jan_code': 'JANコード', 'display_name': '表示名', 'romaji': 'ローマ字', 'price': 価格},
                ...
            }
        """
        menu: dict[str, MenuObject] = {}  # メニュー情報を保持する辞書
        # 料理マスタ.csv(menu.csv)を読み込む
        with open(csv_file_path, mode="r", encoding=csv_encoding) as csvfile:
            reader = csv.DictReader(csvfile)  # CSVの1行目をキーとして扱う
            # janコード、display_name、priceの列インデックスを探す
            menu_code_column = None
            jan_code_column = None
            display_name_column = None
            romaji_column = None
            price_column = None
            yoloname_column = None

            # ヘッダー（列名）を確認し、必要な列を特定
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
                elif "検出名" in field:
                    yoloname_column = field

            # 必要な列が見つかったか確認
            if not (
                menu_code_column
                and jan_code_column
                and display_name_column
                and romaji_column
                and price_column
            ):
                raise ValueError(
                    "必要な列（janコード、お客様向け名称、販売価格(税込)etc）が見つかりませんでした。"
                )

            # CSVの各行を読み込み、janコードをキーとしてメニューを作成
            for row in reader:
                # if(row[yoloname_column] != ""): # yoloモデルの学習名が自作の場合
                #     menu_code = row[yoloname_column].strip()
                # else:
                #     menu_code = row[menu_code_column].strip()

                # ---各値を取得する
                menu_code = str(int(row[menu_code_column].strip()))
                display_name = row[display_name_column].strip()
                romaji = row[romaji_column].strip()
                yolo_name = row[yoloname_column].strip()
                jan_code = row[jan_code_column].strip()
                price = int(row[price_column].strip())

                # ---メニュー情報dictに追加する
                menu[menu_code] = {
                    "menu_code": menu_code,
                    "display_name": display_name,
                    "romaji": romaji,
                    "yolo_name": yolo_name,
                    "jan_code": jan_code,
                    "price": price,
                }

        # print(f"\n\n\nロードしたメニュー数: {len(menu)}")
        self.menu = menu

    def find_menu_by_OsaraShohinResult(
        self, target: OsaraShohinResult
    ) -> list[MenuObject]:
        """OsaraShohinResultからメニューを検索する

        Args:
            target (OsaraShohinResult): 検索したいOsaraShohinResult
        Returns:
            list[MenuObject]: 検索結果のメニューオブジェクトのリスト
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

            # ---検索した結果、候補が複数あった場合、面積で絞り込む(小・中・大があるようなやつ)
            if len(candidate_menu_objects) > 1:
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
                }
                box["menu_object"] = new_menu_object
                results.append(new_menu_object)

            # find_menu_object=self.menu.get(label,None) # homemade_curryがサイズ分複数あるので、これは無理

        return results

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
