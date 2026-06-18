# VOD — DRM (CENC CBC)

Bitmovin Encoder API を用いて、DRM で暗号化した VOD ストリームをエンコードするサンプルです。CENC CBC モードで Widevine / PlayReady / FairPlay をまとめて付与し、content protection 情報を埋め込んだ HLS / DASH マニフェストを出力します。`AKAMAI_JP_OSA` リージョンでエンコードします。

2 つのサンプルは **入出力バックエンドの組み合わせ** が異なります。

| スクリプト | コーデック | 暗号化 | 入力 | 出力 |
| --- | --- | --- | --- | --- |
| `create_vod_h264_aac_fmp4_drm_cbc_with_hls_dash_s3_in_netstorage_out.py` | H.264 + AAC | CENC CBC（WV / PR / FP） | AWS S3 | Akamai NetStorage |
| `create_vod_h264_aac_fmp4_drm_cbc_with_hls_dash_linode_object_storage_in_out.py` | H.264 + AAC | CENC CBC（WV / PR / FP） | Linode Object Storage | Linode Object Storage |

## 特記事項

- `CencDrm` に `encryption_mode=EncryptionMode.CBC`、`iv_size=IvSize.IV_16_BYTES` を指定し、1 つの CENC 設定の中に Widevine（`pssh`）・PlayReady（`la_url`）・FairPlay（`iv` / `uri`）をまとめて含めています。
- 映像・音声の各 fMP4 Muxing に同一の CENC 設定を適用し、DASH と HLS の双方のマニフェストから参照します。DASH では Representation に content protection を付与します。
- **DRM 鍵について（重要）**: スクリプト冒頭の `CENC_KEY` / `CENC_KID` / `CENC_WIDEVINE_PSSH` / `CENC_PLAYREADY_LA_URL` / `CENC_FAIRPLAY_IV` / `CENC_FAIRPLAY_URI` は**サンプルを動作させるためのテスト用プレースホルダ値**です。**本番環境では必ずご自身の値に差し替えてください。**

## 前提条件

- Bitmovin Encoder アカウントと API Key
- DRM 暗号化機能を利用可能なプラン
- 入出力に使用するストレージ（AWS S3 / Akamai NetStorage / Linode Object Storage）の資格情報

## サンプルの利用方法

1. `API_KEY` / `ORG_ID` を設定します。
2. 入出力の資格情報（S3 / NetStorage / Linode）と `INPUT_PATH` を設定します。
3. DRM 鍵の定数をご自身の値に差し替えます。
4. スクリプトを実行します。

## 処理結果例

DRM で暗号化された Muxing と、各 DRM システムの content protection 情報を埋め込んだ HLS / DASH マニフェストが出力先に生成されます。再生テストには対象 DRM に対応したプレイヤーと有効なライセンスサーバーが必要です。
