# Compressor CLI gotchas

All of these were observed on Compressor 5.4 (macOS 27, arm64). `cmp-encode.py` and the
other scripts handle each one. Read this before writing raw `Compressor` commands.

## Submitting

- **`-locationpath` is a file, not a folder.** A folder fails with *"Destination is a
  directory; Expected complete output file path with file name."* (exit 255). Give the
  full name including the extension the setting writes (`.mov`, `.m4v`, `.mp4`, `.mxf`).
- **Existing outputs are silently overwritten.** Compressor neither renames nor refuses.
  If an output already exists, decide whether to skip it or replace it before you submit.
- **`-jobpath` URLs are not decoded.** `file:///Volumes/Card/A001%20C003.mov` fails with
  *path does not exist*. Pass the plain path, or `file://` + the plain path.
- **Missing parent folders are not created.** Make the output folder first.
- **Exit 0 only means the batch was queued.** The encode runs in the background and the
  command returns within about a second. The batch and job IDs are in the
  `-outputformat json` reply.
- **A bad source rejects the whole batch.** A missing file exits 255 with `Parameter
  error`. An unreadable file exits 3 with `Submission Error: INVOKING METHOD OR ACCESSING
  MEMBER FOR NULL REFERENCE`. Nothing is queued, including the good jobs.

## Waiting for the result

- **The output file appears at 0 bytes as soon as the job starts.** A file being there
  doesn't mean it's finished. Wait for the status `Successful`.
- **`-monitor -format json` is rejected**, even though `-help` documents it. Use
  `-monitor -outputformat json`.
- **`-monitor -once` can print empty `[ ]` arrays** before the batch registers, or several
  arrays one after another. Parse every array and use the last non-empty one.
- **`-monitor` doesn't list every job.** A failed batch lists only the failed job, and a
  successful one can omit jobs that finished early. Decide when to stop from the **batch**
  status, then check each output file yourself.
- **`percentComplete: 100` doesn't mean success.** A cancelled or failed job also reports
  100.
- **Timestamps follow the system locale** (`2026. 10. 01., 20:30:55` on a Hungarian
  system). Use the `*Seconds` fields.
- **The background service is shared and fragile under contention.** Every client uses
  the same JobController and Transcoder services: the app, other scripts, other agents.
  While several clients submitted at once and two of them ran
  `-resetBackgroundProcessing`, we saw all of these:
  - `Failed: 2x job controller down`, even for a single 3-second clip
  - batches that ended `Cancelled` although nobody killed them
  - a batch that stayed invisible to `-monitor` (only `[ ]`) until a 600 s timeout.
    `cmp-encode.py` now gives up after `--lost-after` (90 s).

  On an idle machine, the same commands always succeeded. A heavy batch of our own (8
  parallel jobs, 2 of them TIFF sequences) failed one job once. **Recovery: run the same
  command again** (complete outputs are skipped). **Don't** reach for
  `-resetBackgroundProcessing`: it is exactly what breaks the other clients.

## Settings

- **Built-in settings live deep inside the bundle**:
  `Contents/PlugIns/Compressor/CompressorKit.bundle/…/StompUI.framework/Versions/A/Resources/BuiltInSettings/<Group>/`.
  File names are often localisation keys (`proRes422ProxyName.compressorsetting`). The
  names users see come from `StompTypes.framework/…/en.lproj/Localizable.strings`.
  `cmp-settings.py` maps between the two.
- **Display names don't always match the file names.** `Up to 4k (HEVC 8-bit 4:2:0).compressorsetting`
  shows up as **"HEVC 8-bit 420"**, and `uncompressed8BitName` as **"Uncompressed 8-bit 422"**.
- **The same name appears twice.** "Apple ProRes 422 Proxy" exists as a QuickTime setting
  and as an MXF setting. The scripts prefer the QuickTime one. For MXF, pass the path.
- **Frame size is set by `<automatic width height>`, not `<bounds>`.** A setting with only
  `<bounds width="1280" height="720">` changed still encoded 1920×1080. Set both (see
  [settings.md](settings.md)).
- **`<data-rate>` edits didn't cap the bitrate.** Setting 250000 on an HEVC Apple Devices
  setting gave about 4.4 Mb/s. Its units and its interaction with the quality mode are
  unverified, so don't promise a bitrate from an XML edit. Choose a built-in at the right
  quality tier, or have the user set the bitrate in the app and export the setting.
- **Custom settings folder**: `~/Library/Application Support/Compressor/Settings/`. It
  doesn't exist until the first custom setting is saved, and creating it by hand is fine.

## Image sequences

- `-locationpath out/name.tiff` writes the **folder** `out/name/` containing
  `frame-000000.tiff`, `frame-000001.tiff`, …. There is one frame per source frame and no
  audio. 1080p TIFFs are about 16 MB each, so warn the user about disk space.

## Misc

- ProRes outputs include a timecode track (`tmcd`) besides the video and audio streams.
  Select the video stream by type when checking.
- `-resetBackgroundProcessing [cancelJobs]` and `-repairCompressor` affect **every**
  queued job on the machine. Use them only if the user explicitly asks.
