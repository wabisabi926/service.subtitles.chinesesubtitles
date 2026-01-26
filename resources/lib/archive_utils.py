# -*- coding: utf-8 -*-
import os
import urllib.parse
import xbmcvfs

class _NullLogger:
    def log(self, *args, **kwargs):
        pass


def unpack(file_path, logger=None):
    """
    Get the file list from archive file.
    Supports zip, rar.
    """
    exts = (".srt", ".sub", ".ssa", ".ass", ".sup", ".vtt")
    supported_archive_exts = (".zip", ".rar", ".7z")

    logger = logger or _NullLogger()

    if not file_path.endswith(supported_archive_exts):
        logger.log("archive_utils", "Unsupported file ext: %s" % os.path.basename(file_path), 2)
        return '', []

    file_path = file_path.replace('\\', '/').rstrip('/')

    real_path = xbmcvfs.translatePath(file_path)
    archive_url = urllib.parse.quote_plus(real_path)
    ext = file_path.split('.')[-1]
    
    if ext == '7z':
        # libarchive typically uses archive://
        vfs_protocol = 'archive'
    else:
        vfs_protocol = ext
    
    vfs_url = f"{vfs_protocol}://{archive_url}"
    
    logger.log("archive_utils", "Unpacking: %s" % vfs_url)

    try:
        dirs, files = xbmcvfs.listdir(vfs_url)
        
        if '__MACOSX' in dirs:
            dirs.remove('__MACOSX')
        
        target_path = vfs_url
        if not any(f.lower().endswith(exts) for f in files) and dirs:
            target_path = os.path.join(vfs_url, dirs[0]).replace('\\', '/')
            dirs, files = xbmcvfs.listdir(target_path)

        subtitle_list = [f for f in files if f.lower().endswith(exts)]
                
        return target_path, subtitle_list
        
    except Exception as e:
        logger.log("archive_utils", "Unpack error: %s" % e, 2)
        return '', []
