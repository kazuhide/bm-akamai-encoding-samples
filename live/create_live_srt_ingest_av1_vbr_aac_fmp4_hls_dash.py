import time
from time import sleep

from bitmovin_api_sdk import BitmovinApi, BitmovinError
from bitmovin_api_sdk import S3AccessStyle, S3SignatureVersion, GenericS3Output, SrtInput, SrtMode
from bitmovin_api_sdk import Encoding, CloudRegion
from bitmovin_api_sdk import EncodingOutput, AclEntry, AclPermission
from bitmovin_api_sdk import Av1PresetConfiguration, EncodingMode
from bitmovin_api_sdk import Stream, StreamInput, MuxingStream, StreamMode, ColorConfig
from bitmovin_api_sdk import AacAudioConfiguration, AacChannelLayout
from bitmovin_api_sdk import Av1VideoConfiguration, CodecConfigType, AutoLevelSetup
from bitmovin_api_sdk import Fmp4Muxing
from bitmovin_api_sdk import HlsManifest, HlsVersion, AudioMediaInfo, StreamInfo
from bitmovin_api_sdk import DashManifest, Period, VideoAdaptationSet, AudioAdaptationSet
from bitmovin_api_sdk import DashFmp4Representation, DashRepresentationType, DashRepresentationTypeMode
from bitmovin_api_sdk import MessageType, StartLiveEncodingRequest, ManifestGenerator
from bitmovin_api_sdk import LiveHlsManifest, LiveDashManifest, AvailabilityStartTimeMode
from bitmovin_api_sdk import Status

TEST_ITEM = "live-srt-ingest-av1-vbr-aac-fmp4-hls-dash"

API_KEY = '<INSERT YOUR API KEY>'
ORG_ID = '<INSERT YOUR ORG ID>'

LINODE_OBJECT_STORAGE_OUTPUT_ACCESS_KEY = '<INSERT_YOUR_ACCESS_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_SECRET_KEY = '<INSERT_YOUR_SECRET_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_BUCKET_NAME = '<INSERT_YOUR_BUCKET_NAME>'
LINODE_OBJECT_STORAGE_OUTPUT_HOST_NAME = '<INSERT_YOUR_INPUT_HOST_NAME>'

OUTPUT_BASE_PATH = f'output/{TEST_ITEM}/'

bitmovin_api = BitmovinApi(api_key=API_KEY, tenant_org_id=ORG_ID)

video_encoding_profiles = [
    dict(height=240,  bitrate=195000,  mode=StreamMode.STANDARD),
    dict(height=360,  bitrate=385000,  mode=StreamMode.STANDARD),
    dict(height=480,  bitrate=578000,  mode=StreamMode.STANDARD),
    dict(height=540,  bitrate=920000,  mode=StreamMode.STANDARD),
    dict(height=720,  bitrate=1378000, mode=StreamMode.STANDARD),
    dict(height=1080, bitrate=2728000, mode=StreamMode.STANDARD),
]

# Example AAC audio encoding profiles, each with a specified bitrate and sample rate.
audio_encoding_profiles = [
    dict(bitrate=128000, rate=48_000),
    dict(bitrate=64000, rate=44_100)
]


def main():

    # === Input and Output definition ===
    srt_input = bitmovin_api.encoding.inputs.srt.create(
        srt_input=SrtInput(
            mode=SrtMode.LISTENER,
            port=2088
        )
    )
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

    # === Encoding instance definition ===
    encoding = bitmovin_api.encoding.encodings.create(
        encoding=Encoding(
            name="[{}] {}".format(TEST_ITEM, "Test"),
            cloud_region=CloudRegion.AKAMAI_JP_OSA,
            encoder_version='STABLE'
        )
    )

    # === Video Profile definition ===
    for video_profile in video_encoding_profiles:
        """
        Loop through each defined H.265 profile.
        Create a color configuration that automatically copies color flags from the source.
        If the profile is HIGH, we enable certain advanced features like CABAC.
        If MAIN or BASELINE were used, you could set different values here.
        """
        color_config = ColorConfig(
            copy_color_primaries_flag=True,
            copy_color_transfer_flag=True,
            copy_color_space_flag=True
        )
        av1_config = bitmovin_api.encoding.configurations.video.av1.create(
            av1_video_configuration=Av1VideoConfiguration(
                name='AV1 Video Configuration',
                height=video_profile.get("height"),
                bitrate=video_profile.get("bitrate"),
                auto_level_setup=AutoLevelSetup.ENABLED,
                preset_configuration=Av1PresetConfiguration.VOD_SPEED,
                encoding_mode=EncodingMode.TWO_PASS,
                color_config=color_config
            )
        )
        # Create a Stream that uses the above AV1 codec configuration
        av1_stream = bitmovin_api.encoding.encodings.streams.create(
            encoding_id=encoding.id,
            stream=Stream(
                codec_config_id=av1_config.id,
                input_streams=[StreamInput(
                    input_id=srt_input.id,
                    input_path="live",
                    position=0)],
                name=f"Stream AV1 {video_profile.get('height')}p",
                mode=video_profile.get('mode')
            )
        )

        # Define the S3 output path for the final video segments
        video_muxing_output = EncodingOutput(
            output_id=output.id,
            output_path=f"{OUTPUT_BASE_PATH}video/{video_profile.get('height')}p",
            acl=[AclEntry(permission=AclPermission.PUBLIC_READ)]
        )

        # Create an FMP4 Muxing for this particular resolution
        bitmovin_api.encoding.encodings.muxings.fmp4.create(
            encoding_id=encoding.id,
            fmp4_muxing=Fmp4Muxing(
                segment_length=6,
                segment_naming='segment_%number%.m4s',
                init_segment_name='init.mp4',
                streams=[MuxingStream(stream_id=av1_stream.id)],
                outputs=[video_muxing_output],
                name=f"Video FMP4 Muxing {video_profile.get('height')}p"
            )
        )

    # === Audio Profile definition ===
    for audio_profile in audio_encoding_profiles:
        """
        Loop through each defined AAC audio profile.
        Create a codec configuration object and then a Stream object for that profile.
        Finally, create an FMP4 muxing for each variant.
        """

        # Create Audio Codec Configuration
        aac_codec = bitmovin_api.encoding.configurations.audio.aac.create(
            aac_audio_configuration=AacAudioConfiguration(
                bitrate=audio_profile.get("bitrate"),
                rate=audio_profile.get("rate"),
                channel_layout=AacChannelLayout.CL_STEREO
            )
        )

        # Create Audio Stream
        aac_stream = bitmovin_api.encoding.encodings.streams.create(
            encoding_id=encoding.id,
            stream=Stream(
                codec_config_id=aac_codec.id,
                input_streams=[StreamInput(
                    input_id=srt_input.id,
                    input_path="live",
                    position=1)],
                name=f"Stream AAC {audio_profile.get('bitrate')/1000:.0f}kbps",
                mode=StreamMode.STANDARD
            )
        )

        # Define the GCS output path for audio segments
        audio_muxing_output = EncodingOutput(
            output_id=output.id,
            output_path=f"{OUTPUT_BASE_PATH}audio/{audio_profile.get('bitrate')}",
            acl=[AclEntry(permission=AclPermission.PUBLIC_READ)]
        )

        # Create Fmp4 muxing
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

    # Define HLS and DASH manifests
    hls_manifest = _create_hls_manifest(encoding_id=encoding.id, output=output, output_path=OUTPUT_BASE_PATH)
    dash_manifest = _create_dash_manifest(encoding_id=encoding.id, output=output, output_path=OUTPUT_BASE_PATH)

    live_hls_manifest = LiveHlsManifest(
        manifest_id=hls_manifest.id,
        timeshift=120,
        live_edge_offset=12,
        insert_program_date_time=True
    )
    live_dash_manifest = LiveDashManifest(
        manifest_id=dash_manifest.id,
        timeshift=120,
        live_edge_offset=12,
        suggested_presentation_delay=0,
        minimum_update_period=6,
        availability_start_time_mode=AvailabilityStartTimeMode.ON_FIRST_SEGMENT
    )

    # === Start Encoding settings (no manifests attached to the start request in this example) ===
    start_live_encoding_request = StartLiveEncodingRequest(
        dash_manifests=[live_dash_manifest],
        hls_manifests=[live_hls_manifest],
        stream_key="myStreamKey",
        manifest_generator=ManifestGenerator.V2
    )
    _execute_live_encoding(encoding=encoding, start_live_encoding_request=start_live_encoding_request)
    live_encoding = _wait_for_live_encoding_details(encoding=encoding)

    print("Live encoding is up and ready for ingest. SRT URL: SRT://{0}/(port) StreamKey: {1}"
          .format(live_encoding.encoder_ip, live_encoding.stream_key))

    input("Press Enter to shutdown the live encoding...")

    print("Shutting down live encoding.")
    bitmovin_api.encoding.encodings.live.stop(encoding_id=encoding.id)
    _wait_until_encoding_is_in_state(encoding=encoding, expected_status=Status.FINISHED)


def _execute_live_encoding(encoding, start_live_encoding_request):
    bitmovin_api.encoding.encodings.live.start(
        encoding_id=encoding.id,
        start_live_encoding_request=start_live_encoding_request)

    _wait_until_encoding_is_in_state(encoding=encoding, expected_status=Status.RUNNING)


def _wait_until_encoding_is_in_state(encoding, expected_status):
    check_interval_in_seconds = 5
    max_attempts = 5 * (60 / check_interval_in_seconds)
    attempt = 0

    while attempt < max_attempts:
        task = bitmovin_api.encoding.encodings.status(encoding_id=encoding.id)
        if task.status is expected_status:
            return
        if task.status is Status.ERROR:
            _log_task_errors(task=task)
            raise Exception("Encoding failed")

        print("Encoding status is {0}. Waiting for status {1} ({2} / {3})"
              .format(task.status, expected_status, attempt, max_attempts))

        sleep(check_interval_in_seconds)

        attempt += 1

    raise Exception("Encoding did not switch to state {0} within {1} minutes. Aborting."
                    .format(expected_status, 5))


def _wait_for_live_encoding_details(encoding):
    timeout_interval_seconds = 5
    retries = 0
    max_retries = (60 / timeout_interval_seconds) * 5
    while retries < max_retries:
        try:
            return bitmovin_api.encoding.encodings.live.get(encoding_id=encoding.id)
        except BitmovinError:
            print("Failed to fetch live encoding details. Retrying... {0} / {1}"
                  .format(retries, max_retries))
            retries += 1
            sleep(timeout_interval_seconds)

    raise Exception("Live encoding details could not be fetched after {0} minutes"
                    .format(5))


def _create_hls_manifest(encoding_id, output, output_path):
    """
    Create an HLS manifest using the generated FMP4 muxings.
    Loop through all FMP4 muxings and add audio or video entries to the HLS manifest.

    :param encoding_id: The ID of the encoding whose muxings are being processed.
    :param output: A GcsOutput (or other Output) object to specify the target output location.
    :param output_path: Base output path in the bucket for the manifest and segments.
    :return: HlsManifest object that was created.
    """
    manifest_output = EncodingOutput(
        output_id=output.id,
        output_path=output_path,
        acl=[AclEntry(permission=AclPermission.PUBLIC_READ)]
    )

    hls_manifest = bitmovin_api.encoding.manifests.hls.create(
        hls_manifest=HlsManifest(
            manifest_name='stream.m3u8',
            outputs=[manifest_output],
            name='HLS Manifest',
            hls_master_playlist_version=HlsVersion.HLS_V6,
            hls_media_playlist_version=HlsVersion.HLS_V6
        )
    )

    # Retrieve all FMP4 muxings from the encoding,
    # then match them to their streams, and add them to the HLS manifest.
    fmp4_muxings = bitmovin_api.encoding.encodings.muxings.fmp4.list(encoding_id=encoding_id)
    for muxing in fmp4_muxings.items:
        stream = bitmovin_api.encoding.encodings.streams.get(
            encoding_id=encoding_id, stream_id=muxing.streams[0].stream_id)

        # Skip advanced per-title templates if found
        if 'PER_TITLE_TEMPLATE' in stream.mode.value:
            continue

        # Identify if the muxing belongs to an AAC (audio) or AV1 (video) stream
        codec = bitmovin_api.encoding.configurations.type.get(configuration_id=stream.codec_config_id)

        # Build the relative segment path for the manifest
        segment_path = _remove_output_base_path(muxing.outputs[0].output_path)

        if codec.type == CodecConfigType.AAC:
            # Build an HLS audio group
            audio_codec = bitmovin_api.encoding.configurations.audio.aac.get(
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
                    uri=f'audio_{audio_codec.bitrate}.m3u8'))

        elif codec.type == CodecConfigType.AV1:
            # Build an HLS video stream
            video_codec = bitmovin_api.encoding.configurations.video.av1.get(configuration_id=stream.codec_config_id)
            bitmovin_api.encoding.manifests.hls.streams.create(
                manifest_id=hls_manifest.id,
                stream_info=StreamInfo(
                    audio='audio',
                    closed_captions='NONE',
                    segment_path=segment_path,
                    uri=f'video_{video_codec.bitrate}.m3u8',
                    encoding_id=encoding_id,
                    stream_id=stream.id,
                    muxing_id=muxing.id))

    return hls_manifest


def _create_dash_manifest(encoding_id, output, output_path):
    """
    Create a DASH manifest by building a Period, adding Video and Audio Adaptation Sets,
    and appending FMP4 representations for each muxing/stream combination.

    :param encoding_id: The ID of the encoding to associate with this manifest.
    :param output: A GcsOutput (or other Output) for the manifest's final location.
    :param output_path: Base output path in the bucket where the manifest files will be written.
    :return: DashManifest object that was created.
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

    # Create a Period for the manifest
    period = bitmovin_api.encoding.manifests.dash.periods.create(
        manifest_id=dash_manifest.id,
        period=Period())

    # Create Adaptation Sets for video and audio
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

        # Skip advanced per-title templates if found
        if 'PER_TITLE_TEMPLATE' in stream.mode.value:
            continue

        # Identify if the muxing is for an AAC or AV1 stream
        codec = bitmovin_api.encoding.configurations.type.get(configuration_id=stream.codec_config_id)
        segment_path = _remove_output_base_path(muxing.outputs[0].output_path)

        if codec.type == CodecConfigType.AAC:
            # Attach this muxing to the audio adaptation set
            bitmovin_api.encoding.manifests.dash.periods.adaptationsets.representations.fmp4.create(
                manifest_id=dash_manifest.id,
                period_id=period.id,
                adaptationset_id=audio_adaptation_set.id,
                dash_fmp4_representation=DashFmp4Representation(
                    encoding_id=encoding_id,
                    muxing_id=muxing.id,
                    type_=DashRepresentationType.TIMELINE,
                    segment_path=segment_path))

        elif codec.type == CodecConfigType.AV1:
            # Attach this muxing to the video adaptation set
            bitmovin_api.encoding.manifests.dash.periods.adaptationsets.representations.fmp4.create(
                manifest_id=dash_manifest.id,
                period_id=period.id,
                adaptationset_id=video_adaptation_set.id,
                dash_fmp4_representation=DashFmp4Representation(
                    encoding_id=encoding_id,
                    muxing_id=muxing.id,
                    type_=DashRepresentationType.TIMELINE,
                    segment_path=segment_path))

    return dash_manifest


def _execute_hls_manifest_generation(hls_manifest):
    """
    Starts the HLS manifest generation job and polls for completion.

    :param hls_manifest: The HlsManifest object that needs to be generated.
    """
    bitmovin_api.encoding.manifests.hls.start(manifest_id=hls_manifest.id)

    task = _wait_for_hls_manifest_to_finish(manifest_id=hls_manifest.id)

    while task.status is not Status.FINISHED and task.status is not Status.ERROR:
        task = _wait_for_hls_manifest_to_finish(manifest_id=hls_manifest.id)
    if task.status is Status.ERROR:
        _log_task_errors(task=task)
        raise Exception("HLS Manifest Creation failed")

    print("HLS Manifest Creation finished successfully")


def _execute_dash_manifest_generation(dash_manifest):
    """
    Starts the DASH manifest generation job and polls for completion.

    :param dash_manifest: The DashManifest object that needs to be generated.
    """
    bitmovin_api.encoding.manifests.dash.start(manifest_id=dash_manifest.id)

    task = _wait_for_dash_manifest_to_finish(manifest_id=dash_manifest.id)

    while task.status is not Status.FINISHED and task.status is not Status.ERROR:
        task = _wait_for_dash_manifest_to_finish(manifest_id=dash_manifest.id)
    if task.status is Status.ERROR:
        _log_task_errors(task=task)
        raise Exception("DASH Manifest Creation failed")

    print("DASH Manifest Creation finished successfully")


def _wait_for_encoding_to_finish(encoding_id):
    """
    Poll the encoding status every 5 seconds until
    it either finishes or encounters an error.

    :param encoding_id: The ID of the encoding to poll.
    :return: The final task status of the encoding.
    """
    time.sleep(5)
    task = bitmovin_api.encoding.encodings.status(encoding_id=encoding_id)
    print(f"Encoding status is {task.status} (progress: {task.progress} %)")
    return task


def _wait_for_hls_manifest_to_finish(manifest_id):
    """
    Poll the HLS manifest creation status every 5 seconds
    until it either finishes or encounters an error.

    :param manifest_id: The ID of the HLS manifest to poll.
    :return: The final task status of the HLS manifest creation process.
    """
    time.sleep(5)
    task = bitmovin_api.encoding.manifests.hls.status(manifest_id=manifest_id)
    print(f"HLS manifest status is {task.status} (progress: {task.progress} %)")
    return task


def _wait_for_dash_manifest_to_finish(manifest_id):
    """
    Poll the DASH manifest creation status every 5 seconds
    until it either finishes or encounters an error.

    :param manifest_id: The ID of the DASH manifest to poll.
    :return: The final task status of the DASH manifest creation process.
    """
    time.sleep(5)
    task = bitmovin_api.encoding.manifests.dash.status(manifest_id=manifest_id)
    print("DASH manifest status is {} (progress: {} %)".format(task.status, task.progress))
    return task


def _remove_output_base_path(text):
    """
    Remove the OUTPUT_BASE_PATH prefix from the given path.
    Used for constructing relative segment paths for HLS/DASH manifests.

    :param text: The full path (e.g., 'output/av1-aac-fmp4-hls-dash/video/720p')
    :return: Relative path without the OUTPUT_BASE_PATH prefix
    """
    if text.startswith(OUTPUT_BASE_PATH):
        return text[len(OUTPUT_BASE_PATH):]
    return text


def _log_task_errors(task):
    """
    Print any error messages in the task's message list to the console.

    :param task: A task object (encoding, manifest, etc.) that may contain error messages.
    """
    if task is None:
        return

    filtered = filter(lambda msg: msg.type is MessageType.ERROR, task.messages)

    for message in filtered:
        print(message.text)


if __name__ == '__main__':
    main()
