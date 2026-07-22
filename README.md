# Kiro Telegram MCP Server

A Python MCP (Model Context Protocol) server that integrates Kiro IDE with Telegram. Exposes three tools:

- **`enviar_notificacion`** — Send notification messages to a Telegram chat.
- **`solicitar_confirmacion`** — Request interactive confirmations via inline keyboard buttons.
- **`solicitar_input_texto`** — Ask a question and receive a free-text reply from Telegram.

## Requirements

- Python 3.10 or higher
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- A Telegram chat ID

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jcsepulveda/mcp-kiro-telegram.git
   cd mcp-kiro-telegram
   ```

2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

3. Copy the environment example and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your Telegram bot token and chat ID.

## Kiro MCP Configuration

Add the following to your `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "kiro-telegram": {
      "command": "python3",
      "args": ["/path/to/mcp-kiro-telegram/server.py"],
      "cwd": "/path/to/mcp-kiro-telegram"
    }
  }
}
```

The `cwd` field is required so the server finds the `.env` file at startup.

## Usage

Run the server via stdio (used by Kiro IDE):

```bash
python server.py
```

The server communicates over stdin/stdout using the MCP JSON-RPC protocol.

## Tools

### `enviar_notificacion`

Sends a plain text message to the configured Telegram chat.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mensaje` | string | Yes | Message text (1-4096 characters) |

Returns success or error message.

### `solicitar_confirmacion`

Sends a message with inline keyboard buttons and blocks until the user presses one.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mensaje` | string | Yes | Prompt message to display |
| `opciones` | list[str] | Yes | Button labels (1-10 items) |
| `timeout` | int | No | Seconds to wait (10-600, default 300) |

Returns the selected button's callback data, or error on timeout.

### `solicitar_input_texto`

Sends a question and blocks until the user replies with a free-text message.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mensaje` | string | Yes | Question or prompt (1-4096 characters) |
| `timeout` | int | No | Seconds to wait (10-600, default 300) |

Returns the user's text reply, or error on timeout.

## Configuration

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot authentication token from BotFather |
| `TELEGRAM_CHAT_ID` | Numeric ID of the target Telegram chat |

## Kiro Steering (global)

For Kiro to automatically use Telegram for notifications and confirmations across all projects, place a steering file at `~/.kiro/steering/telegram-confirm.md`. See the example in `.kiro/steering/telegram-confirm.md` within this repository.

The recommended steering implements:
1. **Post-task notification**: summary sent after every completed task.
2. **Detail prompt**: asks via buttons if the user wants the full response.
3. **Pre-action confirmation**: blocks before destructive operations.

## Compatibility

- **Python**: 3.10+
- **Platforms**: Windows, macOS, Linux
