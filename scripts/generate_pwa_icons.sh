#!/bin/bash
#
# PWA Icon Generation Script
#
# This script generates PWA icons from a source icon using ImageMagick.
#
# Requirements:
#   - ImageMagick (convert command)
#   - A source icon file at 512x512 or larger
#
# Usage:
#   ./generate_pwa_icons.sh [source_icon]
#
# If no source icon is provided, it will generate a simple placeholder icon.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_PUBLIC="$PROJECT_ROOT/frontend/public"
ICONS_DIR="$FRONTEND_PUBLIC/icons"

# Create icons directory if it doesn't exist
mkdir -p "$ICONS_DIR"

# Source icon - use provided or create a placeholder
SOURCE_ICON="${1:-}"

# If no source icon provided, create a simple placeholder
if [ -z "$SOURCE_ICON" ] || [ ! -f "$SOURCE_ICON" ]; then
    echo "No source icon provided or file not found. Creating placeholder icon..."
    SOURCE_ICON="/tmp/write_agent_source.png"

    # Create a simple gradient placeholder icon
    convert -size 512x512 gradient:#667eea-#764ba2 \
            -gravity center \
            -pointsize 120 -fill white -annotate +0+0 "WA" \
            "$SOURCE_ICON"
fi

echo "Generating PWA icons from: $SOURCE_ICON"

# Define icon sizes for standard PWA icons
SIZES=(
    "72"      # Android 1x
    "96"      # Android 1.5x
    "128"     # Android 2x
    "144"     # Android 3x
    "152"     # iOS iPad
    "192"     # Android 4x, Favicon 192x192
    "384"     # Android 6x
    "512"     # Android 8x, PWA standard
)

# Generate standard icons
for size in "${SIZES[@]}"; do
    output_file="$ICONS_DIR/icon-${size}x${size}.png"
    echo "Generating $output_file..."
    convert "$SOURCE_ICON" -resize "${size}x${size}" "$output_file"
done

# Generate maskable icon (with safe padding)
echo "Generating maskable icon..."
convert "$SOURCE_ICON" \
        -resize 512x512 \
        -gravity center \
        -extent 512x512 \
        "$ICONS_DIR/maskable-icon.png"

# Generate favicon (16x16 and 32x32 for browsers)
echo "Generating favicons..."
convert "$SOURCE_ICON" -resize 16x16 "$FRONTEND_PUBLIC/favicon-16x16.png"
convert "$SOURCE_ICON" -resize 32x32 "$FRONTEND_PUBLIC/favicon-32x32.png"
convert "$SOURCE_ICON" -resize 48x48 "$FRONTEND_PUBLIC/favicon.ico"

# Generate Apple Touch Icon
echo "Generating Apple Touch Icon..."
convert "$SOURCE_ICON" -resize 180x180 "$FRONTEND_PUBLIC/apple-touch-icon.png"

# Generate screenshots (for store listings if needed)
# These are simple placeholders - real screenshots should be captured from the app
echo "Generating screenshot placeholders..."
convert -size 540x720 gradient:#f7fafc-#edf2f7 \
        -gravity center \
        -pointsize 24 -fill #2d3748 \
        -annotate +0+0 "Write-Agent Screenshot 1" \
        "$ICONS_DIR/screenshot1.png"

convert -size 540x720 gradient:#f7fafc-#edf2f7 \
        -gravity center \
        -pointsize 24 -fill #2d3748 \
        -annotate +0+0 "Write-Agent Screenshot 2" \
        "$ICONS_DIR/screenshot2.png"

echo ""
echo "PWA icons generated successfully!"
echo "Icons directory: $ICONS_DIR"
echo ""
echo "Generated files:"
ls -la "$ICONS_DIR/"
echo ""
echo "Generated favicons:"
ls -la "$FRONTEND_PUBLIC/"*.png "$FRONTEND_PUBLIC/"*.ico 2>/dev/null || true
