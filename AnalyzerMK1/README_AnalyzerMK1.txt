AnalyzerMk1 - Automated Batch JSON outputting metadata reporter.

VideoQC Metadata Analyzer is a lightweight, high-performance Python tool for deep technical inspection of video and audio streams. 
It batch-extracts stream properties, color metadata, bitrate stats, and frame rate behavior into clean, structured JSON reports for 
post-production and media asset management (MAM) workflows. 
I chose PyAV (direct FFmpeg C-bindings), because it achieves visually lossless 
container swapping at native filesystem I/O speeds, with the pros of object-driven coding and avoiding 
CLI string-subprocess commands (Which not only difficults bug fixing, incorporates ortographic issues across languages, but also 
adds cross-compatibility severe issues with Mac and Linux systems due to the subprocess usage.)

---

* Key features

* *Color Space Enum Resolution:* Automatically maps raw FFmpeg color space and primaries integer codes (e.g., 1, 9, 11) 
to human-readable broadcast standards like BT.709 (Rec.709), BT.2020 (HDR), and DCI-P3.
* *Smart Fallback Calculations:* Using packet-level data rather than often faulty container flairs.
* *Batch Processing & Auto-Routing:* Filters input files by configurable extensions (`VIDEO_EXTENSIONS`) and outputs mapped files with 
standardized naming conventions.
* *Structured Audit Logging:* Outputs a highly parseable comprehensive JSON log report detailing execution status, file sizes, 
stream directions, audio/video stats, and error diagnostics per file.
* *Exception Handling:* Gracefully handles PyAV parsing errors, corrupted stream packets, missing media streams, and 
OS-level file system exceptions.

---

* Technical architecture

The core pipeline operates on PyAV's low-level C-bindings to manipulate packet streams directly:

1. *Target Filtering:* Inspects input directory files against the allowed `VIDEO_EXTENSIONS` set.
2. *Metadata Block Mapping:* Reads input stream properties (`input_container.streams`) and creates corresponding print statements, then 
appends results to the per-file dicts utilizing error handling-tuned exceptions.
3. *Smart Bitrate Fallback Calculations:*
Video: If container bitrates return "unspecified", "0", or "None", the tool calculates exact average bitrates using 
filesystem byte sizes and duration math.
Audio: If audio metadata is missing or corrupted, it demuxes audio stream packets in memory to compute 
true average kilobits-per-second (Kbps).
4. *FR vs. CFR Detection Engine:* Evaluates variances between stream average_rate and base_rate against a tolerance threshold to 
flag Variable Frame Rate (VFR) files—preventing downstream editor sync issues.
5. *Graceful Pipeline Error Isolation:* Catches av.AVError and system-level exceptions on corrupted files, tagging 
bad assets as Failed or Warning in the JSON log without halting the batch loop.
6. *Diagnostic Reporting:* Appends status metadata (Success, Warning, or Failure) and detailed stack traces into `batch_qc_report.json`.

---

# Configuration & Usage

## 1. Configuration
Set input file types and target container extensions directly in the script constants:

# Set allowed input video extensions
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".m4v", ".flv"}
                                    / here above

# # Run the program once first to automatically create the folders of output and input, later utilize the input folder for the video footage
  drop. And extract the resulting json report from the output folder.                 


### Architectural Workflow:

Input Video Files
       │
       ▼
┌──────────────────────────────────────────────┐
│  Extension Filtering & PyAV Container Open   │
└──────────────────────┬───────────────────────┘
                       │
┌────────────────────────────────────────────────┐
│ Outermost File Metadata collection (Name, Etc) │
└──────────────────────┬─────────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│       Video Stream        │   │       Audio Stream        │
├───────────────────────────┤   ├───────────────────────────┤
│ • Codec & Profile         │   │ • Codec Name              │
│ • Color Space Mapping     │   │ • Sample Rate & Bit Depth │
│ • Resolution & Pix Format │   │ • Channel Layout (Stereo/ │
│ • VFR / CFR Delta Check   │   │   5.1 split)              │
│ • Bitrate Fallback Engine │   │ • Packet-Demux Bitrate    │
└──────────────┬────────────┘   └──────────────┬────────────┘
               │                               │
               └───────────────┬───────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────┐
│ JSON Serialization (batch_qc_report.json)    │
└──────────────────────────────────────────────┘