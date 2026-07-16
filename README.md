# Kiro Telegram MCP Server

A Python MCP (Model Context Protocol) server that integrates Kiro IDE with Telegram. Exposes two tools:

- **`enviar_notificacion`** — Send notification messages to a Telegram chat.
- **`solicitar_confirmacion`** — Request interactive confirmations via inline keyboard buttons.

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

## Configuration

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot authentication token from BotFather |
| `TELEGRAM_CHAT_ID` | Numeric ID of the target Telegram chat |

## Kiro Steering (Confirmaciones automáticas)

Para que Kiro pida confirmación por Telegram antes de ejecutar acciones destructivas, crea el siguiente archivo en tu proyecto:

**`.kiro/steering/telegram-confirm.md`**

~~~markdown
# Confirmaciones y Notificaciones por Telegram

## Confirmaciones

Antes de ejecutar acciones de alto riesgo, usa `solicitar_confirmacion` para pedir aprobación por Telegram. Esto incluye:

- Eliminar archivos o directorios
- Modificar archivos de configuración de producción
- Hacer commits o push a repositorios
- Operaciones destructivas o irreversibles
- Cambios en infraestructura

No procedas hasta recibir confirmación explícita del usuario por Telegram.

## Notificaciones

Usa `enviar_notificacion` para informar al usuario cuando:

- Una tarea larga se completó
- Se encontró un error que requiere atención
- Se necesita input pero no es una confirmación sí/no
~~~

Copia este archivo en cada proyecto donde quieras que Kiro use Telegram para confirmaciones.

## Compatibility

- **Python**: 3.10+
- **Platforms**: Windows, macOS, Linux
