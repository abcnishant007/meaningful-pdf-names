#!/bin/bash
set -euo pipefail

APP_NAME="Meaningful PDF Names"
VOL_NAME="Meaningful PDF Names"
DMG_NAME="meaningful-pdf-names-mac.dmg"
BUILD_ROOT="$(pwd)/mpn-dmg-build"
PKG_DIR="$BUILD_ROOT/$APP_NAME"
WORKFLOW_NAME="$APP_NAME.workflow"
WORKFLOW_DIR="$PKG_DIR/$WORKFLOW_NAME"

echo "==> Cleaning old build..."
rm -rf "$BUILD_ROOT" "$DMG_NAME"
mkdir -p "$PKG_DIR"

###############################################################################
# 1. Create Automator Quick Action (.workflow) that wraps `mpn`
###############################################################################
echo "==> Creating Automator Quick Action workflow..."

mkdir -p "$WORKFLOW_DIR/Contents"

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
    <key>AMApplicationBuild</key>
    <string>2.10</string>
    <key>AMApplicationVersion</key>
    <string>2.10</string>
    <key>AMType</key>
    <string>Action</string>
    <key>NSHumanReadableDescription</key>
    <string>Run Meaningful PDF Names (mpn) on selected files or folders.</string>
</dict>
</plist>
EOF

# document.wflow: minimal Automator Service (Quick Action) with Run Shell Script
# It receives files/folders in Finder and runs our zsh wrapper that invokes `mpn`.
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
            <key>AMShellScriptActionShell</key>
            <string>/bin/zsh</string>
            <key>AMShellScriptActionInput</key>
            <string>arguments</string>
            <key>AMShellScriptActionScript</key>
            <string><![CDATA[
# Wrapper to locate and run `mpn` on selected files/folders.
# No browser, no daemon, no UI.

CANDIDATES=(
  "$HOME/.local/bin/mpn"
  "/usr/local/bin/mpn"
  "/opt/homebrew/bin/mpn"
)

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
    'display notification "Meaningful PDF Names (mpn) is not installed. Please run the installer from the DMG." with title "Meaningful PDF Names"'
  exit 1
fi

if [ "$#" -eq 0 ]; then
  exit 0
fi

"$MPN" "$@"
]]></string>
            <key>AMActionEnabled</key>
            <true/>
        </dict>
    </array>
</dict>
</plist>
EOF

###############################################################################
# 2. Create installer command that:
#    - ensures python3
#    - installs pipx (user)
#    - installs/updates meaningful-pdf-names via pipx
#    - installs the Quick Action into ~/Library/Services
###############################################################################
echo "==> Creating installer script..."

cat > "$PKG_DIR/Install Meaningful PDF Names.command" <<'EOF'
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW_SRC="$SCRIPT_DIR/Meaningful PDF Names.workflow"
SERVICES_DIR="$HOME/Library/Services"

if [ ! -d "$WORKFLOW_SRC" ]; then
  /usr/bin/osascript -e \
    'display notification "Installer is missing the workflow bundle." with title "Meaningful PDF Names"'
  exit 1
fi

# 1. Check python3
if ! command -v python3 >/dev/null 2>&1; then
  /usr/bin/osascript -e \
    'display notification "Python 3 not found. Please install Command Line Tools (xcode-select --install) and rerun the installer." with title "Meaningful PDF Names"'
  exit 1
fi

# 2. Ensure pipx is available
if ! python3 -m pipx --version >/dev/null 2>&1; then
  # Try installing pipx locally for the user
  if ! python3 -m pip install --user pipx >/dev/null 2>&1; then
    /usr/bin/osascript -e \
      'display notification "Failed to install pipx. Please install pipx manually and rerun." with title "Meaningful PDF Names"'
    exit 1
  fi
fi

# 3. Ensure pipx's bin dir is on PATH for this script run
# Common pipx location
export PATH="$HOME/.local/bin:$PATH"

# 4. Install or upgrade meaningful-pdf-names via pipx
if ! python3 -m pipx install --force meaningful-pdf-names >/dev/null 2>&1; then
  /usr/bin/osascript -e \
    'display notification "Failed to install meaningful-pdf-names via pipx." with title "Meaningful PDF Names"'
  exit 1
fi

# 5. Install the Quick Action workflow
mkdir -p "$SERVICES_DIR"
cp -R "$WORKFLOW_SRC" "$SERVICES_DIR/"

# 6. Notify success
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
echo "Distribute this DMG. End users just:"
echo "  1) Open the DMG"
echo "  2) Run 'Install Meaningful PDF Names.command'"
echo "  3) Right-click PDFs/folders → Quick Actions → \"$APP_NAME\""

