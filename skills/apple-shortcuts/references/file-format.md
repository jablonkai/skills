# The .shortcut file format

## Layers

1. **Signed file** (what Shortcuts exports and imports): an Apple Encrypted Archive.
   - The magic is `AEA1`. The profile is 0 (`hkdf_sha256_hmac__none__ecdsa_p256`), which
     means signed but **not encrypted**.
   - Bytes 8–11 are the little-endian length of the auth data, and the auth data (a
     binary plist) follows. What it holds depends on the signing mode:
     - `anyone`: `SigningCertificateChain`, a list of DER certs. The leaf cert's key
       signed the file.
     - `people-who-know-me`: `SigningPublicKey`, a raw 65-byte X9.63 P-256 key, plus
       `SigningPublicKeySignature`, `AppleIDCertificateChain` and `AppleIDValidationRecord`.
2. Inside it is an **Apple Archive** with one file, `Shortcut.wflow`.
3. **`Shortcut.wflow`** is the workflow plist below.

Decode by hand, which is what `sc-decode.py` does:

```bash
openssl x509 -inform der -in leaf.der -pubkey -noout > pub.pem   # or wrap SigningPublicKey as SPKI
aea decrypt -i X.shortcut -o x.aar -sign-pub pub.pem
aa extract -i x.aar -d out && plutil -p out/Shortcut.wflow
```

Encode: write the plist (binary or XML) to `<Name>.shortcut`, then run `shortcuts sign`.
The **file name** becomes the shortcut name on import.

## Workflow plist

```
WFWorkflowActions                    [ {WFWorkflowActionIdentifier, WFWorkflowActionParameters}, ... ]
WFWorkflowInputContentItemClasses    [WFImageContentItem, WFStringContentItem, WFGenericFileContentItem, ...]
WFWorkflowHasShortcutInputVariables  true when the shortcut takes input
WFWorkflowTypes                      [] or e.g. ["QuickActions", "MenuBar"]
WFWorkflowIcon                       {WFWorkflowIconStartColor: int, WFWorkflowIconGlyphNumber: int}
WFWorkflowClientVersion, WFWorkflowMinimumClientVersion(String), WFWorkflowImportQuestions
```

On import, Shortcuts rewrites `WFWorkflowClientVersion` (to `5037.0.19` on 10.0) and adds
`WFQuickActionSurfaces` and `WFWorkflowHasOutputFallback`.

Each action's parameters carry a `UUID`. Other actions use it to refer to that action's
output.

## Variables

```
Shortcut Input, as a whole parameter:
  {"Value": {"Type": "ExtensionInput"}, "WFSerializationType": "WFTextTokenAttachment"}
Output of an earlier action:
  {"Value": {"Type": "ActionOutput", "OutputUUID": "<uuid>", "OutputName": "Count"},
   "WFSerializationType": "WFTextTokenAttachment"}
Inside a text field (e.g. Stop and Output's WFOutput): a token string, U+FFFC marks the slot
  {"Value": {"string": "￼", "attachmentsByRange": {"{0, 1}": <attachment Value>}},
   "WFSerializationType": "WFTextTokenString"}
Named variable: {"Type": "Variable", "VariableName": "x"}
```

## Actions verified on Shortcuts 10.0

These were generated with `sc-build.py`, imported, run, and checked.

| Identifier (`is.workflow.actions.` +) | Parameters | Result |
|---|---|---|
| `image.resize` | `WFImage` (attachment), `WFImageResizeWidth` (string), optional `WFImageResizeHeight` | aspect kept when only width is set |
| `count` | `Input` (attachment), `WFCountType`: `Words` (verified; other values follow the editor's menu labels in English) | number |
| `getitemfromlist` | `WFInput`, `WFItemSpecifier` (`Item At Index`, `First Item`, …), `WFItemIndex` | out-of-range index: exit 1 |
| `output` (Stop and Output) | `WFOutput` (token string) | makes `-o`/stdout get the value |

**Not working as generated:** `text.changecase` with `{"WFCaseType": "UPPERCASE", "text": <token string>}`
imports and then hangs when run. Some required parameter is evidently unset or
misnamed. Don't generate it; ask the user to build it by hand.

To learn an action's real parameter names, have the user build a one-action shortcut
in the editor and export it, then run `sc-decode.py --json` on it. That's the reliable
source. Third-party listings of identifiers go stale between releases.
