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

if grep -q "bitecli serve --hook" "$RC_FILE" 2>/dev/null; then
    echo "🗑️ Removing BiteCLI hook from $RC_FILE..."
    grep -v "# BiteCLI Terminal Hook" "$RC_FILE" | grep -v "bitecli serve --hook" > "${RC_FILE}.tmp" && mv "${RC_FILE}.tmp" "$RC_FILE"
    echo "✅ Hook removed."
else
    echo "✅ No hook found in $RC_FILE."
fi

echo ""
echo "🎉 Uninstallation Complete. All files, cache, cron jobs, and terminal hooks have been deleted."

if command -v bitecli &> /dev/null; then
    echo ""
    echo "⚠️ WARNING: The 'bitecli' command is still available in your terminal."
    echo "   This usually means you manually installed it globally with pip or pipx."
    echo "   To completely remove it, run: pip uninstall -y bitecli"
fi
