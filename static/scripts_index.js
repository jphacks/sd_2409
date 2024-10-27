// なんかめちゃくちゃ長くなっちゃってるので、関数・クラス・コメントの折りたたみ機能を使うと便利です。。。

////////////////////////////////////////
////  会計開始や再スキャン時に共通の関数  ////
////////////////////////////////////////
function handleStartOrRetry() {
    // 会計開始ボタンを非表示にし、コンテンツを表示
    // document.getElementById('start-button').style.display = 'none';
    // document.getElementById('content').style.display = 'flex';
    // document.getElementById('page-title').style.display = 'block';
    // document.querySelector('.header-buttons').style.display = 'flex';
    // document.getElementById('admin-page-button').style.display = 'none'; // 管理ページボタンを非表示
    return
    // カメラを起動して画像を取得し、サーバーに送信する
    captureImage()
        .then(imageBase64 => {
            // クライアントで撮影した画像を、画面に表示する
            document.getElementById('detected-image').src = imageBase64;

            // サーバーに画像を送信して検出結果を取得する
            return fetch('/start_inference', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image: imageBase64 })
            });
            /*以下のようなjsonが返ってくる
            {
                'image': image_base64(str),
                'items': [
                    {'display_name': メニュー名(str), 'romaji': ローマ字(str), 'price': 価格(int), 'yolo_name': yolo名(str), 'jan_code': JANコード(str),},
                    ...
                ],
                'total': 合計金額(int)
            }
            */

        })
        .then(response => response.json())
        .then(data => {
            // ---検出画像を表示する
            document.getElementById('detected-image').src = 'data:image/jpeg;base64,' + data.image;
            // ---合計金額を表示する
            document.getElementById('total-price').textContent = data.total;

            // ---以前のメニューをリセットする
            menuObjects.resetMenuObjects();

            // ---メニューを追加する
            for (const item of data.items) {
                console.log('item:', item);
                if (item.display_name !== "unknown") {
                    const newMenuObject = new MenuObject(menuObjects, item);
                }
            }

            // 処理が完了したタイムスタンプを取得し、時間を表示する
            const endTime = performance.now();  // 終了時間
            const duration = (endTime - startTime) / 1000;  // 経過時間 (秒)
            document.getElementById('load-time').textContent = `処理時間: ${duration.toFixed(2)} 秒`;
        })
        .catch(error => {
            console.error('エラー:', error);
        });
}
/**
 * メニューオブジェクトのパラメータクラス。
 * Pythonの、MenuObjectと同じ形式。
 * HTML要素の実態を持ったものを使いたい場合、MenuObjectを使う。
 * @typedef {Object} MenuObjectParameters
 * @property {string?} display_name 表示名
 * @property {string?} romaji ローマ字
 * @property {string?} yolo_name yolo名
 * @property {string?} jan_code jan_code
 * @property {number?} price 価格
 */

/* # MenuServerクラス
メニューサーバーとの通信を管理するクラス
メニューの検索、メニューキャッシュ(最近入力されたメニュー)の操作を行う

## プロパティ
- url: メニューサーバーのURL
- recentMenuObjectCache: 最近のメニューキャッシュ

## メソッド
- searchMenu(key, value): メニューを検索する
- getMenuCache(): メニューキャッシュを取得する
- addMenuCache(menuObjectParameters): メニューキャッシュに追加する
- removeMenuCache(menuObjectParameters): メニューキャッシュから削除する

## 使い方
```javascript
// ---初期設定
const menuServer = new MenuServer('http://localhost:5000');

// ---メニューを検索する
const searchResult = await menuServer.searchMenu('display_name', 'カレー');
console.log(searchResult);

// ---メニューキャッシュを取得する
const cache = await menuServer.getMenuCache();
console.log(cache);

// ---メニューキャッシュに追加する
const newCache = await menuServer.addMenuCache({
    "display_name": "カレー",
    "romaji": "KARE",
    "yolo_name": "curry",
    "jan_code": "1234567890123",
    "price": 1000
});
console.log(newCache);

// ---メニューキャッシュから削除する
const removedCache = await menuServer.removeMenuCache({
    "display_name": "カレー",
    "romaji": "KARE",
    "yolo_name": "curry",
    "jan_code": "1234567890123",
    "price": 1000
});
console.log(removedCache);
```

## 開発メモ
- それぞれのメソッドと、PythonのAPIの対応は、以下の通り
    - searchMenu(): /search_menu
    - getMenuCache(): /get_menu_cache
    - addMenuCache(): /add_menu_cache
    - removeMenuCache(): /remove_menu_cache

*/
class MenuServer {
    /**
     * メニューサーバーとの通信を管理するクラス
     * @param {string} メニューサーバーのURL
     */
    constructor(url) {
        /**@type {string} メニューサーバーのURL*/
        this.url = url;
        /**@type {MenuObjectParameters[]} 最近のメニューのキャッシュ*/
        this.recentMenuObjectCache = [];
    }

    // ----------
    // ---メニューの検索用API
    // ----------
    /**
     * メニューサーバーから、メニューを検索する
     * @param {string} key 検索するキー
     * @param {string} value 検索する値
     * @returns {Promise<MenuObjectParameters[]>}
     */
    async searchMenu(key, value) {
        const response = await fetch(`${this.url}/search_menu?key=${key}&value=${value}`);
        const json = await response.json();
        if (this.verifyResponseJson(json)) {
            return json;
        } else {
            throw new Error('Invalid response\n', json);
        }
    }

    // ----------
    // ---メニューキャッシュの操作用API
    // ----------
    /**
     * メニューサーバーから、キャッシュ(最近のメニュー)を取得する
     * @returns {Promise<MenuObjectParameters[]>}
     */
    async getMenuCache() {
        const response = await fetch(`${this.url}/get_menu_cache`);
        const json = await response.json();
        const cache = json["cache"];
        if (this.verifyResponseJson(cache)) {
            this.recentMenuObjectCache = cache;
            return cache;
        } else {
            throw new Error('Invalid response\n', cache);
        }
    }

    /**
     * メニューサーバーに、キャッシュ(最近のメニュー)を追加する
     * キャッシュを追加し、追加された後のキャッシュを返す　…ことを想定している
     * @param {MenuObjectParameters} menuObjectParameters キャッシュに追加するメニューパラメータ
     */
    async addMenuCache(menuObjectParameters) {
        const response = await fetch(`${this.url}/add_menu_cache`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "item": menuObjectParameters
            })
        });
        const json = await response.json();
        const cache = json["cache"];
        if (this.verifyResponseJson(cache)) {
            this.recentMenuObjectCache = cache;
            return cache;
        } else {
            throw new Error('Invalid response\n', cache);
        }
    }

    /**
     * メニューサーバーから、キャッシュ(最近のメニュー)を削除する
     * キャッシュを削除し、削除された後のキャッシュを返す　…ことを想定している
     * @param {MenuObjectParameters} menuObjectParameters 
     * @returns 
     */
    async removeMenuCache(menuObjectParameters) {
        const response = await fetch(`${this.url}/remove_menu_cache`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "key": "display_name",
                "value": menuObjectParameters.display_name
            })
        });
        const json = await response.json();
        const cache = json["cache"];
        if (this.verifyResponseJson(cache)) {
            this.recentMenuObjectCache = cache;
            return cache;
        } else {
            throw new Error('Invalid response\n', cache);
        }
    }

    /**
     * 指定したjsonが、メニューオブジェクトのパラメータであるかどうかを判定する
     * @param {any} json
     * @returns 
     */
    verifyResponseJson(json) {
        return Array.isArray(json) && json.every(item => isMenuObjectParameters(item));
    }
}

/**
 * 入力したオブジェクトがMenuObjectParametersであるかどうかを判定する
 * @param {any} obj
 * @returns {boolean} MenuObjectParametersであるかどうか
 */
function isMenuObjectParameters(obj) {
    return obj instanceof Object && 'display_name' in obj && 'romaji' in obj && 'yolo_name' in obj && 'jan_code' in obj && 'price' in obj;
}

/**
 * メニューオブジェクトのDOM要素を表現するクラス
 * @typedef {Object} MenuObjectElements
 * @property {HTMLLIElement} liElement li要素
 * @property {HTMLRubyElement} rubyElement ruby要素
 * @property {HTMLSpanElement} rubySpanElement span要素
 * @property {HTMLRTElement} rtElement rt要素
 * @property {HTMLSpanElement} priceSpan span要素
 * @property {HTMLButtonElement} deleteButton button要素
 */

/* # MenuObjectクラス
商品のデータ・表示を管理するクラス。画面の右側に表示されるやつ。
プルダウンメニューの表示は、このクラスのcreateElement()でおこなっている

## プロパティ
- parentMenuObjects: このMenuObjectを管理するMenuObjects
- display_name: 表示名
- romaji: ローマ字
- yolo_name: yolo名
- jan_code: jan_code
- price: 価格
- isSelectOpen: ドロップダウンメニューが開いているかどうか
- elements: 商品の表示用DOM要素

## メソッド
- setValue(parameters): 商品の値を変更する
- delete(): 商品を削除する
- getMenuObjectParameters(): このMenuObjectを、MenuObjectParametersとして返す
- 内部メソッド
    - createElement(): 商品表示用の要素を作成する
    - update(): 商品表示用の要素を更新する

## 使い方
```javascript
// ---MenuObjectを作成する
const menuObject = new MenuObject(menuObjects, {
    "display_name": "カレー",
    "romaji": "KARE",
    "yolo_name": "curry",
    "jan_code": "1234567890123",
    "price": 1000
});

// ---MenuObjectの値を変更する
menuObject.setValue({
    "display_name": "カレー",
    "romaji": "KARE",
    "yolo_name": "curry",
    "jan_code": "1234567890123",
    "price": 1500 // 価格を変更
});

// ---MenuObjectを削除する
menuObject.delete();

// ---MenuObjectをMenuObjectParametersとして取得する
const parameters = menuObject.getMenuObjectParameters();
console.log(parameters);

```
*/

class MenuObject {
    /**
     * 商品のデータ・表示を管理するクラス
     * @param {MenuObjects} parentMenuObjects 
     * @param {MenuObjectParameters} parameters 
     */
    constructor(parentMenuObjects = undefined, parameters = {}) {
        // ---親となるMenuObjectsを保存する(それぞれのメニューを管理するやつ)
        /**@type {MenuObjects|undefined} 親MenuObjects*/
        this.parentMenuObjects = parentMenuObjects;

        /**@type {string} 表示名*/
        this.display_name = parameters.display_name ?? '';
        /**@type {string} ローマ字*/
        this.romaji = parameters.romaji ?? '';
        /**@type {string} yolo名*/
        this.yolo_name = parameters.yolo_name ?? '';
        /**@type {string} jan_code*/
        this.jan_code = parameters.jan_code ?? '';
        /**@type {number} 価格*/
        this.price = parameters.price ?? 0;

        // 栄養価関連のプロパティを追加
        this.energy = parameters.energy ?? 0;
        this.protein = parameters.protein ?? 0;
        this.fat = parameters.fat ?? 0;
        this.carbohydrates = parameters.carbohydrates ?? 0;
        this.fiber = parameters.fiber ?? 0;
        this.vegetables = parameters.vegetables ?? 0;

        /**@type {boolean} ドロップダウンメニューが開いているかどうか*/
        this.isSelectOpen = false;

        // ---DOM要素の作成・反映
        /**@type {MenuObjectElements} 商品の表示用DOM要素*/
        this.elements = this.createElement();
        if (parentMenuObjects) {
            parentMenuObjects.addMenuObject(this);
        }

    }

    // ----------
    // ---HTMLElementの管理系
    // ----------

    /**
     * 商品表示用の要素を作成する
     * @returns {MenuObjectElements}
     */
    createElement() {
        /*
        これをつくる
        <li>
            <div>
                <ruby>
                    <span>{メニュー名}</span>
                    <rt>{ローマ字}</rt>
                </ruby>
                <span>¥{値段}</span>
            </div>
            <button>x</button>
        </li>
        */

        // ----------
        // ---要素の作成
        // ----------
        const liElement = document.createElement('li');
        const divElement = document.createElement('div');
        liElement.appendChild(divElement);

        const rubyElement = document.createElement('ruby');
        divElement.appendChild(rubyElement);

        const rubySpanElement = document.createElement('span');
        rubySpanElement.textContent = this.display_name;
        rubyElement.appendChild(rubySpanElement);

        const rtElement = document.createElement('rt');
        rtElement.textContent = this.romaji;
        rubyElement.appendChild(rtElement);

        const priceSpan = document.createElement('span');
        priceSpan.textContent = ` ¥${this.price}`;
        divElement.appendChild(priceSpan);

        const deleteButton = document.createElement('button');
        deleteButton.textContent = '-';
        deleteButton.classList.add('delete-button');
        liElement.appendChild(deleteButton);

        // ----------
        // ---イベントの設定
        // ----------
        liElement.addEventListener('click', async () => { // ドロップダウンメニューから選択させる
            // ---開閉の切り替え
            if (this.isSelectOpen) {
                return;
            }
            this.isSelectOpen = true;

            // ---[関数宣言]ドロップダウンメニューを削除する
            const removeSelectMenu = () => {
                this.isSelectOpen = false;
                selectMenuDiv.remove();
                backgroundDiv.remove();
            }

            // ---選択中のメニューを設定する
            this.parentMenuObjects.setSelectedMenu(this);

            // ---ドロップダウンメニューを作成する
            const selectMenuDiv = document.createElement('div');
            selectMenuDiv.classList.add('select-menu'); // クラスを追加

            const backgroundDiv = document.createElement('div');
            backgroundDiv.classList.add('background-overlay'); // クラスを追加

            backgroundDiv.addEventListener('click', () => {
                // ---ドロップダウンメニューを削除する
                removeSelectMenu();
            });
            document.body.appendChild(backgroundDiv);

            // ---未指定のときの選択肢を作る(「最近のメニューから選ぶ…」)
            // const emptyOption = document.createElement('option');
            const emptyOptionDiv = document.createElement('div');
            emptyOptionDiv.textContent = "最近のメニューから選ぶ…";
            emptyOptionDiv.addEventListener('click', (e) => {
                // ---ドロップダウンメニューを削除する
                removeSelectMenu();
            });
            selectMenuDiv.appendChild(emptyOptionDiv);

            // ---手入力の選択肢を作る(「(手入力する)」)
            const manualInputOptionDiv = document.createElement('div');
            manualInputOptionDiv.textContent = "(手入力する)";
            manualInputOptionDiv.addEventListener('click', (e) => {
                e.stopPropagation();
                console.log('手入力選択されました');
                // ---手入力のフォームを表示する
                const customMenuForm = document.getElementById('custom-menu-form');
                customMenuForm.style.display = 'block';
                // ---ドロップダウンメニューを削除する
                removeSelectMenu();
            });
            selectMenuDiv.appendChild(manualInputOptionDiv);

            // ---サーバーから取得した、最近の入力メニューを、ドロップダウンメニューに追加する
            const cache = await this.parentMenuObjects.menuServer.getMenuCache();
            for (const item of cache) {
                // const option = document.createElement('option');
                // ---ドロップダウンメニューの選択肢を作成する
                const optionDiv = document.createElement('div');
                optionDiv.textContent = `${item.display_name}  ¥${item.price}`;

                // ---イベントを設定する
                optionDiv.addEventListener('click', (e) => {
                    e.stopPropagation();
                    console.log('selected:', item.display_name);
                    // ---選択されたメニューに変更する
                    this.setValue(item);
                    // ---ドロップダウンメニューを削除する
                    removeSelectMenu();
                    // ---合計金額を更新する(…は、onChangeでやる)
                });
                selectMenuDiv.appendChild(optionDiv);
            }

            // ---ドロップダウンメニューを表示する
            liElement.appendChild(selectMenuDiv);
        });

        deleteButton.addEventListener('click', (e) => { // 削除ボタンで削除する
            e.stopPropagation();
            this.delete();
        });

        // ---返却
        return {
            liElement,
            rubyElement,
            rubySpanElement,
            rtElement,
            priceSpan,
            deleteButton
        };
    }
    /**
     * 商品表示用の要素を更新する
     */
    update() {
        this.elements.rubySpanElement.textContent = this.display_name;
        this.elements.rtElement.textContent = this.romaji;
        this.elements.priceSpan.textContent = ` ¥${this.price}`;
    }

    // ----------
    // ---商品の操作系
    // ----------

    /**
     * 商品の値を変更する
     * @param {MenuObjectParameters} parameters
     */
    setValue(parameters) {
        this.display_name = parameters.display_name ?? this.display_name;
        this.romaji = parameters.romaji ?? this.romaji;
        this.yolo_name = parameters.yolo_name ?? this.yolo_name;
        this.jan_code = parameters.jan_code ?? this.jan_code;
        this.price = parameters.price ?? this.price;

        // 栄養価の更新を追加
        this.energy = parameters.energy ?? this.energy;
        this.protein = parameters.protein ?? this.protein;
        this.fat = parameters.fat ?? this.fat;
        this.carbohydrates = parameters.carbohydrates ?? this.carbohydrates;
        this.fiber = parameters.fiber ?? this.fiber;
        this.vegetables = parameters.vegetables ?? this.vegetables;

        this.update();
        this.parentMenuObjects.onItemValueChanged(this);
    }

    /**
     * 商品を削除する
     */
    delete() {
        // ---親のリストから削除してもらう
        if (this.parentMenuObjects) {
            this.parentMenuObjects.deleteMenuObject(this);
        }

        // ---要素を削除
        this.elements.liElement.remove();
    }

    /**
     * このMenuObjectを、MenuObjectParametersとして返す
     * @returns {MenuObjectParameters} MenuObjectParametersで表現した形
     */
    getMenuObjectParameters() {
        return {
            display_name: this.display_name,
            romaji: this.romaji,
            yolo_name: this.yolo_name,
            jan_code: this.jan_code,
            price: this.price,
            energy: this.energy,
            protein: this.protein,
            fat: this.fat,
            carbohydrates: this.carbohydrates,
            fiber: this.fiber,
            vegetables: this.vegetables
        };
    }
}

/* # MenuObjectsクラス
商品のリストを管理するクラス。それぞれの商品をまとめて管理するためのクラス。

## プロパティ
- rootElement: 商品リストを入れ込む要素
- menuObjects: 商品のリスト
- selectedMenu: 選択中の商品
- onChange: リスト内の商品の値が変更されたときのコールバック
- menuServer: MenuServer

## メソッド
- addMenuObject(menuObject): MenuObjectを追加する
- findMenuObject(key, value): 指定したキーで、指定した値を持つMenuObjectを探す
- deleteMenuObject(menuObject): MenuObjectをリストから削除する
- setSelectedMenu(menuObject): 現在選択中の商品を設定する
- getSelectedMenu(): 現在選択中の商品を取得する
- calculateTotalPrice(): 合計金額を計算する

## 使い方
```javascript
// ---MenuObjectsを作成する
const menuObjects = new MenuObjects(menuList, menuServer);

// ---MenuObjectを追加する
const menuObject = new MenuObject(menuObjects, {
    "display_name": "カレー",
    "romaji": "KARE",
    "yolo_name": "curry",
    "jan_code": "1234567890123",
    "price": 1000
});
menuObjects.addMenuObject(menuObject);

// ---MenuObjectを検索する
const foundMenuObjects = menuObjects.findMenuObject('display_name', 'カレー');
console.log(foundMenuObjects);

// ---MenuObjectを削除する
menuObjects.deleteMenuObject(menuObject);

// ---現在選択中の商品を設定する
menuObjects.setSelectedMenu(menuObject);

// ---現在選択中の商品を取得する
const selectedMenu = menuObjects.getSelectedMenu();

// ---合計金額を計算する
const totalPrice = menuObjects.calculateTotalPrice();
console.log(totalPrice);

```

*/

class MenuObjects {
    /**
     * 商品のリストを管理するクラス
     * @param {HTMLElement} rootElement 商品リストを入れ込む要素
     * @param {MenuServer} menuServer
     */
    constructor(rootElement, menuServer) {
        /**@type {HTMLElement} 商品リストを入れ込む要素*/
        this.rootElement = rootElement;
        /**@type {MenuObject[]} 商品のリスト*/
        this.menuObjects = [];
        /**@type {MenuObject|undefined} 選択中の商品*/
        this.selectedMenu = undefined;
        /**@type {(changedMenuObject: MenuObject) => void} リスト内商品の値が変更されたときのコールバック*/
        this.onItemValueChanged = (changedMenuObject) => { };

        /**@type {(changedMenuObject: MenuObject) => void} リストが変更されたときのコールバック*/
        this.onItemListChanged = (changedMenuObject) => { };

        this.menuServer = menuServer;
    }

    // ----------
    // ---リスト操作
    // ----------
    /**
     * MenuObjectを追加する
     * @param {MenuObject} menuObject 
     */
    addMenuObject(menuObject) {
        // ---親を設定
        menuObject.parentMenuObjects = this;
        // ---リストに追加
        this.menuObjects.push(menuObject);
        // ---要素を表示する
        this.rootElement.appendChild(menuObject.elements.liElement);
        // ---コールバックを実行
        this.onItemListChanged(menuObject);
    }
    /**
     * 指定したキーで、指定した値を持つMenuObjectを探す
     * @param {"display_name"|"romaji"|"yolo_name"|"jan_code"|"price"} key
     * @param {any} value
     * @returns {MenuObject[]|undefined}
     */
    findMenuObject(key, value) {
        return this.menuObjects.filter(menuObject => menuObject[key] === value);
    }
    /**
     * MenuObjectをリストから削除する
     * @param {MenuObject} menuObject 
     */
    deleteMenuObject(menuObject) {
        // ---フィルターで削除
        this.menuObjects = this.menuObjects.filter(obj => obj !== menuObject);
        // ---コールバックを実行
        this.onItemListChanged(menuObject);
    }

    /**
     * メニューリストをリセットする
     */
    resetMenuObjects() {
        for (const menuObject of this.menuObjects) {
            menuObject.delete();
        }
    }

    // ----------
    // ---現在選択中の商品
    // ----------
    /**
     * 現在選択中の商品を設定する
     * @param {MenuObject} menuObject
     */
    setSelectedMenu(menuObject) {
        this.selectedMenu = menuObject;
    }

    /**
     * 現在選択中の商品を取得する
     * @returns {MenuObject|undefined}
     */
    getSelectedMenu() {
        return this.selectedMenu;
    }
    // ----------
    // ---JANコードの取得
    // ----------
    /**
     * MenuObjectsに格納しているすべてのメニューの、JANコードのリストを取得する
     * @returns {string[]} JANコードのリスト
     */
    getJanCodes() {
        return this.menuObjects.map(menuObject => menuObject.jan_code);
    }

    // ----------
    // ---ほか
    // ----------
    /**
     * 合計金額を計算する
     * @returns {number} 合計金額
     */
    calculateTotalPrice() {
        return this.menuObjects.reduce((sum, menuObject) => sum + menuObject.price, 0);
    }

    /**栄養の合計値を計算し，表を表示する関数
     * @returns {object} 栄養の合計
     */
    calculateNutrition() {
        // 栄養素の合計値を保持するオブジェクト
        const totalNutrition = {
            energy: 0,
            protein: 0,
            fat: 0,
            carbohydrates: 0,
            fiber: 0,
            vegetables: 0,
        };

        // 各メニューオブジェクトをループして栄養素を加算
        for (const menuObject of this.menuObjects) {
            //totalNutrition.energy += parseFloat(menuObject.energy) || menuObject.energy;
            totalNutrition.energy += menuObject.energy;
            console.log(menuObject.price)
            totalNutrition.protein += parseFloat(menuObject.protein) || 0;
            totalNutrition.fat += parseFloat(menuObject.fat) || 0;
            totalNutrition.carbohydrates += parseFloat(menuObject.carbohydrates) || 0;
            totalNutrition.fiber += parseFloat(menuObject.fiber) || 0;
            totalNutrition.vegetables += parseFloat(menuObject.vegetables) || 0;
        }

        return totalNutrition;
    }

    /**栄養情報の表を更新する関数
     * @param {object} nutrition 栄養素の合計
     */
    updateNutritionTable(nutrition) {
        const tbody = document.getElementById('nutrition-table-body');
        tbody.innerHTML = `
            <tr>
                <td>${nutrition.energy.toFixed(2)}</td>
                <td>${nutrition.protein.toFixed(2)}</td>
                <td>${nutrition.fat.toFixed(2)}</td>
                <td>${nutrition.carbohydrates.toFixed(2)}</td>
                <td>${nutrition.fiber.toFixed(2)}</td>
                <td>${nutrition.vegetables.toFixed(2)}</td>
            </tr>
        `;
    }
}

// "追加" ボタンがクリックされたときにフォームを表示
document.getElementById('add-button').addEventListener('click', () => {
    document.getElementById('add-button').style.display = 'none';
    document.getElementById('add-menu-form').style.display = 'block'; // フォームを表示
});

// 一定時間待つ関数
async function wait(ms) {
    return new Promise(resolve => {
        setTimeout(resolve, ms);
    });
}

// ----------
// ---手入力フォーム入力から、メニュー検索と表示を行う
// ----------
const manualInputDatalist = document.getElementById('manual-menu-options'); // HTMLDataListElement
// メニューを検索して候補を表示する共通関数
function searchAndDisplayMenuOptions(inputElement, priceElement, datalistElement) {
    let debounceTimeout = null;
    
    inputElement.addEventListener('input', async () => {
        clearTimeout(debounceTimeout);
        
        debounceTimeout = setTimeout(async () => {
            const inputDisplayName = inputElement.value.trim();
            if (inputDisplayName.length === 0) return;
            
            // サーバーでメニューを検索する
            const items = await menuServer.searchMenu('display_name', inputDisplayName);
            
            // datalistで候補を表示する
            datalistElement.innerHTML = '';  // 既存の候補をクリア
            for (const item of items) {
                const optionElement = document.createElement('option');
                optionElement.value = item.display_name; // メニュー名を表示
                optionElement.textContent = `¥${item.price}`; // 価格を表示
                datalistElement.appendChild(optionElement);
                
                // 一致するメニュー名があれば価格を自動入力
                if (item.display_name === inputDisplayName) {
                    priceElement.value = item.price;
                }
            }
        }, 0); // 0msの遅延処理(サーバー混み合う場合など)
    });
}
// ---追加メニューの検索と表示を設定
const add_menuNameInput = document.getElementById('add-menu-name');
const add_menuPriceInput = document.getElementById('add-menu-price');
searchAndDisplayMenuOptions(add_menuNameInput, add_menuPriceInput, manualInputDatalist);
// ---変更メニューの検索と表示を設定
const menuNameInput = document.getElementById('custom-menu-name');
const menuPriceInput = document.getElementById('custom-menu-price');
searchAndDisplayMenuOptions(menuNameInput, menuPriceInput, manualInputDatalist);


// ----------
// ---メニューを追加/変更確定時、メニューオブジェクトを処理する共通関数(追加/変更)
// ----------
async function handleMenuInput(inputMenuName, inputMenuPrice, datalist, isAddNew) {
    const menuName = inputMenuName.value.trim();
    const menuPrice = parseInt(inputMenuPrice.value, 10);

    // ---入力がない場合、アラートを表示して終了
    if (!menuName || !menuPrice) {
        alert('メニュー名と価格を入力してください');
        return;
    }

    // ---念のため、手入力されたメニューを検索する
    const items = await menuServer.searchMenu('display_name', menuName);

    // メニューリストに存在しない場合、アラートを表示して終了
    if (items.length === 0) {
        alert('メニューが見つかりませんでした');
        return;
    }

    // ---メニューオブジェクトを編集または追加する
    const newMenuObjectParameters = items[0];
    if (!isMenuObjectParameters(newMenuObjectParameters)) {
        throw new Error('Invalid response\n', newMenuObjectParameters);
    }

    if (isAddNew) {
        // 新しいメニューオブジェクトを追加
        new MenuObject(menuObjects, newMenuObjectParameters);
    } else {
        // 選択されたメニューオブジェクトを変更
        const selectedMenu = menuObjects.getSelectedMenu();
        if (selectedMenu) {
            selectedMenu.setValue(newMenuObjectParameters);
        }
    }

    // ---サーバーのメニューキャッシュに追加する
    await menuServer.addMenuCache(newMenuObjectParameters);

    // ---フォームをリセットする
    inputMenuName.value = '';
    inputMenuPrice.value = '';
    datalist.innerHTML = '';  // 候補をクリア

    // ---フォームの表示をリセット
    if (isAddNew) {
        document.getElementById('add-menu-form').style.display = 'none';
        document.getElementById('add-button').style.display = 'block';
    } else {
        document.getElementById('custom-menu-form').style.display = 'none';
    }
}
// ---メニュー追加ボタンクリック時の処理
const addInputAddButton = document.getElementById('add-add-menu');
addInputAddButton.addEventListener('click', () => {
    handleMenuInput(add_menuNameInput, add_menuPriceInput, manualInputDatalist, true);
});
// ---メニュー変更ボタンクリック時の処理
const manualInputAddButton = document.getElementById('add-custom-menu');
manualInputAddButton.addEventListener('click', () => {
    handleMenuInput(menuNameInput, menuPriceInput, manualInputDatalist, false);
});

// 一定時間待つ関数
async function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

var socket = io(); // Socket.IOの初期化

////////////////////////////////////////
///         確定ボタンクリック時         ///////
////////////////////////////////////////
document.getElementById('confirm-button').addEventListener('click', async function () {
    // 栄養素の合計を計算
    const totalNutrition = menuObjects.calculateNutrition();
    
    // 栄養素の割合を棒グラフとして描画
    drawNutritionChart(totalNutrition);
    
    const hitProbability = 0.5; // あたりの出現確率 (0.0 ~ 1.0)
    const isHit = Math.random() < hitProbability; // あたりかどうかの判定

    const videoType = isHit ? 'hit' : 'miss'; // あたり/はずれに応じたフォルダ選択

    try {
        const response = await fetch(`/get_random_video?type=${videoType}`);
        if (!response.ok) throw new Error('動画の取得に失敗しました');

        const videoData = await response.json();
        const videoUrl = videoData.video_url;

        // ポップアップを開き、動画と終了後のあたりメッセージを表示
        const popup = window.open("", "_blank", "width=800,height=600");

        if (popup) {
            popup.document.write(`
                <!DOCTYPE html>
                <html lang="ja">
                <head>
                    <meta charset="UTF-8">
                    <title>動画再生</title>
                    <style>
                        body {
                            margin: 0;
                            display: flex;
                            flex-direction: column;
                            justify-content: flex-start;
                            align-items: center;
                            height: 100vh;
                            background-color: black;
                        }
                        #hitMessage {
                            display: none;
                            color: yellow;
                            font-size: 48px;
                            text-align: center;
                            margin-top: 20px;
                            position: absolute;
                            top: 10px;
                        }
                        video {
                            width: 100%;
                            height: auto;
                        }
                    </style>
                </head>
                <body>
                    <div id="hitMessage">あたり！</div>
                    <video id="popupVideo" controls autoplay muted playsinline>
                        <source src="${videoUrl}" type="video/mp4">
                        お使いのブラウザは動画をサポートしていません。
                    </video>
                    <script>
                        const video = document.getElementById('popupVideo');
                        const hitMessage = document.getElementById('hitMessage');

                        video.addEventListener('ended', () => {
                            if (${isHit}) {
                                hitMessage.style.display = 'block'; // あたりメッセージを表示
                            }
                        });

                        video.play().catch(error => console.error('自動再生に失敗しました:', error));
                    </script>
                </body>
                </html>
            `);

            // あたりの場合にPythonファイルを実行する
            if (isHit) {
                await fetch('/run_hit_script', { method: 'POST' });
            }
        } else {
            alert('ポップアップがブロックされました。');
        }
    } catch (error) {
        alert(error.message);
    }


    const uuid = this.getAttribute('data-uuid'); // data-uuid属性からUUIDを取得
    console.log("Pythonの実行を要求します");
    document.getElementById('payment-message').innerHTML = `(${uuid})<br>お支払いに進んでください`;

    // Pythonの実行要求をサーバーに送信
    socket.emit('request_python_execution', {
        'uuid': uuid,
        'jan_codes': menuObjects.getJanCodes()
    });

    await wait(3000); // 何となく1秒待つ->栄養情報の表示のため，ハッカソン用に3秒に変更．(町田)
    window.location.href = '/start/' + uuid; // 前画面に戻る



    // ---メニューリストを取得する
    // const selectedMenus = menuObjects.menuObjects.map(menuObject => menuObject.getMenuObjectParameters());

    // ---選択されたメニューを、ユビレジへのBluetooth送信用サーバーに送信する
    // TODO 通信用サーバーができたら、実装する
    // const response=await fetch('/send_to_ubiregi', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify({ items: selectedMenus})
    // })
    // if (!response.ok) {
    //     console.error('ユビレジへの送信に失敗しました:', response);
    //     return;
    // }
    // const responseJson = await response.json();



    // fetch('/confirm_order', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify({ items: selectedMenus})
    // })
    //     .then(response => response.json())
    //     .then(data => {
    //         document.getElementById('payment-message').textContent = 'お支払いに進んでください';
    //         console.log('確定メニュー:', data.menus); // コンソールで確認
    //         window.location.href = '/';  // ホーム画面にリダイレクト
    //     })
    //     .catch(error => {
    //         console.error('注文の確定に失敗しました:', error);
    //     });  
    
});

////////////////////////////////////////
///  カメラを起動し、画像をbase64で返す   ///
////////////////////////////////////////
function captureImage() {
    return new Promise((resolve, reject) => {

        const agent = navigator.userAgent.toLowerCase(); // 小文字変換
        const isiPhone = /iphone|ipod/.test(agent);
        const isiPad = /ipad|macintosh/.test(agent) && "ontouchend" in document;
        let constraints = {};

        const selectedCameraId = localStorage.getItem('selectedCameraId');

        if (isiPhone || isiPad) {
            // iPhoneでは facingMode を使用してカメラを指定
            constraints.video = { facingMode: 'environment' };
        } else if (selectedCameraId) {
            // PC/Androidの場合は deviceId を使用してカメラを指定
            constraints.video = { deviceId: { exact: selectedCameraId } };
        } else {
            // カメラIDが指定されていない場合はデフォルトのカメラを使用
            constraints.video = true;
        }

        // カメラを起動
        navigator.mediaDevices.getUserMedia(constraints)
            // navigator.mediaDevices.getUserMedia({ video: true })
            .then(function (stream) {
                const video = document.createElement('video');
                video.srcObject = stream;
                video.play();

                // ビデオが再生されたら写真を撮る
                video.addEventListener('loadedmetadata', async () => {
                    await wait(1000);  //カメラ起動するのをちょっと待つ (1s)
                    // 画像をキャプチャ
                    const canvas = document.createElement('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    const context = canvas.getContext('2d');
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);

                    // 画像をBase64形式で取得
                    const imageData = canvas.toDataURL('image/jpeg');

                    // カメラのストリームを停止
                    stream.getTracks().forEach(track => track.stop());

                    resolve(imageData);  // 画像データを返す
                });
            })
            .catch(function (err) {
                console.error("カメラの起動に失敗しました: ", err);
                reject(err);
            });
    });
}

// ページロード時の開始時間を記録する変数
let startTime;

// ページ読み込み時に handleStartOrRetry を呼び出す
window.onload = function () {
    startTime = performance.now();
    handleStartOrRetry();  // カメラ起動と会計開始処理
};

// 再スキャンボタンを押したときの処理
document.getElementById('retry-button').addEventListener('click', function () {
    startTime = performance.now();
    handleStartOrRetry();
});

// 前の画面に戻るボタン がクリックされたときの処理
document.getElementById('cancel-button').addEventListener('click', function () {
    const uuid = document.getElementById('confirm-button').getAttribute('data-uuid');
    window.location.href = '/start/' + uuid; 
});


const menuList = document.getElementById('menu-list');
const menuServer = new MenuServer("")
const menuObjects = new MenuObjects(menuList, menuServer);
menuObjects.onItemValueChanged = (changedMenuObject) => {
    // ---合計金額を更新する
    const totalPrice = menuObjects.calculateTotalPrice();
    document.getElementById('total-price').textContent = totalPrice.toLocaleString();

    // 栄養素の合計を再計算し、表を更新
    const totalNutrition = menuObjects.calculateNutrition();
    menuObjects.updateNutritionTable(totalNutrition);
}
menuObjects.onItemListChanged = (changedMenuObject) => {
    // ---合計金額を更新する
    const totalPrice = menuObjects.calculateTotalPrice();
    document.getElementById('total-price').textContent = totalPrice.toLocaleString();

    // 栄養素の合計を再計算し、表を更新
    const totalNutrition = menuObjects.calculateNutrition();
    menuObjects.updateNutritionTable(totalNutrition);
}

function drawNutritionChart(nutrition) {
    const canvas = document.getElementById('nutrition-chart');
    const ctx = canvas.getContext('2d');

    // 1/3日分の基準値（例として適当な値を設定）
    const dailyRequirement = {
        energy: 750,          // kcal
        protein: 20,          // g
        fat: 22,              // g
        carbohydrates: 80,    // g
        fiber: 8,             // g
        vegetables: 100       // mg
    };

    // canvasの設定
    canvas.width = 600;
    canvas.height = 300;

    // 背景色を追加
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const labels = ['エネルギー', 'タンパク質', '脂質', '炭水化物', '食物繊維', '野菜量'];
    const values = [
        (nutrition.energy / dailyRequirement.energy) * 100,
        (nutrition.protein / dailyRequirement.protein) * 100,
        (nutrition.fat / dailyRequirement.fat) * 100,
        (nutrition.carbohydrates / dailyRequirement.carbohydrates) * 100,
        (nutrition.fiber / dailyRequirement.fiber) * 100,
        (nutrition.vegetables / dailyRequirement.vegetables) * 100
    ];

    const barWidth = canvas.width / labels.length - 20; // 各バーの幅
    const maxHeight = canvas.height * 0.8; // 最大バーの高さ

    values.forEach((value, index) => {
        const barHeight = Math.min((value / 100) * maxHeight, maxHeight); // 高さを最大値までに制限
        const x = index * (barWidth + 20) + 10;
        const y = canvas.height - barHeight - 30; // バーの上部を少し下げる

        // 100%以上で色を変える
        ctx.fillStyle = value > 100 ? 'rgba(255, 99, 71, 0.8)' : 'rgba(0, 123, 255, 0.7)';

        // バーの描画
        ctx.fillRect(x, y, barWidth, barHeight);

        // %表示の追加
        ctx.fillStyle = '#000';
        ctx.font = '14px Noto Sans JP';
        ctx.textAlign = 'center';
        ctx.fillText(`${value.toFixed(1)}%`, x + barWidth / 2, y - 5); // バーの上に%を表示

        // ラベルの表示
        ctx.fillText(labels[index], x + barWidth / 2, canvas.height - 10); // ラベルを下部に表示
    });
}

// ----------
// ---デバッグ用
// ----------
new MenuObject(menuObjects, {
    "display_name": "中 自家製カレー",
    "jan_code": "2121052120800",
    "price": 341,
    "romaji": "homemade_curry",
    "yolo_name": "homemade_curry",
    "energy": 0,
    "protein": 0,
    "fat": 0,
    "carbohydrates": 0,
    "fiber": 0,
    "vegetables": 0,
});
menuObjects.onItemListChanged();
// const testButton = document.getElementById('start-button');
// testButton.addEventListener('click', async()=>{
//     // ---メニューキャッシュを取得する
//     // const cache = await menuServer.getMenuCache();
//     const cache = await menuServer.removeMenuCache({
//         "display_name": "塩キャベツサラダ",
//         "jan_code": "2121052057441",
//         "price": 66,
//         "romaji": "SHIO KYABETSU SARADA",
//         "yolo_name": "salted_cabbage_salad"
//     });
//     // for (const item of cache){
//     //     menuObjects.addMenuObject(new MenuObject(menuObjects, item));
//     // }
//     // handleStartOrRetry();
//     console.log('cache:\n', cache);
// });

const debugButton = document.getElementById('debugButton');
debugButton.addEventListener('click', async () => {
    // ---ファイルから推論する
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.click();
    fileInput.addEventListener('change', async () => {
        const file = fileInput.files[0];
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = async () => {
            const base64 = reader.result.split(',')[1];
            // ---時間を記録する
            const startTime = performance.now();

            // ---以前のメニューをリセットする
            menuObjects.resetMenuObjects();

            // ---入力された画像を表示する
            const detectedImageElement = document.getElementById("detected-image");
            detectedImageElement.src = 'data:image/jpeg;base64,' + base64;
            // 画像の読み込みを待つ
            await new Promise(resolve => detectedImageElement.onload = resolve);

            // ---bboxを表示する
            // TODO
            // bboxDivの大きさを、画像の大きさに合わせる
            const bboxDiv = document.getElementById("bboxDiv")
            const detectedImageElementRect = detectedImageElement.getBoundingClientRect();
            bboxDiv.style.width = detectedImageElementRect.width + 'px';
            bboxDiv.style.height = detectedImageElementRect.height + 'px';
            bboxDiv.style.display = 'block';

            // ---推論を開始する
            const response = await fetch('/start_inference', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: base64 })
            });
            const json = await response.json();

            // ---検出画像を表示する
            document.getElementById("detected-image").src = 'data:image/jpeg;base64,' + json['image'];

            // ---検出結果を表示する
            for (const item of json['items']) {
                console.log(item);
                if (item["display_name"] !== "unknown") {
                    const menuObject = new MenuObject(menuObjects, {
                        display_name: item.display_name,
                        romaji: item.romaji,
                        yolo_name: item.yolo_name,
                        jan_code: item.jan_code,
                        price: item.price,
                        // 栄養価情報を明示的に渡す
                        energy: Number(item.energy) || 0,
                        protein: Number(item.protein) || 0,
                        fat: Number(item.fat) || 0,
                        carbohydrates: Number(item.carbohydrates) || 0,
                        fiber: Number(item.fiber) || 0,
                        vegetables: Number(item.vegetables) || 0
                    });
                    console.log('Created MenuObject:', menuObject);  // デバッグログ追加
                }
            }

            // 処理が完了したタイムスタンプを取得し、時間を表示する
            const endTime = performance.now();  // 終了時間
            const duration = (endTime - startTime) / 1000;  // 経過時間 (秒)
            document.getElementById('load-time').textContent = `処理時間: ${duration.toFixed(2)} 秒`;
        }
    });

});