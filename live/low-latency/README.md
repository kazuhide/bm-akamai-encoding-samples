# Live — 低遅延（LL-HLS / LL-DASH, chunked CMAF）

Bitmovin Encoder API を用いて、**低遅延ライブ配信（LL-HLS / LL-DASH）** を行うサンプルです。チャンク化された CMAF（chunked CMAF）で出力し、セグメントを「parts / chunks」に分割して live edge を早期に配信することで、グラス・トゥ・グラスの遅延を低減します。出力は Linode Object Storage（Generic S3 互換）、`AKAMAI_JP_OSA` リージョンでエンコードします。

## サンプル一覧

| スクリプト | インジェスト | コンテナ | パッケージング |
| --- | --- | --- | --- |
| `create_live_srt_ingest_h264_aac_cmaf_ll_hls_dash.py` | SRT (LISTENER) | CMAF（chunked） | LL-HLS / LL-DASH |

## 特記事項

- 映像コーデックには低遅延向けプリセット `PresetConfiguration.LIVE_LOW_LATENCY` を使用し、keyframe interval を小さく設定します。
- Muxing は `CmafMuxing` を使用し、`frames_per_cmaf_chunk` で CMAF チャンク（LL の "part"）の粒度を指定します。チャンクが小さいほど低遅延になります。値はソースのフレームレートに対して設定します（例: 約 0.5 秒分のフレーム数）。
- DASH は `representations.cmaf.create`（`DashCmafRepresentation`）で Representation を構成します。HLS は CMAF Muxing をそのまま参照します。
- ライブマニフェストは `live_edge_offset` を小さく設定し、`ManifestGenerator.V2` で生成します。
- **再生・配信の前提**: 真の低遅延再生には LL-HLS / LL-DASH に対応したプレイヤーと、HTTP チャンク転送（chunked transfer）に対応した CDN が必要です。

## 前提条件

- Bitmovin Encoder アカウントと API Key（ライブエンコード対応プラン）
- 出力に使用する Linode Object Storage（Generic S3 互換）バケット
- SRT で送出できるエンコーダー / 配信ソフト
- LL-HLS / LL-DASH 対応のプレイヤーと、チャンク転送に対応した配信経路

## サンプルの利用方法

1. `API_KEY` / `ORG_ID` を設定します。
2. 出力（Linode Object Storage）の資格情報を設定します。
3. 必要に応じて `frames_per_cmaf_chunk` や `segment_length`、`live_edge_offset` を環境に合わせて調整します。
4. スクリプトを実行し、表示されたエンコーダー IP / ポートへ SRT で映像を送出します。
5. 配信を終えるときは Enter キーでライブエンコードを停止します。

## 処理結果例

chunked CMAF のセグメントとライブマニフェスト（`stream.m3u8` / `stream.mpd`）が出力先に生成されます。LL 対応プレイヤーで再生すると、通常の HLS / DASH より低遅延での視聴を確認できます。
