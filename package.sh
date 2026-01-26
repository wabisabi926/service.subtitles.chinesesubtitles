#!/bin/bash
# Packaging script for Kodi addon
# Creates a zip file ready for Kodi installation

set -euo pipefail

ADDON_ID="service.subtitles.chinesesubtitles"
# The XML declaration also contains version="1.0", so only extract the addon's version attr.
VERSION=$(sed -n 's/.*<addon[^>]*version="\([^"]*\)".*/\1/p' addon.xml | head -1)
if [[ -z "${VERSION}" ]]; then
  echo "Failed to read version from addon.xml" >&2
  exit 1
fi
OUTPUT_DIR="dist"
OUTPUT_FILE="${OUTPUT_DIR}/${ADDON_ID}-${VERSION}.zip"

echo "Packaging ${ADDON_ID} version ${VERSION}..."

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Clean previous builds
rm -f "${OUTPUT_DIR}/${ADDON_ID}"*.zip

# Create a temporary directory for packaging
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="${TEMP_DIR}/${ADDON_ID}"

mkdir -p "${PACKAGE_DIR}"

# Copy addon files (excluding dev/test files)
cp addon.xml "${PACKAGE_DIR}/"
cp -r resources "${PACKAGE_DIR}/"

# Remove __pycache__ and .pyc files
find "${PACKAGE_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${PACKAGE_DIR}" -name "*.pyc" -delete 2>/dev/null || true

# Create ZIP
cd "${TEMP_DIR}"
zip -r -X -q "${ADDON_ID}.zip" "${ADDON_ID}"
zip -T "${ADDON_ID}.zip" >/dev/null
mv "${ADDON_ID}.zip" "${OLDPWD}/${OUTPUT_FILE}"

# Cleanup
rm -rf "${TEMP_DIR}"

echo "Successfully created: ${OUTPUT_FILE}"
echo "File size: $(ls -lh "${OLDPWD}/${OUTPUT_FILE}" | awk '{print $5}')"
