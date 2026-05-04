#!/usr/bin/env python3
import hashlib
import html
import os
import shutil
import sys
import zipfile
from pathlib import Path

import markdown

ADDON_ID = "service.subtitles.chinesesubtitles"
REPO_ID = "repository.chinesesubtitles"
DIST_DIR = Path("dist")
SITE_DIR = DIST_DIR / "kodi-repo"
ZIPS_DIR = SITE_DIR / "repo" / "zips"


def read_addon_version(addon_xml):
    import xml.etree.ElementTree as ET

    root = ET.parse(addon_xml).getroot()
    return root.attrib["version"]


def clean_site_dir():
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    ZIPS_DIR.mkdir(parents=True)


def copy_addon_zip():
    version = read_addon_version("addon.xml")
    zip_name = f"{ADDON_ID}-{version}.zip"
    source = DIST_DIR / zip_name
    if not source.exists():
        raise FileNotFoundError(f"Missing add-on zip: {source}")

    target_dir = ZIPS_DIR / ADDON_ID
    target_dir.mkdir(parents=True)
    shutil.copy2(source, target_dir / zip_name)


def build_repository_zip():
    version = read_addon_version(Path(REPO_ID) / "addon.xml")
    zip_name = f"{REPO_ID}-{version}.zip"
    target_dir = ZIPS_DIR / REPO_ID
    target_dir.mkdir(parents=True)

    repo_zip = target_dir / zip_name
    with zipfile.ZipFile(repo_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(Path(REPO_ID).rglob("*")):
            if path.is_file():
                archive.write(path, path.as_posix())
    shutil.copy2(repo_zip, SITE_DIR / zip_name)


def addon_xml_body(path):
    content = Path(path).read_text(encoding="utf-8-sig").strip()
    if content.startswith("<?xml"):
        content = content.split("?>", 1)[1].strip()
    return content


def write_addons_xml():
    body = "\n".join(
        [
            addon_xml_body("addon.xml"),
            addon_xml_body(Path(REPO_ID) / "addon.xml"),
        ]
    )
    content = '<?xml version="1.0" encoding="UTF-8"?>\n<addons>\n%s\n</addons>\n' % body
    addons_xml = ZIPS_DIR / "addons.xml"
    addons_xml.write_text(content, encoding="utf-8")

    digest = hashlib.md5(addons_xml.read_bytes()).hexdigest()
    (ZIPS_DIR / "addons.xml.md5").write_text(digest, encoding="utf-8")


def write_index_html():
    readme = Path("README.md").read_text(encoding="utf-8")
    body = markdown.markdown(readme, extensions=["fenced_code", "nl2br", "sane_lists"])

    repo_version = read_addon_version(Path(REPO_ID) / "addon.xml")
    addon_version = read_addon_version("addon.xml")
    repo_zip = f"{REPO_ID}-{repo_version}.zip"
    addon_zip = f"repo/zips/{ADDON_ID}/{ADDON_ID}-{addon_version}.zip"
    downloads = """<h2>下载</h2>
<ul>
  <li><a href="{repo_zip}">{repo_zip}</a></li>
  <li><a href="{addon_zip}">{addon_name}</a></li>
  <li><a href="repo/zips/addons.xml">addons.xml</a></li>
</ul>
""".format(
        repo_zip=html.escape(repo_zip),
        addon_zip=html.escape(addon_zip),
        addon_name=html.escape(f"{ADDON_ID}-{addon_version}.zip"),
    )

    content = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChineseSub</title>
</head>
<body>
%s
%s
</body>
</html>
""" % (body, downloads)
    (SITE_DIR / "index.html").write_text(content, encoding="utf-8")


def main():
    os.chdir(Path(__file__).resolve().parents[1])
    clean_site_dir()
    copy_addon_zip()
    build_repository_zip()
    write_addons_xml()
    write_index_html()
    print(f"Built Kodi repository at {SITE_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Failed to build Kodi repository: {exc}", file=sys.stderr)
        sys.exit(1)
