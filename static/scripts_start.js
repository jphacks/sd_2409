////////////////////////////////////////
//////         カメラ許可         ///////
////////////////////////////////////////
// ページがよみ込まれたときに実行
navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
    stream.getVideoTracks().forEach(track => {
        track.stop()
    });
})

// ページ読み込み時にカメラリストを取得/アイコンを動かす
window.onload = function() {
    getCameras();  // カメラデバイスをリストアップ
    setTimeout(() => {
        moveToreIcon();
    }, 2000); // 2秒の遅延 
};

var socket = io(); // Socket.IOの初期化

// 会計開始ボタンを押したときの処理
document.getElementById('start-button').addEventListener('click', function() {
    const uuid = this.getAttribute('data-uuid');  // data-uuid属性からUUIDを取得
    // UUIDに対応したroomに参加し，UUIDに応じたindexページに移動
    socket.emit('join', { room: uuid });
    window.location.href = `/index/${uuid}`;  // UUIDをURLに組み込む
});

// ユーザーがカメラを選択したときに選択されたカメラIDを localStorage に保存
document.getElementById('cameraSelect').addEventListener('change', function() {
    const selectedOption = this.value;

    if (selectedOption === '') {
        // 「カメラを選択してください」が選択された場合、カメラ映像を停止
        currentStream.getTracks().forEach(track => track.stop());
    } else {
        // 選択されたカメラIDを localStorage に保存し、カメラを起動
        localStorage.setItem('selectedCameraId', selectedOption);
        changeCamera(selectedOption);
    }
});

// カメラデバイスの一覧を取得してドロップダウンに表示
function getCameras() {
    navigator.mediaDevices.enumerateDevices().then(function(devices) {
        const videoSelect = document.getElementById('cameraSelect');
        videoSelect.innerHTML = ''; // ドロップダウンをクリア
        
        // デフォルトのオプションを追加
        const defaultOption = document.createElement('option');
        defaultOption.text = 'カメラが見つかりません';
        defaultOption.value = '';
        videoSelect.appendChild(defaultOption);
        // カメラを選択するための変数を初期化
        let firstCameraId = null;
        
        // iPhoneかどうかを判定
        const agent = navigator.userAgent.toLowerCase(); // 小文字変換
        const isiPhone = /iphone|ipod/.test(agent);
        const isiPad = /ipad|macintosh/.test(agent) && "ontouchend" in document;
        
        if (isiPhone || isiPad) {
            // iPhone用の選択肢　外カメラのみ     
            const rearCameraOption = document.createElement('option');
            rearCameraOption.text = '外カメラ';
            rearCameraOption.value = 'environment';
            videoSelect.appendChild(rearCameraOption);
            firstCameraId = 'environment';
        } else {
            // PC/Android用のカメラデバイスをリストアップ
            devices.forEach(function(device) {
                if (device.kind === 'videoinput') {
                    const option = document.createElement('option');
                    option.value = device.deviceId;  // デバイスIDを値に設定
                    option.text = device.label || `カメラ ${videoSelect.length}`;  // ラベルがない場合、カメラ番号を表示
                    videoSelect.appendChild(option);
                    // 最初のカメラIDを記録
                    if (!firstCameraId) {
                        firstCameraId = device.deviceId;
                    }
                }
            });
        }
        // 最初のカメラが取得できた場合、そのカメラをデフォルトで選択し、起動
        if (firstCameraId) {
            videoSelect.value = firstCameraId;  // 最初のカメラを選択状態にする
            localStorage.setItem('selectedCameraId', firstCameraId);  // カメラIDを保存
            changeCamera(firstCameraId);  // カメラを起動
        }
    }).catch(function(err) {
        console.error("カメラデバイスの取得に失敗しました: ", err);
    });
}

////////////////////////////////////////
//////         icon動かす         ///////
////////////////////////////////////////
const toreIcon = document.getElementById('tore-icon');
// 初期位置と移動速度の設定
let posX = 0;
let posY = window.innerHeight - toreIcon.offsetHeight; // 初期位置を画面左下に設定
let dx = 2; // X方向の移動量
let dy = -2; // Y方向の移動量

// 画面サイズに応じて画像を移動させる関数
function moveToreIcon() {
    // 現在の位置に移動
    toreIcon.style.left = `${posX}px`;
    toreIcon.style.top = `${posY}px`;

    // 次の位置の計算
    posX += dx;
    posY += dy;

    // ウィンドウの幅と高さを取得
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;

    // 画像のサイズを取得
    const iconWidth = toreIcon.offsetWidth;
    const iconHeight = toreIcon.offsetHeight;

    // 端に達したら方向を反転
    if (posX <= 0 || posX + iconWidth >= windowWidth) {
        dx = -dx; // X方向を反転
    }
    if (posY <= 0 || posY + iconHeight >= windowHeight) {
        dy = -dy; // Y方向を反転
    }

    // アニメーションの更新
    requestAnimationFrame(moveToreIcon);
}
// スタイルの設定（初期位置を設定）
toreIcon.style.position = 'absolute';

////////////////////////////////////////
//////         カメラ選択         ///////
////////////////////////////////////////
let currentStream = null;
// カメラを開始する関数
function changeCamera(optionValue) {
    // 既存のカメラストリームを停止
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
    }
    
    let constraints = {};
    const agent = navigator.userAgent.toLowerCase(); // 小文字変換
    const isiPhone = /iphone|ipod/.test(agent);
    const isiPad = /ipad|macintosh/.test(agent) && "ontouchend" in document;
    
    // iPhoneの場合は facingMode、PC/Androidの場合は deviceId を使用
    if (isiPhone || isiPad) {
        constraints = {
            video: {
                facingMode: optionValue  // 'user'で内カメ、'environment'で外カメ
            }
        };
    } else {
        constraints = {
            video: {
                deviceId: { exact: optionValue }  // 選択されたデバイスIDを使用
            }
        };
    }
    // ストリームを取得し、<video>に表示
    navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
        currentStream = stream;  // 現在のストリームを保存
        const videoElement = document.getElementById('video');
        videoElement.srcObject = stream;
        videoElement.play();
    }).catch(function(err) {
        console.error("カメラの起動に失敗しました: ", err);
    });
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////
///         管理ページ関連         ///////
////////////////////////////////////////
// 管理ページボタンを押したらモーダルを表示
document.getElementById('admin-page-button').addEventListener('click', function() {
    document.getElementById('password-modal').style.display = 'block';
});

// モーダルの閉じるボタンを押したらモーダルを閉じる
document.getElementById('close-modal').addEventListener('click', function() {
    document.getElementById('password-modal').style.display = 'none';
});

// パスワード送信ボタンの処理
document.getElementById('submit-password').addEventListener('click', function() {
    const password = document.getElementById('admin-password').value;

    // サーバーにパスワードを送信して確認
    fetch('/verify_password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password: password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // パスワードが正しければ管理ページに遷移
            window.location.href = '/admin';
        } else {
            // パスワードが間違っている場合はエラーメッセージを表示
            document.getElementById('password-error').style.display = 'block';
        }
    })
    .catch(error => console.error('エラー:', error));
});

// モーダルの外側をクリックした場合にモーダルを閉じる
window.addEventListener('click', function(event) {
    if (event.target == document.getElementById('password-modal')) {
        document.getElementById('password-modal').style.display = 'none';
    }
});
