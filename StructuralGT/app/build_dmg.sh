#!/bin/bash

APP_NAME="StructuralGT"
APP_PATH="dist/StructuralGT.app"
DMG_PATH="dist/dmg/StructuralGT.dmg"

mkdir -p "dist/dmg"

create-dmg \
    --volname "$APP_NAME" \
    --volicon "src/view/resources/icons/StructuralGT.icns" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "StructuralGT.app" 200 190 \
    --hide-extension "StructuralGT.app" \
    --app-drop-link 600 185 \
    "$DMG_PATH" \
    "$APP_PATH"

echo "DMG file created successfully at $DMG_PATH"
