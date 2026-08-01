VideoQC Conformance Checker (ConforCheckMK1)

VideoQC Conformance Checker is an automated, rules-driven batch validation engine for post-production, broadcast, and streaming 
ingest pipelines. Built on direct PyAV C-bindings, it audits media assets against an external JSON delivery 
specification (Example_Standard.json) and generates actionable compliance reports with per-file diagnostic logs.


* Technical Highlights

* JSON-Driven Delivery Specs: Separates program logic from business rules. Delivery requirements (codecs, resolutions, color metadata, 
audio configurations) are declared in external standard files without requiring code modifications.
* Floating-Point FPS & Bitrate Tolerance Matching: Evaluates non-exact metadata (such as 23.976 vs 24.0 fps drift or container 
bitrate spikes) using delta checks ($\Delta < 0.03$) and upper-threshold boundaries to prevent false negatives on valid renders.
* Granular Incompliance Diagnostics: Assets failing validation are tagged as "Uncompliant" and populated with a detailed 
"Incompliances" array listing the exact stream properties that violated spec.
* PyAV Low-Level Stream Parsing: Directly inspects container headers and demuxes audio/video packets via C-bindings (libavformat/libavcodec),
ensuring cross-platform stability without subprocess CLI wrapping.
* Isolated Pipeline Exception Handling: Catches stream corruptions (av.FFmpegError), missing tracks, or file system errors without 
breaking the batch loop, outputting execution statuses of Compliant, Uncompliant, Warning Uncompliant, or Failed.
Target Standard Configuration (Example_Standard.json): Define your required broadcast or Web ingest spec in JSON format:


* Architectural Workflow:


Input Video Assets          Target Delivery Spec
  (InputFolder/)            (Example_Standard.json)
       │                              │
       └──────────────┬───────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│  PyAV Inspection & Metadata Extraction Engine │
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│           Conformance Rules Engine           │
├──────────────────────────────────────────────┤
│ • Video Codec & Profile Verification         │
│ • Color Space & Primaries Code Matching      │
│ • Resolution & Pixel Format Audit            │
│ • FPS Variance & Frame Rate Mode (CFR/VFR)   │
│ • Bitrate Ceiling Enforcement                │
│ • Audio Stream Count, Sample Rate & Bit Depth│
│ • Channel Count & Layout Alignment           │
└─────────────────────┬────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────┐
│ Diagnostic JSON Audit Report                 │
│ (Compliance_Report/conformance_report.json)  │
└──────────────────────────────────────────────┘

* Usage & Execution:

Place your target video assets in InputFolder/.

Define your target requirements in Example_Standard.json.

Run the conformance script:

Bash
python ConforCheckMK1.py
Retrieve the audit log from Compliance_Report/conformance_report.json.

# # Run the program once first to automatically create the folders of output and input, later utilize the input folder for the video footage
  drop. And extract the resulting json report from the output folder.                 

