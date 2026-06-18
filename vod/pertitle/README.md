# VOD — Per-Title エンコーディング

Bitmovin Encoder API を用いて **Per-Title エンコーディング** を行うサンプルです。Per-Title は入力コンテンツの複雑さをエンコード時に解析し、タイトルごとに最適な ABR ラダー（解像度・ビットレートの組み合わせ）を自動的に決定する機能です。固定ラダーを用意する代わりに Per-Title テンプレートを定義しておくことで、実際のレンディションをエンコーダーが自動展開します。入出力に Linode Object Storage（Generic S3 互換）を利用し、`AKAMAI_JP_OSA` リージョンでエンコードします。

## サンプル

| スクリプト | コーデック | コンテナ | パッケージング |
| --- | --- | --- | --- |
| `create_vod_pertitle_h264_aac_fmp4_hls_dash.py` | H.264 + AAC | fMP4 | HLS / DASH |

## 特記事項

- 映像ストリームを Per-Title テンプレート（`StreamMode.PER_TITLE_TEMPLATE`）として定義しています。`video_encoding_profiles` の各エントリはテンプレートであり、実際の ABR ラダーはエンコード時に自動展開されます。
- レンディション数はエンコード完了後に確定するため、**エンコードを実行してから** HLS / DASH マニフェストを生成しています。マニフェスト生成時は Muxing 一覧を走査し、テンプレートの Stream（`PER_TITLE_TEMPLATE` を含む mode）はスキップして、展開済みレンディションのみを追加します。
- 展開後の各レンディションで出力パスが衝突しないよう、出力パスにプレースホルダーを用いています。

## 前提条件

- Bitmovin Encoder アカウントと API Key
- Per-Title エンコーディングを利用可能なプラン
- 入出力に使用する Linode Object Storage（Generic S3 互換）バケット

## サンプルの利用方法

1. `API_KEY` / `ORG_ID` を設定します。
2. Linode Object Storage の入出力情報と `INPUT_PATH` を設定します。
3. 必要に応じて Per-Title テンプレート（`video_encoding_profiles`）を調整します。
4. スクリプトを実行します。エンコード完了後にマニフェストが生成されます。

## 処理結果例

Per-Title により展開された各レンディションが出力先に生成され、それらを参照する `stream.m3u8` / `stream.mpd` が出力されます。入力に応じて最適化された ABR ラダーになっていることを確認できます。
