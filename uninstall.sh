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

echo ""
echo "⚠️ ALMOST DONE!"
echo "Please manually remove the BiteCLI hook from your $RC_FILE if you added it."
echo "Simply open the file and delete the lines that look like this:"
echo "-----------------------------------"
echo "# BiteCLI Terminal Hook"
echo "~/.bitecli/venv/bin/bitecli serve --hook"
echo "-----------------------------------"
echo ""

echo "🎉 Uninstallation Complete. All files and cache have been deleted."
