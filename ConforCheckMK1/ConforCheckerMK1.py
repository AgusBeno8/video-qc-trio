import os
import av
import av.datasets
import av.filter
import pathlib
from pathlib import Path
import json

# 1. Creates a "InputFolder" folder in the exact same directory as your script, move the script outside, and put the videos to analyze inside.
# The further lines create the __file__ self locating function parameter, as well as the "Compliance_Report" OUTPUT FOLDER for the json report.
# And lastly it also direct the compliance standard's json.
SCRIPT_DIR = Path(__file__).resolve().parent
input_folder = (SCRIPT_DIR / "InputFolder").resolve()
output_folder = (SCRIPT_DIR / "Compliance_Report").resolve()
compliance_standard = (SCRIPT_DIR / "Example_Standard.json").resolve()

# Automatically create the folder if it doesn't exist yet
input_folder.mkdir(parents=True, exist_ok=True)
output_folder.mkdir(parents=True, exist_ok=True)

# 2. Safe Batch Processing Loop
def batch_conformance_check(folder_path):
    print(f"Starting batch analysis in: {folder_path}\n")
    
    # Check if directory exists
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Error: The directory {folder_path} does not exist.")
        return
    
    counter = 0
    all_reports = [] # Master list for JSON report output.

    # Load the JSON standard here:
    try:
        with open(compliance_standard, "r", encoding="utf-8") as f:
            standard_data = json.load(f)
    except: 
        print("Missing compliance standard JSON.")

    # 3. Iterate through all files in the folder
    for file_path in folder_path.iterdir():
        # Filter for files matching your video extensions
        if file_path.is_file():
            print(f"Processing: {file_path.name} file number: {counter}")

            # Dictionary per loop (per file) and counter:
            counter += 1
            file_data = {
                "batch_idnum": counter,
                "file_name": file_path.name,
                "video": {},
                "audio": {},
                "analysis_status": "Compliant",
                "errors": [],
                "Incompliances": []
            }
            try:
                # 4. Open the video container securely
                with av.open(os.fspath(file_path)) as container:

                    # 5. COLOR SPACE/PRIMARIES DICTIONARIES NAME LOOKUP BIT LINE 51-60
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

                        # COLOR SPACE/PRIMARIES BIT:
                        cs_raw = video_stream.codec_context.colorspace
                        cp_raw = video_stream.color_primaries
                        print(f"Color Space code:      {cs_raw}")
                        print(f"Color Primaries code:  {cp_raw}")
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
                            "color_space": f"{cs_raw}",
                            "color_primaries": f"{cp_raw}",
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
                        file_data["analysis_status"] = "Warning Uncompliant"


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
                        file_data["analysis_status"] = "Warning Uncompliant"



                    # CONFORMANCE CHECKING BLOCK:
                    print("-" * 10)
                    print("CONFORMANCE CHECKING BLOCK:")
                    try:
                        if file_data["errors"] == standard_data["errors"]: # Empty error dict check
                            print("No errors, compliant")
                        else:
                            print(f"Errors found: {file_data["errors"]}. Uncompliant")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append(f"Errors: {file_data["errors"]}")


                        # Video block:
                        print("CONFORMANCE VIDEO:")
                        if file_data["video"]["codec_name"] in standard_data["video"]["codec_name"]:
                            print("Compliant codec")
                        else:
                            print("Uncompliant codec")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant codec")



                        if file_data["video"]["codec_profile"] in standard_data["video"]["codec_profile"]:
                            print("Compliant codec profile")
                        else:
                            print("Uncompliant codec profile")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant codec profile")



                        if file_data["video"]["color_space"] in standard_data["video"]["color_space"]:
                            print("Compliant color space")
                        else:
                            print("Uncompliant color space")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant color space")



                        if file_data["video"]["color_primaries"] in standard_data["video"]["color_primaries"]:
                            print("Compliant color primaries")
                        else:
                            print("Uncompliant color primaries")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant color primaries")



                        if file_data["video"]["pixel_format"] in standard_data["video"]["pixel_format"]:
                            print("Compliant pixel_format")
                        else:
                            print("Uncompliant pixel format")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant pixel format")



                        if file_data["video"]["resolution"] in standard_data["video"]["resolution"]:
                            print("Compliant resolution")
                        else:
                            print("Uncompliant resolution")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant resolution")


                        # Worry not, the only possibilities for the below dict value of "average_fps" is either "Unknown" or a digit.
                        # This is detailed in line 162.
                        # This bit won't throw valuerror due to an operation with non-values.
                        if file_data["video"]["average_fps"] != "Unknown" and abs(file_data["video"]["average_fps"] - standard_data["video"]["average_fps"]) < 0.03:
                            print("Compliant fps")
                        else:
                            print("Uncompliant fps")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant fps")


                        # Read line 298 discretion. Works the same for this one.
                        if file_data["video"]["bitrate"] != "Unknown" and file_data["video"]["bitrate"] <= standard_data["video"]["bitrate"]:
                            print("Compliant bitrate")
                        else:
                            print("Uncompliant bitrate")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant bitrate")



                        if file_data["video"]["frame_rate_mode"] in standard_data["video"]["frame_rate_mode"]:
                            print("Compliant frame rate mode")
                        else:
                            print("Uncompliant frame rate mode")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant frame rate mode")



                        # Audio block:
                        print("CONFORMANCE AUDIO:")
                        if file_data["audio"]["audio_streams"] == standard_data["audio"]["audio_streams"]:
                            print("Compliant audio stream amount")
                        else:
                            print("Uncompliant audio stream amount")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant audio stream amount")



                        if file_data["audio"]["audio_codec"] in standard_data["audio"]["audio_codec"]:
                            print("Compliant audio codec")
                        else:
                                print("Uncompliant audio codec")
                                file_data["analysis_status"] = "Uncompliant"
                                file_data["Incompliances"].append("Uncompliant audio codec")



                        if file_data["audio"]["bitrate_kbps"] == standard_data["audio"]["bitrate_kbps"]:
                            print("Compliant audio bitrate")
                        else:
                            print("Uncompliant audio bitrate")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant audio bitrate")



                        if file_data["audio"]["audio_bit_depth"] == standard_data["audio"]["audio_bit_depth"]:
                            print("Compliant audio bit depth")
                        else:
                            print("Uncompliant audio bit depth")
                            file_data["analysis_status"] = "Uncompliant"
                            file_data["Incompliances"].append("Uncompliant audio bit depth")



                        if file_data["audio"]["audio_sample_rate"] == standard_data["audio"]["audio_sample_rate"]:
                            print("Compliant audio sample rate")
                        else:
                                print("Uncompliant audio sample rate")
                                file_data["analysis_status"] = "Uncompliant"
                                file_data["Incompliances"].append("Uncompliant audio sample rate")



                        if file_data["audio"]["audio_channels"] == standard_data["audio"]["audio_channels"]:
                            print("Compliant audio channels amount")
                        else:
                                print("Uncompliant audio channels amount")
                                file_data["analysis_status"] = "Uncompliant"
                                file_data["Incompliances"].append("Uncompliant audio channels amount")



                        if file_data["audio"]["channel_layout"] in standard_data["audio"]["channel_layout"]:
                            print("Compliant audio channel layout")
                        else:
                                print("Uncompliant audio channel layout")
                                file_data["analysis_status"] = "Uncompliant"
                                file_data["Incompliances"].append("Uncompliant channel layout")


                        # MASTER LIST FINAL APPEND FOR EACH DICT FOR EACH FILE, IN THE FOR LOOP
                        all_reports.append(file_data)

                    except Exception as e:
                        print(f"Something exploded in the conformance block: {e}")


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
                file_data["errors"].append(f"Unexpected error, possible corruption, {file_path.name}, {e}.")
                all_reports.append(file_data)
                continue
                
            print("-" * 50)
    
    output_json_path = output_folder / "conformance_report.json" # CHANGE FOR STANDARD PYINSTALLER OUTPUT DIR INSTEAD OF folder_path
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(all_reports, json_file, indent=4)
        print(f"\nSUCCESS: Written final professional tracking report to: {output_json_path.name}")

# Run the batch analyzer
if __name__ == "__main__":
    batch_conformance_check(input_folder)









