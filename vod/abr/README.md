# VOD — 固定 ABR ラダー

Bitmovin Encoder API を用いて、固定の ABR ラダー（あらかじめ定義した解像度・ビットレートの組み合わせ）で VOD コンテンツをエンコードし、HLS / DASH で配信するための基本サンプル群です。いずれも入出力に Linode Object Storage（Generic S3 互換）を利用し、`AKAMAI_JP_OSA` リージョンでエンコードします。

## サンプル一覧

| スクリプト | コーデック | コンテナ | パッケージング | 備考 |
| --- | --- | --- | --- | --- |
| `create_vod_h264_aac_fmp4_hls_dash.py` | H.264 + AAC | fMP4 | HLS / DASH | 標準的な ABR。`VOD_HIGH_QUALITY` プリセット |
| `create_vod_h265_aac_fmp4_hls_dash.py` | H.265 (HEVC) + AAC | fMP4 | HLS / DASH | 単一 fMP4 Muxing を両マニフェストから参照 |
| `create_vod_av1_aac_fmp4_hls_dash.py` | AV1 + AAC | fMP4 | HLS / DASH | `THREE_PASS` / `VOD_QUALITY` |
| `create_vod_vp9_webm_aac_fmp4_dash.py` | VP9 + AAC | 映像 WebM / 音声 fMP4 | DASH のみ | 映像と音声を別コンテナで出力 |
| `create_vod_h264_aac_ts_fmp4_hls_dash.py` | H.264 + AAC | HLS 用 TS / DASH 用 fMP4 | HLS / DASH | パッケージングごとに Muxing を分離 |

## 特記事項

- 各スクリプト冒頭の `video_encoding_profiles` / `audio_encoding_profiles` が ABR ラダーの定義です。解像度・ビットレートを変更することで出力レンディションを調整できます。
- H.264 サンプルでは Profile（HIGH / MAIN / BASELINE）に応じて CABAC・B フレーム数・重み付き予測などの詳細パラメータを切り替えています。
- fMP4 Muxing は `segment_length=6` 秒、`segment_naming='segment_%number%.m4s'`、`init_segment_name='init.mp4'` で統一しています。
- VP9 サンプルのみ HLS を生成せず、WebM（映像）と fMP4（音声）を組み合わせた DASH を生成します。

## 前提条件

- Bitmovin Encoder アカウントと API Key
- 入出力に使用する Linode Object Storage（Generic S3 互換）バケット

## サンプルの利用方法

1. `API_KEY` / `ORG_ID` を設定します。
2. Linode Object Storage の入出力情報（アクセスキー / シークレットキー / バケット名 / ホスト名）と `INPUT_PATH` を設定します。
3. 必要に応じて `video_encoding_profiles` / `audio_encoding_profiles` を調整します。
4. スクリプトを実行するとエンコードが開始され、完了後に HLS / DASH マニフェスト（`stream.m3u8` / `stream.mpd`）が生成されます。

## 処理結果例

出力先バケットの `output/<TEST_ITEM>/` 配下に、各レンディションのセグメントとマニフェストが生成されます。生成された `stream.m3u8` / `stream.mpd` を対応プレイヤーで再生して ABR ストリーミングを確認できます。
