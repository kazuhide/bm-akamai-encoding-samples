import time

from bitmovin_api_sdk import BitmovinApi
from bitmovin_api_sdk import GenericS3Input, S3AccessStyle, S3SignatureVersion, GenericS3Output
from bitmovin_api_sdk import Encoding, CloudRegion
from bitmovin_api_sdk import EncodingOutput, AclEntry, AclPermission
from bitmovin_api_sdk import IngestInputStream, StreamSelectionMode, PresetConfiguration
from bitmovin_api_sdk import Stream, StreamInput, MuxingStream, StreamMode, ColorConfig
from bitmovin_api_sdk import AacAudioConfiguration, AacChannelLayout
from bitmovin_api_sdk import Vp9VideoConfiguration, CodecConfigType
from bitmovin_api_sdk import Fmp4Muxing, WebmMuxing
from bitmovin_api_sdk import DashManifest, Period, VideoAdaptationSet, AudioAdaptationSet
from bitmovin_api_sdk import DashFmp4Representation, DashWebmRepresentation, DashRepresentationType, DashRepresentationTypeMode
from bitmovin_api_sdk import MessageType, StartEncodingRequest
from bitmovin_api_sdk import Status

TEST_ITEM = "vod-vp9-webm-aac-fmp4-dash"

API_KEY = '<INSERT YOUR API KEY>'
ORG_ID = '<INSERT YOUR ORG ID>'

LINODE_OBJECT_STORAGE_INPUT_ACCESS_KEY = '<INSERT_YOUR_ACCESS_KEY>'
LINODE_OBJECT_STORAGE_INPUT_SECRET_KEY = '<INSERT_YOUR_SECRET_KEY>'
LINODE_OBJECT_STORAGE_INPUT_BUCKET_NAME = '<INSERT_YOUR_BUCKET_NAME>'
LINODE_OBJECT_STORAGE_INPUT_HOST_NAME = '<INSERT_YOUR_INPUT_HOST_NAME>'

INPUT_PATH = '/path/to/your/input/file.mp4'
# e.g. 'inputs/big_buck_bunny_1080p_h264.mov'

LINODE_OBJECT_STORAGE_OUTPUT_ACCESS_KEY = '<INSERT_YOUR_ACCESS_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_SECRET_KEY = '<INSERT_YOUR_SECRET_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_BUCKET_NAME = '<INSERT_YOUR_BUCKET_NAME>'
LINODE_OBJECT_STORAGE_OUTPUT_HOST_NAME = '<INSERT_YOUR_INPUT_HOST_NAME>'

OUTPUT_BASE_PATH = f'output/{TEST_ITEM}/'

bitmovin_api = BitmovinApi(api_key=API_KEY, tenant_org_id=ORG_ID)

# Example VP9 encoding profiles for video, defining different resolutions, bitrates, and encoding modes.
video_encoding_profiles = [
    dict(height=240,  bitrate=300000,  mode=StreamMode.STANDARD),
    dict(height=360,  bitrate=800000,  mode=StreamMode.STANDARD),
    dict(height=480,  bitrate=1200000, mode=StreamMode.STANDARD),
    dict(height=540,  bitrate=2000000, mode=StreamMode.STANDARD),
    dict(height=720,  bitrate=4000000, mode=StreamMode.STANDARD),
    dict(height=1080, bitrate=6000000, mode=StreamMode.STANDARD)
]

# Example AAC audio encoding profiles, each with a specified bitrate and sample rate.
audio_encoding_profiles = [
    dict(bitrate=128000, rate=48000),
    dict(bitrate=64000,  rate=44100)
]


def main():
    """
    Main entry point for the encoding script.
    This script demonstrates a Bitmovin encoding workflow using VP9 for video (muxed as WebM) and AAC for audio (muxed as FMP4).
    The steps are:
      1) Create Generic S3 input/output resources for Linode Object Storage.
      2) Create an Encoding object.
      3) Define video and audio input streams from the source file.
      4) Create multiple VP9 video streams with advanced color configuration and corresponding WebM muxings for different resolutions.
      5) Create multiple AAC audio streams with corresponding FMP4 muxings.
      6) Start the encoding process and poll until completion.
      7) Generate a DASH manifest for adaptive streaming.
    """

    # 1) Create Generic S3 Input/Output resources
    input = bitmovin_api.encoding.inputs.generic_s3.create(
        generic_s3_input=GenericS3Input(
            access_key=LINODE_OBJECT_STORAGE_INPUT_ACCESS_KEY,
            secret_key=LINODE_OBJECT_STORAGE_INPUT_SECRET_KEY,
            bucket_name=LINODE_OBJECT_STORAGE_INPUT_BUCKET_NAME,
            host=LINODE_OBJECT_STORAGE_INPUT_HOST_NAME,
            access_style=S3AccessStyle.VIRTUAL_HOSTED,
            ssl=True,
            port=443,
            signature_version=S3SignatureVersion.V4,
            name='Test Linote Object Storage Input'))
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

    # 2) Create the Encoding instance specifying cloud region and encoder version.
    encoding = bitmovin_api.encoding.encodings.create(
        encoding=Encoding(
            name=f"[{TEST_ITEM}] {INPUT_PATH}",
            cloud_region=CloudRegion.AKAMAI_JP_OSA,
            encoder_version='STABLE'
        )
    )

    # 3) Define input streams for video and audio from the source file.
    video_ingest_input_stream = bitmovin_api.encoding.encodings.input_streams.ingest.create(
        encoding_id=encoding.id,
        ingest_input_stream=IngestInputStream(
            input_id=input.id,
            input_path=INPUT_PATH,
            selection_mode=StreamSelectionMode.VIDEO_RELATIVE,
            position=0
        )
    )
    audio_ingest_input_stream = bitmovin_api.encoding.encodings.input_streams.ingest.create(
        encoding_id=encoding.id,
        ingest_input_stream=IngestInputStream(
            input_id=input.id,
            input_path=INPUT_PATH,
            selection_mode=StreamSelectionMode.AUDIO_RELATIVE,
            position=0
        )
    )

    video_input_stream = StreamInput(input_stream_id=video_ingest_input_stream.id)
    audio_input_stream = StreamInput(input_stream_id=audio_ingest_input_stream.id)

    # 4) Create VP9 video streams and corresponding WebM muxings for adaptive streaming.
    for video_profile in video_encoding_profiles:
        color_config = ColorConfig(
            copy_color_primaries_flag=True,
            copy_color_transfer_flag=True,
            copy_color_space_flag=True
        )
        # Adjust encoding parameters based on resolution.
        if video_profile.get("height") <= 240:
            cpu_used = 1
            tile_columns = 0
        elif video_profile.get("height") <= 480:
            cpu_used = 1
            tile_columns = 1
        elif video_profile.get("height") <= 1080:
            cpu_used = 2
            tile_columns = 2
        elif video_profile.get("height") <= 1440:
            cpu_used = 2
            tile_columns = 3
        else:
            cpu_used = 2
            tile_columns = 4

        vp9_codec = bitmovin_api.encoding.configurations.video.vp9.create(
            vp9_video_configuration=Vp9VideoConfiguration(
                name='Sample video codec configuration',
                height=video_profile.get("height"),
                bitrate=video_profile.get("bitrate"),
                max_keyframe_interval=2,
                min_keyframe_interval=2,
                color_config=color_config,
                tile_columns=tile_columns,
                cpu_used=cpu_used,
                preset_configuration=PresetConfiguration.VOD_HIGH_QUALITY
            )
        )

        vp9_stream = bitmovin_api.encoding.encodings.streams.create(
            encoding_id=encoding.id,
            stream=Stream(
                codec_config_id=vp9_codec.id,
                input_streams=[video_input_stream],
                name=f"Stream VP9 {video_profile.get('height')}p",
                mode=video_profile.get('mode')
            )
        )

        video_muxing_output = EncodingOutput(
            output_id=output.id,
            output_path=f"{OUTPUT_BASE_PATH}video/{video_profile.get('height')}p",
            acl=[AclEntry(permission=AclPermission.PUBLIC_READ)]
        )

        bitmovin_api.encoding.encodings.muxings.webm.create(
            encoding_id=encoding.id,
            webm_muxing=WebmMuxing(
                segment_length=6,
                segment_naming='segment_%number%.chk',
                init_segment_name='init.hdr',
                streams=[MuxingStream(stream_id=vp9_stream.id)],
                outputs=[video_muxing_output],
                name=f"Video WebM Muxing {video_profile.get('height')}p"
            )
        )

    # 5) Create AAC audio streams and corresponding FMP4 muxings.
    for audio_profile in audio_encoding_profiles:
        aac_codec = bitmovin_api.encoding.configurations.audio.aac.create(
            aac_audio_configuration=AacAudioConfiguration(
                bitrate=audio_profile.get("bitrate"),
                rate=audio_profile.get("rate"),
                channel_layout=AacChannelLayout.CL_STEREO
            )
        )

        aac_stream = bitmovin_api.encoding.encodings.streams.create(
            encoding_id=encoding.id,
            stream=Stream(
                codec_config_id=aac_codec.id,
                input_streams=[audio_input_stream],
                name=f"Stream AAC {audio_profile.get('bitrate')/1000:.0f}kbps",
                mode=StreamMode.STANDARD
            )
        )

        audio_muxing_output = EncodingOutput(
            output_id=output.id,
            output_path=f"{OUTPUT_BASE_PATH}audio/{audio_profile.get('bitrate')}",
            acl=[AclEntry(permission=AclPermission.PUBLIC_READ)]
        )

        bitmovin_api.encoding.encodings.muxings.fmp4.create(
            encoding_id=encoding.id,
            fmp4_muxing=Fmp4Muxing(
                segment_length=6,
                segment_naming='segment_%number%.m4s',
                init_segment_name='init.mp4',
                streams=[MuxingStream(stream_id=aac_stream.id)],
                outputs=[audio_muxing_output],
                name=f"Audio FMP4 Muxing {audio_profile.get('bitrate') / 1000:.0f}kbps"
            )
        )

    # 6) Start the encoding process and wait until it finishes.
    start_encoding_request = StartEncodingRequest()
    _execute_encoding(encoding=encoding, start_encoding_request=start_encoding_request)

    # 7) Create a DASH manifest for adaptive streaming.
    dash_manifest = _create_dash_manifest(encoding_id=encoding.id, output=output, output_path=OUTPUT_BASE_PATH)

    # 8) Generate the DASH manifest and wait until completion.
    _execute_dash_manifest_generation(dash_manifest=dash_manifest)


def _execute_encoding(encoding, start_encoding_request):
    """
    Start the encoding process on Bitmovin and poll until it finishes or fails.
    """
    bitmovin_api.encoding.encodings.start(encoding_id=encoding.id, start_encoding_request=start_encoding_request)
    task = _wait_for_encoding_to_finish(encoding_id=encoding.id)

    while task.status not in [Status.FINISHED, Status.ERROR]:
        task = _wait_for_encoding_to_finish(encoding_id=encoding.id)

    if task.status == Status.ERROR:
        _log_task_errors(task)
        raise Exception("Encoding failed")

    print("Encoding finished successfully")


def _create_dash_manifest(encoding_id, output, output_path):
    """
    Create a DASH manifest by:
      - Defining the manifest output.
      - Creating a Period.
      - Adding Video and Audio Adaptation Sets.
      - Attaching a WebM representation for VP9 video and an FMP4 representation for AAC audio.
    """
    manifest_output = EncodingOutput(
        output_id=output.id,
        output_path=output_path,
        acl=[AclEntry(permission=AclPermission.PUBLIC_READ)]
    )

    dash_manifest = bitmovin_api.encoding.manifests.dash.create(
        dash_manifest=DashManifest(
            manifest_name='stream.mpd',
            outputs=[manifest_output],
            name='DASH Manifest'
        )
    )

    period = bitmovin_api.encoding.manifests.dash.periods.create(
        manifest_id=dash_manifest.id,
        period=Period()
    )

    video_adaptation_set = bitmovin_api.encoding.manifests.dash.periods.adaptationsets.video.create(
        video_adaptation_set=VideoAdaptationSet(),
        manifest_id=dash_manifest.id,
        period_id=period.id
    )
    audio_adaptation_set = bitmovin_api.encoding.manifests.dash.periods.adaptationsets.audio.create(
        audio_adaptation_set=AudioAdaptationSet(lang='en'),
        manifest_id=dash_manifest.id,
        period_id=period.id
    )

    # Attach WebM representations for VP9 video muxings.
    webm_muxings = bitmovin_api.encoding.encodings.muxings.webm.list(encoding_id=encoding_id)
    for muxing in webm_muxings.items:
        stream = bitmovin_api.encoding.encodings.streams.get(encoding_id=encoding_id,
                                                             stream_id=muxing.streams[0].stream_id)
        if 'PER_TITLE_TEMPLATE' in stream.mode.value:
            continue

        codec = bitmovin_api.encoding.configurations.type.get(configuration_id=stream.codec_config_id)
        segment_path = _remove_output_base_path(muxing.outputs[0].output_path)

        if codec.type == CodecConfigType.VP9:
            bitmovin_api.encoding.manifests.dash.periods.adaptationsets.representations.webm.create(
                manifest_id=dash_manifest.id,
                period_id=period.id,
                adaptationset_id=video_adaptation_set.id,
                dash_webm_representation=DashWebmRepresentation(
                    encoding_id=encoding_id,
                    muxing_id=muxing.id,
                    type_=DashRepresentationType.TEMPLATE,
                    mode=DashRepresentationTypeMode.TEMPLATE_REPRESENTATION,
                    segment_path=segment_path
                )
            )

    # Attach FMP4 representations for AAC audio muxings.
    fmp4_muxings = bitmovin_api.encoding.encodings.muxings.fmp4.list(encoding_id=encoding_id)
    for muxing in fmp4_muxings.items:
        stream = bitmovin_api.encoding.encodings.streams.get(encoding_id=encoding_id, stream_id=muxing.streams[0].stream_id)
        codec = bitmovin_api.encoding.configurations.type.get(configuration_id=stream.codec_config_id)
        segment_path = _remove_output_base_path(muxing.outputs[0].output_path)

        if codec.type == CodecConfigType.AAC:
            bitmovin_api.encoding.manifests.dash.periods.adaptationsets.representations.fmp4.create(
                manifest_id=dash_manifest.id,
                period_id=period.id,
                adaptationset_id=audio_adaptation_set.id,
                dash_fmp4_representation=DashFmp4Representation(
                    encoding_id=encoding_id,
                    muxing_id=muxing.id,
                    type_=DashRepresentationType.TEMPLATE,
                    mode=DashRepresentationTypeMode.TEMPLATE_REPRESENTATION,
                    segment_path=segment_path
                )
            )

    return dash_manifest


def _execute_dash_manifest_generation(dash_manifest):
    """
    Start DASH manifest generation and poll until completed or fails.
    """
    bitmovin_api.encoding.manifests.dash.start(manifest_id=dash_manifest.id)
    task = _wait_for_dash_manifest_to_finish(manifest_id=dash_manifest.id)

    while task.status not in [Status.FINISHED, Status.ERROR]:
        task = _wait_for_dash_manifest_to_finish(manifest_id=dash_manifest.id)

    if task.status == Status.ERROR:
        _log_task_errors(task)
        raise Exception("DASH Manifest creation failed")

    print("DASH Manifest creation finished successfully")


def _wait_for_encoding_to_finish(encoding_id):
    """
    Poll encoding status every 5 seconds until finished or an error occurs.
    """
    time.sleep(5)
    task = bitmovin_api.encoding.encodings.status(encoding_id=encoding_id)
    print(f"Encoding status is {task.status} (progress: {task.progress} %)")
    return task


def _wait_for_dash_manifest_to_finish(manifest_id):
    """
    Poll DASH manifest creation status every 5 seconds until finished or an error occurs.
    """
    time.sleep(5)
    task = bitmovin_api.encoding.manifests.dash.status(manifest_id=manifest_id)
    print(f"DASH manifest status is {task.status} (progress: {task.progress} %)")
    return task


def _remove_output_base_path(text):
    """
    Remove the OUTPUT_BASE_PATH prefix from the given path to create a relative segment path.
    """
    if text.startswith(OUTPUT_BASE_PATH):
        return text[len(OUTPUT_BASE_PATH):]
    return text


def _log_task_errors(task):
    """
    Print error messages from the given task to the console.
    """
    if not task:
        return

    for message in filter(lambda m: m.type == MessageType.ERROR, task.messages):
        print(message.text)


if __name__ == '__main__':
    main()
