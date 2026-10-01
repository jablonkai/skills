# Photos AppleScript / JXA

From `sdef /System/Applications/Photos.app` on Photos 12.0. The dictionary is small.
Use it only for what osxphotos can't do: writing albums and importing. **It acts on
the library Photos has open**, not on `--library`.

## Object model

- `application`: `albums` (**top-level only**), `folders` (top-level), `media items`
  (all), `selection`, `favorites album`, `recently deleted album`,
  `last import album`, `version`.
- `folder`: `name`, `id`, `parent`, `albums`, `folders`.
- `album`: `name`, `id`, `parent`, `media items`.
- `media item`: `id` (`"<UUID>/L0/001"`, where the UUID is osxphotos' `uuid`),
  `filename`, `name` (title), `description`, `keywords`, `favorite`, `date`,
  `location` ({lat, lon}), `altitude`, `width`, `height`, `size`. The writable ones
  are `name`, `description`, `keywords`, `favorite`, `date` and `location`. Don't set
  them unless the user asked.

Commands: `make new album|folder named N [at FOLDER]`, `add {items} to ALBUM`,
`import {aliases} [into ALBUM] [skip check duplicates BOOL]`,
`export {items} to FOLDER [using originals BOOL]`, `search for TEXT`,
`spotlight ITEM`, `delete ALBUM|FOLDER` (it can't delete media items), `count`,
`exists`, and slideshow control.

## JXA snippets

```javascript
const P = Application('Photos');
P.mediaItems.byId(uuid + '/L0/001');                  // osxphotos uuid → item
P.albums.whose({name: 'Hiking'})();                   // top-level albums with that name
P.folders.whose({name: 'Trips'})()[0].albums();       // albums inside a folder
const f = P.make({new: 'folder', named: 'Trips'});
const a = P.make({new: 'album', named: 'Lisbon', at: f});
P.add([P.mediaItems.byId(u + '/L0/001')], {to: a});   // adding an existing member is a no-op
a.mediaItems.id();                                    // read back membership
P.import([Path('/abs/file.jpg')], {into: a, skipCheckDuplicates: true});  // returns the new items
```

`whose({filename: …})` over every media item is slow on big libraries. Resolve items
by id from an osxphotos query instead.

## Errors

| Code | Meaning | Fix |
|---|---|---|
| -1743 | not authorised to send Apple events | Privacy & Security › Automation › allow the terminal to control Photos |
| -1712 | Apple event timed out | a modal sheet is waiting in Photos (duplicate-import prompt, library upgrade, iCloud notice). Dismiss it, then make the call idempotent and retry |
| -1728 | can't get object | wrong name or id, or the item is in a folder (app-level `albums` is top-level only) |
| -1719 | invalid index | the element isn't there. Sandboxed save/open panels don't expose their fields |

## Choosing the open library

AppleScript can't switch libraries. To work on another library: quit Photos, then
`open -a Photos /path/X.photoslibrary`. Check what's open with
`bash scripts/photos.sh --check` (it reads the `Photos.sqlite` path from `lsof`).
Creating a new library is only possible in the GUI: hold ⌥ while launching Photos,
then choose Create New… Switching changes which library Photos opens next time, so
switch back to the user's library when done.
