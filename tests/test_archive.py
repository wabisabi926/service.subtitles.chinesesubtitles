# -*- coding: utf-8 -*-
"""Offline tests for the zip extractor and GBK filename recovery."""
import io
import os
import struct
import sys
import tempfile
import zipfile

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
lib_dir = os.path.join(base_dir, "resources", "lib")
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

from core._gbk_codec import decode_gbk, fix_zip_filename
from core.archive import _unzip, save_and_extract


def test_decode_gbk_basic():
    assert decode_gbk(b'\xd6\xd0\xce\xc4') == '中文'
    assert decode_gbk(b'\xd7\xd6\xc4\xbb') == '字幕'


def test_decode_gbk_ascii():
    assert decode_gbk(b'hello') == 'hello'


def test_decode_gbk_mixed():
    assert decode_gbk(b'\xd6\xd0\xce\xc4.srt') == '中文.srt'


def test_fix_zip_filename_ascii():
    assert fix_zip_filename('subtitle.srt') == 'subtitle.srt'


def test_fix_zip_filename_utf8_passthrough():
    assert fix_zip_filename('中文字幕.srt') == '中文字幕.srt'


def test_fix_zip_filename_garbled():
    # zipfile decodes GBK bytes as cp437 when the UTF-8 flag is missing
    garbled = '中文字幕.srt'.encode('gbk').decode('cp437')
    assert fix_zip_filename(garbled) == '中文字幕.srt'


def _create_zip_with_gbk_filename(zip_path, filename_gbk_bytes, content=b'fake subtitle'):
    """Create a ZIP with a raw GBK filename (no UTF-8 flag)."""
    with open(zip_path, 'wb') as f:
        fn_len = len(filename_gbk_bytes)
        crc = zipfile.crc32(content) & 0xFFFFFFFF
        local_header = struct.pack(
            '<4sHHHHHIIIHH',
            b'PK\x03\x04', 20, 0, 0, 0, 0, crc,
            len(content), len(content), fn_len, 0)
        f.write(local_header)
        f.write(filename_gbk_bytes)
        f.write(content)

        offset = 0
        cd_header = struct.pack(
            '<4sHHHHHHIIIHHHHHII',
            b'PK\x01\x02', 20, 20, 0, 0, 0, 0, crc,
            len(content), len(content), fn_len, 0, 0, 0, 0, 0, offset)
        cd_offset = f.tell()
        f.write(cd_header)
        f.write(filename_gbk_bytes)

        cd_size = f.tell() - cd_offset
        f.write(struct.pack('<4sHHHHIIH', b'PK\x05\x06', 0, 0, 1, 1, cd_size, cd_offset, 0))


def test_unzip_recovers_cjk_filename():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'test.zip')
        gbk_name = '中文字幕.srt'.encode('gbk')
        _create_zip_with_gbk_filename(zip_path, gbk_name, b'1\n00:00:01,000 --> 00:00:02,000\nHello')
        entries = dict(_unzip(zip_path))
        assert list(entries) == ['中文字幕.srt']
        assert os.path.exists(entries['中文字幕.srt'])


def test_unzip_lists_but_skips_non_subtitles():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'test.zip')
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('readme.txt', 'not a subtitle')
        assert dict(_unzip(zip_path)) == {'readme.txt': None}
        assert not os.path.exists(zip_path + '_extracted')


def test_save_and_extract_uses_the_backend_listing():
    with tempfile.TemporaryDirectory() as tmpdir:
        listing = [('readme.txt', 'rar://p/readme.txt'), ('ep01.srt', 'rar://p/ep01.srt'),
                   ('ep01.srt', 'rar://p/Subs/ep01.srt'), ('._ep01.srt', 'rar://p/__MACOSX/._ep01.srt')]
        result = save_and_extract(tmpdir, 'pack.rar', b'Rar!', backend=lambda path: listing)
        assert (result.files, result.paths) == (['ep01.srt'], ['rar://p/ep01.srt'])
        result = save_and_extract(tmpdir, 'pack.rar', b'Rar!', backend=lambda path: 1 / 0)
        assert (result.status, result.entries) == ('invalid', [])
        assert save_and_extract(tmpdir, 'pack.rar', b'Rar!').status == 'invalid'


def test_save_and_extract_reports_archive_contents():
    with tempfile.TemporaryDirectory() as tmpdir:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('share.doc', 'pan link')
            zf.writestr('readme.txt', 'noise')
        result = save_and_extract(tmpdir, 'pack.zip', buf.getvalue())
        assert result.status == 'invalid' and result.entries == ['share.doc', 'readme.txt']
        with zipfile.ZipFile(buf, 'a') as zf:
            zf.writestr('Movie.srt', '1\n')
        result = save_and_extract(tmpdir, 'pack.zip', buf.getvalue())
        assert result.status == 'ok' and result.files == ['Movie.srt']


def test_save_and_extract_keeps_the_first_of_duplicate_names():
    with tempfile.TemporaryDirectory() as tmpdir:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('a/Movie.srt', 'first')
            zf.writestr('b/Movie.srt', 'second')
            zf.writestr('__MACOSX/._Movie.srt', 'resource fork')
        result = save_and_extract(tmpdir, 'pack.zip', buf.getvalue())
        assert result.files == ['Movie.srt']
        with open(result.paths[0]) as f:
            assert f.read() == 'first'


def test_unzip_keeps_vobsub_sidecar():
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'test.zip')
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('pack.chs.sub', b'\x00\x00fake vobsub')
            zf.writestr('pack.chs.idx', b'VobSub index')
            zf.writestr('readme.txt', 'noise')
        entries = dict(_unzip(zip_path))
        assert list(entries) == ['pack.chs.sub', 'pack.chs.idx', 'readme.txt']
        assert os.path.exists(entries['pack.chs.idx']) and entries['readme.txt'] is None
