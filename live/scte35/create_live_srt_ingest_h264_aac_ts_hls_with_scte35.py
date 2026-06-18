from time import sleep

from bitmovin_api_sdk import BitmovinApi, BitmovinError
from bitmovin_api_sdk import S3AccessStyle, S3SignatureVersion, GenericS3Output, SrtInput, SrtMode
from bitmovin_api_sdk import Encoding, CloudRegion
from bitmovin_api_sdk import EncodingOutput, AclEntry, AclPermission
from bitmovin_api_sdk import PresetConfiguration
from bitmovin_api_sdk import Stream, StreamInput, MuxingStream, StreamMode, ColorConfig
from bitmovin_api_sdk import AacAudioConfiguration, AacChannelLayout
from bitmovin_api_sdk import H264VideoConfiguration, CodecConfigType, ProfileH264, LevelH264, WeightedPredictionPFrames
from bitmovin_api_sdk import TsMuxing
from bitmovin_api_sdk import HlsManifest, HlsVersion, AudioMediaInfo, StreamInfo
from bitmovin_api_sdk import HlsManifestAdMarkerSettings, HlsManifestAdMarkerType, Scte35Cue
from bitmovin_api_sdk import MessageType, StartLiveEncodingRequest, ManifestGenerator
from bitmovin_api_sdk import LiveHlsManifest
from bitmovin_api_sdk import Status

TEST_ITEM = "live-srt-ingest-h264-aac-ts-hls-scte35"

API_KEY = '<INSERT YOUR API KEY>'
ORG_ID = '<INSERT YOUR ORG ID>'

LINODE_OBJECT_STORAGE_OUTPUT_ACCESS_KEY = '<INSERT_YOUR_ACCESS_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_SECRET_KEY = '<INSERT_YOUR_SECRET_KEY>'
LINODE_OBJECT_STORAGE_OUTPUT_BUCKET_NAME = '<INSERT_YOUR_BUCKET_NAME>'
LINODE_OBJECT_STORAGE_OUTPUT_HOST_NAME = '<INSERT_YOUR_OUTPUT_HOST_NAME>'

OUTPUT_BASE_PATH = f'output/{TEST_ITEM}/'

bitmovin_api = BitmovinApi(api_key=API_KEY, tenant_org_id=ORG_ID)

# Example H.264 encoding profiles, including different resolutions, bitrates, and profiles.
video_encoding_profiles = [
    {"height": 240, "bitrate": 300000, "profile": ProfileH264.HIGH, "level": None, "mode": StreamMode.STANDARD},
    {"height": 360, "bitrate": 800000, "profile": ProfileH264.HIGH, "level": None, "mode": StreamMode.STANDARD},
    {"height": 480, "bitrate": 1200000, "profile": ProfileH264.HIGH, "level": None, "mode": StreamMode.STANDARD},
    {"height": 540, "bitrate": 2000000, "profile": ProfileH264.HIGH, "level": None, "mode": StreamMode.STANDARD},
    {"height": 720, "bitrate": 4000000, "profile": ProfileH264.HIGH, "level": None, "mode": StreamMode.STANDARD},
    {"height": 1080, "bitrate": 6000000, "profile": ProfileH264.HIGH, "level": LevelH264.L4, "mode": StreamMode.STANDARD}
]

# Example AAC audio encoding profiles, each with a specified bitrate and sample rate.
audio_encoding_profiles = [
    {"bitrate": 128000, "rate": 48_000},
    {"bitrate": 64000, "rate": 44_100}
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
            name='Test Linode Object Storage Output'))

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
        Loop through each defined H.264 profile.
        Create a color configuration that automatically copies color flags from the source.
        If the profile is HIGH, we enable certain advanced features like CABAC.
        If MAIN or BASELINE were used, you could set different values here.
        """
        color_config = ColorConfig(
            copy_color_primaries_flag=True,
            copy_color_transfer_flag=True,
            copy_color_space_flag=True
        )

        if video_profile.get("profile") == ProfileH264.HIGH:
            adaptive_spatial_transform = True
            use_cabac = True
            num_refframe = 4
            num_bframe = 3
            weighted_prediction_p_frames = WeightedPredictionPFrames.SMART
        elif video_profile.get("profile") == ProfileH264.MAIN:
            adaptive_spatial_transform = False
            use_cabac = True
            num_refframe = 4
            num_bframe = 3
            weighted_prediction_p_frames = WeightedPredictionPFrames.SMART
        elif video_profile.get("profile") == ProfileH264.BASELINE:
            adaptive_spatial_transform = False
            use_cabac = False
            num_refframe = 4
            num_bframe = 0
            weighted_prediction_p_frames = WeightedPredictionPFrames.DISABLED
        else:
            raise Exception("Unknown profile. Please specify a valid H.264 profile (HIGH, MAIN, or BASELINE).")

        # Create Video Codec Configuration with advanced H.264 parameters
        h264_codec = bitmovin_api.encoding.configurations.video.h264.create(
            h264_video_configuration=H264VideoConfiguration(
                name='Sample video codec configuration',
                height=video_profile.get("height"),
                bitrate=video_profile.get("bitrate"),
                max_bitrate=int(video_profile.get("bitrate") * 1.2),
                bufsize=int(video_profile.get("bitrate") * 1.5),
                profile=video_profile.get("profile"),
                level=video_profile.get("level"),
                min_keyframe_interval=2,
                max_keyframe_interval=2,
                color_config=color_config,
                ref_frames=num_refframe,
                bframes=num_bframe,
                cabac=use_cabac,
                adaptive_spatial_transform=adaptive_spatial_transform,
                weighted_prediction_p_frames=weighted_prediction_p_frames,
                preset_configuration=PresetConfiguration.LIVE_ULTRAHIGH_QUALITY
            )
        )

        # Create a Stream that uses the above H.264 codec configuration
        h264_stream = bitmovin_api.encoding.encodings.streams.create(
            encoding_id=encoding.id,
            stream=Stream(
                codec_config_id=h264_codec.id,
                input_streams=[StreamInput(
                    input_id=srt_input.id,
                    input_path="live",
                    position=0)],
                name=f"Stream H264 {video_profile.get('height')}p",
                mode=video_profile.get('mode')
            )
        )

        # Define the S3 output path for the final video segments
        video_muxing_output = EncodingOutput(
            output_id=output.id,
            output_path=f"{OUTPUT_BASE_PATH}video/{video_profile.get('height')}p",
            acl=[AclEntry(permission=AclPermission.PUBLIC_READ)]
        )

        # Create an MPEG-TS Muxing for this particular resolution.
        # SSAI (Server-Side Ad Insertion) workflows generally expect TS segments,
        # so each video variant is muxed into TS instead of fMP4 (TS has no init segment).
        bitmovin_api.encoding.encodings.muxings.ts.create(
            encoding_id=encoding.id,
            ts_muxing=TsMuxing(
                segment_length=6,
                segment_naming='segment_%number%.ts',
                streams=[MuxingStream(stream_id=h264_stream.id)],
                outputs=[video_muxing_output],
                name=f"Video TS Muxing {video_profile.get('height')}p"
            )
        )

    # === Audio Profile definition ===
    for audio_profile in audio_encoding_profiles:
        """
        Loop through each defined AAC audio profile.
        Create a codec configuration object and then a Stream object for that profile.
        Finally, create an MPEG-TS muxing for each variant.
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
                name=f"Stream AAC {audio_profile.get('bitrate') / 1000:.0f}kbps",
                mode=StreamMode.STANDARD
            )
        )

        # Define the output path for audio segments
        audio_muxing_output = EncodingOutput(
            output_id=output.id,
            output_path=f"{OUTPUT_BASE_PATH}audio/{audio_profile.get('bitrate')}",
            acl=[AclEntry(permission=AclPermission.PUBLIC_READ)]
        )

        # Create TS muxing (TS has no init_segment_name)
        bitmovin_api.encoding.encodings.muxings.ts.create(
            encoding_id=encoding.id,
            ts_muxing=TsMuxing(
                segment_length=6,
                segment_naming='segment_%number%.ts',
                streams=[MuxingStream(stream_id=aac_stream.id)],
                outputs=[audio_muxing_output],
                name=f"Audio TS Muxing {audio_profile.get('bitrate') / 1000:.0f}kbps"
            )
        )

    # Define HLS manifest only.
    # SSAI workflows typically require MPEG-TS segments, therefore this sample intentionally
    # produces an HLS manifest with SCTE-35 ad markers and omits DASH.
    hls_manifest = _create_hls_manifest(encoding_id=encoding.id, output=output, output_path=OUTPUT_BASE_PATH)

    # === SCTE-35 ad marker handling ===
    # SCTE-35 ad insertion triggers (splice information) must already be present in the
    # incoming MPEG-TS stream delivered over SRT. In the transport stream, SCTE-35 sections
    # are carried in a dedicated PES of stream type 0x86. The encoder parses those triggers
    # and writes the corresponding ad markers into the HLS media playlists, e.g.
    # #EXT-X-CUE-OUT / #EXT-X-CUE-IN (EXT_X_CUE_OUT_IN) and #EXT-X-SPLICEPOINT-SCTE35
    # (EXT_X_SPLICEPOINT_SCTE35). Downstream SSAI systems read these markers to stitch ads.
    #
    # If the source does not carry SCTE-35, ad cues can instead be injected manually while
    # the live encoding is RUNNING (see the optional _insert_ad_cue helper below).
    live_hls_manifest = LiveHlsManifest(
        manifest_id=hls_manifest.id,
        timeshift=120,
        live_edge_offset=12,
        insert_program_date_time=True,
        ad_marker_settings=HlsManifestAdMarkerSettings(
            enabled_marker_types=[
                HlsManifestAdMarkerType.EXT_X_CUE_OUT_IN,
                HlsManifestAdMarkerType.EXT_X_SPLICEPOINT_SCTE35,
            ]
        )
    )

    # === Start Encoding settings (HLS only for this SCTE-35 / SSAI sample) ===
    start_live_encoding_request = StartLiveEncodingRequest(
        hls_manifests=[live_hls_manifest],
        stream_key="myStreamKey",
        manifest_generator=ManifestGenerator.V2
    )
    _execute_live_encoding(encoding=encoding, start_live_encoding_request=start_live_encoding_request)
    live_encoding = _wait_for_live_encoding_details(encoding=encoding)

    print(f"Live encoding is up and ready for ingest. SRT URL: SRT://{live_encoding.encoder_ip}/(port) StreamKey: {live_encoding.stream_key}"
          )

    # Optional: while the encoding is RUNNING you may manually trigger an ad break by
    # calling _insert_ad_cue(encoding.id, hls_manifest.id) instead of relying solely on
    # SCTE-35 markers carried in the incoming MPEG-TS stream. It is left uninvoked here.

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

        print(f"Encoding status is {task.status}. Waiting for status {expected_status} ({attempt} / {max_attempts})"
              )

        sleep(check_interval_in_seconds)

        attempt += 1

    raise Exception(f"Encoding did not switch to state {expected_status} within {5} minutes. Aborting."
                    )


def _wait_for_live_encoding_details(encoding):
    timeout_interval_seconds = 5
    retries = 0
    max_retries = (60 / timeout_interval_seconds) * 5
    while retries < max_retries:
        try:
            return bitmovin_api.encoding.encodings.live.get(encoding_id=encoding.id)
        except BitmovinError:
            print(f"Failed to fetch live encoding details. Retrying... {retries} / {max_retries}"
                  )
            retries += 1
            sleep(timeout_interval_seconds)

    raise Exception(f"Live encoding details could not be fetched after {5} minutes"
                    )


def _insert_ad_cue(encoding_id, manifest_id, duration_seconds=30.0):
    """Manually insert a SCTE-35 ad cue into the running live HLS manifest (optional)."""
    bitmovin_api.encoding.encodings.live.scte35_cue.create(
        encoding_id=encoding_id,
        scte35_cue=Scte35Cue(cue_duration=duration_seconds, manifest_ids=[manifest_id])
    )


def _create_hls_manifest(encoding_id, output, output_path):
    """
    Create an HLS manifest using the generated MPEG-TS muxings.
    Loop through all TS muxings and add audio or video entries to the HLS manifest.

    :param encoding_id: The ID of the encoding whose muxings are being processed.
    :param output: An Output object that specifies the target output location.
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

    # Retrieve all TS muxings from the encoding,
    # then match them to their streams, and add them to the HLS manifest.
    ts_muxings = bitmovin_api.encoding.encodings.muxings.ts.list(encoding_id=encoding_id)
    for muxing in ts_muxings.items:
        stream = bitmovin_api.encoding.encodings.streams.get(
            encoding_id=encoding_id, stream_id=muxing.streams[0].stream_id)

        # Skip advanced per-title templates if found
        if 'PER_TITLE_TEMPLATE' in stream.mode.value:
            continue

        # Identify if the muxing belongs to an AAC (audio) or H.264 (video) stream
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

        elif codec.type == CodecConfigType.H264:
            # Build an HLS video stream
            video_codec = bitmovin_api.encoding.configurations.video.h264.get(configuration_id=stream.codec_config_id)
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


def _remove_output_base_path(text):
    """
    Remove the OUTPUT_BASE_PATH prefix from the given path.
    Used for constructing relative segment paths for HLS manifests.

    :param text: The full path (e.g., 'output/live-srt-ingest-h264-aac-ts-hls-scte35/video/720p')
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
