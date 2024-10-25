"""
# MenuCache.py
メニューキャッシュ(最近入力されたメニュー)を管理するモジュール。

## メソッド
- add_cache: MenuObjectをキャッシュに追加する
- remove_cache: MenuObjectをキャッシュから削除する
- find_cache: キャッシュから、指定したキーと値が一致するMenuObjectを取得する
- get_cache: キャッシュを取得する
- export_as_json: キャッシュをJSONファイルにエクスポートする
- import_from_json: JSONファイルからキャッシュをインポートする
- _is_valid_menu_object: MenuObjectが有効かどうかをチェックする

## 使用例
```python
# インスタンス生成
menu_cache = MenuCache()

# キャッシュにMenuObjectを追加
menu_cache.add_cache(menu_object)

# キャッシュからMenuObjectを削除
menu_cache.remove_cache(menu_object)

# キャッシュからMenuObjectを検索
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
- メニューキャッシュは、MenuObjectのリストで管理される
"""

import json
from typing import Literal
from modules.Types import MenuObject


class MenuCache:
    def __init__(self):
        self.cached_menu_objects: list[MenuObject] = []

    def __repr__(self):
        return f"MenuCache(cached_menu_objects={self.cached_menu_objects})"

    def add_cache(self, menu_object: MenuObject):
        """MenuObjectをキャッシュに追加する

        Args:
            menu_object (MenuObject): キャッシュに追加するMenuObject
        """
        self.cached_menu_objects.append(menu_object)

    def remove_cache(self, menu_object: MenuObject):
        """MenuObjectをキャッシュから削除する

        Args:
            menu_object (MenuObject): キャッシュから削除するMenuObject
        """
        if menu_object in self.cached_menu_objects:
            self.cached_menu_objects.remove(menu_object)
        else:
            raise ValueError("MenuObject not found in the cache")

    def find_cache(
        self,
        key: Literal["display_name", "romaji", "yolo_name", "jan_code", "price"],
        value: str,
    ) -> list[MenuObject]:
        """キャッシュから、指定したキーと値が一致するMenuObjectを取得する

        Args:
            key (Literal['display_name', 'romaji', 'yolo_name', 'jan_code', 'price']): 検索するキー
            value (str|int): 検索する値

        Returns:
            list[MenuObject]: 検索結果のMenuObjectのリスト
        """
        return [
            menu_object
            for menu_object in self.cached_menu_objects
            if str(menu_object[key]) == value
        ]

    def get_cache(self) -> list[MenuObject]:
        """キャッシュを取得する

        Returns:
            list[MenuObject]: キャッシュされたMenuObjectのリスト
        """
        return self.cached_menu_objects

    def export_as_json(self, file_path: str):
        """キャッシュをJSONファイルにエクスポートする

        Args:
            file_path (str): エクスポート先のファイルパス
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.cached_menu_objects, f, ensure_ascii=False)

    def import_from_json(self, file_path: str):
        """JSONファイルからキャッシュをインポートする

        Args:
            file_path (str): インポート元のファイルパス

        Raises:
            ValueError: キャッシュ内に無効なMenuObjectが含まれている場合
        """
        with open(file_path, "r", encoding="utf-8") as f:
            self.cached_menu_objects = json.load(f)
        if not all(
            [
                self._is_valid_menu_object(menu_object)
                for menu_object in self.cached_menu_objects
            ]
        ):
            raise ValueError("Invalid menu object in the cache")

    def _is_valid_menu_object(self, menu_object: dict) -> bool:
        """MenuObjectが有効かどうかをチェックする。それぞれのキーが含まれているかを確認する

        Args:
            menu_object (dict): チェックするMenuObject

        Returns:
            bool: 有効なMenuObjectの場合はTrue
        """
        return (
            "display_name" in menu_object
            and "romaji" in menu_object
            and "yolo_name" in menu_object
            and "jan_code" in menu_object
            and "price" in menu_object
        )
