import time

from bitmovin_api_sdk import BitmovinApi
from bitmovin_api_sdk import HttpsInput, S3AccessStyle, S3SignatureVersion, GenericS3Output
from bitmovin_api_sdk import Encoding, CloudRegion
from bitmovin_api_sdk import EncodingOutput, AclEntry, AclPermission
from bitmovin_api_sdk import DolbyVisionInputStream, Stream, StreamInput, MuxingStream, StreamMode
from bitmovin_api_sdk import DolbyAtmosAudioConfiguration, DolbyAtmosLoudnessControl, DolbyAtmosMeteringMode
from bitmovin_api_sdk import DolbyAtmosDialogueIntelligence, DolbyAtmosIngestInputStream, DolbyAtmosInputFormat
from bitmovin_api_sdk import H265VideoConfiguration, CodecConfigType
from bitmovin_api_sdk import H265DynamicRangeFormat, MaxCtuSize, MotionSearch, TuInterDepth, TuIntraDepth
from bitmovin_api_sdk import AdaptiveQuantMode
from bitmovin_api_sdk import Fmp4Muxing
from bitmovin_api_sdk import DashManifest, Period, VideoAdaptationSet, AudioAdaptationSet
from bitmovin_api_sdk import DashFmp4Representation, DashRepresentationType, DashRepresentationTypeMode
from bitmovin_api_sdk import HlsManifest, HlsVersion, AudioMediaInfo, StreamInfo
from bitmovin_api_sdk import MessageType, StartEncodingRequest, ManifestResource, ManifestGenerator
from bitmovin_api_sdk import Status

TEST_ITEM = "vod-dolbyvision-dolbyatmos-adm-hls-dash-fmp4-https-input"

API_KEY = '<INSERT YOUR API KEY>'
ORG_ID = '<INSERT YOUR ORG ID>'

# from https://opencontent.netflix.com/
HTTPS_INPUT_HOST = 'apac-inputs.s3.ap-southeast-1.amazonaws.com'
DOLBY_VISION_INPUT_PATH = "netflix-opencontent/SolLevante/dolbyvision/sollevante_j2k.mxf"
DOLBY_VISION_INPUT_METADATA = "netflix-opencontent/SolLevante/dolbyvision/sollevante_j2k_sidecar.xml"
DOLBY_ATMOS_ADM_PATH = 'netflix-opencontent/SolLevante/atmos-adm/sollevante_lp_v01_DAMF_Nearfield_48k_24b_24.wav'

LINODE_OBJECT_STORAGE_OUTPUT_ACCESS_KEY = '<INSERT_YOUR_ACCESS_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_SECRET_KEY = '<INSERT_YOUR_SECRET_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_BUCKET_NAME = '<INSERT_YOUR_BUCKET_NAME>'
LINODE_OBJECT_STORAGE_OUTPUT_HOST_NAME = '<INSERT_YOUR_INPUT_HOST_NAME>'

OUTPUT_BASE_PATH = 'output/{}/'.format(TEST_ITEM)

bitmovin_api = BitmovinApi(api_key=API_KEY, tenant_org_id=ORG_ID)

encoding_profiles_h265_dolbyvision = [
    dict(height=1080, bitrate=2_000_000, level=None, aqs=0.5, mode=StreamMode.STANDARD, dynamic_range=H265DynamicRangeFormat.DOLBY_VISION),
    dict(height=540, bitrate=1_000_000, level=None, aqs=1.2, mode=StreamMode.STANDARD, dynamic_range=H265DynamicRangeFormat.DOLBY_VISION)
]

encoding_profiles_atmos = [
    dict(bitrate=448000, rate=48_000)
]


def main():
    # === Input and Output definition ===
    https_input = bitmovin_api.encoding.inputs.https.create(
        https_input=HttpsInput(
            host=HTTPS_INPUT_HOST,
            name='Test HTTPS Input'))
    output = bitmovin_api.encoding.outputs.generic_s3.create(
        generic_s3_output=GenericS3Output(
            access_key=LINODE_OBJECT_STORAGE_OUTPUT_ACCESS_KEY,
            secret_key=LINODE_OBJECT_STORAGE_OUTPUT_SECRET_KEY,
            bucket_name=LINODE_OBJECT_STORAGE_OUTPUT_BUCKET_NAME,
            host=LINODE_OBJECT_STORAGE_OUTPUT_HOST_NAME,
            access_style=S3AccessStyle.VIRTUAL_HOSTED,
            ssl=True,
            port=443,
            signature_version=S3SignatureVersion.V4,
            name='Test Linote Object Storage Output'))

    # === Encoding definition ===
    encoding = bitmovin_api.encoding.encodings.create(
        encoding=Encoding(
            name=f"[{TEST_ITEM}] DolbyVision / DolbyAtmos (ADM)",
            cloud_region=CloudRegion.AKAMAI_JP_OSA,
            encoder_version='STABLE'))

    # === Input Stream definition ===
    video_ingest_input_stream = bitmovin_api.encoding.encodings.input_streams.dolby_vision.create(
        encoding_id=encoding.id,
        dolby_vision_input_stream=DolbyVisionInputStream(
            input_id=https_input.id,
            video_input_path=DOLBY_VISION_INPUT_PATH,
            metadata_input_path=DOLBY_VISION_INPUT_METADATA))

    audio_ingest_input_stream = bitmovin_api.encoding.encodings.input_streams.dolby_atmos.create(
        encoding_id=encoding.id,
        dolby_atmos_ingest_input_stream=DolbyAtmosIngestInputStream(
            input_id=https_input.id,
            input_path=DOLBY_ATMOS_ADM_PATH,
            input_format=DolbyAtmosInputFormat.ADM))
    video_input_stream = StreamInput(input_stream_id=video_ingest_input_stream.id)
    audio_input_stream = StreamInput(input_stream_id=audio_ingest_input_stream.id)

    # === Video Codec Configuration definition ===
    video_encoding_configs = []
    for idx, _ in enumerate(encoding_profiles_h265_dolbyvision):
        profile_h265 = encoding_profiles_h265_dolbyvision[idx]
        encoding_config = dict(profile_h265=profile_h265)
        encoding_config['h265_codec'] = bitmovin_api.encoding.configurations.video.h265.create(
            h265_video_configuration=H265VideoConfiguration(
                name='Sample video codec configuration',
                height=profile_h265.get("height"),
                bitrate=profile_h265.get("bitrate"),
                max_bitrate=profile_h265.get("bitrate") * 2,
                bufsize=profile_h265.get("bitrate") * 4,
                level=profile_h265.get("level"),
                dynamic_range_format=profile_h265.get("dynamic_range"),
                max_keyframe_interval=2,
                min_keyframe_interval=2,
                rc_lookahead=60,
                sub_me=5,
                max_ctu_size=MaxCtuSize.S64,
                motion_search=MotionSearch.STAR,
                tu_intra_depth=TuIntraDepth.D4,
                tu_inter_depth=TuInterDepth.D4,
                weight_prediction_on_p_slice=True,
                weight_prediction_on_b_slice=True,
                scene_cut_threshold=40,
                motion_search_range=92,
                adaptive_quantization_mode=AdaptiveQuantMode.AUTO_VARIANCE_DARK_SCENES,
                adaptive_quantization_strength=profile_h265.get('aqs'),
                psy_rate_distortion_optimization=0,
                psy_rate_distortion_optimized_quantization=0,
                qp_min=15,
                sao=True))
        video_encoding_configs.append(encoding_config)

    # === Audio Codec Configuration definition ===
    audio_encoding_configs = []
    for idx, _ in enumerate(encoding_profiles_atmos):
        profile_atmos = encoding_profiles_atmos[idx]
        encoding_config = dict(profile_atmos=profile_atmos)
        encoding_config['atmos_codec'] = bitmovin_api.encoding.configurations.audio.dolby_atmos.create(
            dolby_atmos_audio_configuration=DolbyAtmosAudioConfiguration(
                bitrate=profile_atmos.get("bitrate"),
                rate=profile_atmos.get("rate"),
                loudness_control=DolbyAtmosLoudnessControl(
                    metering_mode=DolbyAtmosMeteringMode.ITU_R_BS_1770_4,
                    dialogue_intelligence=DolbyAtmosDialogueIntelligence.ENABLED,
                    speech_threshold=15
                )
            ))
        audio_encoding_configs.append(encoding_config)

    # === Video Stream definition ===
    for encoding_config in video_encoding_configs:
        encoding_profile = encoding_config.get("profile_h265")
        video_stream = Stream(codec_config_id=encoding_config.get("h265_codec").id,
                              input_streams=[video_input_stream],
                              name='Stream H265 {}p'.format(encoding_profile.get('height')),
                              mode=encoding_profile.get('mode'))
        encoding_config['h265_stream'] = bitmovin_api.encoding.encodings.streams.create(
            encoding_id=encoding.id, stream=video_stream)

    # === Audio Stream definition ===
    for encoding_config in audio_encoding_configs:
        encoding_profile = encoding_config.get("profile_atmos")
        audio_stream = Stream(
            codec_config_id=encoding_config.get("atmos_codec").id,
            input_streams=[audio_input_stream],
            name='Stream Atmos {}bps'.format(encoding_profile.get('bitrate')),
            mode=StreamMode.STANDARD
        )
        encoding_config['atmos_stream'] = bitmovin_api.encoding.encodings.streams.create(
            encoding_id=encoding.id, stream=audio_stream)

    # === Fmp4 Muxings ===
    for encoding_config in video_encoding_configs:
        encoding_profile = encoding_config.get("profile_h265")
        video_muxing_stream = MuxingStream(stream_id=encoding_config['h265_stream'].id)
        video_muxing_output = EncodingOutput(output_id=output.id,
                                             output_path=OUTPUT_BASE_PATH + "video/{}".format(encoding_profile.get('height')),
                                             acl=[AclEntry(permission=AclPermission.PUBLIC_READ)])
        bitmovin_api.encoding.encodings.muxings.fmp4.create(
            encoding_id=encoding.id,
            fmp4_muxing=Fmp4Muxing(
                segment_length=6,
                segment_naming='seg_%number%.m4s',
                init_segment_name='init.mp4',
                streams=[video_muxing_stream],
                outputs=[video_muxing_output],
                name="Video FMP4 Muxing {}p".format(encoding_profile.get('height'))))

    for encoding_config in audio_encoding_configs:
        encoding_profile = encoding_config.get("profile_atmos")
        audio_muxing_stream = MuxingStream(stream_id=encoding_config['atmos_stream'].id)
        audio_muxing_output = EncodingOutput(output_id=output.id,
                                             output_path=OUTPUT_BASE_PATH + "audio/{}".format(encoding_profile.get('bitrate')),
                                             acl=[AclEntry(permission=AclPermission.PUBLIC_READ)])
        bitmovin_api.encoding.encodings.muxings.fmp4.create(
            encoding_id=encoding.id,
            fmp4_muxing=Fmp4Muxing(
                segment_length=6,
                segment_naming='seg_%number%.m4s',
                init_segment_name='init.mp4',
                streams=[audio_muxing_stream],
                outputs=[audio_muxing_output],
                name="Audio FMP4 Muxing {}bps".format(encoding_profile.get('bitrate'))))

    # === Start Encoding settings together with DASh & HLS Manifest definition ===
    dash_manifest = _create_dash_manifest(encoding_id=encoding.id, output=output, output_path=OUTPUT_BASE_PATH)
    hls_manifest = _create_hls_manifest(encoding_id=encoding.id, output=output, output_path=OUTPUT_BASE_PATH)

    start_encoding_request = StartEncodingRequest(
        vod_dash_manifests=[ManifestResource(manifest_id=dash_manifest.id)],
        vod_hls_manifests=[ManifestResource(manifest_id=hls_manifest.id)],
        manifest_generator=ManifestGenerator.V2
    )
    _execute_encoding(encoding=encoding, start_encoding_request=start_encoding_request)


def _execute_encoding(encoding, start_encoding_request):
    bitmovin_api.encoding.encodings.start(encoding_id=encoding.id, start_encoding_request=start_encoding_request)

    task = _wait_for_enoding_to_finish(encoding_id=encoding.id)

    while task.status is not Status.FINISHED and task.status is not Status.ERROR:
        task = _wait_for_enoding_to_finish(encoding_id=encoding.id)

    if task.status is Status.ERROR:
        _log_task_errors(task=task)
        raise Exception("Encoding failed")

    print("Encoding finished successfully")


def _create_dash_manifest(encoding_id, output, output_path):
    manifest_output = EncodingOutput(output_id=output.id,
                                     output_path=output_path,
                                     acl=[AclEntry(permission=AclPermission.PUBLIC_READ)])
    dash_manifest = bitmovin_api.encoding.manifests.dash.create(
        dash_manifest=DashManifest(
            manifest_name='stream.mpd',
            outputs=[manifest_output],
            name='DASH Manifest'))
    period = bitmovin_api.encoding.manifests.dash.periods.create(
        manifest_id=dash_manifest.id,
        period=Period())
    video_adaptation_set = bitmovin_api.encoding.manifests.dash.periods.adaptationsets.video.create(
        video_adaptation_set=VideoAdaptationSet(),
        manifest_id=dash_manifest.id,
        period_id=period.id)

    audio_adaptation_set = bitmovin_api.encoding.manifests.dash.periods.adaptationsets.audio.create(
        audio_adaptation_set=AudioAdaptationSet(lang='en'),
        manifest_id=dash_manifest.id,
        period_id=period.id)

    fmp4_muxings = bitmovin_api.encoding.encodings.muxings.fmp4.list(encoding_id=encoding_id)
    for muxing in fmp4_muxings.items:
        stream = bitmovin_api.encoding.encodings.streams.get(
            encoding_id=encoding_id, stream_id=muxing.streams[0].stream_id)

        if 'PER_TITLE_TEMPLATE' in stream.mode.value:
            continue

        codec = bitmovin_api.encoding.configurations.type.get(configuration_id=stream.codec_config_id)
        segment_path = _remove_output_base_path(muxing.outputs[0].output_path)

        if codec.type == CodecConfigType.DOLBY_ATMOS:
            bitmovin_api.encoding.manifests.dash.periods.adaptationsets.representations.fmp4.create(
                manifest_id=dash_manifest.id,
                period_id=period.id,
                adaptationset_id=audio_adaptation_set.id,
                dash_fmp4_representation=DashFmp4Representation(
                    encoding_id=encoding_id,
                    muxing_id=muxing.id,
                    type_=DashRepresentationType.TEMPLATE,
                    mode=DashRepresentationTypeMode.TEMPLATE_REPRESENTATION,
                    segment_path=segment_path))

        elif codec.type == CodecConfigType.H265:
            bitmovin_api.encoding.manifests.dash.periods.adaptationsets.representations.fmp4.create(
                manifest_id=dash_manifest.id,
                period_id=period.id,
                adaptationset_id=video_adaptation_set.id,
                dash_fmp4_representation=DashFmp4Representation(
                    encoding_id=encoding_id,
                    muxing_id=muxing.id,
                    type_=DashRepresentationType.TEMPLATE,
                    mode=DashRepresentationTypeMode.TEMPLATE_REPRESENTATION,
                    segment_path=segment_path))
    return dash_manifest


def _create_hls_manifest(encoding_id, output, output_path):
    manifest_output = EncodingOutput(output_id=output.id,
                                     output_path=output_path,
                                     acl=[AclEntry(permission=AclPermission.PUBLIC_READ)])

    hls_manifest = bitmovin_api.encoding.manifests.hls.create(
        hls_manifest=HlsManifest(
            manifest_name='stream.m3u8',
            outputs=[manifest_output],
            name='HLS Manifest',
            hls_master_playlist_version=HlsVersion.HLS_V8,
            hls_media_playlist_version=HlsVersion.HLS_V8))

    fmp4_muxings = bitmovin_api.encoding.encodings.muxings.fmp4.list(encoding_id=encoding_id)
    for muxing in fmp4_muxings.items:
        stream = bitmovin_api.encoding.encodings.streams.get(
            encoding_id=encoding_id, stream_id=muxing.streams[0].stream_id)

        if 'PER_TITLE_TEMPLATE' in stream.mode.value:
            continue

        codec = bitmovin_api.encoding.configurations.type.get(configuration_id=stream.codec_config_id)
        segment_path = _remove_output_base_path(muxing.outputs[0].output_path)

        if codec.type == CodecConfigType.DOLBY_ATMOS:
            audio_codec = bitmovin_api.encoding.configurations.audio.dolby_atmos.get(
                configuration_id=stream.codec_config_id)
            bitmovin_api.encoding.manifests.hls.media.audio.create(
                manifest_id=hls_manifest.id,
                audio_media_info=AudioMediaInfo(
                    name='HLS Audio Media',
                    group_id='audio',
                    language='en',
                    segment_path=segment_path,
                    encoding_id=encoding_id,
                    stream_id=stream.id,
                    muxing_id=muxing.id,
                    uri='audio_{}.m3u8'.format(audio_codec.bitrate)))

        elif codec.type == CodecConfigType.H265:
            video_codec = bitmovin_api.encoding.configurations.video.h265.get(configuration_id=stream.codec_config_id)
            bitmovin_api.encoding.manifests.hls.streams.create(
                manifest_id=hls_manifest.id,
                stream_info=StreamInfo(
                    audio='audio',
                    closed_captions='NONE',
                    segment_path=segment_path,
                    uri='video_{}.m3u8'.format(video_codec.bitrate),
                    encoding_id=encoding_id,
                    stream_id=stream.id,
                    muxing_id=muxing.id))
    return hls_manifest


def _execute_dash_manifest_generation(dash_manifest):
    bitmovin_api.encoding.manifests.dash.start(manifest_id=dash_manifest.id)

    task = _wait_for_dash_manifest_to_finish(manifest_id=dash_manifest.id)

    while task.status is not Status.FINISHED and task.status is not Status.ERROR:
        task = _wait_for_dash_manifest_to_finish(manifest_id=dash_manifest.id)
    if task.status is Status.ERROR:
        _log_task_errors(task=task)
        raise Exception("DASH Manifest Creation failed")

    print("DASH Manifest Creation finished successfully")


def _execute_hls_manifest_generation(hls_manifest):
    bitmovin_api.encoding.manifests.hls.start(manifest_id=hls_manifest.id)

    task = _wait_for_hls_manifest_to_finish(manifest_id=hls_manifest.id)

    while task.status is not Status.FINISHED and task.status is not Status.ERROR:
        task = _wait_for_hls_manifest_to_finish(manifest_id=hls_manifest.id)
    if task.status is Status.ERROR:
        _log_task_errors(task=task)
        raise Exception("HLS Manifest Creation failed")

    print("DASH Manifest Creation finished successfully")


def _wait_for_enoding_to_finish(encoding_id):
    time.sleep(5)
    task = bitmovin_api.encoding.encodings.status(encoding_id=encoding_id)
    print("Encoding status is {} (progress: {} %)".format(task.status, task.progress))
    return task


def _wait_for_dash_manifest_to_finish(manifest_id):
    time.sleep(5)
    task = bitmovin_api.encoding.manifests.dash.status(manifest_id=manifest_id)
    print("DASH manifest status is {} (progress: {} %)".format(task.status, task.progress))
    return task


def _wait_for_hls_manifest_to_finish(manifest_id):
    time.sleep(5)
    task = bitmovin_api.encoding.manifests.hls.status(manifest_id=manifest_id)
    print("HLS manifest status is {} (progress: {} %)".format(task.status, task.progress))
    return task


def _remove_output_base_path(text):
    if text.startswith(OUTPUT_BASE_PATH):
        return text[len(OUTPUT_BASE_PATH):]
    return text


def _log_task_errors(task):
    if task is None:
        return

    filtered = filter(lambda msg: msg.type is MessageType.ERROR, task.messages)

    for message in filtered:
        print(message.text)


if __name__ == '__main__':
    main()
