# Live — SCTE-35 アドマーカー

Bitmovin Encoder API を用いて、**SCTE-35 アドマーカー**を HLS マニフェストに埋め込むライブ配信のサンプルです。SRT で取り込んだ MPEG-TS 内の SCTE-35 シグナルをエンコーダーが解析し、HLS マニフェストに広告挿入用のタグ（`#EXT-X-CUE-OUT` / `#EXT-X-CUE-IN` / `#EXT-X-SPLICEPOINT-SCTE35` など）を書き出します。SSAI（サーバーサイド広告挿入）連携を想定し、コンテナは TS、パッケージングは HLS のみとしています。出力は Linode Object Storage（Generic S3 互換）、`AKAMAI_JP_OSA` リージョンでエンコードします。

## サンプル一覧

| スクリプト | インジェスト | コンテナ | パッケージング |
| --- | --- | --- | --- |
| `create_live_srt_ingest_h264_aac_ts_hls_with_scte35.py` | SRT (MPEG-TS) | TS | HLS（SCTE-35 アドマーカー付き） |

## 特記事項

- **SCTE-35 の入力要件**: 広告マーカーの元になる SCTE-35 トリガーは、SRT で取り込む MPEG-TS ストリーム内（PES タイプ `0x86`）に含まれている必要があります。エンコーダーがこれを解析して HLS マニフェストへ反映します。
- マニフェストは `LiveHlsManifest` の `ad_marker_settings`（`HlsManifestAdMarkerSettings`）で有効化するマーカー種別を指定します。本サンプルでは `EXT_X_CUE_OUT_IN` と `EXT_X_SPLICEPOINT_SCTE35` を有効化しています。
- 多くの SSAI サービスは TS Muxing を前提とするため、本サンプルは TS / HLS のみを生成します（DASH は別の SCTE-35 シグナリング方式となるため対象外）。
- 入力に SCTE-35 が含まれない場合に備え、稼働中のライブへ手動でアドキューを挿入する任意のヘルパー（`_insert_ad_cue`、`live.scte35_cue.create` を使用）も同梱しています。

## 前提条件

- Bitmovin Encoder アカウントと API Key（ライブエンコード対応プラン）
- 出力に使用する Linode Object Storage（Generic S3 互換）バケット
- SCTE-35 を含む MPEG-TS を SRT で送出できるエンコーダー / 配信ソフト

## サンプルの利用方法

1. `API_KEY` / `ORG_ID` を設定します。
2. 出力（Linode Object Storage）の資格情報を設定します。
3. スクリプトを実行し、表示されたエンコーダー IP / ポートへ SCTE-35 付き MPEG-TS を SRT で送出します。
4. 配信を終えるときは Enter キーでライブエンコードを停止します。

## 処理結果例

HLS マニフェスト（`stream.m3u8`）に SCTE-35 由来の広告マーカーが書き込まれます。これらのマーカーを SSAI サービスやプレイヤーが解釈することで、広告挿入ポイントを認識できます。
