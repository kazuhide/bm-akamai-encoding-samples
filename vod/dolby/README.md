# VOD — Dolby Vision + Dolby Atmos

Bitmovin Encoder API を用いて、**Dolby Vision**（HDR 映像）と **Dolby Atmos**（イマーシブ音声）を含む VOD ストリームをエンコードするサンプルです。映像は H.265（`H265DynamicRangeFormat.DOLBY_VISION`）、音声は Dolby Atmos でエンコードし、HLS / DASH を生成します。入力には HTTPS 入力（Netflix のオープンコンテンツ「Sol Levante」）を利用し、出力は Linode Object Storage、`AKAMAI_JP_OSA` リージョンでエンコードします。

2 つのサンプルは **Dolby Atmos の入力フォーマット** が異なります。

| スクリプト | 映像 | 音声（入力フォーマット） | パッケージング |
| --- | --- | --- | --- |
| `create_vod_dolbyvision_dolbyatmos_adm_with_hls_dash_https_input.py` | H.265 Dolby Vision | Dolby Atmos **ADM**（`DolbyAtmosInputFormat.ADM`） | HLS / DASH |
| `create_vod_dolbyvision_dolbyatmos_damf_with_hls_dash_https_input.py` | H.265 Dolby Vision | Dolby Atmos **DAMF**（`DolbyAtmosInputFormat.DAMF`） | HLS / DASH |

## 特記事項

- 映像は `DolbyVisionInputStream`（映像本体＋メタデータの sidecar XML）から取り込み、H.265 の Dolby Vision として出力します。コーデック設定には HDR 向けのチューニング（`AdaptiveQuantMode` / `rc_lookahead` 等）を適用しています。
- 音声は `DolbyAtmosIngestInputStream` で取り込み、`DolbyAtmosAudioConfiguration` でエンコードします。ADM / DAMF の違いは入力フォーマットの指定（`input_format`）です。
- マニフェスト生成は `ManifestGenerator.V2` を使用します。
- 入力の HTTPS ホストと各入力パスはサンプル冒頭の定数（`HTTPS_INPUT_HOST` ほか）で定義しています。別の入力を使う場合はここを変更します。

## 前提条件

- Bitmovin Encoder アカウントと API Key
- Dolby Vision / Dolby Atmos を利用可能なプラン
- 出力に使用する Linode Object Storage（Generic S3 互換）バケット
- 入力に使用する HTTPS アクセス可能なソース（既定では Netflix オープンコンテンツを参照）

## サンプルの利用方法

1. `API_KEY` / `ORG_ID` を設定します。
2. 出力（Linode Object Storage）の資格情報を設定します。必要に応じて入力（`HTTPS_INPUT_HOST` ほか）を変更します。
3. スクリプトを実行します。

## 処理結果例

Dolby Vision 映像と Dolby Atmos 音声を含む Muxing と、それらを参照する HLS / DASH マニフェストが出力先に生成されます。再生には Dolby Vision / Dolby Atmos に対応した再生環境が必要です。
