#Cloud [[CLoud Workflows]]

* Added whole cloud workflows: Dockerfile, Docker compose yml, Localstack, S3-SQS Bucket and processing Daemon.
* Added hardcoded VIDEO_EXTENSIONS suffixes filter to conformance checker for loop function, to avoid filetype processing errors, like admitting other types of accidental files from the S3 bucket dump.
* Modified "2. Safe Batch Processing Loop" (and the initial for loop running of the main function, removing ".iterdir()") in the three QC suite trio of programs to a block that admits single files and not only folders, to allow the cloud workflow to work with the pushed single files in the S3 bucket. Lines changed are: AnalyzerMK1 (24-41, 47), ConforCheckerMK1 (25-42, 55), RemuxerMK1 (25-42, 48).
* Fixed typo error in lines 249 and 251 in ConforCheckerMK1 (Used " instead of ') for the {Errors}.
* Added extra md file for clarity in the process of the cloud enviroment setup (Video-qc-trio_Cloud_Setup)
* 

