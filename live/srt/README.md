# Live — SRT インジェスト

Bitmovin Encoder API を用いて、**SRT インジェスト**によるライブ配信をエンコードするサンプルです。エンコーダーを SRT の Listener（`SrtMode.LISTENER`）として起動し、AAC 音声とともに fMP4 で出力、ライブ用の HLS / DASH マニフェストを生成します。出力は Linode Object Storage（Generic S3 互換）、`AKAMAI_JP_OSA` リージョンでエンコードします。

## サンプル一覧

| スクリプト | コーデック | レート制御 | プリセット |
| --- | --- | --- | --- |
| `create_live_srt_ingest_h264_crf_aac_fmp4_hls_dash.py` | H.264 + AAC | CRF（`crf=22`、`SINGLE_PASS`） | `LIVE_ULTRAHIGH_QUALITY` |
| `create_live_srt_ingest_h264_vbr_aac_fmp4_hls_dash.py` | H.264 + AAC | VBR（ビットレート指定） | `LIVE_ULTRAHIGH_QUALITY` |
| `create_live_srt_ingest_hevc_crf_aac_fmp4_hls_dash.py` | H.265 (HEVC) + AAC | CRF（`crf=21`、`SINGLE_PASS`） | `LIVE_HIGH_QUALITY` |
| `create_live_srt_ingest_hevc_vbr_aac_fmp4_hls_dash.py` | H.265 (HEVC) + AAC | VBR（ビットレート指定） | `LIVE_HIGH_QUALITY` |
| `create_live_srt_ingest_av1_vbr_aac_fmp4_hls_dash.py` | AV1 + AAC | VBR（`TWO_PASS`） | `VOD_SPEED` |

## 特記事項

- SRT 入力は `SrtInput(mode=SrtMode.LISTENER, port=...)` で作成します。エンコーダー側が待ち受けるため、送出側は表示されたエンコーダー IP / ポートへ接続します。
- ライブ用マニフェスト（`LiveHlsManifest` / `LiveDashManifest`）を `StartLiveEncodingRequest` に渡し、`ManifestGenerator.V2` で生成します。
- 配信フローは「ライブエンコード開始 → `RUNNING` まで待機 → エンコーダーの IP を表示 → SRT で送出 → Enter キーで停止」です。
- コーデックやレート制御（CRF / VBR）、プリセットはサンプルごとに異なります。`video_encoding_profiles` で各レンディションを定義しています。

## 前提条件

- Bitmovin Encoder アカウントと API Key（ライブエンコード対応プラン）
- 出力に使用する Linode Object Storage（Generic S3 互換）バケット
- SRT で送出できるエンコーダー / 配信ソフト

## サンプルの利用方法

1. `API_KEY` / `ORG_ID` を設定します。
2. 出力（Linode Object Storage）の資格情報を設定します。
3. スクリプトを実行し、表示されたエンコーダー IP / ポートへ SRT で映像を送出します。
4. 配信を終えるときは Enter キーでライブエンコードを停止します。

## 処理結果例

ライブ配信中、出力先にセグメントとライブマニフェスト（`stream.m3u8` / `stream.mpd`）が継続的に生成・更新されます。対応プレイヤーでマニフェスト URL を再生してライブ視聴を確認できます。
