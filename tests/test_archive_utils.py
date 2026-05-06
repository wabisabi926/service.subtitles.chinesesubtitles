import os
import sys
import struct
import tempfile
import zipfile

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
lib_dir = os.path.join(base_dir, "resources", "lib")
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

from _gbk_codec import decode_gbk, fix_zip_filename


def test_decode_gbk_basic():
    assert decode_gbk(b'\xd6\xd0\xce\xc4') == '中文'
    assert decode_gbk(b'\xd7\xd6\xc4\xbb') == '字幕'


def test_decode_gbk_ascii():
    assert decode_gbk(b'hello') == 'hello'


def test_decode_gbk_mixed():
    result = decode_gbk(b'\xd6\xd0\xce\xc4.srt')
    assert result == '中文.srt'


def test_fix_zip_filename_ascii():
    assert fix_zip_filename('subtitle.srt') == 'subtitle.srt'


def test_fix_zip_filename_utf8_passthrough():
    assert fix_zip_filename('中文字幕.srt') == '中文字幕.srt'


def test_fix_zip_filename_garbled():
    # Simulate what zipfile does: GBK bytes decoded as cp437
    gbk_bytes = '中文字幕.srt'.encode('gbk')
    garbled = gbk_bytes.decode('cp437')
    result = fix_zip_filename(garbled)
    assert result == '中文字幕.srt'


def _create_zip_with_gbk_filename(zip_path, filename_gbk_bytes, content=b'fake subtitle'):
    """Create a ZIP file with raw GBK-encoded filename (no UTF-8 flag)."""
    with open(zip_path, 'wb') as f:
        # Local file header
        fn_len = len(filename_gbk_bytes)
        crc = zipfile.crc32(content) & 0xFFFFFFFF
        local_header = struct.pack(
            '<4sHHHHHIIIHH',
            b'PK\x03\x04',  # signature
            20,              # version needed
            0,               # flags (no UTF-8 flag)
            0,               # compression (stored)
            0,               # mod time
            0,               # mod date
            crc,             # crc32
            len(content),    # compressed size
            len(content),    # uncompressed size
            fn_len,          # filename length
            0,               # extra field length
        )
        f.write(local_header)
        f.write(filename_gbk_bytes)
        f.write(content)

        # Central directory
        offset = 0
        cd_header = struct.pack(
            '<4sHHHHHHIIIHHHHHII',
            b'PK\x01\x02',  # signature
            20,              # version made by
            20,              # version needed
            0,               # flags
            0,               # compression
            0,               # mod time
            0,               # mod date
            crc,             # crc32
            len(content),    # compressed size
            len(content),    # uncompressed size
            fn_len,          # filename length
            0,               # extra field length
            0,               # comment length
            0,               # disk number start
            0,               # internal attrs
            0,               # external attrs
            offset,          # local header offset
        )
        cd_offset = f.tell()
        f.write(cd_header)
        f.write(filename_gbk_bytes)

        # End of central directory
        cd_size = f.tell() - cd_offset
        eocd = struct.pack(
            '<4sHHHHIIH',
            b'PK\x05\x06',  # signature
            0,               # disk number
            0,               # disk with cd
            1,               # entries on disk
            1,               # total entries
            cd_size,         # cd size
            cd_offset,       # cd offset
            0,               # comment length
        )
        f.write(eocd)


def test_unpack_zip_cjk_filename():
    from unittest.mock import MagicMock
    sys.modules.setdefault('xbmcvfs', MagicMock())
    import archive_utils

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'test.zip')
        gbk_name = '中文字幕.srt'.encode('gbk')
        _create_zip_with_gbk_filename(zip_path, gbk_name, b'1\n00:00:01,000 --> 00:00:02,000\nHello')

        class Logger:
            def log(self, *args, **kwargs):
                pass

        extract_dir, files = archive_utils._unpack_zip(zip_path, Logger())
        assert len(files) == 1
        assert files[0] == '中文字幕.srt'
        assert os.path.exists(os.path.join(extract_dir, '中文字幕.srt'))


if __name__ == '__main__':
    test_decode_gbk_basic()
    test_decode_gbk_ascii()
    test_decode_gbk_mixed()
    test_fix_zip_filename_ascii()
    test_fix_zip_filename_utf8_passthrough()
    test_fix_zip_filename_garbled()
    test_unpack_zip_cjk_filename()
    print("All tests passed!")
