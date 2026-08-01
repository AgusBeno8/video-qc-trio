RemuxerMk1 - Automated Batch Remuxer

The RemuxerMk1 is a high-efficiency fast Python tool for batch-transmuxing video files between container formats 
(e.g., `.mp4`, `.mkv`, `.avi` to `.mov`) without re-encoding video or audio streams. I chose PyAV (direct FFmpeg C-bindings), because it
achieves visually lossless container swapping at native filesystem I/O speeds, with the pros of object-driven coding and avoiding 
CLI string-subprocess commands (Which not only difficults bug fixing, incorporates ortographic issues across languages, but also 
adds cross-compatibility severe issues with Mac and Linux systems due to the subprocess usage.)

---

* Key features

* *Lossless Stream Copying:* Direct packet demux-to-mux pipeline avoids CPU-heavy re-encoding and preserves original stream quality.
* *Stream Filtering:* Automatically filters out unsupported or unwanted data streams while mapping video, audio, 
and subtitle streams to the target container.
* *Batch Processing & Auto-Routing:* Filters input files by configurable extensions (`VIDEO_EXTENSIONS`) and outputs mapped files with 
standardized naming conventions.
* *Structured Audit Logging:* Outputs a highly parseable comprehensive JSON log report detailing execution status, file sizes, 
stream directions, and error diagnostics per file.
* *Exception Handling:* Gracefully handles PyAV parsing errors, corrupted stream packets, missing media streams, and 
OS-level file system exceptions.

---

* Technical architecture

The core pipeline operates on PyAV's low-level C-bindings to manipulate packet streams directly:

1. *Target Filtering:* Inspects input directory files against the allowed `VIDEO_EXTENSIONS` set.
2. *Stream Template Mapping:* Reads input stream properties (`input_container.streams`) and creates corresponding target streams 
in the output container using `add_stream_from_template()`.
3. *Packet Relinking & Muxing:* Iterates through input packets (`demux()`), updates packet stream assignments, and writes 
directly to the destination container (`mux()`).
4. *Diagnostic Reporting:* Appends status metadata (Success, Warning, or Failure) and detailed stack traces into `doneremuxing_log.json`.

---

# Configuration & Usage

## 1. Configuration
Set input file types and target container extensions directly in the script constants:

# Set allowed input video extensions
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".m4v", ".flv"}
                                    / here above
# Set target output filename and container format
output_file_dir = Path(output_folder / f"{file_path.stem}_REMUXED.mov")
                                                                   / here above suffix

## Run the program once first to automatically create the folders of output and input, later utilize the input folder for the video footage
  drop. And extract the resulting json report and remuxed files from the output folder.                                                    