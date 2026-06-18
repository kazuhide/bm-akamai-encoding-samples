# bm-akamai-encoding-samples

本リポジトリは、Bitmovin Encoder を利用して **Akamai Connected Cloud**（リージョン `AKAMAI_JP_OSA`）上でビデオコンテンツをエンコードおよび配信するためのサンプルスクリプト（Python）を集めたものです。VOD（オンデマンド）と Live（ライブ配信）の双方を対象とし、多様なコーデック・コンテナ・パッケージング・DRM の設定例を含みます。

## 構成

サンプルは用途（VOD / Live）と機能ごとにディレクトリを分けています。各ディレクトリの README に、サンプルの一覧・特記事項・利用方法をまとめています。

### VOD（オンデマンド）

- [`vod/abr`](vod/abr/) — 固定 ABR ラダーの基本サンプル（H.264 / H.265 / AV1 / VP9 / TS）
- [`vod/pertitle`](vod/pertitle/) — Per-Title エンコーディング
- [`vod/drm`](vod/drm/) — DRM（CENC CBC、Widevine / PlayReady / FairPlay）
- [`vod/dolby`](vod/dolby/) — Dolby Vision + Dolby Atmos（ADM / DAMF）

### Live（ライブ配信）

- [`live/rtmp`](live/rtmp/) — RTMP インジェスト（H.264、CRF / VBR）
- [`live/srt`](live/srt/) — SRT インジェスト（H.264 / H.265 / AV1、CRF / VBR）

## 使用方法

### システム条件

- 各サンプルスクリプトの実行には Python 3.6 以降（f-string を使用）が必要です。
- 依存管理に `uv` を利用する場合は Python 3.13 を前提とします（`pyproject.toml` / `.python-version`）。

### セットアップ

Python 用の Bitmovin SDK を取得します。Bitmovin Encoder に新機能が追加され API に新しいエンドポイントやパラメータが追加された場合、SDK を更新しないと利用できないことがあります（[リリースノート](https://bitmovin.com/docs/encoding/changelogs/rest)）。

以下のいずれかの方法でセットアップします。

```sh
# pip を利用する場合
pip install bitmovin-api-sdk
# または
pip install -r requirements.txt
```

```sh
# uv を利用する場合（pyproject.toml / uv.lock で固定された依存を使用）
uv sync
```

有効な Bitmovin API key および Organization ID をスクリプトに設定します。API key は Bitmovin アカウントごとに発行され、スクリプトを実行すると Organization ID に紐づくサブスクリプションプランを消費してエンコードを行います。

```python
API_KEY = '<INSERT YOUR API KEY>'
ORG_ID = '<INSERT YOUR ORG ID>'
```

入出力ファイルへアクセスするための情報、入力ファイルパス、出力先パスを設定します。利用するバックエンド（Linode Object Storage / AWS S3 / Akamai NetStorage / HTTPS 入力）はサンプルにより異なります。設定が必要なパラメータの詳細は各スクリプトおよび各ディレクトリの README をご確認ください。

```python
# 例: Linode Object Storage（Generic S3 互換）を入出力に使う場合
LINODE_OBJECT_STORAGE_INPUT_ACCESS_KEY = '<INSERT_YOUR_ACCESS_KEY>'
LINODE_OBJECT_STORAGE_INPUT_SECRET_KEY = '<INSERT_YOUR_SECRET_KEY>'
LINODE_OBJECT_STORAGE_INPUT_BUCKET_NAME = '<INSERT_YOUR_BUCKET_NAME>'
LINODE_OBJECT_STORAGE_INPUT_HOST_NAME = '<INSERT_YOUR_INPUT_HOST_NAME>'

INPUT_PATH = '/path/to/your/input/file.mp4'

LINODE_OBJECT_STORAGE_OUTPUT_ACCESS_KEY = '<INSERT_YOUR_ACCESS_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_SECRET_KEY = '<INSERT_YOUR_SECRET_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_BUCKET_NAME = '<INSERT_YOUR_BUCKET_NAME>'
LINODE_OBJECT_STORAGE_OUTPUT_HOST_NAME = '<INSERT_YOUR_OUTPUT_HOST_NAME>'
```

> DRM サンプルでは、スクリプト冒頭の DRM 鍵はテスト用のプレースホルダ値です。本番環境では必ずご自身の値に差し替えてください。詳細は [`vod/drm`](vod/drm/) を参照してください。

---

詳細は各ディレクトリの README および各スクリプト内のコメント、[Bitmovin 公式ドキュメント](https://bitmovin.com/docs/encoding)をご参照ください。

なお、本リポジトリは Bitmovin 公式のサンプル実装ではありません。一実装例として参照ください。
