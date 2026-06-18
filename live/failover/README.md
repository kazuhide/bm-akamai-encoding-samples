# Live — 冗長インジェスト（フェイルオーバー）

Bitmovin Encoder API を用いて、**冗長 RTMP インジェスト（main + backup）** によるフェイルオーバー対応のライブ配信をエンコードするサンプルです。`RedundantRtmpInput` に主系・予備系の 2 つのインジェストポイントを定義し、主系が途切れた場合に予備系へ自動的に切り替えます。出力は Linode Object Storage（Generic S3 互換）、`AKAMAI_JP_OSA` リージョンでエンコードします。

## サンプル一覧

| スクリプト | インジェスト | コーデック | パッケージング |
| --- | --- | --- | --- |
| `create_live_rtmp_redundant_ingest_h264_vbr_aac_fmp4_hls_dash.py` | RTMP 冗長（main + backup） | H.264 (VBR) + AAC | HLS / DASH |

## 特記事項

- 入力は `RedundantRtmpInput` で作成し、`ingest_points` に主系（`application_name='live'` / `stream_key='primary'`）と予備系（`application_name='live-backup'` / `stream_key='backup'`）の 2 つの `RtmpIngestPoint` を指定します。`delay_threshold`（ミリ秒）で切り替えのしきい値を設定します。
- ストリームキーは各インジェストポイント側で定義するため、`StartLiveEncodingRequest` の `stream_key` は `"notused"` を指定します。
- ライブ起動後、主系・予備系それぞれの RTMP URL（`rtmp://<encoder_ip>/<application_name>/<stream_key>`）を表示します。コントリビューション側のエンコーダーから、両系へ同一ソースを送出してください。
- 主系・予備系のインジェストは Bitmovin の標準機能として追加費用なしで利用できます。

## 前提条件

- Bitmovin Encoder アカウントと API Key（ライブエンコード対応プラン）
- 出力に使用する Linode Object Storage（Generic S3 互換）バケット
- RTMP で送出できるエンコーダー / 配信ソフト（冗長構成のため主系・予備系の 2 系統を推奨）

## サンプルの利用方法

1. `API_KEY` / `ORG_ID` を設定します。
2. 出力（Linode Object Storage）の資格情報を設定します。
3. スクリプトを実行し、表示された主系・予備系の RTMP URL へ映像を送出します。
4. 配信を終えるときは Enter キーでライブエンコードを停止します。

## 処理結果例

配信中、出力先にセグメントとライブマニフェスト（`stream.m3u8` / `stream.mpd`）が継続的に生成されます。主系を停止すると予備系へ切り替わり、配信が継続されることを確認できます。
