#!/usr/bin/env bash
set -e

echo "🚀 Starting 1-Click Installation for BiteCLI..."

# 1. Environment Setup
INSTALL_DIR="${BITECLI_INSTALL_DIR:-$HOME/.bitecli}"
VENV_DIR="$INSTALL_DIR/venv"
CLI_BIN="$VENV_DIR/bin/bitecli"

echo "📦 Setting up isolated environment in $VENV_DIR..."
mkdir -p "$INSTALL_DIR"
python3 -m venv "$VENV_DIR"

echo "⬇️ Installing BiteCLI dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install . --quiet

# 2. Add hook to bash/zsh profile
SHELL_NAME=$(basename "$SHELL")
RC_FILE=""

if [[ "$SHELL_NAME" == *"zsh"* ]]; then
    RC_FILE="$HOME/.zshrc"
elif [[ "$SHELL_NAME" == *"bash"* ]]; then
    RC_FILE="$HOME/.bashrc"
else
    RC_FILE="$HOME/.profile"
fi

if ! grep -q "$CLI_BIN serve --hook" "$RC_FILE"; then
    echo "🔗 Adding BiteCLI hook to $RC_FILE..."
    echo "" >> "$RC_FILE"
    echo "# BiteCLI Terminal Hook" >> "$RC_FILE"
    echo "$CLI_BIN serve --hook" >> "$RC_FILE"
else
    echo "✅ BiteCLI hook already exists in $RC_FILE."
fi

# 3. Add to cron for automatic background fetching (Daily at 10 AM)
# You can change the '0 10 * * *' to '0 0 * * 0' for weekly.
CRON_CMD="0 10 * * * $CLI_BIN fetch >/dev/null 2>&1"

# Check if it's already in crontab
if crontab -l 2>/dev/null | grep -q "$CLI_BIN fetch"; then
    echo "✅ Cron job for auto-fetching already exists."
else
    echo "⏱️ Setting up daily cron job for background fetch..."
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab - || echo "⚠️ Could not set up cron job. You might need to add it manually."
    echo "   (To change the schedule to weekly, run 'crontab -e' and change '0 10 * * *' to '0 0 * * 0')"
fi

# 4. Perform the initial layout and fetch
echo "📥 Performing initial content fetch (this might take a few seconds)..."
"$CLI_BIN" fetch

echo "🎉 Installation Complete!"
echo "--------------------------------------------------------"
echo "BiteCLI is ready to educate you!"
echo "Please configure your LLM Provider and API Key:"
echo "  $CLI_BIN config --provider <gemini|openai|claude|perplexity>"
echo "  $CLI_BIN config --key <YOUR_KEY>"
echo ""
echo "Open a new terminal or run 'source $RC_FILE' to see your first bite-sized lesson!"
