"""
# MenuCache.py
メニューキャッシュ(最近入力されたメニュー)を管理するモジュール。

## メソッド
- add_cache: CachedMenuObjectをキャッシュに追加する
- remove_cache: CachedMenuObjectをキャッシュから削除する
- find_cache: キャッシュから、指定したキーと値が一致するCachedMenuObjectを取得する
- get_cache: キャッシュを取得する
- export_as_json: キャッシュをJSONファイルにエクスポートする
- import_from_json: JSONファイルからキャッシュをインポートする
- _is_valid_menu_object: CachedMenuObjectが有効かどうかをチェックする

## 使用例
```python
# インスタンス生成
menu_cache = MenuCache()

# キャッシュにCachedMenuObjectを追加
menu_cache.add_cache(menu_object)

# キャッシュからCachedMenuObjectを削除
menu_cache.remove_cache(menu_object)

# キャッシュからCachedMenuObjectを検索
menu_cache.find_cache("display_name", "自家製カレー")

# キャッシュを取得
menu_cache.get_cache()

# キャッシュをJSONファイルにエクスポート
menu_cache.export_as_json("cache.json")

# JSONファイルからキャッシュをインポート
menu_cache.import_from_json("cache.json")
```

## 開発メモ
- 最近入力されたメニューを、「メニューキャッシュ」として管理する
- サーバーが動いている間は、メニューキャッシュが保持される
- jsonファイルに出力することで、サーバー再起動時にもメニューキャッシュを復元できる
- メニューキャッシュは、CachedMenuObjectのリストで管理される
"""

import json
from typing import Literal
from modules.Types import MenuObject


class CachedMenuObject(MenuObject):
    """キャッシュされたMenuObjectを表すデータクラス。
    個数の情報が追加されている。

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
        "count": int  # これまでに注文された数。「2」
    }
    """

    count: int  # これまでに注文された数。「2」


class MenuCache:
    def __init__(self):
        self.cached_menu_objects: list[CachedMenuObject] = []

    def __repr__(self):
        return f"MenuCache(cached_menu_objects={self.cached_menu_objects})"

    def add_cache(self, menu_object: CachedMenuObject):
        """CachedMenuObjectをキャッシュに追加する

        Args:
            menu_object (CachedMenuObject): キャッシュに追加するCachedMenuObject
        """
        # ---もしすでにキャッシュされている場合は、カウントを増やす
        for cached_menu_object in self.cached_menu_objects:
            if cached_menu_object["display_name"] == menu_object["display_name"]:
                cached_menu_object["count"] += 1
                return
        self.cached_menu_objects.append(
            {
                "menu_code": menu_object["menu_code"],
                "display_name": menu_object["display_name"],
                "romaji": menu_object["romaji"],
                "yolo_name": menu_object["yolo_name"],
                "jan_code": menu_object["jan_code"],
                "price": menu_object["price"],
                "count": 1,
            }
        )

    def remove_cache(self, menu_object: CachedMenuObject):
        """CachedMenuObjectをキャッシュから削除する

        Args:
            menu_object (CachedMenuObject): キャッシュから削除するCachedMenuObject
        """
        if menu_object in self.cached_menu_objects:
            self.cached_menu_objects.remove(menu_object)
        else:
            raise ValueError("CachedMenuObject not found in the cache")

    def find_cache(
        self,
        key: Literal["display_name", "romaji", "yolo_name", "jan_code", "price"],
        value: str,
    ) -> list[CachedMenuObject]:
        """キャッシュから、指定したキーと値が一致するCachedMenuObjectを取得する

        Args:
            key (Literal['display_name', 'romaji', 'yolo_name', 'jan_code', 'price']): 検索するキー
            value (str|int): 検索する値

        Returns:
            list[CachedMenuObject]: 検索結果のCachedMenuObjectのリスト
        """
        return [
            menu_object
            for menu_object in self.cached_menu_objects
            if str(menu_object[key]) == value
        ]

    def get_cache(self) -> list[CachedMenuObject]:
        """キャッシュを取得する

        Returns:
            list[CachedMenuObject]: キャッシュされたCachedMenuObjectのリスト
        """
        return self.cached_menu_objects

    def export_as_json(self, file_path: str):
        """キャッシュをJSONファイルにエクスポートする

        Args:
            file_path (str): エクスポート先のファイルパス
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.cached_menu_objects, f, ensure_ascii=False, indent=4)

    def import_from_json(self, file_path: str):
        """JSONファイルからキャッシュをインポートする

        Args:
            file_path (str): インポート元のファイルパス

        Raises:
            ValueError: キャッシュ内に無効なCachedMenuObjectが含まれている場合
        """
        with open(file_path, "r", encoding="utf-8") as f:
            self.cached_menu_objects = json.load(f)
        if self.cached_menu_objects == []:
            return
        if not all(
            [
                self._is_valid_menu_object(menu_object)
                for menu_object in self.cached_menu_objects
            ]
        ):
            raise ValueError("Invalid menu object in the cache")

    def _is_valid_menu_object(self, menu_object: dict) -> bool:
        """CachedMenuObjectが有効かどうかをチェックする。それぞれのキーが含まれているかを確認する

        Args:
            menu_object (dict): チェックするCachedMenuObject

        Returns:
            bool: 有効なCachedMenuObjectの場合はTrue
        """
        return (
            "menu_code" in menu_object
            and "display_name" in menu_object
            and "romaji" in menu_object
            and "yolo_name" in menu_object
            and "jan_code" in menu_object
            and "price" in menu_object
            and "count" in menu_object
        )
