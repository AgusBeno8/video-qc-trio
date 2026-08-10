MK1 Video Quality Control Suite:

Python 3.10+ https://img.shields.io/badge/python-3.10%2B-blue.svg https://www.python.org/

Engine: PyAV https://img.shields.io/badge/engine-PyAV%20(FFmpeg%20C--bindings)-green.svg)] https://pyav.org/

Cross-Platform CI: https://github.com/AgusBeno8/video-qc-trio/actions/workflows/ci.yml/badge.svg https://github.com/AgusBeno8/video-qc-trio/actions

License: MIT https://img.shields.io/badge/license-MIT-informational.svg)](LICENSE)

A lightweight, high-throughput Python suite for Tier-1 video quality control, metadata inspection, and stream remuxing**. Built specifically for batch operations in media pipelines where high-end SaaS subscriptions are unnecessary, but precision C-level stream evaluation is required.

Developer Note: This suite is designed as an architectural reference and modular foundation. It operates via CLI / IDE execution rather than a desktop GUI, prioritizing raw engine performance, cross-platform stability, and transparent code structure over end-user packaging.

The MK1 trio of Video QC programs is an array of structural Tier 1 (Surface container Metadata and packet data fallbacks) tools for semi professional scenarios where the metadata specificity of open source tools like QCTools or mediainfo are needed, but also the capability to run batches at high speeds without paying high-end SaaS subscriptions for popular QC companies. The direct-executable (client-ready) capability of them is low, because the purpose of this work is exemplyfing metadata management, compatibilities, conversions, and PyAv object handling, therefore they lack direct executables and UI, even if it is easily possible to add these small updates down the line for myself.
It is recommended that users utilize an IDE like VScode to modify the structures to their liking and necessities, even if the only specific dependencies are those of the Remuxer MK1 and the Confor Checker MK1, the line-specified suffix modification for intake and output container type remuxing, and as-needed JSON Standard template funneling, respectively.

I utilized PyAv mainly (after a two-day long analysis and research of different wrappers or options, pondering their capabilities and ease of use, besides constraints) to avoid cross-language CLI grammatical errors when using subprocess-strings with command interfaces of OS or ffmpeg executables and cross-compatibility errors due to Linux and Mac detecting and locking down foreign subprocesses or even exectuables like ffmpeg when it is utilized as the main engine of the script. Besides, the object-oriented architecture allowed me to learn and debug incredibly fast. The result is that PyAv allowed me a single script handling the whole program's needs, solely on python. This makes the further translation to a single-executable client-ready version essentially short.

These projects utilize Python as the basis of the structure, PyAV as the engine utilizing it's object-oriented ffmpeg C-Libraries with high speed container metadata and packet management, Pathlib library for input/output folder creation and finding and flagging directories, and JSON dictionaries for output reports specifically, but also standard-setting in the Conformance Checker MK1.

Utilize the specific READMEs and JSON report examples of the folders of every program to have insight in their inner work, besides guiding yourself by the in-code comments.

The inclusion of AI in these projects served as primarily learning leverage by documentation funneling, but also strict debugging, small-block acquiring that was analyzed properly, and late general checks pre delivery.

My experience regarding the fields this project are dedicated to learning orchestrational python basics and foundations, video engineering learning across programs like davinci resolve, handbrake, mediainfo, qctools, and finally, Python-orchestrated custom programming using PyAv or wrappers, leveraging ffmpeg's performance. Spending hours and hours every single day chasing my career dream.

I am focusing on Qc Operator Metadata and artifacts detection currently after i post this project, but i intend to update these programs with first and foremost exemplified cloud workflows utilizing boto3-s3, daemons, and Docker enviroments in short time. A basic UI and ready-compiled cross-OS actions is also considered.

1.1 Version Note: The Cloud Workflow mockup with localstack has been completed and added. Be sure to read the files "Video-qc-trio_1.1_Cloud_Setup.md" and "video-qc-trio_1.1 Cloud Mockup version Notes.md" To grasp the context of the updates and the differences.
