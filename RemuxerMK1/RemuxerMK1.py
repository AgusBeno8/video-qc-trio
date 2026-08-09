import os
import av
import av.datasets
import av.filter
import pathlib
from pathlib import Path
import json

# 1. Creates a "InputFolder" folder in the exact same directory as your script, move the script outside, and put the videos to analyze inside.
# Also does the same for output folder.
SCRIPT_DIR = Path(__file__).resolve().parent
input_folder = (SCRIPT_DIR / "InputFolder").resolve()
output_folder = (SCRIPT_DIR / "Remuxed").resolve()

# Automatically create the folder if it doesn't exist yet:
input_folder.mkdir(parents=True, exist_ok=True)
output_folder.mkdir(parents=True, exist_ok=True)


# Video extension suffixes for initial checks AND DETERMINING WHICH SUFFIXES ARE THOSE TO REMUX. In this example, the chosen method is to
# remux everything to mov.
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".m4v", ".flv"}

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
            # The video_extensions works as the primary funnel for intake, thus the loop only accepts the files with 
            # the suffixes specified for remuxing. 
            print(f"Processing Remux for: {file_path.name} file number: {counter}")

            # File size bit:
            try:
                file_size = round(os.path.getsize(file_path)/ 1_048_576, 2)
            except:
               file_size = 0
               print("File size unavailable, check file")

            # Dictionary per loop (per file) and counter:
            counter += 1
            file_data = {
                "batch_idnum": counter,
                "file_name": file_path.name,
                "file_size_mb": file_size,
                "remuxing_status": "Success",
                "input_direction": [],
                "output_direction": [],
                "errors": []
            }
            container = None

            # Mapping dictionary to track corresponding streams
            stream_mapping = {} 
            # Pathlib slashes autochange for output direction specifics (needs a specific filename for the output):
            # IT ALSO DEFINES THE OUTPUT SUFFIX (CONTAINER)
            output_file_dir = Path(output_folder / f"{file_path.stem}_REMUXED.mov")

            try:
                with av.open(file_path) as input_container, av.open(output_file_dir, 'w') as output_container: # SWAP THESE, REMEMBER NON TEST
                   if len(input_container.streams.video) > 0 and len(input_container.streams.audio) > 0:
                     # Copy stream configurations from input to output
                     for in_stream in input_container.streams:
                        # Skip unsupported stream types if necessary (e.g. data or attachment streams)
                        if in_stream.type in ('video', 'audio', 'subtitles'):
                            out_stream = output_container.add_stream_from_template(in_stream)
                            stream_mapping[in_stream.index] = out_stream

                     # Demux packets from input, reassign stream, and mux to output
                     for packet in input_container.demux():
                         if packet.stream.index not in stream_mapping or packet.dts is None:
                             continue # Skips non-specified streams
                         
                         # Link packet to corresponding output stream
                         out_stream = stream_mapping[packet.stream.index]
                         packet.stream = out_stream

                         # Write packet
                         output_container.mux(packet)

                     # Remuxing report in JSON:
                     file_data["input_direction"].append(f"{input_container}")
                     file_data["output_direction"].append(f"{output_container}")
                     all_reports.append(file_data)
                    
                         
                   else:
                      print("ERROR, VIDEO/AUDIO STREAM NONE / Error on sequence")
                      file_data["errors"].append("No video stream found.")
                      file_data["remuxing_status"] = "Warning"


            except av.FFmpegError as av_err:
                # Catches PyAV-specific errors (corrupt streams, parsing errors)
                print(f"-> PyAV Error parsing {file_path.name}: {av_err}")
                file_data["remuxing_status"] = "Failed"
                file_data["errors"].append(f"Possible file corruption, {file_path.name}, {av_err}.")
                all_reports.append(file_data)
                            
            except Exception as e:
             # Catches any other unexpected errors (OS errors, permissions)
             print(f"-> Unexpected error with {file_path.name}: {e}")
             file_data["remuxing_status"] = "Failed"
             file_data["errors"].append(f"Unexpected error, {file_path.name}, {e}.")
             all_reports.append(file_data)
                            
            
            print("-" * 50)

    output_json_path = output_folder / "doneremuxing_log.json" # CHANGE FOR STANDARD PYINSTALLER OUTPUT DIR
    with open(output_json_path, "w", encoding="utf-8") as json_file:
        json.dump(all_reports, json_file, indent=4)
        print(f"\nSUCCESS: Written final professional tracking report to: {output_json_path.name}") 



# Run the batch remuxer
if __name__ == "__main__":
   batch_remux(input_folder)