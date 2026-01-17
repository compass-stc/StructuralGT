#!/bin/bash

APP_NAME="SGT"
APP_PATH="dist/SGT.app"
DMG_PATH="dist/dmg/SGT.dmg"

mkdir -p "dist/dmg"

create-dmg \
    --volname "$APP_NAME" \
    --volicon "src/view/resources/icons/StructuralGT.icns" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "SGT.app" 200 190 \
    --hide-extension "SGT.app" \
    --app-drop-link 600 185 \
    "$DMG_PATH" \
    "$APP_PATH"

echo "DMG file created successfully at $DMG_PATH"
