"""Helpers for scripting DaVinci Resolve 21.x from Python.

resolve_run.py injects every public name here into the job script's namespace, bound to the
live session. They can also be imported directly by a script that runs from Resolve's
Workspace > Scripts menu: ``from resolve_helpers import bind; H = bind(resolve)``.

The Resolve API reports failure by returning False or None rather than raising, and it keeps
going after a failed step — so a job that ignores return values produces a half-built
timeline with no error. ``need()`` turns those silent failures into exceptions with the call
named, and every helper below uses it.
"""

import json
import os
import time

MEDIA_EXTS = {
    ".mov", ".mp4", ".m4v", ".mxf", ".avi", ".mkv", ".braw", ".r3d", ".ari", ".crm", ".mts",
    ".wav", ".aif", ".aiff", ".mp3", ".m4a", ".flac",
    ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".dpx", ".psd",
}


class ResolveError(RuntimeError):
    pass


def need(value, what):
    """Return value, or raise if the API signalled failure (False / None / empty)."""
    if value is None or value is False:
        raise ResolveError(f"{what} failed (Resolve returned {value!r})")
    return value


class Helpers:
    """Session-bound helpers. `bind(resolve)` returns one; resolve_run.py exposes its methods."""

    def __init__(self, resolve):
        self.resolve = resolve

    # ---- session -------------------------------------------------------------------------

    @property
    def project(self):
        return need(self.resolve.GetProjectManager().GetCurrentProject(), "GetCurrentProject")

    @property
    def media_pool(self):
        return self.project.GetMediaPool()

    def timelines(self):
        p = self.project
        return [p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)]

    def timeline_by_name(self, name):
        for tl in self.timelines():
            if tl.GetName() == name:
                return tl
        return None

    def current_timeline(self):
        return need(self.project.GetCurrentTimeline(), "GetCurrentTimeline (no timeline open)")

    def use_timeline(self, tl_or_name):
        tl = self.timeline_by_name(tl_or_name) if isinstance(tl_or_name, str) else tl_or_name
        need(tl, f"timeline {tl_or_name!r} not found; timeline lookup")
        need(self.project.SetCurrentTimeline(tl), "SetCurrentTimeline")
        return tl

    def new_timeline(self, name, replace=False):
        """Create an empty timeline and make it current. Refuses to clobber unless replace=True."""
        old = self.timeline_by_name(name)
        if old is not None:
            if not replace:
                raise ResolveError(f"timeline {name!r} exists; pass replace=True or pick another name")
            need(self.media_pool.DeleteTimelines([old]), f"DeleteTimelines([{name!r}])")
        tl = need(self.media_pool.CreateEmptyTimeline(name), f"CreateEmptyTimeline({name!r})")
        self.project.SetCurrentTimeline(tl)
        return tl

    def copy_timeline(self, src, name):
        """Duplicate a timeline under a new name (e.g. before making a 9:16 version).

        Round-trips through a .drt export/import instead of Timeline.DuplicateTimeline(),
        which was in flight both times Resolve froze during testing (not reproducible in a
        fresh session). The copy is made current.
        """
        import tempfile
        src = self.timeline_by_name(src) if isinstance(src, str) else src
        need(src, "source timeline lookup")
        if self.timeline_by_name(name):
            raise ResolveError(f"timeline {name!r} exists; pick another name")
        path = os.path.join(tempfile.mkdtemp(prefix="resolve-drt-"), "copy.drt")
        need(src.Export(path, self.resolve.EXPORT_DRT, self.resolve.EXPORT_NONE), "Timeline.Export(DRT)")
        tl = need(self.media_pool.ImportTimelineFromFile(path), "ImportTimelineFromFile(DRT)")
        need(tl.SetName(name), f"SetName({name!r})")
        self.project.SetCurrentTimeline(tl)
        return tl

    def save(self):
        return need(self.resolve.GetProjectManager().SaveProject(), "SaveProject")

    # ---- time ----------------------------------------------------------------------------

    def fps(self, tl=None):
        tl = tl or self.current_timeline()
        return float(tl.GetSettings()["timelineFrameRate"])

    def _tc_params(self, tl):
        s = tl.GetSettings()
        fps = float(s["timelineFrameRate"])
        return int(round(fps)), str(s.get("timelineDropFrameTimecode", "0")) == "1"

    def tc_to_frame(self, tc, tl=None):
        """Absolute timeline frame for a timecode string ('01:00:10:00', ';' marks drop frame)."""
        tl = tl or self.current_timeline()
        base, drop = self._tc_params(tl)
        h, m, s, f = (int(x) for x in tc.replace(";", ":").split(":"))
        frames = ((h * 60 + m) * 60 + s) * base + f
        if drop:
            d = base // 15  # 2 frames per minute at 29.97, 4 at 59.94
            minutes = h * 60 + m
            frames -= d * (minutes - minutes // 10)
        return frames

    def frame_to_tc(self, frame, tl=None):
        tl = tl or self.current_timeline()
        base, drop = self._tc_params(tl)
        frame = int(frame)
        if drop:
            d = base // 15
            per10 = base * 600 - d * 9
            per1 = base * 60 - d
            tens, rem = divmod(frame, per10)
            frame += d * 9 * tens + (d * ((rem - d) // per1) if rem > d else 0)
        f = frame % base
        s = frame // base % 60
        m = frame // (base * 60) % 60
        h = frame // (base * 3600)
        return f"{h:02d}:{m:02d}:{s:02d}{';' if drop else ':'}{f:02d}"

    def sec(self, seconds, tl=None):
        """Seconds → frame count at the timeline rate (a duration, not a position)."""
        return int(round(seconds * self.fps(tl)))

    def at(self, seconds, tl=None):
        """Absolute timeline frame `seconds` after the timeline start."""
        tl = tl or self.current_timeline()
        return tl.GetStartFrame() + self.sec(seconds, tl)

    # ---- media pool ----------------------------------------------------------------------

    def bin(self, path, create=True):
        """Get (or create) a Media Pool bin by slash path under the root, e.g. 'Footage/Day 1'."""
        folder = self.media_pool.GetRootFolder()
        for part in [p for p in path.split("/") if p]:
            nxt = next((f for f in folder.GetSubFolderList() if f.GetName() == part), None)
            if nxt is None:
                if not create:
                    return None
                nxt = need(self.media_pool.AddSubFolder(folder, part), f"AddSubFolder({part!r})")
            folder = nxt
        return folder

    def media_files(self, directory, exts=MEDIA_EXTS):
        """Sorted media paths in a directory, skipping macOS AppleDouble '._*' and dotfiles."""
        out = []
        for name in sorted(os.listdir(directory)):
            if name.startswith("."):
                continue
            if os.path.splitext(name)[1].lower() in exts:
                out.append(os.path.join(directory, name))
        return out

    def import_media(self, paths, folder=None):
        """Import files into `folder` (bin object or path), reusing clips already there.

        Dedupes on the clip's real 'File Path', not its name — a same-named clip pointing at
        an older file is otherwise silently reused. Returns MediaPoolItems in input order.
        """
        mp = self.media_pool
        if isinstance(folder, str):
            folder = self.bin(folder)
        folder = folder or mp.GetCurrentFolder()
        need(mp.SetCurrentFolder(folder), "SetCurrentFolder")
        paths = [os.path.abspath(p) for p in paths]
        missing = [p for p in paths if not os.path.exists(p)]
        if missing:
            raise ResolveError(f"files not found: {missing}")
        existing = {}
        for clip in folder.GetClipList() or []:
            fp = clip.GetClipProperty().get("File Path")
            if fp:
                existing[os.path.abspath(fp)] = clip
        todo = [p for p in paths if p not in existing]
        if todo:
            # 21.1.0: MediaPool.ImportMedia([{"FilePath": p}]) — the README's canonical form —
            # returns None for plain files; MediaStorage's dict form works, and the
            # "deprecated" path-list form is the fallback.
            new = (self.resolve.GetMediaStorage().AddItemListToMediaPool([{"media": p} for p in todo])
                   or mp.ImportMedia(todo))
            need(new, "AddItemListToMediaPool / ImportMedia")
            for clip in new:
                existing[os.path.abspath(clip.GetClipProperty().get("File Path", ""))] = clip
        missing = [p for p in paths if p not in existing]
        if missing:
            raise ResolveError(f"import produced no clip for: {missing}")
        return [existing[p] for p in paths]

    # ---- editing -------------------------------------------------------------------------

    def ensure_tracks(self, kind, count, tl=None):
        tl = tl or self.current_timeline()
        while tl.GetTrackCount(kind) < count:
            need(tl.AddTrack(kind, "stereo") if kind == "audio" else tl.AddTrack(kind), f"AddTrack({kind!r})")
        return tl.GetTrackCount(kind)

    def place(self, clip, at=None, track=1, src_in=None, src_out=None, media="both", tl=None):
        """Put a MediaPoolItem on the current timeline.

        at       absolute record frame (use at(seconds) / tc_to_frame); None = append at end
        src_in   first source frame (0-based, inclusive)
        src_out  source frame to stop at (EXCLUSIVE: length = src_out - src_in)
        media    'both' | 'video' | 'audio' — 'both' appends linked video+audio in one call
        Returns the created TimelineItems (with media='both' only the video item comes back;
        reach its audio through item.GetLinkedItems()).
        """
        tl = tl or self.current_timeline()
        info = {"mediaPoolItem": clip}
        if src_in is not None or src_out is not None:
            # endFrame alone is ignored — Resolve only honours the pair.
            info["startFrame"] = src_in or 0
        if src_out is not None:
            info["endFrame"] = src_out
        if at is not None:
            info["recordFrame"] = at
        if media != "both":
            info["mediaType"] = {"video": 1, "audio": 2}[media]
            info["trackIndex"] = track
            self.ensure_tracks(media, track, tl)
        elif track != 1:
            info["trackIndex"] = track
            self.ensure_tracks("video", track, tl)
        items = need(self.media_pool.AppendToTimeline([info]), f"AppendToTimeline({clip.GetName()!r})")
        return items

    def marker(self, seconds, name, color="Blue", note="", duration=1, custom_data=None, tl=None):
        """Add a timeline marker `seconds` after the timeline start.

        Timeline.AddMarker takes a frame OFFSET from the timeline start — unlike
        AppendToTimeline's absolute recordFrame. Passing an absolute frame is accepted
        silently and lands the marker hours past the end.
        """
        tl = tl or self.current_timeline()
        off = self.sec(seconds, tl)
        args = [off, color, name, note, max(1, int(duration))]
        if custom_data is not None:
            args.append(custom_data)
        need(tl.AddMarker(*args), f"AddMarker({off}, {color!r}, {name!r}) — frame already has a marker?")
        return off

    def title_clip(self, text, seconds=5.0, name=None, template="Text+", size=None, center=None):
        """Build a Text+ title as a compound clip in the Media Pool and return its MediaPoolItem.

        Place it with place(item, at=..., track=N, media='video', src_out=sec(seconds)).
        Timeline.Insert*IntoTimeline performs a ripple INSERT edit at the playhead on the UI's
        destination track — it splits and shifts every clip on the target timeline. Building
        the title on a throwaway timeline and compounding it avoids that entirely. A title is
        5 s long and cannot be lengthened, so longer titles chain several and compound them;
        trim the placed clip with src_out, never extend it past its length.
        """
        p = self.project
        keep = p.GetCurrentTimeline()
        scratch = self.new_timeline("__title_scratch__", replace=True)
        try:
            parts, total = [], 0
            want = self.sec(seconds, scratch)
            while total < want:
                t = need(scratch.InsertFusionTitleIntoTimeline(template), f"InsertFusionTitleIntoTimeline({template!r})")
                tool = t.GetFusionCompByIndex(1).FindToolByID("TextPlus")
                need(tool, "TextPlus tool in title comp")
                tool.SetInput("StyledText", text)
                if size is not None:
                    tool.SetInput("Size", size)
                if center is not None:
                    tool.SetInput("Center", {1: center[0], 2: center[1]})
                parts.append(t)
                total += int(t.GetDuration())
            cc = need(scratch.CreateCompoundClip(parts, {"name": name or f"Title - {text[:40]}"}), "CreateCompoundClip")
            return need(cc.GetMediaPoolItem(), "compound clip MediaPoolItem")
        finally:
            if keep:
                p.SetCurrentTimeline(keep)
            self.media_pool.DeleteTimelines([scratch])

    def overlay_text(self, item, text, size=None, center=None, comp_path=None):
        """Burn Text+ over a video TimelineItem through its own Fusion composition.

        Uses ImportFusionComp with assets/text-overlay.comp: TimelineItem.AddFusionComp()
        returns a composition that is not the one Resolve renders (21.1.0), so tools built
        on it never reach the output. Returns the TextPlus tool for further styling.
        """
        path = comp_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                         "assets", "text-overlay.comp")
        comp = need(item.ImportFusionComp(path), f"ImportFusionComp({path!r})")
        tool = need(comp.FindTool("Text1"), "Text1 in overlay comp")
        tool.SetInput("StyledText", text)
        if size is not None:
            tool.SetInput("Size", size)
        if center is not None:
            tool.SetInput("Center", {1: center[0], 2: center[1]})
        return tool

    def items(self, kind="video", tl=None):
        """All items on every track of `kind`, as (trackIndex, TimelineItem), in time order."""
        tl = tl or self.current_timeline()
        out = []
        for i in range(1, tl.GetTrackCount(kind) + 1):
            out += [(i, it) for it in (tl.GetItemListInTrack(kind, i) or [])]
        return sorted(out, key=lambda x: (x[1].GetStart(), x[0]))

    # ---- deliver -------------------------------------------------------------------------

    def render(self, target_dir, name=None, preset=None, format=None, codec=None,
               settings=None, tl=None, wait=True, timeout=None, poll=2.0, keep_job=False):
        """Queue the timeline as a render job, start it, and (by default) wait for it.

        preset loads a Deliver preset first ('YouTube - 1080p', 'H.264 Master', ...);
        format/codec override it (see project.GetRenderFormats / GetRenderCodecs(ext));
        settings is merged into SetRenderSettings. Returns the finished job info incl. 'path'.
        The finished job is removed from the queue unless keep_job=True.
        """
        p = self.project
        tl = self.use_timeline(tl) if tl else self.current_timeline()
        bad = set('/:\\*?"<>|') & set(name or tl.GetName())
        if bad:
            raise ResolveError(f"render name {name or tl.GetName()!r} contains {sorted(bad)}; pass name= without them")
        self.resolve.OpenPage("deliver")
        if preset:
            need(p.LoadRenderPreset(preset), f"LoadRenderPreset({preset!r}) — see project.GetRenderPresetList()")
        if format:
            need(p.SetCurrentRenderFormatAndCodec(format, codec), f"SetCurrentRenderFormatAndCodec({format!r}, {codec!r})")
        os.makedirs(target_dir, exist_ok=True)
        s = {"SelectAllFrames": True, "TargetDir": os.path.abspath(target_dir)}
        if name:
            s["CustomName"] = name
        s.update(settings or {})
        need(p.SetRenderSettings(s), f"SetRenderSettings({s})")
        job = need(p.AddRenderJob(), "AddRenderJob")
        need(p.StartRendering([job]), "StartRendering")
        if not wait:
            return {"JobId": job}
        return self.wait_render(job, timeout=timeout, poll=poll, keep_job=keep_job)

    def wait_render(self, job, timeout=None, poll=2.0, keep_job=True):
        p = self.project
        t0 = time.time()
        while True:
            st = p.GetRenderJobStatus(job) or {}
            if st.get("JobStatus") in ("Complete", "Failed", "Cancelled"):
                break
            if timeout and time.time() - t0 > timeout:
                p.StopRendering()
                raise ResolveError(f"render {job} timed out after {timeout}s at {st.get('CompletionPercentage')}%")
            time.sleep(poll)
        info = next((j for j in p.GetRenderJobList() if j.get("JobId") == job), {})
        info.update(st)
        if info.get("TargetDir") and info.get("OutputFilename"):
            info["path"] = os.path.join(info["TargetDir"], info["OutputFilename"])
        if not keep_job and st.get("JobStatus") == "Complete":
            p.DeleteRenderJob(job)
        if st.get("JobStatus") != "Complete":
            raise ResolveError(f"render {job} ended {st.get('JobStatus')}: {st.get('Error', '')}")
        return info

    # ---- inspection ----------------------------------------------------------------------

    def timeline_summary(self, tl=None, with_items=True):
        tl = tl or self.current_timeline()
        s = tl.GetSettings()
        out = {
            "name": tl.GetName(),
            "fps": float(s["timelineFrameRate"]),
            "resolution": f'{s.get("timelineResolutionWidth")}x{s.get("timelineResolutionHeight")}',
            "start_frame": tl.GetStartFrame(),
            "end_frame": tl.GetEndFrame(),
            "start_tc": tl.GetStartTimecode(),
            "markers": len(tl.GetMarkers() or {}),
            "tracks": {},
        }
        for kind in ("video", "audio", "subtitle"):
            tracks = []
            for i in range(1, tl.GetTrackCount(kind) + 1):
                items = tl.GetItemListInTrack(kind, i) or []
                t = {"index": i, "name": tl.GetTrackName(kind, i),
                     "enabled": tl.GetIsTrackEnabled(kind, i), "items": len(items)}
                if with_items:
                    t["clips"] = [{"name": it.GetName(), "start": it.GetStart(), "end": it.GetEnd()}
                                  for it in items[:50]]
                tracks.append(t)
            out["tracks"][kind] = tracks
        return out

    def state(self):
        r = self.resolve
        pm = r.GetProjectManager()
        p = pm.GetCurrentProject()
        out = {
            "product": r.GetProductName(), "version": r.GetVersionString(),
            "studio": r.IsStudio(), "page": r.GetCurrentPage(),
            "database": pm.GetCurrentDatabase(),
            "project": p.GetName() if p else None,
        }
        if not p:
            return out
        cur = p.GetCurrentTimeline()
        out["timelines"] = [t.GetName() for t in self.timelines()]
        out["current_timeline"] = self.timeline_summary(cur, with_items=False) if cur else None
        out["render"] = {
            "in_progress": p.IsRenderingInProgress(),
            "queue": [{k: j.get(k) for k in ("JobId", "TimelineName", "TargetDir", "OutputFilename")}
                      for j in p.GetRenderJobList()],
            "format": p.GetCurrentRenderFormatAndCodec(),
            "presets": p.GetRenderPresetList(),
        }
        return out

    def dump(self, obj, path=None):
        """Print obj as JSON (and write it to path if given). Resolve objects print by repr."""
        text = json.dumps(obj, indent=2, default=repr, ensure_ascii=False)
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
        print(text)
        return obj


def bind(resolve):
    return Helpers(resolve)


EXPORTED = [
    "timelines", "timeline_by_name", "current_timeline", "use_timeline", "new_timeline", "copy_timeline", "save",
    "fps", "tc_to_frame", "frame_to_tc", "sec", "at",
    "bin", "media_files", "import_media",
    "ensure_tracks", "place", "marker", "title_clip", "overlay_text", "items",
    "render", "wait_render",
    "timeline_summary", "state", "dump",
]
