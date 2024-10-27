# TORE（自動会計システム） #

[![IMAGE ALT TEXT HERE](https://jphacks.com/wp-content/uploads/2024/07/JPHACKS2024_ogp.jpg)](https://www.youtube.com/watch?v=DZXUkEj-CSI)


# 製品概要 #

## 背景（製品開発のきっかけ、課題等） #
学食ではピーク時の混雑が大きな課題となり、利用者の満足度が低下していました。この問題を解消するため、私たちはレジの自動化システム**「TORE」**を開発し、運営の効率化を目指しました。自動化によりレジ待ち時間の削減は実現しましたが、新メニュー導入時の料理のラベルづけ（料理名やカテゴリの設定）に時間と労力がかかり、運営者の負担が新たな課題として浮上しました。そこで、利用者が備え付けのタッチパネルからラベルづけを行う仕組みを導入し、AIモデルの精度向上とメニュー更新の効率化を図りました。

## 製品説明（具体的な製品の説明） #
「TORE」は、学食利用者が備え付けのタッチパネルから料理のラベルづけを行い、蓄積されたデータをAIモデルの改善に活用するシステムです。これにより、運営者の手を借りずにメニューの更新が効率化されます。

また、学食の利用体験を向上させるために、ルーレット機能を実装しました。ルーレットの当選者はその日の食事が無料となり、当選時にはサーボモーターでロゴが回転し、LEDライトが点滅する演出が楽しめます。これにより、利用者の満足度と学食の利用意欲が向上します。

## 特長 #
### 1. 利用者による料理のラベルづけ機能 #
タッチパネルから新メニューのラベルづけを行うことで、運営者の負担を軽減し、メニュー更新を支援します。

### 2. ルーレットによる無料提供のチャンス #
ルーレットが定期的に起動し、当選者のその日の食事が無料になります。これにより、学食利用の楽しみを提供し、利用促進につながります。

### 3. ハードウェア演出による特別な体験 #
ルーレットの当選時には、サーボモーターでロゴが回転し、LEDライトが点滅することで、特別な演出を提供します。

## 解決できること #

レジ待ち時間の削減：自動会計によってピーク時の混雑を解消し、利用者の満足度を向上させます。
運営者の負担軽減：ラベルづけ作業を利用者に委ねることで、メニュー更新の手間を削減します。
利用者体験の向上と利用促進：ルーレットの無料提供で学食の利用意欲を高め、売上向上につなげます。
## 今後の展望 #

東北大学全学食への展開：川内キャンパスの学食での実証を経て、東北大学全学食へ展開します。
全国の学食への展開：東北大学での成功をもとに、他大学の学食への導入を進め、全国規模での展開を目指します。
人気メニュー予測システムの導入：蓄積データを活用して売れ筋メニューを予測し、運営の効率化を支援します。
データに基づくルーレット戦略の最適化：売上データを活用し、ルーレットの還元方法を売上向上に直結する形で最適化し、利用者満足度と経営効果を両立します。
## 注力したこと（こだわり等） #

UIUXデザイン：誰でも簡単に操作できるタッチパネル設計で、スムーズな利用体験を提供します。
ハードウェア演出：サーボモーターとLEDライトによる特別な演出で、利用者に楽しみを提供します。
売上促進：ルーレットによる無料提供で利用者の関心を高め、学食利用の促進と売上向上を目指します。
## 開発技術 #

### 活用した技術 #

#### API・データ #

WebSocket：リアルタイム通信でデータを反映
YOLOv9：学食メニューを高精度に認識するAIモデル
#### フレームワーク・ライブラリ・モジュール #

Python：システム全体の開発と管理
Flask：Webアプリケーション構築
JavaScript：フロントエンドの実装
OpenCV：画像処理
#### デバイス #

Raspberry Pi：画像処理とデータ送信
ESP32：通信モジュール
Arduino + サーボモーター：ロゴ回転演出
LEDライト：ルーレット当選時の点滅演出
## 独自技術 #

利用者参加型の料理ラベルづけ機能：タッチパネルを使ったラベルづけで、AIモデルの精度向上に貢献します。
ルーレットとハードウェア演出の融合：サーボモーターでロゴを回転させ、LEDライトを点滅させることで、当選者のその日の食事を無料にする仕組みを提供します。
YOLOv9のカスタマイズ：学食メニューの認識に特化したAIモデルを実装し、高精度な認識を実現します。
重要なcommit_id：commit_id_123456 にて、ラベルづけ機能の実装内容を確認可能です。
