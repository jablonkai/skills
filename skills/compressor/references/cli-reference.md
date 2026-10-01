# Compressor CLI reference

The binary is `/Applications/Compressor.app/Contents/MacOS/Compressor`. Below is its own
`-help` output, captured verbatim on **Compressor 5.4**, followed by what actually happens
when you run it. Where the two disagree, the observed behaviour wins. The gotchas are
explained in [gotchas.md](gotchas.md).

## Observed behaviour (5.4)

| Flag | What `-help` says | What it really does |
|---|---|---|
| `-jobpath` | "url to source file" | Takes a `file://` URL **or** a plain path. The URL text is used literally, so `file:///a%20b.mov` fails with *path does not exist*. Pass `file:///a b.mov` or `/a b.mov` |
| `-locationpath` | "path to location file" | Must be the **full output file path**. A folder fails with *"Destination is a directory; Expected complete output file path"* (exit 255). Missing parent folders must already exist. An existing file is **overwritten without warning**. For image-sequence settings, `dir/name.tiff` writes the folder `dir/name/frame-NNNNNN.tiff` |
| `-settingpath` | "path to settings file" | Any `.compressorsetting` / `.cmprstng` / `.setting` file. It does not have to be in a Settings folder |
| `-jobpath … -settingpath … -locationpath …` | "repeated to enter multiple job targets" | Each repetition is one job. All jobs share one batch and run in parallel |
| `-outputformat json` | on submission | Prints `{ "batch" : { "batchID" : "…", "jobs" : [ {"jobID" : "…"}, … ] }}` on stdout. Job IDs come back in submission order. Exit 0 means **queued**, not finished |
| `-monitor -format json` | documented | **Rejected**: `Invalid parameter: -format`. Use `-monitor -outputformat json` |
| `-monitor … -once` | "show job status only once" | Prints one or more JSON arrays. The early ones are `[ ]` until the batch registers. Each non-empty one is `[{ "batchStatus": {…, "jobs": [{"jobStatus": {…}}]} }]` |
| `-kill -batchid ID` | kill | The status becomes `Cancelled` with `percentComplete` `100`. Partial outputs are deleted |
| Submission errors | — | A missing source or a folder as location: `Parameter error: …`, exit 255. An unreadable/corrupt source: `Submission Error: …` on stderr, exit 3. No batch is created in either case |

Status values seen: `Waiting`, `Processing`, `Successful`, `Cancelled`,
`Failed: <reason>`. Use the `timeElapsedSeconds`/`timeRemainingSeconds` fields. The
`submissionTime` strings follow the system locale (e.g. `2026. 10. 01., 20:30:55`).

NSLog noise such as `2026-10-01 20:30:44.162 Compressor[93565:…] fileURL is NOT a directory`
goes to stderr on every call and does not mean anything went wrong.

## `Compressor -help` (5.4, verbatim)

```text


Usage:  Compressor [Cluster Info] [Batch Specific Info] [Optional Info] [Other Options]

	-computergroup <name> -- name of the Computer Group to use.
--Batch Specific Info:--
	-batchname <name> -- name to be given to the batch.
	-priority <value> -- priority to be given to the batch. Possible values are: low, medium or high 
Job Info: Used when submitting individual source files. Following parameters are repeated to enter multiple job targets in a batch
	-jobpath <url> -- url to source file.
				   -- In case of Image Sequence, URL should be a file URL pointing to directory with image sequence.
				   -- Additional URL query style parameters may be specified to set frameRate (file:///myImageSequenceDir?frameRate=29.97) and audio file (e.g. file:///myImageSequenceDir?audio=/usr/me/myaudiofile.mov). 
	-settingpath <path> -- path to settings file.
	-locationpath <path> -- path to location file.
	-info <xml> -- xml for job info.
	-jobaction <xml> -- xml for job action.
	-scc <url> -- url to scc file for source
	-startoffset <hh:mm:ss;ff> -- time offset from beginning
	-in <hh:mm:ss;ff> -- in time
	-out <hh:mm:ss;ff> -- out time
	-annotations <path> -- path to file to import annotations from; a plist file or a Quicktime movie
	-chapters <path> -- path to file to import chapters from
--Optional Info:--
	-help -- Displays, on stdout, this help information.
	-checkstream <url> -- url to source file to analyze
	-findletterbox <url> -- url to source file to analyze

	-outputformat legacy|xml|json -- output format for job submission and monitoring (default is legacy)
--Batch Monitoring Info:--
Actions on Job:
	-monitor [-format legacy|xml|json] -- monitor the job or batch specified by jobid or batchid; output format is optional (default is legacy)
	-kill -- kill the job or batch specified by jobid or batchid.
	-pause -- pause the job or batch specified by jobid or batchid.
	-resume -- resume previously paused job or batch specified by jobid or batchid.
Optional Info:
	-jobid <id> -- unique id of the job usually obtained when job was submitted.
	-batchid <id> -- unique id of the batch usually obtained when job was submitted.
	-query <seconds> -- The value in seconds, specifies how often to query the cluster for job status.
	-timeout <seconds> -- the timeOut value, in seconds, specifies when to quit the process.
	-once -- show job status only once and quit the process.

--Sharing Related Options:--
	-resetBackgroundProcessing [cancelJobs] -- Restart all processes used in background processing, and optionally cancel all queued jobs.

	-repairCompressor -- Repair Compressor config files and restart all processes used in background processing.

	-instances <number>  -- Enables additional Compressor instances. 

--File Modification Options (all parameters EXCEPT -jobpath and -locationpath are ignored):--
	-relabelaudiotracks <layout[1] layout[2]... layout[N]
		Supported values:
			5_0 : 5.0 (L R C Ls Rs)
			5_1_A : 5.1 (L R C LFE Ls Rs)
			5_1_D : 5.1 (C L R Ls Rs LFE)
			C : Center
			L : Left
			LFE : LFE Screen
			Lc : Left Center
			Ls : Left Surround
			Lt : Left Total
			LtRt : Matrix Stereo (Lt Rt)
			R : Right
			Rc : Right Center
			Rls : Rear Surround Left
			Rrs : Rear Surround Right
			Rs : Right Surround
			Rt : Right Total
			SMTPE : SMPTE DTV (L R C LFE Ls Rs Lt Rt)
			mono : Mono
			stereo : Stereo (L R)
        -jobpath <url> -- url to source file. - Must be a QuickTime Movie file
        --Optional Info:--
            -renametrackswithlayouts (Optional, rename the tracks with the new channel layouts)
            -locationpath <path> -- path to location file.  Modified movie will be saved here.  If unspecified, changes will be saved in place, overwriting the original file.
    -relabelcolorspace <primaries> <transfer> <matrix>  (these are integer values corresponding to the NCLC standard)
	    -jobpath <url> -- url to source file. - Must be a QuickTime Movie file
	    --Optional Info:--
            -locationpath <path> -- path to location file.  Modified movie will be saved here.  If unspecified, changes will be saved in place, overwriting the original file.

```
