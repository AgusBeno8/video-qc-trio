import os
import av
import av.datasets
import av.filter
import pathlib
from pathlib import Path
import json

# 1. Creates a "InputFolder" folder in the exact same directory as your script, move the script outside, and put the videos to analyze inside.
# The further lines create the __file__ self locating function parameter, as well as the "Compliance_Report" OUTPUT FOLDER for the json report.
SCRIPT_DIR = Path(__file__).resolve().parent
input_folder = (SCRIPT_DIR / "InputFolder").resolve()
output_folder = (SCRIPT_DIR / "Analysis").resolve()

# Automatically create the folder if it doesn't exist yet

input_folder.mkdir(parents=True, exist_ok=True)
output_folder.mkdir(parents=True, exist_ok=True)

# Video extension suffixes for initial checks.
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".m4v", ".flv"}

# 2. Safe Batch Processing Loop
def batch_analyze_videos(target_path):
    target_path = Path(target_path)

    if not target_path.exists():
        print(f"Error: The path {target_path} does not exist.")
        return

    # Determine if target_path is a single file or a directory
    if target_path.is_file():
        video_files = [target_path] if target_path.suffix.lower() in VIDEO_EXTENSIONS else []
    else:
        video_files = [f for f in target_path.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS]

    if not video_files:
        print(f"No valid video files found at: {target_path}")
        return

    print(f"Starting analysis on {len(video_files)} video file(s)...\n")
    
    counter = 0
    all_reports = [] # Master list for JSON report output.

    # 3. Iterate through all files in the folder
    for file_path in video_files:
        # Filter for files matching your video extensions
        if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
            print(f"Processing: {file_path.name} file number: {counter}")

            # Dictionary per loop (per file) and counter:
            counter += 1
            file_data = {
                "batch_idnum": counter,
                "file_name": file_path.name,
                "video": {},
                "audio": {},
                "analysis_status": "Success",
                "errors": []
            }
            try:
                # 4. Open the video container securely
                with av.open(os.fspath(file_path)) as container:

                    # 5. COLOR SPACE/PRIMARIES DICTIONARIES NAME FIXING BIT LINE 51-60
                    COLOR_SPACE_MAP = {
                        0: "RGB",
                        1: "BT.709 (HD/Rec.709)",
                        2: "Unspecified",
                        4: "FCC",
                        5: "BT.470BG (PAL)",
                        6: "SMPTE 170M (SDR/NTSC)",
                        7: "SMPTE 240M",
                        8: "YCGCO",
                        9: "BT.2020 Non-Constant (UHD/HDR)",
                        10: "BT.2020 Constant (HDR)"
                    }
                    COLOR_PRIMARIES_MAP = {
                        1: "BT.709 (Rec.709)",
                        2: "Unspecified",
                        4: "BT.470M",
                        5: "BT.470BG (PAL)",
                        6: "SMPTE 170M (NTSC)",
                        7: "SMPTE 240M",
                        9: "BT.2020 (UHD/HDR10/DV)",
                        11: "SMPTE 431 (DCI-P3)",
                        12: "SMPTE 432 (Display P3)"
                    }

                    # 7. Extract core QC metrics cleanly
                    print(f"--- TECHNICAL QC REPORT ---")

                    print(f"---       VIDEO         ---")
                    if len(container.streams.video) > 0:
                        video_stream = container.streams.video[0]
                        print("WARNING: THIS VIDEO BLOCK IS DESIGNED TO DESCRIBE THE FIRST VIDEO STREAM ONLY")

                        print(f"Codec Name:       {video_stream.codec_context.name}")
                        print(f"Codec Profile:    {video_stream.codec_context.profile}")                   
                        print(f"File Size:        {os.path.getsize(file_path)/ 1_048_576:,.2f} Mb")

                        # COLOR SPACE/PRIMARIES FIXING BIT:
                        # Extract raw integers 
                        cs_raw = video_stream.codec_context.colorspace
                        cp_raw = video_stream.color_primaries
                        # Map to clean text strings
                        color_space_text = COLOR_SPACE_MAP.get(cs_raw, f"Unknown Code ({cs_raw})")
                        color_primaries_text = COLOR_PRIMARIES_MAP.get(cp_raw, f"Unknown Code ({cp_raw})")
                        print(f"Color Space:      {color_space_text}")
                        print(f"Color Primaries:  {color_primaries_text}")

                        # RETURN TO USUAL PRINTS...:


                        print(f"Pixel Format:     {video_stream.pix_fmt}")
                        print(f"Resolution:       {video_stream.width}x{video_stream.height}")
                        print(f"Total Frames:     {video_stream.frames}")

                        # Safe Video FPS:
                        avg_fps = float(video_stream.average_rate) if video_stream.average_rate else 0.0
                        if avg_fps > 0:
                            print(f"Average FPS:      {avg_fps:.2f}")
                        else:
                            print(f"Average FPS:       unavailable")

                        # BITRATE AND VBR FIXING BIT:
                        if video_stream.bit_rate and video_stream.bit_rate != "unspecified" and int(video_stream.bit_rate) > 0: 
                            print(f"BitRate:      {float(video_stream.bit_rate) / 1_048_576:.2f} Mbps") 
                            vidbitrate = float(video_stream.bit_rate) / 1_048_576
                            # BITRATES IN VIDEO STREAMS CAN LAND "UNSPECIFIED" DUE TO CONTAINER CONSTRAINTS, THE FOLLOWING 
                            # ELSE BLOCK IN LINE 37 CALCULATES AVERAGE BITRATES IF SUCH CASE.
                        else:
                            # 2. Fallback: Calculate it manually using file size and duration
                                file_size_bytes = os.path.getsize(file_path)

                                if container.duration and container.duration > 0:
                                    duration_secs = float(container.duration / av.time_base)
                                    calculated_bps = (file_size_bytes * 8) / duration_secs
                                    calculated_mbps = calculated_bps / 1_048_576                       
                                    print(f"BitRate:      {calculated_mbps:.2f} Mbps (Calculated Avg, Container Bitrate unavailable)")
                                    vidbitrate = calculated_mbps
                                else:
                                    print("BitRate:      Unavailable (Missing container duration)")
                                    vidbitrate = 0.0

                        avg_fps = float(video_stream.average_rate) if video_stream.average_rate else 0.0
                        base_fps = float(video_stream.base_rate) if video_stream.base_rate else 0.0
                        umbral_vfr = 0.1
                        if avg_fps > 0 and base_fps > 0:
                            difference = abs(avg_fps - base_fps)

                            if difference > umbral_vfr:
                                print(f"VARIABLE FRAMERATE DETECTED")
                                framerate = "VFR"
                            else:
                                print(f"Constant frame rate valid")
                                framerate = "CFR"
                        else:
                            print("UNKNOWN FRAMERATE - Metadata missing or corrupt")
                            framerate = "Warning, unknown"
                            file_data["errors"].append("Framerate unavailable, possible video corruption")

                        # ----------------------------------
                        print(f"Duration (Secs):  {float(container.duration / av.time_base):.2f}")
                        print(f"Duration (Mins):  {float(container.duration / av.time_base) / 60:.2f}")

                        # Per loop dict mass add for the metadata stats:
                        file_data["video"] = {
                            "codec_name": f"{video_stream.codec_context.name}",
                            "codec_profile": f"{video_stream.codec_context.profile}",
                            "file_size_mb": round(os.path.getsize(file_path)/ 1_048_576, 2),
                            "color_space": f"{color_space_text}",
                            "color_primaries": f"{color_primaries_text}",
                            "pixel_format": f"{video_stream.pix_fmt}",
                            "resolution": f"{video_stream.width}x{video_stream.height}",
                            "total_frames": f"{video_stream.frames}",
                            "average_fps": round(float(video_stream.average_rate), 2) if avg_fps > 0 else "Unknown",
                            "bitrate": round(vidbitrate, 2) if vidbitrate != 0 else "Unknown",
                            "frame_rate_mode": framerate,
                            "duration_mins": round(float(container.duration / av.time_base) / 60, 2) if container.duration else "Unknown"
                        }

                    else:
                        print("ERROR, VIDEO STREAM NONE / Error on sequence")
                        file_data["errors"].append("No video stream found.")
                        file_data["analysis_status"] = "Warning"


                    print(f"---       AUDIO         ---") 
                    if len(container.streams.audio) > 0:
                        audio_stream = container.streams.audio[0]
                        print("WARNING: THIS AUDIO BLOCK IS DESIGNED TO DESCRIBE THE FIRST AUDIO STREAM ONLY")
                        print(f"Total Audio Streams: {len(container.streams.audio)}")
                        print(f"Audio Codec:         {audio_stream.codec_context.name}")

                        # BITRATE FIXING BIT:
                        if audio_stream.bit_rate and audio_stream.bit_rate != "unspecified" and int(audio_stream.bit_rate) > 0: 
                            print(f"BitRate:             {float(audio_stream.bit_rate) / 1000:.2f} Kbps") 
                            audbitrate = float(audio_stream.bit_rate) / 1000
                            # BITRATES IN AUDIO STREAMS TOO CAN LAND "UNSPECIFIED" DUE TO CONTAINER CONSTRAINTS, THE FOLLOWING 
                            # ELSE BLOCK IN LINE 104 CALCULATES AVERAGE BITRATES IF SUCH CASE.
                        else:
                            try:
                                # Safely compute avg audio bitrate by isolating and counting only audio track packets
                                calculated_kbps = (sum(pkt.size for pkt in container.demux(audio_stream)) * 8) / (float(audio_stream.duration) / audio_stream.sample_rate) / 1000
                                print(f"BitRate:          {calculated_kbps:.2f} Kbps (Calculated Avg, Conatainer Bitrate unavailable)")
                                audbitrate = calculated_kbps
                            except:
                                print(f"Audio Bitrate corrupted, average unfound")
                                audbitrate = "Corrupted audio bitrate"
                                file_data["errors"].append("Audio bitrate unavailable, possible audio corruption")
                                pass

                        print(f"Audio Bit Depth:     {audio_stream.format.bits} bit")
                        print(f"Audio Sample Rate:   {float(audio_stream.sample_rate) / 1000:.2f} KHz")

                        # Safe Audio Duration:
                        if audio_stream.duration and audio_stream.sample_rate:
                            aud_dur_mins = float(audio_stream.duration) / (audio_stream.sample_rate * 60)
                            aud_dur_str = f"{aud_dur_mins:.2f} Mins"
                        else:
                            aud_dur_mins = "Unknown"
                            aud_dur_str = "Unknown"
                        print(f"Audio Duration:      {aud_dur_str}")

                        print(f"Audio Channels:      {len(audio_stream.layout.channels)}")
                        print(f"Channel Layout:        {audio_stream.layout.name}")

                        #
                        file_data["audio"] = {
                            "audio_streams": round(len(container.streams.audio)),
                            "audio_codec": audio_stream.codec_context.name,
                            "bitrate_kbps": audbitrate,
                            "audio_bit_depth": audio_stream.format.bits if audio_stream.format else "Unknown",
                            "audio_sample_rate": round(float(audio_stream.sample_rate) / 1000, 2),
                            "audio_duration": round(float(audio_stream.duration) / (audio_stream.sample_rate * 60), 2) if audio_stream.duration else "Unknown",
                            "audio_channels": len(audio_stream.layout.channels),
                            "channel_layout": audio_stream.layout.name
                        }
                            
                    else:
                        print("Audio streams nonexistant: Failure analyzing none / Error on sequence")
                        file_data["errors"].append("No audio stream found.")
                        file_data["analysis_status"] = "Warning"


                    # MASTER LIST FINAL APPEND FOR EACH DICT FOR EACH FILE, IN THE FOR LOOP
                    all_reports.append(file_data)

                print(f"---------------------------")
            except av.FFmpegError as av_err:
                # Catches PyAV-specific errors (corrupt streams, parsing errors)
                print(f"-> PyAV Error parsing {file_path.name}: {av_err}")
                file_data["analysis_status"] = "Failed"
                file_data["errors"].append(f"Possible file corruption, {file_path.name}, {av_err}.")
                all_reports.append(file_data)
                continue
                
            except Exception as e:
                # Catches any other unexpected errors (OS errors, permissions)
                print(f"-> Unexpected error with {file_path.name}: {e}")
                file_data["analysis_status"] = "Failed"
                file_data["errors"].append(f"Unexpected error, {file_path.name}, {e}.")
                all_reports.append(file_data)
                continue
                
            print("-" * 50)
    
    output_json_path = output_folder / "batch_qc_report.json" # CHANGE FOR STANDARD PYINSTALLER OUTPUT DIR INSTEAD OF folder_path
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(all_reports, json_file, indent=4)
        print(f"\nSUCCESS: Written final professional tracking report to: {output_json_path.name}")

# Run the batch analyzer
if __name__ == "__main__":
    batch_analyze_videos(input_folder)









