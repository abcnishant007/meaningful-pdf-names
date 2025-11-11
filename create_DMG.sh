#!/bin/bash
set -euo pipefail

APP_NAME="Meaningful PDF Names"
VOL_NAME="Meaningful PDF Names"
DMG_NAME="meaningful-pdf-names-mac.dmg"

# Build root and package directory inside it
BUILD_ROOT="$(pwd)/mpn-dmg-build"
PKG_DIR="$BUILD_ROOT/$APP_NAME"

WORKFLOW_NAME="$APP_NAME.workflow"
WORKFLOW_DIR="$PKG_DIR/$WORKFLOW_NAME"

echo "==> Cleaning old build artifacts..."
rm -rf "$BUILD_ROOT" "$DMG_NAME"
mkdir -p "$PKG_DIR"

###############################################################################
# 1. Create Automator Quick Action (.workflow) that wraps `mpn`
###############################################################################
echo "==> Creating Automator Quick Action workflow..."

mkdir -p "$WORKFLOW_DIR/Contents"

# Basic Info.plist for the workflow bundle
cat > "$WORKFLOW_DIR/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleIdentifier</key>
    <string>com.meaningfulpdfnames.workflow</string>
    <key>CFBundleName</key>
    <string>Meaningful PDF Names</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>NSHumanReadableDescription</key>
    <string>Run Meaningful PDF Names (mpn) on selected files or folders.</string>
</dict>
</plist>
EOF

# document.wflow: Quick Action that receives files/folders in Finder
# and runs a zsh script that locates `mpn` and calls it with the selection.
cat > "$WORKFLOW_DIR/Contents/document.wflow" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>AMApplicationBuild</key>
    <string>2.10</string>
    <key>AMApplicationVersion</key>
    <string>2.10</string>
    <key>AMDocumentVersion</key>
    <string>2</string>
    <key>AMWorkflowType</key>
    <string>Service</string>

    <key>NSServices</key>
    <array>
        <dict>
            <key>NSMenuItem</key>
            <dict>
                <key>default</key>
                <string>Meaningful PDF Names</string>
            </dict>
            <key>NSMessage</key>
            <string>runWorkflowAsService</string>
            <key>NSReturnTypes</key>
            <array>
                <string>public.data</string>
            </array>
            <key>NSSendFileTypes</key>
            <array>
                <string>public.item</string>
            </array>
        </dict>
    </array>

    <key>AMServiceInputType</key>
    <string>public.data</string>
    <key>AMServiceOutputType</key>
    <string>public.data</string>
    <key>AMServiceRequestsUserData</key>
    <false/>
    <key>AMServiceRunsInUserDataDomain</key>
    <true/>

    <key>AMWorkflowInputProperties</key>
    <dict>
        <key>AMDefaultLocale</key>
        <string>en_US</string>
        <key>AMInputContentType</key>
        <string>AMInputContentTypeFiles</string>
    </dict>

    <key>AMWorkflowActions</key>
    <array>
        <dict>
            <key>AMActionClass</key>
            <string>AMShellScriptAction</string>
            <key>AMActionName</key>
            <string>Run Shell Script</string>
            <key>AMActionVersion</key>
            <string>2.0.3</string>
            <key>AMActionEnabled</key>
            <true/>
            <key>AMShellScriptActionShell</key>
            <string>/bin/zsh</string>
            <key>AMShellScriptActionInput</key>
            <string>arguments</string>
            <key>AMShellScriptActionScript</key>
            <string><![CDATA[
# Finder Quick Action wrapper for `mpn`

CANDIDATES=(
  "$HOME/.local/bin/mpn"
  "/usr/local/bin/mpn"
  "/opt/homebrew/bin/mpn"
)

# Try PATH as well (Automator may have a minimal env)
CMD=$(command -v mpn 2>/dev/null)
if [ -n "$CMD" ]; then
  CANDIDATES+=("$CMD")
fi

MPN=""

for c in "${CANDIDATES[@]}"; do
  if [ -n "$c" ] && [ -x "$c" ]; then
    MPN="$c"
    break
  fi
done

if [ -z "$MPN" ]; then
  /usr/bin/osascript -e \
    'display notification "Meaningful PDF Names (mpn) is not installed. Please rerun the installer." with title "Meaningful PDF Names"'
  exit 1
fi

if [ "$#" -eq 0 ]; then
  exit 0
fi

"$MPN" "$@"
]]></string>
        </dict>
    </array>
</dict>
</plist>
EOF

###############################################################################
# 2. Create installer script:
#    - checks Python 3
#    - installs pipx (user)
#    - installs/updates meaningful-pdf-names via pipx
#    - copies workflow into ~/Library/Services
#    - strips quarantine on installed workflow
#    - restarts Finder so Quick Action appears
###############################################################################
echo "==> Creating installer script..."

cat > "$PKG_DIR/Install Meaningful PDF Names.command" <<'EOF'
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW_SRC="$SCRIPT_DIR/Meaningful PDF Names.workflow"
SERVICES_DIR="$HOME/Library/Services"
TARGET_WORKFLOW="$SERVICES_DIR/Meaningful PDF Names.workflow"

# 1. Ensure bundled workflow exists
if [ ! -d "$WORKFLOW_SRC" ]; then
  /usr/bin/osascript -e \
    'display notification "Installer is missing the workflow bundle." with title "Meaningful PDF Names"'
  exit 1
fi

# 2. Ensure Python 3 is available
if ! command -v python3 >/dev/null 2>&1; then
  /usr/bin/osascript -e \
    'display notification "Python 3 not found. Please install Command Line Tools (xcode-select --install) and rerun the installer." with title "Meaningful PDF Names"'
  exit 1
fi

# 3. Ensure pipx is installed (user-local)
if ! python3 -m pipx --version >/dev/null 2>&1; then
  if ! python3 -m pip install --user pipx >/dev/null 2>&1; then
    /usr/bin/osascript -e \
      'display notification "Failed to install pipx." with title "Meaningful PDF Names"'
    exit 1
  fi
fi

# 4. Ensure pipx bin dir is in PATH for this process
export PATH="$HOME/.local/bin:$PATH"

# 5. Install or upgrade meaningful-pdf-names via pipx
if ! python3 -m pipx install --force meaningful-pdf-names >/dev/null 2>&1; then
  /usr/bin/osascript -e \
    'display notification "Failed to install meaningful-pdf-names via pipx." with title "Meaningful PDF Names"'
  exit 1
fi

# 6. Install the Quick Action workflow into user's Services
mkdir -p "$SERVICES_DIR"
rm -rf "$TARGET_WORKFLOW"
cp -R "$WORKFLOW_SRC" "$TARGET_WORKFLOW"

# 7. Remove quarantine attributes from the installed workflow so Finder trusts it
/usr/bin/xattr -dr com.apple.quarantine "$TARGET_WORKFLOW" >/dev/null 2>&1 || true

# 8. Restart Finder so the new Quick Action becomes visible immediately
/usr/bin/killall Finder >/dev/null 2>&1 || true

# 9. Notify success
/usr/bin/osascript -e \
  'display notification "Meaningful PDF Names installed. Use via Finder → Quick Actions → Meaningful PDF Names." with title "Meaningful PDF Names"'

exit 0
EOF

chmod +x "$PKG_DIR/Install Meaningful PDF Names.command"

###############################################################################
# 3. Build DMG
###############################################################################
echo "==> Building DMG: $DMG_NAME"

hdiutil create \
  -volname "$VOL_NAME" \
  -srcfolder "$PKG_DIR" \
  -ov -format UDZO \
  "$DMG_NAME"

echo "==> Done."
echo "Generated DMG: $DMG_NAME"
echo "Distribute this DMG. Users:"
echo "  1) Open the DMG"
echo "  2) Double-click 'Install Meaningful PDF Names.command' (allow via Open Anyway once if prompted)"
echo "  3) Right-click PDFs/folders → Quick Actions → 'Meaningful PDF Names'"

