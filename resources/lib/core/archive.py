# -*- coding: utf-8 -*-
"""Subtitle archive handling: zip natively (with GBK name recovery), others via backend."""
import os
import zipfile

from ._gbk_codec import fix_zip_filename
from .models import DownloadResult

SUBTITLE_EXTS = (".srt", ".sub", ".smi", ".ssa", ".ass", ".sup", ".vtt")
# vobsub index files ride along with their .sub (extracted but never
# returned as pickable subtitles)
SUBTITLE_SIDECAR_EXTS = (".idx",)
ARCHIVE_EXTS = (".zip", ".7z", ".tar", ".bz2", ".rar", ".gz", ".xz", ".iso", ".tgz", ".tbz2", ".cbr")


def _unzip(path):
    """(name, path) of every zip entry in archive order. Names recover GBK
    mojibake; subtitles and sidecars are extracted beside the archive in
    the zip's own layout, anything else gets no path."""
    target = path + "_extracted"
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            # Without the UTF-8 flag zipfile decodes names as cp437
            name = info.filename if info.flag_bits & 0x800 else fix_zip_filename(info.filename)
            name = os.path.basename(name)
            wanted = name.lower().endswith(SUBTITLE_EXTS + SUBTITLE_SIDECAR_EXTS)
            yield name, zf.extract(info, target) if wanted else None


def save_and_extract(dest, filename, data, backend=None):
    """Save downloaded bytes and extract when needed; never raises on bad content.

    zip is handled natively; any other archive is listed by backend(path)
    -> [(name, path)] when the host provides one (Kodi: vfs.rar / vfs.libarchive).
    """
    filename = os.path.basename(filename)
    path = os.path.join(dest, filename)
    with open(path, "wb") as f:
        f.write(data)
    if filename.lower().endswith(SUBTITLE_EXTS):
        return DownloadResult("ok", files=[filename], display_names=[filename], paths=[path])
    if not filename.lower().endswith(ARCHIVE_EXTS):
        return DownloadResult("invalid")
    entries = {}  # the first of each name wins; macOS "._" resource forks are noise
    try:
        found = _unzip(path) if filename.lower().endswith(".zip") else backend(path) if backend else ()
        for name, entry_path in found:
            if not name.startswith("._"):
                entries.setdefault(name, entry_path)
    except Exception:
        pass
    files = [n for n in entries if n.lower().endswith(SUBTITLE_EXTS)]
    if not files:
        return DownloadResult("invalid", entries=list(entries))
    return DownloadResult("ok", files=files, display_names=shorten_names(files),
                          paths=[entries[n] for n in files])


def shorten_names(names):
    """Trim the longest common prefix (up to a dot) so picker entries stay readable."""
    if len(names) < 2:
        return list(names)
    dot = os.path.commonprefix(names).rfind(".") + 1
    return [n[dot:] for n in names]
