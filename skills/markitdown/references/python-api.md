# markitdown Python API and cloud options

Verified against markitdown 0.1.8. Load this when conversion is part of a Python program,
or when the user asks for LLM image captions, Azure OCR, or plugins.

## Basics

```python
from markitdown import MarkItDown

md = MarkItDown()                     # enable_plugins=False by default
result = md.convert("report.pdf")     # local path, http(s)/file/data URI, or binary stream
result.markdown                       # Markdown string; .text_content is an alias
result.title                          # detected title or None
str(result)                           # same as .markdown
```

Specific entry points, when you already know the source kind:

| Method | Input |
|--------|-------|
| `convert_local(path)` | File on disk |
| `convert_stream(fh, stream_info=...)` | Binary file-like object (`open(..., "rb")`, `io.BytesIO`) |
| `convert_uri(uri)` | `file:`, `data:`, `http(s):` URI |
| `convert_response(resp)` | A `requests.Response` you fetched yourself |

Streams carry no filename, so pass a hint — detection is usually right without one, but
a hint removes the guesswork:

```python
from markitdown import MarkItDown, StreamInfo

with open("upload.bin", "rb") as fh:
    result = MarkItDown().convert_stream(fh, stream_info=StreamInfo(extension=".docx"))
```

`StreamInfo` fields: `extension` (with the dot), `mimetype`, `charset`, `filename`, `url`.
The old `file_extension=` / `url=` keyword arguments are deprecated.

Per-call options go as keyword arguments to `convert*()`:

- `keep_data_uris=True` — keep inline base64 images instead of truncating them.
- `style_map="..."` — mammoth style map for `.docx` (custom Word styles → headings).

## Errors

All inherit from `MarkItDownException`:

| Exception | Meaning | Typical response |
|-----------|---------|------------------|
| `UnsupportedFormatException` | No converter accepts the file (e.g. legacy `.doc`) | Skip and report, or pre-convert |
| `MissingDependencyException` | A converter needs an extra that isn't installed | Install `markitdown[<extra>]` or `[all]` |
| `FileConversionException` | A converter tried and failed (corrupt/encrypted file) | Report per file; `.attempts` lists what was tried |

A batch pipeline should catch these per file and keep going, then report failures —
and should also treat an empty `result.markdown.strip()` as a failure, since image-only
input converts "successfully" to nothing:

```python
from pathlib import Path
from markitdown import MarkItDown, MarkItDownException

md = MarkItDown()
for path in sorted(Path("inbox").rglob("*")):
    if not path.is_file():
        continue
    try:
        text = md.convert(str(path)).markdown
    except MarkItDownException as exc:
        print(f"FAILED {path}: {type(exc).__name__}")
        continue
    if not text.strip():
        print(f"EMPTY  {path} (image-only? needs OCR)")
        continue
    path.with_name(path.name + ".md").write_text(text, encoding="utf-8")
```

## LLM image captions

Images otherwise yield only EXIF metadata. With an OpenAI-compatible client, markitdown
appends a `# Description:` section (also used for images inside `.pptx`):

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(llm_client=OpenAI(), llm_model="gpt-4o",
                llm_prompt="Transcribe any visible text, then describe the image.")
result = md.convert("diagram.png")
```

This calls a paid API and uploads the image — only on explicit request, with
`OPENAI_API_KEY` in the environment. Any client exposing
`client.chat.completions.create` works, so OpenAI-compatible gateways are fine.

EXIF extraction needs the `exiftool` binary on PATH (or `exiftool_path=` /
`EXIFTOOL_PATH`); without it, images convert to an empty string.

## Azure Document Intelligence (cloud OCR, layout)

Best for scanned or layout-heavy PDFs. Needs `markitdown[az-doc-intel]` and Azure
credentials (`DefaultAzureCredential`, or `AZURE_API_KEY`).

```bash
markitdown scan.pdf -d -e "https://<resource>.cognitiveservices.azure.com/"
# or set MARKITDOWN_DOCINTEL_ENDPOINT and pass just -d
```

```python
md = MarkItDown(docintel_endpoint="https://<resource>.cognitiveservices.azure.com/")
```

## Azure Content Understanding

Newer Azure service that also handles images, audio and video. Needs
`markitdown[az-content-understanding]`.

```bash
markitdown clip.mp4 --use-cu --cu-endpoint "https://<resource>.services.ai.azure.com/"
# --cu-analyzer ID      pick an analyzer (auto-selected by file type otherwise)
# --cu-file-types pdf,jpeg   route only these types to Azure; the rest stay local
# MARKITDOWN_CU_ENDPOINT can replace --cu-endpoint
```

Both Azure routes upload the document — get the user's go-ahead first.

## Plugins

Third-party converters, found via the `#markitdown-plugin` GitHub hashtag. None ship by
default. `markitdown --list-plugins` shows installed ones; enable with `-p` on the CLI or
`MarkItDown(enable_plugins=True)`. Custom converters can also be registered in-process
with `md.register_converter(MyConverter())` (subclass `DocumentConverter`, implement
`accepts()` and `convert()`).
