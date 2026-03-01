#!/usr/bin/env bash

echo "🗑️ Starting Uninstallation for BiteCLI..."

# 1. Remove Environment and DB
INSTALL_DIR="$HOME/.bitecli"
if [ -d "$INSTALL_DIR" ]; then
    echo "🗑️ Removing BiteCLI directory ($INSTALL_DIR)..."
    rm -rf "$INSTALL_DIR"
else
    echo "✅ BiteCLI directory not found."
fi

# 2. Remove from cron
if crontab -l 2>/dev/null | grep -q "bitecli fetch"; then
    echo "🗑️ Removing cron job..."
    (crontab -l 2>/dev/null | grep -v "bitecli fetch") | crontab -
    echo "✅ Cron job removed."
else
    echo "✅ No cron job found."
fi

# 3. Inform about shell hook
SHELL_NAME=$(basename "$SHELL")
RC_FILE=""

if [[ "$SHELL_NAME" == *"zsh"* ]]; then
    RC_FILE="$HOME/.zshrc"
elif [[ "$SHELL_NAME" == *"bash"* ]]; then
    RC_FILE="$HOME/.bashrc"
else
    RC_FILE="$HOME/.profile"
fi

if grep -q "BITECLI\|bitecli serve --hook" "$RC_FILE" 2>/dev/null; then
    echo "🗑️ Removing BiteCLI entries from $RC_FILE..."
    grep -v "# BiteCLI" "$RC_FILE" | grep -v "bitecli" > "${RC_FILE}.tmp" && mv "${RC_FILE}.tmp" "$RC_FILE"
    echo "✅ BiteCLI entries removed."
else
    echo "✅ No BiteCLI entries found in $RC_FILE."
fi

# 4. Remove global pip/pipx install if present
BITECLI_CMD=$(command -v bitecli 2>/dev/null || true)
if [ -n "$BITECLI_CMD" ]; then
    echo "🗑️ Found 'bitecli' at $BITECLI_CMD. Attempting to remove..."
    REMOVED=false

    if command -v pipx &> /dev/null && pipx list 2>/dev/null | grep -q "bitecli"; then
        pipx uninstall bitecli && REMOVED=true
    fi

    if [ "$REMOVED" = false ] && pip uninstall -y bitecli 2>/dev/null; then
        REMOVED=true
    fi

    if [ "$REMOVED" = true ]; then
        echo "✅ Global 'bitecli' package removed."
    else
        echo "⚠️  Could not auto-remove 'bitecli'. Run manually: pip uninstall -y bitecli"
    fi
fi

echo ""
echo "🎉 Uninstallation Complete. All files, cache, cron jobs, and terminal hooks have been deleted."
