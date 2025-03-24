# bm-akamai-encoding-samples

本リポジトリは、Bitmovinエンコーダーを利用して Akamai Connected Cloud 上でビデオコンテンツをエンコードおよび配信するためのサンプルスクリプトを集めたものです。サンプルはVOD（オンデマンド動画）およびLive
（ライブ配信）の両方のユースケースを対象としており、多様なフォーマットとエンコード設定を含んでいます。

## 構成

### VOD (Video On Demand)

以下のフォーマットでエンコードするサンプルが含まれています。

- **H.264/AAC（fMP4形式、HLSおよびDASH）**
  - `create_vod_h264_aac_fmp4_hls_dash.py`

- **H.265/AAC（fMP4形式、HLSおよびDASH）**
  - `create_vod_h265_aac_fmp4_hls_dash.py`

- **VP9/WebM（AAC、fMP4形式、DASH）**
  - `create_vod_vp9_webm_aac_fmp4_dash.py`

- **H.264/AAC（TSおよびfMP4形式、HLSおよびDASH）**
  - `create_vod_h264_aac_ts_fmp4_hls_dash.py`

- **Dolby VisionおよびDolby Atmos（ADMおよびDAMF形式）**
  - HTTPS入力からのエンコードに対応
  - `create_vod_dolbyvision_dolbyatmos_adm_with_hls_dash_https_input.py`
  - `create_vod_dolbyvision_dolbyatmos_damf_with_hls_dash_https_input.py`

- **AV1/AAC（fMP4形式、HLSおよびDASH）**
  - `create_vod_av1_aac_fmp4_hls_dash.py`

- **Per-Titleエンコーディング（H.264/AAC、fMP4形式、HLSおよびDASH）**
  - `create_vod_pertitle_h264_aac_fmp4_hls_dash.py`

- **H.264/AAC + DRM (CENC CBC)（fMP4形式、HLSおよびDASH）**
  - Widevine、PlayReady、FairPlayの複数DRMに対応
  - Amazon S3入力とAkamai NetStorage出力: `create_vod_h264_aac_fmp4_drm_cbc_with_hls_dash_s3_in_netstorage_out.py`
  - Linode Object Storage入出力: `create_vod_h264_aac_fmp4_drm_cbc_with_hls_dash_linote_object_storage_in_out.py`

### Live（ライブ配信）

ライブ配信で使用可能な以下のサンプルスクリプトが含まれています。

- **RTMPインジェスト（H.264、CRFおよびVBRエンコーディング、AAC、fMP4形式、HLSおよびDASH）**
  - `create_live_rtmp_ingest_h264_crf_aac_fmp4_hls_dash.py`
  - `create_live_rtmp_ingest_h264_vbr_aac_fmp4_hls_dash.py`

- **SRTインジェスト（AV1、H.265、H.264の各種エンコーディング設定、AAC、fMP4形式、HLSおよびDASH）**
  - `create_live_srt_ingest_av1_vbr_aac_fmp4_hls_dash.py`
  - `create_live_srt_ingest_hevc_vbr_aac_fmp4_hls_dash.py`
  - `create_live_srt_ingest_h264_crf_aac_fmp4_hls_dash.py`
  - `create_live_srt_ingest_hevc_crf_aac_fmp4_hls_dash.py`
  - `create_live_srt_ingest_h264_vbr_aac_fmp4_hls_dash.py`

## 使用方法

### システム条件
Python 2.7 もしくは Python 3.4 - 3.11 推奨

### セットアップ方法
pip コマンドを利用し、Python 用の Bitmovin SDK を取得します。Bitmovin エンコーダーに新しい機能が追加され、API に新しいエンドポイントやパラメータが追加された場合、SDK を更新しないと機能が利用できない場合があります。詳細な API の追加機能についてはリリースノートを参照ください。（https://bitmovin.com/docs/encoding/changelogs/rest)

以下のいずれかの方法でSDKをインストールしてください。

```sh
pip install bitmovin-api-sdk-python
```

または

```sh
pip install -r requirements.txt
```

有効な Bitmovin API key および Organization ID をスクリプトに設定します。API key は Bitmovin アカウントごとに発行され、スクリプトを実行すると Organization ID に紐づくサブスクリプションプランを消費してエンコードを行います。

```python
API_KEY = '<INSERT YOUR API KEY>'
ORG_ID = '<INSERT YOUR ORG ID>'
```

入出力ファイルが保存されている場所にアクセスするための情報、入力ファイルパス、出力先パスを指定します。Akamai Compute Cloud を利用した入出力設定はスクリプト内に用意されているため、各入出力にアクセスするために必要な情報を設定します。設定が必要なパラメータはスクリプトごとに異なる場合があるため、詳細はスクリプト内の記述をご確認ください。

```python
LINODE_OBJECT_STORAGE_INPUT_ACCESS_KEY = '<INSERT_YOUR_ACCESS_KEY>'
LINODE_OBJECT_STORAGE_INPUT_SECRET_KEY = '<INSERT_YOUR_SECRET_KEY>'
LINODE_OBJECT_STORAGE_INPUT_BUCKET_NAME = '<INSERT_YOUR_BUCKET_NAME>'
LINODE_OBJECT_STORAGE_INPUT_HOST_NAME = '<INSERT_YOUR_INPUT_HOST_NAME>'

INPUT_PATH = '/path/to/your/input/file.mp4'
# e.g. 'inputs/big_buck_bunny_1080p_h264.mov'

LINODE_OBJECT_STORAGE_OUTPUT_ACCESS_KEY = '<INSERT_YOUR_ACCESS_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_SECRET_KEY = '<INSERT_YOUR_SECRET_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_BUCKET_NAME = '<INSERT_YOUR_BUCKET_NAME>'
LINODE_OBJECT_STORAGE_OUTPUT_HOST_NAME = '<INSERT_YOUR_INPUT_HOST_NAME>'

OUTPUT_BASE_PATH = f'output/path/to/this/job/'
```

---

詳細は各スクリプト内のコメントおよび公式ドキュメントをご参照ください。

