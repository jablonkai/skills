# DaVinci Resolve Python API — 21.1 reference

Generated from `DaVinciResolveScript.pyi` shipped with **DaVinci Resolve Studio 21.1.0**. Every
signature below is the canonical 21.1 form; overloaded calling conventions are deprecated (see
[gotchas.md](gotchas.md)). The stub on disk is authoritative for the installed version —
`bash scripts/resolve-api.sh <Name>` greps it for anything missing here, including the full
`ProjectSettings` / `TimelineSettings` key lists, which are omitted for size.

Indices are **1-based** everywhere (tracks, timelines, nodes, takes, comps). Frames are
**absolute timeline frames** (a timeline starting at 01:00:00:00 at 24 fps starts at frame 86400).
A failed call returns `False` or `None` — it does not raise.

## Contents

- [Classes](#classes): Resolve, ProjectManager, Project, MediaPool, MediaPoolItem, Timeline,
  TimelineItem, ColorGroup, Folder, Gallery, GalleryStillAlbum, Graph, MediaStorage
- [Parameter dicts](#parameter-dicts)
- [Constants](#constants)
- [Literal types](#literal-types)

## Classes

### Resolve

The Resolve application: pages, the current project and application-wide presets.

```text
GetProjectManager() -> ProjectManager
    Returns the project manager object for currently open database
GetMediaStorage() -> MediaStorage
    Returns the media storage object to query and act on media locations
Fusion() -> Fusion
    Starting point for Fusion scripts
GetCurrentProject() -> Project
    Returns the currently loaded Resolve project
GetCurrentTimeline() -> Timeline
    Returns the currently loaded timeline
GetMediaPool() -> MediaPool
    Returns the MediaPool object for the current project
GetGallery() -> Gallery
    Returns the Gallery object for the current project
OpenPage(pageName: str) -> bool
    Switches DaVinci Resolve Page. pageName can be: 'media', 'photo', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver'
GetCurrentPage() -> str
    Returns current DaVinci Resolve Page: 'media', 'photo', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver'
SetHighPriority(highPriority: bool) -> bool
    Sets the script execution priority to high or normal
GetVersion() -> list[int | str]
    Returns list of product version fields in [major, minor, patch, build, suffix] format
GetVersionString() -> str
    Returns product version in major.minor.patch[suffix].build format
GetProductName() -> str
    Returns product name
IsStudio() -> bool
    Returns whether this is the Studio version of the product
GetLayoutPresetList() -> list[str]
    Returns a list of available UI layout preset names
LoadLayoutPreset(presetName: str) -> bool
    Loads UI layout from saved preset
UpdateLayoutPreset(presetName: str) -> bool
    Overwrites preset named 'presetName' with current UI layout
ExportLayoutPreset(presetName: str, presetFilePath: str) -> bool
    Exports preset named 'presetName' to path 'presetFilePath'
DeleteLayoutPreset(presetName: str) -> bool
    Deletes preset named 'presetName'
SaveLayoutPreset(presetName: str) -> bool
    Saves current UI layout as a preset
ImportLayoutPreset(presetFilePath: str, presetName: str | None=None) -> bool
    Imports UI layout preset from file
Quit() -> bool
    Quits the Resolve App
ImportRenderPreset(presetPath: str) -> bool
    Import a render preset from a file and select it
ExportRenderPreset(presetName: str, exportPath: str) -> bool
    Export a render preset to a file
GetBurnInPresetList() -> list[str]
    Returns a list of available data burn in preset names
DeleteBurnInPreset(presetName: str) -> bool
    Deletes the named data burn in preset
ImportBurnInPreset(presetPath: str) -> bool
    Import a data burn in preset from a file
ExportBurnInPreset(presetName: str, exportPath: str) -> bool
    Export a data burn in preset to a file
GetKeyboardPresetList() -> list[str]
    Returns a list of available keyboard preset names
LoadKeyboardPreset(presetName: str) -> bool
    Loads the named keyboard preset
DeleteKeyboardPreset(presetName: str) -> bool
    Deletes the named keyboard preset
GetCurrentKeyboardPreset() -> str
    Returns the name of the currently active keyboard preset
ImportKeyboardPreset(filePath: str, presetName: str | None=None) -> bool
    Imports a keyboard preset from file. Uses file base name as preset name if not specified.
ExportKeyboardPreset(presetName: str, exportPath: str) -> bool
    Exports the named keyboard preset to the specified file path
GetKeyframeMode() -> int
    Returns the currently set keyframe mode, one of the resolve.KEYFRAME_MODE_* constants. Color Page only.
SetKeyframeMode(keyframeMode: KeyframeMode) -> bool
    Set keyframe mode
GetFairlightPresets() -> list[str]
    Returns a list of Fairlight presets by name
DisableBackgroundTasksForCurrentResolveSession() -> None
    Disables all background tasks for current Resolve session
ValidateDCTL(dctlSource: str) -> str | None
    Validates DCTL source code. Returns None on success, error string on failure.
EncryptDCTL(inputPath: str, encryptDCTLOptions: EncryptDCTLOptions | None=None) -> bool
    Encrypts the DCTL at inputPath and writes it to an output folder.
GetUserPreferencesPresetList() -> list[str]
    Returns a list of available user preferences preset names
LoadUserPreferencesPreset(presetName: str) -> bool
    Loads the named user preferences preset
SaveUserPreferencesPreset(presetName: str) -> bool
    Saves current user preferences as a preset with the given name
DeleteUserPreferencesPreset(presetName: str) -> bool
    Deletes the named user preferences preset
ImportUserPreferencesPreset(filePath: str, presetName: str | None=None) -> bool
    Imports a user preferences preset from file. Uses file base name as preset name if not specified.
ExportUserPreferencesPreset(presetName: str, exportPath: str) -> bool
    Exports the named user preferences preset to the specified file path
```

### ProjectManager

Creates, loads and organizes projects, project folders and databases. See README.md section 'Cloud Projects Settings'.

```text
LoadProject(projectName: str) -> Project | None
    Loads and returns a project. Returns None if project was not found.
CreateProject(projectName: str, mediaLocationPath: str | None=None) -> Project | None
    Creates and returns a project. Returns None if projectName exists.
DeleteProject(projectName: str) -> bool
    Delete project in the current folder. Project must not be currently loaded.
SaveProject() -> bool
    Saves the currently loaded project with its own name.
GetCurrentProject() -> Project
    Returns the currently loaded Resolve project
CreateFolder(folderName: str) -> bool
    Creates a folder. Returns False if it already existed.
GetProjectListInCurrentFolder() -> list[str]
    Returns a list of project names in current folder
GetFolderListInCurrentFolder() -> list[str]
    Returns a list of folder names in current folder
GotoRootFolder() -> bool
    Opens root folder in database
GotoParentFolder() -> bool
    Opens parent folder of current folder in database. Returns False if current folder has no parent.
OpenFolder(folderName: str) -> bool
    Opens folder
ImportProject(filePath: str, projectName: str | None=None) -> bool
    Imports a project from the file
ExportProject(projectName: str, filePath: str, withStillsAndLUTs=True) -> bool
    Exports project to a file.
ArchiveProject(projectName: str, filePath: str, isArchiveSrcMedia=True, isArchiveRenderCache=True, isArchiveProxyMedia=False) -> bool
    Archives project to a file
RestoreProject(filePath: str, projectName: str | None=None) -> bool
    Restores a project from the file
GetProjectLastModifiedTime(projectName: str) -> int
    Returns the last modified time of the project as an epoch timestamp
GetProjectAttributesInCurrentFolder() -> dict[str, ProjectAttributes]
    Returns a dict of project names mapped to their attributes (lastModifiedDate, creationDate, notes, liveCollaborationMode) for all projects in the current folder
CloseProject(project: Project) -> bool
    Closes the specified project without saving
GetCurrentFolder() -> str
    Returns the current folder name
DeleteFolder(folderName: str) -> bool
    Deletes the specified folder
GetCurrentDatabase() -> DatabaseInfo
    Returns a dictionary (with keys 'DbType', 'DbName' and optional 'IpAddress') corresponding to the current database connection
GetDatabaseList() -> list[DatabaseInfo]
    Returns a list of dictionary items (with keys 'DbType', 'DbName' and optional 'IpAddress') corresponding to all the databases added to Resolve
SetCurrentDatabase(dbInfo: DatabaseInfo) -> bool
    Switches current database connection to the database specified by the keys below, and closes any open project
LoadCloudProject(cloudSettings: CloudSettings) -> Project | None
    Loads and returns a cloud project with the given cloud settings. Returns None if not found
CreateCloudProject(cloudSettings: CloudSettings) -> Project | None
    Creates and returns a cloud project
ImportCloudProject(filePath: str, cloudSettings: CloudSettings) -> bool
    Imports a cloud project from the file path with given cloud settings
RestoreCloudProject(folderPath: str, cloudSettings: CloudSettings) -> bool
    Restores a cloud project from the folder path with given cloud settings
```

### Project

A project: timelines, settings, presets and render jobs. See README.md section 'Looking up Project and Clip properties'.

```text
GetMediaPool() -> MediaPool
    Returns the MediaPool object
GetCurrentTimeline() -> Timeline
    Returns the currently loaded timeline
SetCurrentTimeline(timeline: Timeline) -> bool
    Sets given timeline as current timeline for the project
GetTimelineCount() -> int
    Returns the number of timelines in the project
GetTimelineByIndex(idx: int) -> Timeline | None
    Returns timeline at the given index, 1 <= idx <= project.GetTimelineCount()
GetGallery() -> Gallery
    Returns the Gallery object
GetName() -> str
    Returns project name
SetName(projectName: str) -> bool
    Sets project name if given projectName is unique
GetProjectSettingsPresetList() -> list[ProjectSettingsPresetInfo]
    Returns a list of project settings presets and their information
SetProjectSettingsPreset(presetName: str) -> bool
    Sets project settings preset by given name into project
DeleteProjectSettingsPreset(presetName: str) -> bool
    Deletes the project settings preset with the given name
SaveCurrentProjectSettingsAsNewPreset(presetName: str) -> bool
    Saves the current project settings as a new preset with the given name
UpdateProjectSettingsPreset(presetName: str) -> bool
    Updates the given project settings preset with current settings
ExportProjectSettingsPreset(presetName: str, exportPath: str) -> bool
    Exports the given project settings preset to the specified file path
ImportProjectSettingsPreset(presetFilePath: str, presetName: str | None=None) -> bool
    Imports a project settings preset from file. Uses file base name as preset name if not specified.
GetRenderJobList() -> list[RenderJobInfo]
    Returns a list of render jobs and their information
GetRenderPresetList() -> list[str]
    Returns a list of render preset names
LoadRenderPreset(presetName: str) -> bool
    Loads a render preset by name
SaveAsNewRenderPreset(presetName: str) -> bool
    Saves current render settings as a new preset with the given name
DeleteRenderPreset(presetName: str) -> bool
    Deletes given render preset
UpdateRenderPreset(presetName: str) -> bool
    Updates given render preset with current render settings
SetQuickExportEnabledForRenderPreset(presetName: str, isEnabled: bool) -> bool
    Enables or disables quick export for the named render preset
StartRendering(jobIds: list[str], isInteractiveMode=False) -> bool
    Starts rendering jobs indicated by the input job ids
StopRendering() -> None
    Stops any current render processes
IsRenderingInProgress() -> bool
    Returns True if a rendering is in progress
AddRenderJob() -> str
    Adds a render job based on current render settings to the render queue
DeleteRenderJob(jobId: str) -> bool
    Deletes render job for input job id
DeleteAllRenderJobs() -> bool
    Deletes all render jobs in the queue
SetRenderSettings(settings: RenderSettings) -> bool
    Sets given settings for rendering
GetRenderResolutions(format: str | None=None, codec: str | None=None) -> list[ResolutionInfo]
    Returns list of resolutions applicable for the given render format and codec
GetSettings() -> ProjectSettings
    Returns a dict with all project settings. See README.md section 'Looking up Project and Clip properties'.
SetSettings(settings: ProjectSettings) -> bool
    Sets the project settings with specified dict of setting names and values. See README.md section 'Looking up Project and Clip properties'.
GetRenderJobStatus(jobId: str) -> RenderJobStatus
    Returns a dict with job status and completion percentage
GetQuickExportRenderPresets() -> list[str]
    Returns a list of quick export render presets
RenderWithQuickExport(quickExportPresetName: str, presetInfo: QuickExportRenderSettings) -> QuickExportRenderStatus
    Renders current timeline with quick export preset
GetRenderFormats() -> dict
    Returns a dict (format -> file extension) of available render formats
GetAudioRenderFormats() -> dict
    Returns a dict (format -> file extension) of available audio render formats
GetRenderCodecs(renderFormatFileExtension: str) -> dict
    Returns a dict (codec description -> codec name) of available codecs
GetAudioRenderCodecs(audioRenderFormatFileExtension: str) -> dict
    Returns a dict (codec description -> codec name) of available audio codecs for the given format
GetCurrentRenderFormatAndCodec() -> dict[str, str]
    Returns a dict with currently selected format and render codec
SetCurrentRenderFormatAndCodec(format: str, codec: str) -> bool
    Sets given render format and render codec as options for rendering
GetCurrentRenderMode() -> int
    Returns the render mode: 0 - Individual clips, 1 - Single clip
SetCurrentRenderMode(renderMode: int) -> bool
    Sets the render mode: 0 for Individual clips, 1 for Single clip
RefreshLUTList() -> bool
    Refreshes LUT List
GetUniqueId() -> str
    Returns a unique ID for the project item
InsertAudioToCurrentTrackAtPlayhead(mediaPath: str, startOffsetInSamples: int, durationInSamples: int) -> bool
    Inserts the media with startOffset and duration in samples to the current track at the playhead
LoadBurnInPreset(presetName: str) -> bool
    Loads user defined data burn in preset
ExportCurrentFrameAsStill(filePath: str) -> bool
    Exports current frame as still to supplied filePath
GetColorGroupsList() -> list[ColorGroup]
    Returns a list of all group objects in the timeline
AddColorGroup(groupName: str) -> ColorGroup
    Creates a new ColorGroup with unique groupName
DeleteColorGroup(colorGroup: ColorGroup) -> bool
    Deletes the given ColorGroup and sets clips to ungrouped
ApplyFairlightPresetToCurrentTimeline(presetName: str) -> bool
    Applies Fairlight preset to current timeline
ResetIntellisearchAnalysis() -> bool
    Resets intellisearch analysis for the project
GenerateSpeech(speechSettings: SpeechSettings) -> MediaPoolItem
    Generates speech for given speechSettings dict
```

### MediaPool

The media pool of a project: its folders, its clips and the timelines created from them.

```text
AddSubFolder(folder: Folder, name: str) -> Folder
    Adds new subfolder under specified Folder object with the given name
GetCurrentFolder() -> Folder
    Returns currently selected Folder
RefreshFolders() -> bool
    Updates the folders in collaboration mode
SetCurrentFolder(folder: Folder) -> bool
    Sets current folder by given Folder
GetRootFolder() -> Folder
    Returns root Folder of Media Pool
CreateTimelineFromClips(name: str, clipInfos: list[CreateTimelineClipInfo]) -> Timeline
    Creates new timeline with specified name, and appends the specified MediaPoolItem objects
AppendToTimeline(clipInfos: list[AppendClipInfo]) -> list[TimelineItem]
    Appends specified MediaPoolItem objects in the current timeline. Returns the list of appended timelineItems
CreateEmptyTimeline(name: str) -> Timeline
    Adds new timeline with given name
ImportTimelineFromFile(filePath: str, importOptions: ImportOptions | None=None) -> Timeline
    Creates timeline based on parameters within given file (AAF/EDL/XML/FCPXML/DRT/ADL/OTIO) and optional importOptions dict
DeleteTimelines(timelines: list[Timeline]) -> bool
    Deletes specified timelines in the media pool
ExportMetadata(fileName: str, clips: list[MediaPoolItem] | None=None) -> bool
    Exports metadata of specified clips to 'fileName' in CSV format. If no clips are specified, all clips from media pool will be used
DeleteClips(clips: list[MediaPoolItem]) -> bool
    Deletes specified clips or timeline mattes in the media pool
ImportFolderFromFile(filePath: str, sourceClipsPath: str | None=None) -> bool
    Imports a DRB folder from the given file path
DeleteFolders(subfolders: list[Folder]) -> bool
    Deletes specified subfolders in the media pool
MoveClips(clips: list[MediaPoolItem], targetFolder: Folder) -> bool
    Moves specified clips to target folder
MoveFolders(folders: list[Folder], targetFolder: Folder) -> bool
    Moves specified folders to target folder
GetClipMatteList(mediaPoolItem: MediaPoolItem) -> list[str]
    Get mattes for specified MediaPoolItem, as a list of paths to the matte files
GetTimelineMatteList(folder: Folder) -> list[MediaPoolItem]
    Get mattes in specified Folder, as list of MediaPoolItems
DeleteClipMattes(mediaPoolItem: MediaPoolItem, paths: list[str]) -> bool
    Delete mattes based on their file paths, for specified MediaPoolItem
RelinkClips(clips: list[MediaPoolItem], folderPath: str) -> bool
    Update the folder location of specified media pool clips with the specified folder path
UnlinkClips(clips: list[MediaPoolItem]) -> bool
    Unlink specified media pool clips
ImportMedia(clipInfos: list[ImportClipInfo]) -> list[MediaPoolItem]
    Imports specified file/folder paths into current Media Pool folder. Returns a list of the MediaPoolItems created
GetUniqueId() -> str
    Returns a unique ID for the media pool
CreateStereoClip(leftMediaPoolItem: MediaPoolItem, rightMediaPoolItem: MediaPoolItem) -> MediaPoolItem
    Takes in two existing media pool items and creates a new 3D stereoscopic media pool entry replacing the input media
CreateMulticamClip(clips: list[MediaPoolItem], multicamOptions: MulticamOptions) -> list[MediaPoolItem]
    Creates Multicam clips from the specified MediaPoolItems and options
AutoSyncAudio(mediaPoolItems: list[MediaPoolItem], audioSyncSettings: AudioSyncSettings) -> bool
    Syncs audio for specified MediaPoolItems. The list must contain at least one video and one audio clip.
GetSelectedClips() -> list[MediaPoolItem]
    Returns the current selected MediaPoolItems
SetSelectedClip(mediaPoolItem: MediaPoolItem) -> bool
    Sets the selected MediaPoolItem to the given MediaPoolItem
```

### MediaPoolItem

A clip in the media pool. See README.md section 'Looking up Project and Clip properties'.

```text
GetName() -> str
    Returns the clip name.
SetName(name: str) -> bool
    Sets the clip's name to name(string).
GetTimeline() -> Timeline
    Returns the timeline object if the mpItem is a timeline clip
GetMetadata(metadataType: str | None=None) -> str | dict
    Returns the metadata value for the key 'metadataType'. If no argument is specified, a dict of all set metadata properties is returned.
SetMetadata(metadata: dict) -> bool
    Sets the item metadata with specified dict of key-value pairs
GetThirdPartyMetadata(metadataType: str | None=None) -> str | dict
    Returns the third party metadata value for the key 'metadataType'. If no argument, a dict of all set third party metadata properties is returned.
SetThirdPartyMetadata(metadata: dict) -> bool
    Sets/Add the item third party metadata with specified dict of key-value pairs
GetMediaId() -> str
    Returns the unique ID for the MediaPoolItem.
AddMarker(frameId: int, color: MarkerColor, name: str, note: str, duration: int, customData: str | None=None) -> bool
    Creates a new marker at given frameId position. 'customData' is optional.
DeleteMarkersByColor(color: MarkerColor | Literal['All']) -> bool
    Delete all markers of the specified color. 'All' as argument deletes all color markers.
DeleteMarkerAtFrame(frameNum: int) -> bool
    Delete marker at frame number from the media pool item.
DeleteMarkerByCustomData(customData: str) -> bool
    Delete first matching marker with specified customData.
GetMarkers() -> dict[int, MarkerInfo]
    Returns a dict (frameId -> {information}) of all markers.
GetMarkerByCustomData(customData: str) -> MarkerInfo
    Returns marker {information} for the first matching marker with specified customData.
UpdateMarkerCustomData(frameId: int, customData: str) -> bool
    Updates customData for the marker at given frameId position.
GetMarkerCustomData(frameId: int) -> str
    Returns customData string for the marker at given frameId position.
AddFlag(color: FlagColor) -> bool
    Adds a flag with given color (string).
GetFlagList() -> list[str]
    Returns a list of flag colors assigned to the item.
ClearFlags(color: FlagColor | Literal['All']) -> bool
    Clears the flag of the given color if one exists. An 'All' argument is supported and clears all flags.
GetClipColor() -> ClipColor | Literal['']
    Returns the item color as a string.
SetClipColor(colorName: ClipColor) -> bool
    Sets the item color based on the colorName (string).
ClearClipColor() -> bool
    Clears the item color.
LinkFullResolutionMedia(fullResMediaPath: str) -> bool
    Links proxy media to full resolution media files specified via its path.
LinkProxyMedia(proxyMediaFilePath: str) -> bool
    Links proxy media located at path specified by arg 'proxyMediaFilePath' with the current clip.
UnlinkProxyMedia() -> bool
    Unlinks any proxy media associated with clip.
ReplaceClip(filePath: str) -> bool
    Replaces the underlying asset and metadata of MediaPoolItem with the specified absolute clip path.
ReplaceClipPreserveSubClip(filePath: str) -> bool
    Replaces the underlying asset and metadata preserving original sub clip extents.
GetClipProperty(propertyName: str | None=None) -> str | ClipProperties
    Returns the property value for the key 'propertyName'. If no argument, a dict of all clip properties is returned.
SetClipProperty(propertyName: str, propertyValue: str) -> bool
    Sets the given property to propertyValue (string).
GetUniqueId() -> str
    Returns a unique ID for the media pool item
TranscribeAudio(useSpeakerDetection: bool | None=None, transcribeAsNestedClip=False) -> bool
    Transcribes audio of the MediaPoolItem
ClearTranscription(clearNestedClipTranscription=False) -> bool
    Clears audio transcription of the MediaPoolItem.
PerformAudioClassification() -> bool
    Analyzes and classifies the audio of a MediaPoolItem.
ClearAudioClassification() -> bool
    Clears audio classification of the MediaPoolItem.
GetAudioMapping() -> str
    Returns a string with MediaPoolItem's audio mapping information (JSON format).
SetAudioMapping(audioMapping: str) -> bool
    Sets audio mapping from a JSON string.
GetMarkInOut() -> MarkInOut
    Returns dict of in/out marks set.
SetMarkInOut(markIn: int, markOut: int, markType: MarkType | None=None) -> bool
    Sets mark in/out of type MarkType (default: 'all').
ClearMarkInOut(markType: MarkType | None=None) -> bool
    Clears mark in/out of type MarkType (default: 'all').
MonitorGrowingFile() -> bool
    Monitor a file as long as it keeps growing.
RemoveMotionBlur(deblurOption: DeblurOptions) -> MediaPoolItem
    Apply Motion Deblur on MediaPoolItem, Returns newly created MediaPoolItem.
AnalyzeForIntellisearch(identifyFaces: bool, isBetterMode: bool) -> bool
    Perform Intellisearch analysis on the MediaPoolItem.
AnalyzeForSlate(markerColor: SlateMarkerColor) -> bool
    Perform Slate analysis on the MediaPoolItem.
GetTranscription(useNestedClipTranscription=False) -> Transcription
    Returns transcription data for the media pool item if available.
```

### Timeline

A timeline: tracks, items, markers and export. See README.md section 'Looking up timeline export properties'.

```text
GetName() -> str
    Returns the timeline name.
SetName(timelineName: str) -> bool
    Sets the timeline name if timelineName (string) is unique.
GetStartFrame() -> int
    Returns the frame number at the start of timeline.
GetEndFrame() -> int
    Returns the frame number at the end of timeline.
GetTrackCount(trackType: TrackType) -> int
    Returns the number of tracks for the given TrackType.
GetItemListInTrack(trackType: TrackType, index: int) -> list[TimelineItem]
    Returns a list of timeline items on specified track.
GetSelectedClips() -> list[TimelineItem]
    Returns the currently selected timeline items
GetCurrentTimecode() -> str
    Returns a string timecode representation for the current playhead position.
SetCurrentTimecode(timecode: str) -> bool
    Sets current playhead position from input timecode.
GetCurrentVideoItem() -> TimelineItem | None
    Returns the current video timeline item.
AddMarker(frameId: int, color: MarkerColor, name: str, note: str, duration: int, customData: str | None=None) -> bool
    Creates a new marker at given frameId position.
DeleteMarkersByColor(color: MarkerColor | Literal['All']) -> bool
    Deletes all timeline markers of the specified color.
DeleteMarkerAtFrame(frameNum: int) -> bool
    Deletes the timeline marker at the given frame number.
DeleteMarkerByCustomData(customData: str) -> bool
    Delete first matching marker with specified customData.
GetMarkers() -> dict[int, MarkerInfo]
    Returns a dict (frameId -> {information}) of all markers.
GetMarkerByCustomData(customData: str) -> MarkerInfo
    Returns marker {information} for the first matching marker with specified customData.
UpdateMarkerCustomData(frameId: int, customData: str) -> bool
    Updates customData for the marker at given frameId position.
GetMarkerCustomData(frameId: int) -> str
    Returns customData string for the marker at given frameId position.
GetCurrentClipThumbnailImage() -> ThumbnailData
    Returns a dict with data containing raw thumbnail image data for current media in the Color Page.
AddTrack(trackType: TrackType, subTrackType: str | None=None) -> bool
    Adds track of TrackType. Optional argument subTrackType.
DeleteTrack(trackType: TrackType, trackIndex: int) -> bool
    Deletes track of trackType and given trackIndex. 1 <= trackIndex <= GetTrackCount(trackType).
GetTrackSubType(trackType: TrackType, trackIndex: int) -> str
    Returns an audio track's format.
SetTrackEnable(trackType: TrackType, trackIndex: int, enabled: bool) -> bool
    Enables/Disables track with given trackType and trackIndex
GetIsTrackEnabled(trackType: TrackType, trackIndex: int) -> bool
    Returns True if track with given trackType and trackIndex is enabled.
SetTrackLock(trackType: TrackType, trackIndex: int, locked: bool) -> bool
    Locks/Unlocks track with given trackType and trackIndex
GetIsTrackLocked(trackType: TrackType, trackIndex: int) -> bool
    Returns True if track with given trackType and trackIndex is locked.
DeleteClips(timelineItems: list[TimelineItem], rippleDelete=False) -> bool
    Deletes specified TimelineItems from the timeline, performing ripple delete if second argument is True.
SetClipsLinked(timelineItems: list[TimelineItem], linked: bool) -> bool
    Links or unlinks the specified TimelineItems depending on second argument.
NormalizeAudioLevel(timelineItems: list[TimelineItem], normalizeAudioOptions: NormalizeAudioOptions | None=None) -> bool
    Normalizes the audio level of specified TimelineItems using the given normalizeAudioOptions.
AutoAlignClips(timelineItems: list[TimelineItem], autoAlignOptions: AutoAlignOptions | None=None) -> bool
    Aligns specified TimelineItems using the given options. Returns True if successful, False otherwise.
GetNormalizeAudioModes() -> list[str]
    Returns the list of valid normalizationMode strings for NormalizeAudioLevel.
GetTrackName(trackType: TrackType, trackIndex: int) -> str
    Returns the track name for track indicated by trackType and index.
SetTrackName(trackType: TrackType, trackIndex: int, name: str) -> bool
    Sets the track name for track indicated by trackType and index.
DuplicateTimeline(timelineName: str) -> Timeline
    Duplicates the timeline and returns the created timeline.
GrabStill() -> GalleryStill
    Grabs still from the current video clip. Returns a GalleryStill object.
GrabAllStills(stillFrameSource: int) -> list[GalleryStill]
    Grabs stills from all clips at 'stillFrameSource' (1=First frame, 2=Middle frame).
CreateCompoundClip(timelineItems: list[TimelineItem], clipInfo: CompoundClipOptions | None=None) -> TimelineItem
    Creates a compound clip of input timeline items.
CreateFusionClip(timelineItems: list[TimelineItem]) -> TimelineItem
    Creates a Fusion clip of input timeline items.
Export(fileName: str, exportType: TimelineExportType, exportSubtype: TimelineExportSubtype) -> bool
    Exports timeline to 'fileName' as per input exportType & exportSubtype format. See README.md section 'Looking up timeline export properties'.
GetSettings() -> TimelineSettings | ProjectSettings
    Returns a dict with all timeline settings, or the project settings when useCustomSettings is '0'. See README.md section 'Looking up Project and Clip properties'.
SetSettings(settings: TimelineSettings) -> bool
    Sets the timeline settings with specified dict of setting names and values. See README.md section 'Looking up Project and Clip properties'.
GetStartTimecode() -> str
    Returns the start timecode for the timeline.
SetStartTimecode(timecode: str) -> bool
    Set the start timecode of the timeline to the string 'timecode'.
ImportIntoTimeline(filePath: str, importOptions: AAFImportOptions | None=None) -> bool
    Imports timeline items from an AAF file.
InsertGeneratorIntoTimeline(generatorName: str) -> TimelineItem
    Inserts a generator into the timeline.
InsertFusionGeneratorIntoTimeline(generatorName: str) -> TimelineItem
    Inserts a Fusion generator into the timeline.
InsertFusionCompositionIntoTimeline() -> TimelineItem
    Inserts a Fusion composition into the timeline.
InsertOFXGeneratorIntoTimeline(generatorName: str) -> TimelineItem
    Inserts an OFX generator into the timeline.
InsertTitleIntoTimeline(titleName: str) -> TimelineItem
    Inserts a title into the timeline.
InsertFusionTitleIntoTimeline(titleName: str) -> TimelineItem
    Inserts a Fusion title into the timeline.
CreateSubtitlesFromAudio(autoCaptionSettings: AutoCaptionSettings | None=None) -> bool
    Creates subtitles from audio for the timeline.
GetUniqueId() -> str
    Returns a unique ID for the timeline
DetectSceneCuts() -> bool
    Detects and makes scene cuts along the timeline.
ConvertTimelineToStereo() -> bool
    Converts timeline to stereo.
GetNodeGraph() -> Graph
    Returns the timeline's node graph object.
AnalyzeDolbyVision(timelineItems: list[TimelineItem], analysisType: DolbyVisionAnalysisType) -> bool
    Analyzes Dolby Vision on clips present on the timeline.
GetMediaPoolItem() -> MediaPoolItem | None
    Returns the media pool item corresponding to the timeline
GetMarkInOut() -> MarkInOut
    Returns dict of in/out marks set.
SetMarkInOut(markIn: int, markOut: int, markType: MarkType | None=None) -> bool
    Sets mark in/out of type MarkType (default: 'all')
ClearMarkInOut(markType: MarkType | None=None) -> bool
    Clears mark in/out of type MarkType (default: 'all')
GetVoiceIsolationState(trackIndex: int) -> VoiceIsolationState
    Returns the Voice Isolation State as a dict.
SetVoiceIsolationState(trackIndex: int, voiceIsolationState: VoiceIsolationState) -> bool
    Sets Voice Isolation state of audio track.
SetOutputBlanking(outputBlanking: OutputBlanking) -> bool
    Sets the output blanking for the timeline. Accepts a dictionary with keys 'Top', 'Bottom', 'Left' and 'Right'. The values are in pixels.
GetOutputBlanking() -> OutputBlanking
    Returns the output blanking for the timeline as a dictionary with keys 'Top', 'Bottom', 'Left' and 'Right'. The values are in pixels.
```

### TimelineItem

A clip, title, generator or transition on a timeline track. See README.md section 'Looking up Timeline item properties'.

```text
GetType() -> str
    Returns the type of the item: 'video', 'audio', 'generator' or 'transition'
AddTransition(transitionOptions: TransitionOptions) -> TimelineItem | None
    Adds a transition of the given type/category to the start or end of this item. Returns the created transition item or None on failure.
GetName() -> str
    Returns the item name
SetName(name: str) -> bool
    Sets the clip's name to name.
GetStart(subframePrecision=False) -> float
    Returns the start frame position on the timeline. Returns fractional frames if subframe_precision is True
GetEnd(subframePrecision=False) -> float
    Returns the end frame position on the timeline. Returns fractional frames if subframe_precision is True
GetSourceStartFrame() -> int
    Returns the start frame position of the media pool clip in the timeline clip
GetSourceEndFrame() -> int
    Returns the end frame position of the media pool clip in the timeline clip
GetSourceStartTime() -> float
    Returns the start time position of the media pool clip in the timeline clip
GetSourceEndTime() -> float
    Returns the end time position of the media pool clip in the timeline clip
GetDuration(subframePrecision=False) -> float
    Returns the item duration. Returns fractional frames if subframe_precision is True
GetLeftOffset(subframePrecision=False) -> float
    Returns the maximum extension by frame for clip from left side. Returns fractional frames if subframe_precision is True
GetRightOffset(subframePrecision=False) -> float
    Returns the maximum extension by frame for clip from right side. Returns fractional frames if subframe_precision is True
GetFusionCompCount() -> int
    Returns number of Fusion compositions associated with the timeline item
GetFusionCompNameList() -> list[str]
    Returns a list of Fusion composition names associated with the timeline item
GetFusionCompByIndex(compIndex: int) -> FusionComp | None
    Returns the Fusion composition object based on given index. 1 <= compIndex <= timelineItem.GetFusionCompCount()
GetFusionCompByName(compName: str) -> FusionComp | None
    Returns the Fusion composition object based on given name
AddFusionComp() -> FusionComp
    Adds a new Fusion composition associated with the timeline item
GetMediaPoolItem() -> MediaPoolItem | None
    Returns the media pool item corresponding to the timeline item if one exists
AddMarker(frameId: int, color: MarkerColor, name: str, note: str, duration: int, customData: str | None=None) -> bool
    Creates a new marker at given frameId position and with given marker information. 'customData' is optional and helps to attach user specific data to the marker
DeleteMarkersByColor(color: MarkerColor | Literal['All']) -> bool
    Deletes all markers of the specified color from the timeline item. 'All' as argument deletes all color markers
DeleteMarkerAtFrame(frameNum: int) -> bool
    Deletes marker at frame number from the timeline item
DeleteMarkerByCustomData(customData: str) -> bool
    Deletes first matching marker with specified customData
GetMarkers() -> dict[int, MarkerInfo]
    Returns a dict (frameId -> {information}) of all markers and dicts with their information
GetMarkerByCustomData(customData: str) -> MarkerInfo
    Returns marker {information} for the first matching marker with specified customData
UpdateMarkerCustomData(frameId: int, customData: str) -> bool
    Updates customData (string) for the marker at given frameId position. CustomData is not exposed via UI and is useful for scripting developer to attach any user specific data to markers
GetMarkerCustomData(frameId: int) -> str
    Returns customData string for the marker at given frameId position
SetProperties(properties: TimelineItemProperties) -> bool
    Sets the item properties with specified dict of property keys and values. See README.md section 'Looking up Timeline item properties'.
GetProperties() -> TimelineItemProperties
    Returns a dict with all supported item properties. See README.md section 'Looking up Timeline item properties'.
SetSpeed(speedOptions: SpeedOptions) -> bool
    Sets the Clip Speed
GetSpeed() -> SpeedOptions
    Returns the clip speed options
AddFlag(color: FlagColor) -> bool
    Adds a flag with given color (string)
GetFlagList() -> list[str]
    Returns a list of flag colors assigned to the item
ClearFlags(color: FlagColor | Literal['All']) -> bool
    Clears flags of the specified color. An 'All' argument is supported to clear all flags
GetStereoConvergenceValues() -> dict[int, float]
    Returns a dict (offset -> value) of keyframe offsets and respective convergence values
GetStereoLeftFloatingWindowParams() -> dict[int, FloatingWindowParams]
    For the LEFT eye -> returns a dict (offset -> dict) of keyframe offsets and respective floating window params
GetStereoRightFloatingWindowParams() -> dict[int, FloatingWindowParams]
    For the RIGHT eye -> returns a dict (offset -> dict) of keyframe offsets and respective floating window params
GetClipColor() -> ClipColor | Literal['']
    Returns the item color as a string
SetClipColor(colorName: ClipColor) -> bool
    Sets the item color based on the colorName (string)
ClearClipColor() -> bool
    Clears the item color
ImportFusionComp(path: str) -> FusionComp
    Imports a Fusion composition from given file path by creating and adding a new composition for the item
ExportFusionComp(path: str, compIndex: int) -> bool
    Exports the Fusion composition based on given index to the path provided
DeleteFusionCompByName(compName: str) -> bool
    Deletes the named Fusion composition
LoadFusionCompByName(compName: str) -> FusionComp
    Loads the named Fusion composition as the active composition
RenameFusionCompByName(oldName: str, newName: str) -> bool
    Renames the Fusion composition identified by oldName
RenameVersionByName(oldName: str, newName: str, versionType: int) -> bool
    Renames the color version identified by oldName and versionType (0 - local, 1 - remote)
DeleteVersionByName(versionName: str, versionType: int) -> bool
    Deletes a color version by name and versionType (0 - local, 1 - remote)
LoadVersionByName(versionName: str, versionType: int) -> bool
    Loads a named color version as the active version. versionType: 0 - local, 1 - remote
AddVersion(versionName: str, versionType: int) -> bool
    Adds a new color version for a video clip based on versionType (0 - local, 1 - remote)
GetVersionNameList(versionType: int) -> list[str]
    Returns a list of all color versions for the given versionType (0 - local, 1 - remote)
SetCDL(CDL: CDL) -> bool
    Sets CDL values on the node. Keys of map are: 'NodeIndex', 'Slope', 'Offset', 'Power', 'Saturation'
AddTake(mediaPoolItem: MediaPoolItem, startFrame: int | None=None, endFrame: int | None=None) -> bool
    Adds mediaPoolItem as a new take. Initializes a take selector for the timeline item if needed. By default, the full clip extents is added. startFrame and endFrame are optional arguments used to specify the extents
GetSelectedTakeIndex() -> int
    Returns the index of the currently selected take, or 0 if the clip is not a take selector
GetTakesCount() -> int
    Returns the number of takes in take selector, or 0 if the clip is not a take selector
GetTakeByIndex(idx: int) -> TakeInfo | None
    Returns a dict with take info for specified index
DeleteTakeByIndex(idx: int) -> bool
    Deletes a take by index, 1 <= idx <= number of takes
SelectTakeByIndex(idx: int) -> bool
    Selects a take by index, 1 <= idx <= number of takes
FinalizeTake() -> bool
    Finalizes take selection
CopyGrades(tgtTimelineItems: list[TimelineItem]) -> bool
    Copies the current node stack layer grade to the same layer for each item in tgtTimelineItems.
GetClipEnabled() -> bool
    Gets clip enabled status
SetClipEnabled(enabled: bool) -> bool
    Sets clip enabled based on argument
GetCurrentVersion() -> VersionInfo
    Returns the current version of the video clip. The returned value will have the keys versionName and versionType (0 - local, 1 - remote)
UpdateSidecar() -> bool
    Updates sidecar file for BRAW clips or RMD file for R3D clips
GetUniqueId() -> str
    Returns a unique ID for the timeline item
LoadBurnInPreset(presetName: str) -> bool
    Loads user defined data burn in preset for clip when supplied presetName (string).
CreateMagicMask(mode: str) -> bool
    Creates a magic mask. mode can be 'F' (forward), 'B' (backward), or 'BI' (bidirectional)
RegenerateMagicMask() -> bool
    Regenerates the magic mask
Stabilize() -> bool
    Performs stabilization on the clip
SmartReframe() -> bool
    Performs Smart Reframe.
GetNodeGraph(layerIdx: int | None=None) -> Graph
    Returns the clip's node graph object at layerIdx (int, optional). Returns the first layer if layerIdx is skipped. 1 <= layerIdx <= project.GetSetting('nodeStackLayers')
GetColorGroup() -> ColorGroup | None
    Returns the clip's color group if one exists
AssignToColorGroup(colorGroup: ColorGroup) -> bool
    Assigns the clip to the given ColorGroup. ColorGroup must be an existing group in the current project
RemoveFromColorGroup() -> bool
    Removes the clip from its ColorGroup
ExportLUT(exportType: ExportLutType, path: str) -> bool
    Exports a LUT of the size given by 'exportType', saving it in the provided 'path'
GetLinkedItems() -> list[TimelineItem]
    Returns a list of linked timeline items
GetTrackTypeAndIndex() -> list[str | int]
    Returns a list of two values that correspond to the TimelineItem's trackType (string) and trackIndex (int) respectively
GetSourceAudioChannelMapping() -> str
    Returns a string with TimelineItem's audio mapping information
SetSourceAudioChannelMapping(audioMapping: str) -> bool
    Sets source audio channel mapping from a JSON string.
GetIsColorOutputCacheEnabled() -> bool
    Returns if the cache corresponding to cache_type is enabled
GetIsFusionOutputCacheEnabled() -> str
    Returns if the cache corresponding to cache_type is enabled (or auto)
SetColorOutputCache(enabled: bool) -> bool
    Sets caching to enabled or disabled. Equivalent to clip context menu action 'Render Cache Color Output'
SetFusionOutputCache(cacheValue: str) -> bool
    Sets caching to auto, enabled or disabled. Equivalent to clip context menu action 'Render Cache Fusion Output'
GetVoiceIsolationState() -> VoiceIsolationState
    Returns the Voice Isolation State as a dict {isEnabled, amount}, of the timelineItem
SetVoiceIsolationState(state: VoiceIsolationState) -> bool
    Sets Voice Isolation state of the timelineItem to the given VoiceIsolationState of {isEnabled (bool), amount (int)}. amount is in range of [0, 100].
ResetAllNodeColors() -> bool
    Resets node color for all nodes in the active version of the clip.
SetOutputBlanking(outputBlanking: OutputBlanking) -> bool
    Sets the output blanking for the clip. Accepts a dictionary with keys 'Top', 'Bottom', 'Left' and 'Right'. The values are in pixels.
GetOutputBlanking() -> OutputBlanking
    Returns the output blanking for the clip as a dictionary with keys 'Top', 'Bottom', 'Left' and 'Right'. The values are in pixels. The dictionary will be empty if the timeline's output blanking is used.
SetUseTimelineForOutputBlanking(useTimelineOutputBlanking: bool) -> bool
    Sets the flag to use the timeline's output blanking for the clip.
GetUseTimelineForOutputBlanking() -> bool
    Gets the flag to use the timeline's output blanking for the clip.
PerformMulticamSmartSwitch(smartSwitchSettings: SmartSwitchSettings) -> bool
    Performs Multicam SmartSwitch on the multicam TimelineItem using the given smartSwitchSettings
FlattenMulticam(gradeOption: FlattenMulticamGrade) -> bool
    Flattens the multicam TimelineItem, using the grade source specified by gradeOption
GetFades() -> FadeInfo
    Returns a dict {FadeIn, FadeOut} of the fade durations (in frames) for the item's video or audio fader
SetFades(fades: FadeInfo) -> bool
    Sets the fade durations (in frames) for the item's video or audio fader from a dict {FadeIn, FadeOut}
```

### ColorGroup

A group of clips sharing a pre-clip and a post-clip grade.

```text
GetName() -> str
    Returns the name of the ColorGroup
SetName(groupName: str) -> bool
    Renames ColorGroup to groupName
GetClipsInTimeline(timeline: Timeline | None=None) -> list[TimelineItem]
    Returns a list of TimelineItems in the ColorGroup for the given Timeline
GetPreClipNodeGraph() -> Graph
    Returns the ColorGroup Pre-clip graph
GetPostClipNodeGraph() -> Graph
    Returns the ColorGroup Post-clip graph
```

### Folder

A media pool folder: its clips, its subfolders and their analysis.

```text
GetName() -> str
    Returns the media folder name
GetSubFolderList() -> list[Folder]
    Returns a list of subfolders in the folder
GetClipList() -> list[MediaPoolItem]
    Returns a list of clips (items) within the folder
GetIsFolderStale() -> bool
    Returns true if folder is stale in collaboration mode
GetUniqueId() -> str
    Returns a unique ID for the media pool folder
Export(filePath: str) -> bool
    Exports the folder as a DRB file to filePath
TranscribeAudio(useSpeakerDetection: bool | None=None, transcribeAsNestedClip=False) -> bool
    Transcribes audio of the MediaPoolItems within the folder and nested folders.
ClearTranscription() -> bool
    Clears audio transcription of the MediaPoolItems within the folder and nested folders.
PerformAudioClassification() -> bool
    Analyzes and classifies the audio of the MediaPoolItems within the folder and nested folders into categories and subcategories
ClearAudioClassification() -> bool
    Clears audio classification of the MediaPoolItems within the folder and nested folders
RemoveMotionBlur(deblurOption: DeblurOptions | None=None) -> list[list[MediaPoolItem]]
    Apply Motion Deblur on MediaPoolItems in Folder, Returns a list of original to newly created MediaPoolItems
AnalyzeForIntellisearch(identifyFaces: bool, isBetterMode: bool) -> bool
    Perform Intellisearch analysis to all the MediaPoolItems in the folder.
AnalyzeForSlate(markerColor: SlateMarkerColor) -> bool
    Perform Slate analysis with current settings and use the stated markerColor to all the MediaPoolItems in the folder.
```

### Gallery

The gallery of a project: its still albums and PowerGrade albums.

```text
GetAlbumName(galleryStillAlbum: GalleryStillAlbum) -> str
    Returns the name of a GalleryStillAlbum object
SetAlbumName(galleryStillAlbum: GalleryStillAlbum, albumName: str) -> bool
    Sets the name of a GalleryStillAlbum object
GetCurrentStillAlbum() -> GalleryStillAlbum
    Returns current album as a GalleryStillAlbum object
SetCurrentStillAlbum(galleryStillAlbum: GalleryStillAlbum) -> bool
    Sets current album to the given GalleryStillAlbum object
CreateGalleryStillAlbum() -> GalleryStillAlbum
    Creates a new gallery still album
CreateGalleryPowerGradeAlbum() -> GalleryStillAlbum
    Creates a new gallery power grade album
GetGalleryStillAlbums() -> list[GalleryStillAlbum]
    Returns the gallery still albums as a list of GalleryStillAlbum objects
GetGalleryPowerGradeAlbums() -> list[GalleryStillAlbum]
    Returns the gallery PowerGrade albums as a list of GalleryStillAlbum objects
```

### GalleryStillAlbum

An album of gallery stills, which can be labelled, imported and exported.

```text
GetStills() -> list[GalleryStill]
    Returns the list of GalleryStill objects in the album
GetLabel(galleryStill: GalleryStill) -> str
    Returns the label of the galleryStill
SetLabel(galleryStill: GalleryStill, label: str) -> bool
    Sets the new label to a GalleryStill object
ImportStills(filePaths: list[str]) -> bool
    Imports GalleryStill from each filePath in the list
ExportStills(galleryStill: list[GalleryStill], folderPath: str, filePrefix: str, format: str) -> bool
    Exports list of GalleryStill objects to a directory
DeleteStills(galleryStill: list[GalleryStill]) -> bool
    Deletes specified list of GalleryStill objects
```

### Graph

The node graph of a clip or of a color group: its nodes, LUTs and grades. See README.md section 'Cache Mode information'.

```text
GetNumNodes() -> int
    Returns the number of nodes in the graph
SetLUT(nodeIndex: int, lutPath: str) -> bool
    Sets LUT on the node mapping the node index provided, 1 <= nodeIndex <= GetNumNodes()
GetLUT(nodeIndex: int) -> str
    Gets relative LUT path based on the node index provided, 1 <= nodeIndex <= GetNumNodes()
SetNodeCacheMode(nodeIndex: int, cacheValue: CacheMode) -> bool
    Sets the cache mode type on the node mapping the node index provided
GetNodeCacheMode(nodeIndex: int) -> int
    Returns the cache mode type on the node mapping the node index provided
GetNodeLabel(nodeIndex: int) -> str
    Returns the label of the node at nodeIndex
GetToolsInNode(nodeIndex: int) -> list[str]
    Returns toolsList of the tools used in the node indicated by given nodeIndex
SetNodeEnabled(nodeIndex: int, isEnabled: bool) -> bool
    Sets the node at the given nodeIndex to isEnabled, 1 <= nodeIndex <= GetNumNodes()
ApplyArriCdlLut() -> bool
    Applies ARRI CDL and LUT.
ApplyGradeFromDRX(path: str, gradeMode: int) -> bool
    Loads a still from given file path and applies grade to graph with gradeMode (0=No keyframes, 1=Source Timecode aligned, 2=Start Frames aligned)
ResetAllGrades() -> bool
    Resets all grades in the graph
```

### MediaStorage

Browses the volumes of the file system and adds media files to the media pool.

```text
GetMountedVolumeList() -> list[str]
    Returns list of folder paths corresponding to mounted volumes displayed in Resolve's Media Storage
GetSubFolderList(folderPath: str) -> list[str]
    Returns list of folder paths in the given absolute folder path
GetFileList(folderPath: str) -> list[str]
    Returns list of media and file listings in the given absolute folder path
RevealInStorage(path: str) -> bool
    Expands and displays given file/folder path in Resolve's Media Storage
AddItemListToMediaPool(itemInfos: list[MediaStorageItemInfo]) -> list[MediaPoolItem]
    Adds specified file/folder paths from Media Storage into current Media Pool folder. Returns a list of the MediaPoolItems created
AddClipMattesToMediaPool(mediaPoolItem: MediaPoolItem, paths: list[str], stereoEye: str | None=None) -> bool
    Adds specified media files as mattes for the specified MediaPoolItem. stereoEye is 'left' or 'right' for stereo clips
AddTimelineMattesToMediaPool(paths: list[str]) -> list[MediaPoolItem]
    Adds specified media files as timeline mattes in current media pool folder. Returns a list of created MediaPoolItems
StartCloneMedia(sourceDir: str, targetDirs: str | list[str]) -> bool
    Starts cloning media from sourceDir to targetDirs. Use SetCloneToolSettings to configure PreserveFolderName/ChecksumType beforehand.
SetCloneToolSettings(cloneToolSettings: CloneToolSettings | None=None) -> bool
    Sets the PreserveFolderName/ChecksumType options used by subsequent StartCloneMedia calls (and by the Clone Tool UI).
StopCloneMedia() -> bool
    Stops the currently in-progress clone job started via StartCloneMedia. Returns False if no clone job is in progress.
GetCloneStatus() -> CloneStatus
    Returns a dict with the status of the current (or most recently started) clone job
```

## Parameter dicts

`TypedDict` shapes accepted or returned by the methods above (all keys optional unless the method says otherwise).

### AAFImportOptions

```text
autoImportSourceClipsIntoMediaPool: bool  # Import source clips into media pool (default: True)
ignoreFileExtensionsWhenMatching: bool  # Ignore file extensions when matching (default: False)
linkToSourceCameraFiles: bool  # Link to source camera files (default: False)
useSizingInfo: bool  # Use sizing information (default: False)
importMultiChannelAudioTracksAsLinkedGroups: bool  # Import multi-channel audio tracks as linked groups (default: False)
insertAdditionalTracks: bool  # Insert additional tracks (default: True)
insertWithOffset: str  # Insert with timecode offset, e.g. '00:00:00:00' (applies when insertAdditionalTracks is False)
sourceClipsPath: str  # Filesystem path to search for source clips if media is inaccessible
sourceClipsFolders: list[Folder]  # Media Pool folders to search for source clips
```

### AppendClipInfo

```text
mediaPoolItem: MediaPoolItem  # MediaPoolItem object to append
startFrame: float  # Source start frame (optional)
endFrame: float  # Source end frame (optional)
mediaType: int  # 1 - Video only, 2 - Audio only (optional)
trackIndex: int  # Destination track index (optional)
recordFrame: float  # Record frame position (optional)
```

### AudioSyncSettings

```text
syncMode: AudioSyncMode  # Default: resolve.AUDIO_SYNC_TIMECODE
channelNumber: int | AudioSyncChannel  # For AUDIO_SYNC_WAVEFORM mode: channel offset, 1 to min channel count across input clips (default: 1)
retainEmbeddedAudio: bool  # Keep original embedded audio (default: False)
retainVideoMetadata: bool  # Keep video metadata (default: False)
```

### AutoAlignOptions

```text
SyncUsing: AutoAlignSyncUsing  # Default: resolve.AUTO_ALIGN_CLIPS_USING_TIMECODE
UseTrack: int | AutoAlignUseTrack  # For USING_WAVEFORM mode: track index, 1, 2, ... (default: 1)
```

### AutoCaptionSettings

```text
language: AutoCaptionLanguage  # Default: resolve.AUTO_CAPTION_AUTO
captionPreset: AutoCaptionPreset  # Default: resolve.AUTO_CAPTION_SUBTITLE_DEFAULT
charsPerLine: int  # Max characters per line, 1 to 60 (default: 42, varies by preset/language)
lineBreak: AutoCaptionLineBreak  # Default: resolve.AUTO_CAPTION_LINE_SINGLE
gap: int  # Gap between subtitles in frames, 0 to 10 (default: 0)
```

### CDL

```text
NodeIndex: int  # Target node index, 1 <= NodeIndex <= total number of nodes
Slope: str  # RGB slope values as space-separated string, e.g. '0.5 0.4 0.2'
Offset: str  # RGB offset values as space-separated string, e.g. '0.4 0.3 0.2'
Power: str  # RGB power values as space-separated string, e.g. '0.6 0.7 0.8'
Saturation: float  # Saturation value, e.g. 0.65
```

### CompoundClipOptions

```text
startTimecode: str  # Start timecode, e.g. '00:00:00:00'
name: str  # Compound clip name
```

### CreateTimelineClipInfo

```text
mediaPoolItem: MediaPoolItem  # MediaPoolItem object to append
startFrame: float  # Source start frame (optional)
endFrame: float  # Source end frame (optional)
recordFrame: float  # Record frame position (optional)
```

### FadeInfo

```text
FadeIn: int  # Duration in frames
FadeOut: int  # Duration in frames
```

### ImportClipInfo

```text
FilePath: str  # File path (supports %0Nd frame pattern for image sequences)
StartIndex: int  # Start frame index for image sequences (optional)
EndIndex: int  # End frame index for image sequences (optional)
```

### ImportOptions

```text
timelineName: str  # Name for the created timeline (not valid for DRT import)
importSourceClips: bool  # Import source clips into media pool (default: True, not valid for DRT)
sourceClipsPath: str  # Filesystem path to search for source clips if media is inaccessible
sourceClipsFolders: list[Folder]  # Media Pool folders to search for source clips if importSourceClips is False
interlaceProcessing: bool  # Enable interlace processing (AAF import only)
```

### MarkInOut

```text
video: MarkInOutRange  # Video mark in/out range
audio: MarkInOutRange  # Audio mark in/out range
```

### MarkerInfo

```text
color: MarkerColor  # Color name, e.g. 'Blue', 'Green'
duration: int  # Duration in frames, e.g. 1
note: str  # Text note
name: str  # Name, e.g. 'Marker 1'
customData: str  # Custom data field not exposed via UI
```

### MediaStorageItemInfo

```text
media: str  # File/folder path
startFrame: int  # Start frame (optional)
endFrame: int  # End frame (optional)
```

### MulticamOptions

```text
name: str  # Clip name (auto-generated from first clip if omitted)
startTimecode: str  # Start timecode, default: '01:00:00:00'
frameRate: float  # Frame rate, e.g. 23.976 (default: project timeline frame rate)
angleSyncMode: MulticamAngleSyncMode  # Default: resolve.MULTICAM_ANGLE_SYNC_TIMECODE
channelConfig: int | AudioSyncChannel  # Audio channel for sync: 1-8 (angleSyncMode=MULTICAM_ANGLE_SYNC_AUDIO only)
multicamAudioMode: MulticamAudioMode  # Default: resolve.MULTICAM_AUDIO_SOURCE
angleNameMode: MulticamAngleNameMode  # Default: resolve.MULTICAM_ANGLE_NAME_SEQUENTIAL
splitAtGaps: bool  # Split at gaps (angleSyncMode=MULTICAM_ANGLE_SYNC_AUDIO only, default: False)
useFullClipExtents: bool  # Use full clip extents (default: False)
createBinForSourceClips: bool  # Create bin for source clips (default: True)
detectSameCameraClipsMode: MulticamDetectMode  # Default: resolve.MULTICAM_DETECT_NONE
```

### NormalizeAudioOptions

```text
normalizationMode: str  # Mode name from GetNormalizeAudioModes() (default: 'Sample Peak Program')
targetLevel: float  # Target level in dBFS, e.g. -9.0
targetLoudness: float  # Target loudness in LKFS, e.g. -24.0
setLevelMode: NormalizeAudioSetLevelMode  # Default: resolve.NORMALIZE_AUDIO_SET_LEVEL_RELATIVE
```

### OutputBlanking

```text
Top: int  # Top blanking in pixels
Bottom: int  # Bottom blanking in pixels
Left: int  # Left blanking in pixels
Right: int  # Right blanking in pixels
```

### QuickExportRenderSettings

```text
TargetDir: str  # Output directory path
CustomName: str  # Custom output filename
VideoQuality: int  # Bit rate limit (0 = automatic)
EnableUpload: bool  # Enable direct upload for supported web presets (default: False)
```

### QuickExportRenderStatus

```text
JobStatus: str  # 'Render Complete', 'Render Failed', 'Render Cancelled', 'Upload Completed', 'Upload Failed' or 'Upload Cancelled'
CompletionPercentage: int  # Completion percentage
TimeTakenToRenderInMs: int  # Time taken to render (set on completion)
Error: str  # Error details (set on failure)
```

### RenderJobStatus

```text
JobStatus: str  # Current status, one of 'Ready', 'Ready for background render', 'Rendering', 'Complete', 'Cancelled', 'Background Render Cancelled', 'Failed', 'Ready to remotely render' or 'Remote Render Cancelled'
CompletionPercentage: int  # Completion percentage
TimeTakenToRenderInMs: int  # Time taken to complete render, set for 'Complete' jobs
EstimatedTimeRemainingInMs: int  # Time remaining to render, set for 'Rendering' jobs
Error: str  # Error details, set for 'Failed' jobs
```

### RenderSettings

```text
SelectAllFrames: bool  # Select all frames (MarkIn/MarkOut ignored when True)
MarkIn: int  # Render mark in frame
MarkOut: int  # Render mark out frame
TargetDir: str  # Output directory path
CustomName: str  # Custom output filename
UseUniqueFilenames: bool  # Enable unique filenames
UniqueFilenameStyle: int  # 0 = Prefix, 1 = Suffix
ExportVideo: bool  # Enable video export
ExportAudio: bool  # Enable audio export
FormatWidth: int  # Output width in pixels
FormatHeight: int  # Output height in pixels
FrameRate: float  # Frame rate, e.g. 23.976, 24.0
PixelAspectRatio: str  # SD: '16_9' or '4_3'; other: 'square' or 'cinemascope'
VideoQuality: int | str  # 0 = automatic, int > 0 = bit rate, or 'Least'/'Low'/'Medium'/'High'/'Best'
AudioFormat: str  # Audio format, e.g. 'mp3' (only if ExportVideo is False)
AudioCodec: str  # Audio codec, e.g. 'aac'
AudioBitDepth: int  # Audio bit depth, e.g. 16, 24
AudioSampleRate: int  # Audio sample rate, e.g. 48000
ColorSpaceTag: str  # Color space, e.g. 'Same as Project', 'AstroDesign'
GammaTag: str  # Gamma, e.g. 'Same as Project', 'ACEScct'
ExportAlpha: bool  # Enable alpha channel export
AlphaMode: int  # 0 = Premultiplied, 1 = Straight (requires ExportAlpha True)
EncodingProfile: str  # Encoding profile, e.g. 'Main10' (H.264/H.265 only)
MultiPassEncode: bool  # Multi-pass encoding (H.264 only)
NetworkOptimization: bool  # Network optimization (QuickTime/MP4 only)
ClipStartFrame: int  # Clip start frame number
TimelineStartTimecode: str  # Timeline start timecode, e.g. '01:00:00:00'
ReplaceExistingFilesInPlace: bool  # Replace existing files in place
ExportSubtitle: bool  # Enable subtitle export
SubtitleFormat: str  # 'BurnIn', 'EmbeddedCaptions' or 'SeparateFile'
UseFullExtents: bool  # Use full extents of clips
AddFrameHandles: int  # Frame handles count >= 0 (ignored if UseFullExtents is True)
DataBurnIn: str  # Data burn-in preset, e.g. 'Same as project', 'None'
```

### SmartSwitchSettings

```text
minEditDuration: float  # Minimum edit duration in seconds, 0.5 to 10.0 (default: 1.0)
editChangeDelay: float  # Edit change delay in seconds, 0.0 to 2.0 (default: 0.3)
isAutoDetectWideAngle: bool  # Auto-detect wide angle from analysis (default: True)
analysisMode: SmartSwitchAnalysisMode  # Overrides isAutoDetectWideAngle
wideAngleID: str  # Wide angle name, or 'None' to disable (used when isAutoDetectWideAngle is False)
wideAngleFrequency: SmartSwitchWideAngleFrequency  # Default: resolve.SMART_SWITCH_WIDE_ANGLE_FREQ_MEDIUM
isUseWideAngleForIntroOutro: bool  # Use wide angle for intro/outro (default: True)
isUseWideAngleForSilence: bool  # Use wide angle for silence (default: True)
switchOnVideoOnly: bool  # Switch on video only, not supported in adaptive/source mode (default: False)
quality: SmartSwitchQuality  # Default: resolve.SMART_SWITCH_QUALITY_BETTER
```

### SpeechSettings

```text
TextInput: str  # Input text to synthesize (max 350 chars)
VoiceModel: str  # Voice model name, e.g. 'Female 1', 'Male 1', 'Custom Voice'
CustomVoiceFile: str  # Full path to custom voice file (required when VoiceModel is 'Custom Voice')
Speed: float  # Speed adjustment, -10.0 to 10.0
Variation: float  # Variation amount, 0.0 to 1.0
Pitch: float  # Pitch adjustment, -2.0 to 2.0
GenerationID: int  # Generation ID for reproducibility (> 0)
Filename: str  # Output filename
AddToTimeline: bool  # Add generated audio to timeline (default: False)
AudioTrack: int  # Target audio track number (0 = new track)
```

### SpeedOptions

```text
Percentage: float  # Speed in percentage, e.g. 110.0 (0.0 = freeze frame)
PitchCorrection: bool  # Pitch correction of linked audio (default: clip's existing state)
StretchKeyframesToFit: bool  # Stretch keyframes to fit (default: False)
RippleTimeline: bool  # Ripple timeline (default: False)
```

### TimelineItemProperties

```text
TransformEnabled: bool  # Enable/disable Transform filter section
Pan: float  # -4.0*width to 4.0*width
Tilt: float  # -4.0*height to 4.0*height
ZoomX: float  # 0.0 to 100.0
ZoomY: float  # 0.0 to 100.0
ZoomGang: bool  # Gang ZoomX and ZoomY
RotationAngle: float  # -360.0 to 360.0
AnchorPointX: float  # -4.0*width to 4.0*width
AnchorPointY: float  # -4.0*height to 4.0*height
Pitch: float  # -1.5 to 1.5
Yaw: float  # -1.5 to 1.5
FlipX: bool  # Flip horizontally
FlipY: bool  # Flip vertically
CroppingEnabled: bool  # Enable/disable Cropping filter section
CropLeft: float  # 0.0 to width
CropRight: float  # 0.0 to width
CropTop: float  # 0.0 to height
CropBottom: float  # 0.0 to height
CropSoftness: float  # -100.0 to 100.0
CropRetain: bool  # Retain Image Position
DynamicZoomEnabled: bool  # Enable/disable Dynamic Zoom filter section
DynamicZoomEase: DynamicZoomEase
CompositeEnabled: bool  # Enable/disable Composite filter section
CompositeMode: CompositeMode  # See README.md section 'Looking up Timeline item properties'.
Opacity: float  # 0.0 to 100.0
LensCorrectionEnabled: bool  # Enable/disable Lens Correction filter section
Distortion: float  # -1.0 to 1.0
RetimeAndScalingEnabled: bool  # Enable/disable Retime and Scaling filter section
RetimeProcess: RetimeProcess
MotionEstimation: MotionEstimation
Scaling: Scaling
ResizeFilter: ResizeFilter
AudioVolumeEnabled: bool  # Enable/disable audio volume filter
AudioVolume: float  # -100.0 to 30.0 (dB)
AudioPanEnabled: bool  # Enable/disable audio pan filter
AudioPan: float  # -100.0 to 100.0
AudioPitchEnabled: bool  # Enable/disable audio pitch filter
AudioPitchSemiTones: float  # -24.0 to 24.0
AudioPitchCents: float  # -100.0 to 100.0
AudioVoiceIsolationEnabled: bool  # Enable/disable Voice Isolation [Active Timeline Only]
AudioVoiceIsolationAmount: int  # 0 to 100 (isolation strength) [Active Timeline Only]
AudioDialogueLevelerEnabled: bool  # Enable/disable Dialogue Leveler [Active Timeline Only]
AudioDialogueLevelerMode: DialogueLevelerMode  # [Active Timeline Only]
AudioDialogueLevelerReduceLoudDialogue: bool  # Reduce loud dialogue [Active Timeline Only]
AudioDialogueLevelerLiftSoftDialogue: bool  # Lift soft dialogue [Active Timeline Only]
AudioDialogueLevelerBackgroundReduction: bool  # Enable background reduction [Active Timeline Only]
AudioDialogueLevelerOutputGain: float  # 0.0 to 6.0 (dB) [Active Timeline Only]
```

### Transcription

```text
language: str  # Transcription language code
segments: list[TranscriptionSegment]  # List of transcription segments
```

### TranscriptionSegment

```text
start: str  # Start timecode, e.g. '01:00:02:05'
end: str  # End timecode, e.g. '01:00:04:10'
text: str  # Concatenated text of all words in segment; '(...)' denotes silence
speaker: str | None  # Speaker name if detected, None otherwise
words: list[TranscriptionWord]  # Individual words with timing
```

### TransitionOptions

```text
type: str  # Transition type name, e.g. 'Cross Dissolve'
category: str  # Transition category: 'simple', 'fusion', 'ofx' or 'audio'
position: str  # Edge of the item to attach the transition to: 'start' or 'end'
alignment: str  # Placement relative to the edge: 'left', 'center' or 'right'
duration: int | None  # Duration in frames (default: automatically calculated)
```

### VoiceIsolationState

```text
isEnabled: bool  # Enabled flag
amount: int  # Amount in range [0, 100]
```

## Constants

Read them off the live object — `resolve.EXPORT_OTIO`, `resolve.CACHE_ENABLED`, … They are floats.

```text
KeyframeMode: KEYFRAME_MODE_ALL, KEYFRAME_MODE_COLOR, KEYFRAME_MODE_SIZING
CloudSettingKey: CLOUD_SETTING_PROJECT_NAME, CLOUD_SETTING_PROJECT_MEDIA_PATH, CLOUD_SETTING_IS_COLLAB, CLOUD_SETTING_SYNC_MODE, CLOUD_SETTING_IS_CAMERA_ACCESS
CloudSyncMode: CLOUD_SYNC_NONE, CLOUD_SYNC_PROXY_ONLY, CLOUD_SYNC_PROXY_AND_ORIG
AudioSyncSettingKey: AUDIO_SYNC_MODE, AUDIO_SYNC_CHANNEL_NUMBER, AUDIO_SYNC_RETAIN_EMBEDDED_AUDIO, AUDIO_SYNC_RETAIN_VIDEO_METADATA
AudioSyncMode: AUDIO_SYNC_WAVEFORM, AUDIO_SYNC_TIMECODE, AUDIO_SYNC_IN, AUDIO_SYNC_OUT, AUDIO_SYNC_MARKER
AudioSyncChannel: AUDIO_SYNC_CHANNEL_AUTOMATIC, AUDIO_SYNC_CHANNEL_MIX
MulticamAngleSyncMode: MULTICAM_ANGLE_SYNC_IN, MULTICAM_ANGLE_SYNC_OUT, MULTICAM_ANGLE_SYNC_TIMECODE, MULTICAM_ANGLE_SYNC_AUDIO, MULTICAM_ANGLE_SYNC_MARKER
MulticamAngleNameMode: MULTICAM_ANGLE_NAME_SEQUENTIAL, MULTICAM_ANGLE_NAME_ANGLE, MULTICAM_ANGLE_NAME_CAMERA, MULTICAM_ANGLE_NAME_CLIP, MULTICAM_ANGLE_NAME_FILE
MulticamDetectMode: MULTICAM_DETECT_BY_CAMERA_NUMBER, MULTICAM_DETECT_BY_ANGLE, MULTICAM_DETECT_BY_REEL_NUMBER, MULTICAM_DETECT_BY_REEL_NAME, MULTICAM_DETECT_BY_ROLL_CARD, MULTICAM_DETECT_NONE
MulticamAudioMode: MULTICAM_AUDIO_ADAPTIVE, MULTICAM_AUDIO_SOURCE, MULTICAM_AUDIO_REFERENCE, MULTICAM_AUDIO_ALL
CloudSyncStatus: CLOUD_SYNC_DEFAULT, CLOUD_SYNC_DOWNLOAD_IN_QUEUE, CLOUD_SYNC_DOWNLOAD_IN_PROGRESS, CLOUD_SYNC_DOWNLOAD_SUCCESS, CLOUD_SYNC_DOWNLOAD_FAIL, CLOUD_SYNC_DOWNLOAD_NOT_FOUND, CLOUD_SYNC_UPLOAD_IN_QUEUE, CLOUD_SYNC_UPLOAD_IN_PROGRESS, CLOUD_SYNC_UPLOAD_SUCCESS, CLOUD_SYNC_UPLOAD_FAIL, CLOUD_SYNC_UPLOAD_NOT_FOUND, CLOUD_SYNC_SUCCESS
SlateMarkerColor: MARKER_NONE, MARKER_BLUE, MARKER_CYAN, MARKER_GREEN, MARKER_YELLOW, MARKER_RED, MARKER_PINK, MARKER_PURPLE, MARKER_FUCHSIA, MARKER_ROSE, MARKER_LAVENDER, MARKER_SKY, MARKER_MINT, MARKER_LEMON, MARKER_SAND, MARKER_COCOA, MARKER_CREAM
NormalizeAudioSetLevelMode: NORMALIZE_AUDIO_SET_LEVEL_RELATIVE, NORMALIZE_AUDIO_SET_LEVEL_INDEPENDENT
AutoAlignSyncUsing: AUTO_ALIGN_CLIPS_USING_WAVEFORM, AUTO_ALIGN_CLIPS_USING_TIMECODE
AutoAlignUseTrack: AUTO_ALIGN_CLIPS_WAVEFORM_TRACK_MIX, AUTO_ALIGN_CLIPS_WAVEFORM_TRACK_AUTOMATIC
TimelineExportType: EXPORT_AAF, EXPORT_DRT, EXPORT_EDL, EXPORT_FCP_7_XML, EXPORT_FCPXML_1_8, EXPORT_FCPXML_1_9, EXPORT_FCPXML_1_10, EXPORT_HDR_10_PROFILE_A, EXPORT_HDR_10_PROFILE_B, EXPORT_TEXT_CSV, EXPORT_TEXT_TAB, EXPORT_DOLBY_VISION_VER_2_9, EXPORT_DOLBY_VISION_VER_4_0, EXPORT_DOLBY_VISION_VER_5_1, EXPORT_OTIO, EXPORT_ALE, EXPORT_ALE_CDL
TimelineExportSubtype: EXPORT_NONE, EXPORT_AAF_NEW, EXPORT_AAF_EXISTING, EXPORT_CDL, EXPORT_SDL, EXPORT_MISSING_CLIPS
SubtitleSettingKey: SUBTITLE_LANGUAGE, SUBTITLE_CAPTION_PRESET, SUBTITLE_CHARS_PER_LINE, SUBTITLE_LINE_BREAK, SUBTITLE_GAP
AutoCaptionLanguage: AUTO_CAPTION_AUTO, AUTO_CAPTION_MANDARIN_SIMPLIFIED, AUTO_CAPTION_DUTCH, AUTO_CAPTION_ENGLISH, AUTO_CAPTION_FINNISH, AUTO_CAPTION_FRENCH, AUTO_CAPTION_GERMAN, AUTO_CAPTION_HINDI, AUTO_CAPTION_INDONESIAN, AUTO_CAPTION_ITALIAN, AUTO_CAPTION_JAPANESE, AUTO_CAPTION_KOREAN, AUTO_CAPTION_MALAY, AUTO_CAPTION_NORWEGIAN, AUTO_CAPTION_POLISH, AUTO_CAPTION_PORTUGUESE, AUTO_CAPTION_ROMANIAN, AUTO_CAPTION_RUSSIAN, AUTO_CAPTION_SPANISH, AUTO_CAPTION_SWEDISH, AUTO_CAPTION_TURKISH, AUTO_CAPTION_VIETNAMESE, AUTO_CAPTION_TAMIL, AUTO_CAPTION_THAI, AUTO_CAPTION_DANISH, AUTO_CAPTION_MANDARIN_TRADITIONAL
AutoCaptionPreset: AUTO_CAPTION_SUBTITLE_DEFAULT, AUTO_CAPTION_TELETEXT, AUTO_CAPTION_NETFLIX
AutoCaptionLineBreak: AUTO_CAPTION_LINE_SINGLE, AUTO_CAPTION_LINE_DOUBLE
DolbyVisionAnalysisType: DLB_BLEND_SHOTS
DynamicZoomEase: DYNAMIC_ZOOM_EASE_LINEAR, DYNAMIC_ZOOM_EASE_IN, DYNAMIC_ZOOM_EASE_OUT, DYNAMIC_ZOOM_EASE_IN_AND_OUT
CompositeMode: COMPOSITE_NORMAL, COMPOSITE_ADD, COMPOSITE_SUBTRACT, COMPOSITE_DIFF, COMPOSITE_MULTIPLY, COMPOSITE_SCREEN, COMPOSITE_OVERLAY, COMPOSITE_HARDLIGHT, COMPOSITE_SOFTLIGHT, COMPOSITE_DARKEN, COMPOSITE_LIGHTEN, COMPOSITE_COLOR_DODGE, COMPOSITE_COLOR_BURN, COMPOSITE_EXCLUSION, COMPOSITE_HUE, COMPOSITE_SATURATE, COMPOSITE_COLORIZE, COMPOSITE_LUMA_MASK, COMPOSITE_DIVIDE, COMPOSITE_LINEAR_DODGE, COMPOSITE_LINEAR_BURN, COMPOSITE_LINEAR_LIGHT, COMPOSITE_VIVID_LIGHT, COMPOSITE_PIN_LIGHT, COMPOSITE_HARD_MIX, COMPOSITE_LIGHTER_COLOR, COMPOSITE_DARKER_COLOR, COMPOSITE_FOREGROUND, COMPOSITE_ALPHA, COMPOSITE_INVERTED_ALPHA, COMPOSITE_LUM, COMPOSITE_INVERTED_LUM
RetimeProcess: RETIME_USE_PROJECT, RETIME_NEAREST, RETIME_FRAME_BLEND, RETIME_OPTICAL_FLOW
MotionEstimation: MOTION_EST_USE_PROJECT, MOTION_EST_STANDARD_FASTER, MOTION_EST_STANDARD_BETTER, MOTION_EST_ENHANCED_FASTER, MOTION_EST_ENHANCED_BETTER, MOTION_EST_SPEED_WARP_FASTER, MOTION_EST_SPEED_WARP_BETTER, MOTION_EST_METAL
Scaling: SCALE_USE_PROJECT, SCALE_CROP, SCALE_FIT, SCALE_FILL, SCALE_STRETCH
ResizeFilter: RESIZE_FILTER_USE_PROJECT, RESIZE_FILTER_SHARPER, RESIZE_FILTER_SMOOTHER, RESIZE_FILTER_BICUBIC, RESIZE_FILTER_BILINEAR, RESIZE_FILTER_BESSEL, RESIZE_FILTER_BOX, RESIZE_FILTER_CATMULL_ROM, RESIZE_FILTER_CUBIC, RESIZE_FILTER_GAUSSIAN, RESIZE_FILTER_LANCZOS, RESIZE_FILTER_MITCHELL, RESIZE_FILTER_NEAREST_NEIGHBOR, RESIZE_FILTER_QUADRATIC, RESIZE_FILTER_SINC, RESIZE_FILTER_LINEAR
CacheMode: CACHE_AUTO_ENABLED, CACHE_DISABLED, CACHE_ENABLED
DialogueLevelerMode: DIALOGUE_LEVELER_MODE_ALLOW_WIDER_DYNAMICS, DIALOGUE_LEVELER_MODE_OPTIMIZE_MODERATE_LEVELS, DIALOGUE_LEVELER_MODE_MORE_LIFT_FOR_LOW_LEVELS, DIALOGUE_LEVELER_MODE_LIFT_SOFT_WHISPERY_SOURCES
FlattenMulticamGrade: FLATTEN_MULTICAM_COPY_GRADE, FLATTEN_MULTICAM_RETAIN_GRADE_FROM_ANGLE
ExportLutType: EXPORT_LUT_17PTCUBE, EXPORT_LUT_33PTCUBE, EXPORT_LUT_65PTCUBE, EXPORT_LUT_PANASONICVLUT
SmartSwitchQuality: SMART_SWITCH_QUALITY_FASTER, SMART_SWITCH_QUALITY_BETTER
SmartSwitchWideAngleFrequency: SMART_SWITCH_WIDE_ANGLE_FREQ_LOW, SMART_SWITCH_WIDE_ANGLE_FREQ_MEDIUM, SMART_SWITCH_WIDE_ANGLE_FREQ_HIGH
SmartSwitchAnalysisMode: SMART_SWITCH_ANALYSIS_MODE_NONE, SMART_SWITCH_ANALYSIS_MODE_DETECT_WIDE_ANGLE, SMART_SWITCH_ANALYSIS_MODE_AUDIO_ONLY
CloneChecksumType: CLONE_CHECKSUM_TYPE_NONE, CLONE_CHECKSUM_TYPE_FILESIZE, CLONE_CHECKSUM_TYPE_CRC32, CLONE_CHECKSUM_TYPE_MD5, CLONE_CHECKSUM_TYPE_SHA256, CLONE_CHECKSUM_TYPE_SHA512, CLONE_CHECKSUM_TYPE_XXH_64
```

## Literal types

```text
ClipColor = ('Orange', 'Apricot', 'Yellow', 'Lime', 'Olive', 'Green', 'Teal', 'Navy', 'Blue', 'Purple', 'Violet', 'Pink', 'Tan', 'Beige', 'Brown', 'Chocolate')
FlagColor = ('Blue', 'Cyan', 'Green', 'Yellow', 'Red', 'Pink', 'Purple', 'Fuchsia', 'Rose', 'Lavender', 'Sky', 'Mint', 'Lemon', 'Sand', 'Cocoa', 'Cream')
MarkerColor = ('Blue', 'Cyan', 'Green', 'Yellow', 'Red', 'Pink', 'Purple', 'Fuchsia', 'Rose', 'Lavender', 'Sky', 'Mint', 'Lemon', 'Sand', 'Cocoa', 'Cream')
MarkType = ('video', 'audio', 'all')
TrackType = ('video', 'audio', 'subtitle')
```
