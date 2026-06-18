# Live — RTMP インジェスト

Bitmovin Encoder API を用いて、**RTMP インジェスト**によるライブ配信をエンコードするサンプルです。H.264 + AAC を fMP4 で出力し、ライブ用の HLS / DASH マニフェストを生成します。出力は Linode Object Storage（Generic S3 互換）、`AKAMAI_JP_OSA` リージョンでエンコードします。

## サンプル一覧

| スクリプト | コーデック | レート制御 | プリセット |
| --- | --- | --- | --- |
| `create_live_rtmp_ingest_h264_crf_aac_fmp4_hls_dash.py` | H.264 + AAC | CRF（`crf=22`、`SINGLE_PASS`） | `LIVE_HIGH_QUALITY` |
| `create_live_rtmp_ingest_h264_vbr_aac_fmp4_hls_dash.py` | H.264 + AAC | VBR（ビットレート指定） | `LIVE_HIGH_QUALITY` |

## 特記事項

- ライブ用マニフェスト（`LiveHlsManifest` / `LiveDashManifest`）に timeshift・live edge offset 等を設定し、`StartLiveEncodingRequest` に渡して `ManifestGenerator.V2` で生成します。
- 配信フローは「ライブエンコード開始 → `RUNNING` まで待機 → エンコーダーの IP / Stream Key を表示 → RTMP で送出 → Enter キーで停止」です。停止後にエンコードが `FINISHED` になるまで待機します。
- Stream Key は `start_live_encoding_request` の `stream_key` で指定します（サンプルでは固定値）。

## 前提条件

- Bitmovin Encoder アカウントと API Key（ライブエンコード対応プラン）
- 出力に使用する Linode Object Storage（Generic S3 互換）バケット
- RTMP で送出できるエンコーダー / 配信ソフト

## サンプルの利用方法

1. `API_KEY` / `ORG_ID` を設定します。
2. 出力（Linode Object Storage）の資格情報を設定します。
3. スクリプトを実行し、表示された RTMP URL と Stream Key に向けて映像を送出します。
4. 配信を終えるときは Enter キーでライブエンコードを停止します。

## 処理結果例

ライブ配信中、出力先にセグメントとライブマニフェスト（`stream.m3u8` / `stream.mpd`）が継続的に生成・更新されます。対応プレイヤーでマニフェスト URL を再生してライブ視聴を確認できます。
