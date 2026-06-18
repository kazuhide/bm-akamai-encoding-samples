# Live — DRM (CENC CBC)

Bitmovin Encoder API を用いて、**DRM で暗号化したライブ配信**をエンコードするサンプルです。SRT で取り込んだライブ入力を H.264 + AAC でエンコードし、各 fMP4 Muxing に CENC CBC（Widevine / PlayReady / FairPlay）を付与して、content protection 情報を埋め込んだ HLS / DASH を生成します。出力は Linode Object Storage（Generic S3 互換）、`AKAMAI_JP_OSA` リージョンでエンコードします。

## サンプル一覧

| スクリプト | インジェスト | 暗号化 | パッケージング |
| --- | --- | --- | --- |
| `create_live_srt_ingest_h264_aac_fmp4_drm_cbc_hls_dash.py` | SRT (LISTENER) | CENC CBC（WV / PR / FP） | HLS / DASH |

## 特記事項

- 各 fMP4 Muxing は出力を指定せずに作成し、`muxings.fmp4.drm.cenc.create` で `CencDrm`（`encryption_mode=EncryptionMode.CBC`、`iv_size=IvSize.IV_16_BYTES`）に出力を付与します。1 つの CENC 設定に Widevine（`pssh`）・PlayReady（`la_url`）・FairPlay（`iv` / `uri`）をまとめて含めています。
- HLS / DASH マニフェストは Muxing の DRM 設定（`drm.cenc.list`）を参照し、`drm_id` を付与します。DASH には Representation に content protection を付与します。
- マニフェストはライブ起動前に作成し、`StartLiveEncodingRequest` に `LiveHlsManifest` / `LiveDashManifest` と `ManifestGenerator.V2` を渡して生成します。
- **DRM 鍵について（重要）**: スクリプト冒頭の `CENC_KEY` / `CENC_KID` / `CENC_WIDEVINE_PSSH` / `CENC_PLAYREADY_LA_URL` / `CENC_FAIRPLAY_IV` / `CENC_FAIRPLAY_URI` は**テスト用プレースホルダ値**です。**本番環境では必ずご自身の値に差し替えてください。**

## 前提条件

- Bitmovin Encoder アカウントと API Key（ライブエンコード・DRM 対応プラン）
- 出力に使用する Linode Object Storage（Generic S3 互換）バケット
- SRT で送出できるエンコーダー / 配信ソフト

## サンプルの利用方法

1. `API_KEY` / `ORG_ID` を設定します。
2. 出力（Linode Object Storage）の資格情報を設定します。
3. DRM 鍵の定数をご自身の値に差し替えます。
4. スクリプトを実行し、表示されたエンコーダー IP / ポートへ SRT で映像を送出します。
5. 配信を終えるときは Enter キーでライブエンコードを停止します。

## 処理結果例

DRM で暗号化されたライブセグメントと、各 DRM システムの content protection 情報を埋め込んだ HLS / DASH マニフェストが出力先に生成されます。再生テストには対象 DRM に対応したプレイヤーと有効なライセンスサーバーが必要です。
