"""Kiro Telegram MCP Server."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
import sys
import time

import dotenv
from fastmcp import FastMCP
import httpx
import os


@dataclass
class Config:
    """Server configuration loaded from environment variables."""

    bot_token: str
    chat_id: str
    base_url: str


def load_config() -> Config:
    """Load configuration from environment variables.

    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment
    (loading .env via python-dotenv first).

    Returns:
        Config object with validated values.

    Raises:
        ValueError: If required environment variables are missing or empty.
    """
    dotenv.load_dotenv()

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    missing = []

    if not bot_token or not bot_token.strip():
        missing.append("TELEGRAM_BOT_TOKEN")

    if not chat_id or not chat_id.strip():
        missing.append("TELEGRAM_CHAT_ID")

    if missing:
        names = ", ".join(missing)
        raise ValueError(
            f"Missing required environment variable(s): {names}"
        )

    return Config(
        bot_token=bot_token,
        chat_id=chat_id,
        base_url=f"https://api.telegram.org/bot{bot_token}",
    )


class TelegramClient:
    """Async client wrapping httpx for Telegram Bot API communication."""

    def __init__(self, config: Config):
        self._chat_id = config.chat_id
        self._client = httpx.AsyncClient(base_url=config.base_url, timeout=30.0)

    async def get_me(self) -> dict:
        """Validate bot token by calling /getMe.

        Uses a 10s timeout (stricter than the default 30s).

        Returns:
            The 'result' object from the Telegram API response.

        Raises:
            RuntimeError: On authentication failure (HTTP 401),
                network errors, or unexpected API errors.
        """
        try:
            response = await self._client.get("/getMe", timeout=10.0)
        except httpx.ConnectError as exc:
            raise RuntimeError(
                "Could not connect to Telegram API: connection failed"
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Could not connect to Telegram API: request timed out"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Could not connect to Telegram API: {exc}"
            ) from exc

        if response.status_code == 401:
            raise RuntimeError("Telegram Bot Token is invalid (HTTP 401)")

        if response.status_code != 200:
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            description = data.get("description", "unknown error")
            raise RuntimeError(
                f"Telegram API returned unexpected error {response.status_code}: {description}"
            )

        return response.json().get("result", {})

    async def send_message(self, text: str, reply_markup: dict | None = None) -> dict:
        """Send a message to the configured chat.

        Args:
            text: The message text to send.
            reply_markup: Optional inline keyboard markup dict.

        Returns:
            The 'result' object from the Telegram API response (sent message).

        Raises:
            RuntimeError: On API errors (with status code and description)
                or network errors.
        """
        payload: dict = {
            "chat_id": self._chat_id,
            "text": text,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        try:
            response = await self._client.post("/sendMessage", json=payload)
        except httpx.ConnectError as exc:
            raise RuntimeError(
                "Could not connect to Telegram API: connection failed"
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Could not connect to Telegram API: request timed out"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Could not connect to Telegram API: {exc}"
            ) from exc

        if response.status_code != 200:
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            description = data.get("description", "unknown error")
            raise RuntimeError(
                f"Telegram API returned {response.status_code}: {description}"
            )

        return response.json().get("result", {})

    async def get_updates(self, offset: int, timeout: int, allowed_updates: list[str]) -> list[dict]:
        """Long-poll for updates from Telegram.

        Args:
            offset: Identifier of the first update to be returned.
            timeout: Long-polling timeout in seconds for the Telegram server.
            allowed_updates: List of update types to receive.

        Returns:
            List of update objects from the Telegram API.

        Raises:
            RuntimeError: On API errors (with status code and description)
                or network errors.
        """
        payload = {
            "offset": offset,
            "timeout": timeout,
            "allowed_updates": allowed_updates,
        }

        # Use a client timeout larger than the Telegram long-poll timeout
        # to avoid cutting off Telegram's response prematurely.
        request_timeout = timeout + 5

        try:
            response = await self._client.post(
                "/getUpdates", json=payload, timeout=request_timeout
            )
        except httpx.ConnectError as exc:
            raise RuntimeError(
                "Could not connect to Telegram API: connection failed"
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Could not connect to Telegram API: request timed out"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Could not connect to Telegram API: {exc}"
            ) from exc

        if response.status_code != 200:
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            description = data.get("description", "unknown error")
            raise RuntimeError(
                f"Telegram API returned {response.status_code}: {description}"
            )

        return response.json().get("result", [])

    async def answer_callback_query(self, callback_query_id: str) -> bool:
        """Acknowledge a callback query.

        Args:
            callback_query_id: Unique identifier for the callback query to answer.

        Returns:
            True if the callback query was acknowledged successfully.

        Raises:
            RuntimeError: On API errors (with status code and description)
                or network errors.
        """
        payload = {
            "callback_query_id": callback_query_id,
        }

        try:
            response = await self._client.post("/answerCallbackQuery", json=payload)
        except httpx.ConnectError as exc:
            raise RuntimeError(
                "Could not connect to Telegram API: connection failed"
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Could not connect to Telegram API: request timed out"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Could not connect to Telegram API: {exc}"
            ) from exc

        if response.status_code != 200:
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            description = data.get("description", "unknown error")
            raise RuntimeError(
                f"Telegram API returned {response.status_code}: {description}"
            )

        return response.json().get("result", False)

    async def close(self):
        """Close the underlying httpx client."""
        await self._client.aclose()


def build_inline_keyboard(opciones: list[str]) -> dict:
    """Construct an InlineKeyboardMarkup from a list of option labels.

    Each option becomes a single-button row. The callback_data is the option
    text truncated to 64 bytes (Telegram API limit).

    Args:
        opciones: List of button label strings.

    Returns:
        Dict representing InlineKeyboardMarkup with one button per row.
    """
    return {
        "inline_keyboard": [
            [
                {
                    "text": opt,
                    "callback_data": opt.encode("utf-8")[:64].decode(
                        "utf-8", errors="ignore"
                    ),
                }
            ]
            for opt in opciones
        ]
    }


async def poll_for_callback(
    client: TelegramClient,
    message_id: int,
    timeout_seconds: int,
) -> str:
    """Poll getUpdates for a callback_query matching message_id.

    Uses long-polling with 10s per-request timeout. On API error, waits 2s
    and retries. After 3 consecutive errors, raises RuntimeError.

    Args:
        client: TelegramClient instance to use for API calls.
        message_id: The message_id of the sent inline keyboard message.
        timeout_seconds: Maximum seconds to wait for a callback response.

    Returns:
        The callback_data string from the matching button press.

    Raises:
        TimeoutError: If no matching callback is received within timeout_seconds.
        RuntimeError: After 3 consecutive polling failures.
    """
    offset = 0
    consecutive_errors = 0
    start = time.monotonic()

    while True:
        elapsed = time.monotonic() - start
        if elapsed >= timeout_seconds:
            raise TimeoutError(
                f"No response received within {timeout_seconds} seconds"
            )

        try:
            updates = await client.get_updates(
                offset=offset,
                timeout=10,
                allowed_updates=["callback_query"],
            )
        except RuntimeError:
            consecutive_errors += 1
            if consecutive_errors >= 3:
                raise RuntimeError(
                    "Polling failed: 3 consecutive API errors"
                )
            await asyncio.sleep(2)
            continue

        # Successful response: reset consecutive error counter
        consecutive_errors = 0

        if updates:
            # Advance offset past ALL received updates (matching or not)
            max_update_id = max(u["update_id"] for u in updates)
            offset = max_update_id + 1

            # Filter for matching callback_query
            for update in updates:
                callback_query = update.get("callback_query")
                if callback_query is None:
                    continue
                msg = callback_query.get("message", {})
                if msg.get("message_id") == message_id:
                    # Acknowledge the callback query
                    await client.answer_callback_query(callback_query["id"])
                    return callback_query["data"]


# Module-level TelegramClient instance, initialized at startup.
telegram_client: TelegramClient | None = None


@asynccontextmanager
async def lifespan(server):
    """Initialize TelegramClient on server start, close on shutdown."""
    global telegram_client

    try:
        config = load_config()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    telegram_client = TelegramClient(config)

    try:
        await telegram_client.get_me()
    except RuntimeError as exc:
        print(f"Startup error: {exc}", file=sys.stderr)
        await telegram_client.close()
        sys.exit(1)

    try:
        yield
    finally:
        await telegram_client.close()


mcp = FastMCP("kiro-telegram", lifespan=lifespan)


@mcp.tool()
async def enviar_notificacion(mensaje: str) -> str:
    """Sends a notification message to the configured Telegram chat.

    Args:
        mensaje: Message text (1-4096 characters)

    Returns:
        Success or error message string.
    """
    # Validate message is not empty or whitespace-only
    if not mensaje or not mensaje.strip():
        return "Error: El mensaje no puede estar vacío"

    # Validate message length
    if len(mensaje) > 4096:
        return "Error: El mensaje excede el límite de 4096 caracteres"

    try:
        await telegram_client.send_message(mensaje)
        return "Mensaje enviado exitosamente"
    except RuntimeError as exc:
        return f"Error: {exc}"


@mcp.tool()
async def solicitar_confirmacion(
    mensaje: str,
    opciones: list[str],
    timeout: int = 300,
) -> str:
    """Sends an interactive confirmation with inline keyboard buttons.

    Blocks until a user presses a button or the timeout elapses.

    Args:
        mensaje: Prompt message to display
        opciones: List of button labels (1-10 items)
        timeout: Seconds to wait for response (10-600, default 300)

    Returns:
        Selected button's callback data, or error message.
    """
    # Validate opciones count
    if len(opciones) < 1 or len(opciones) > 10:
        return "Error: Las opciones deben ser entre 1 y 10"

    # Validate timeout range
    if timeout < 10 or timeout > 600:
        return "Error: El timeout debe estar entre 10 y 600 segundos"

    # Build inline keyboard
    reply_markup = build_inline_keyboard(opciones)

    # Send message with inline keyboard
    try:
        result = await telegram_client.send_message(mensaje, reply_markup=reply_markup)
    except RuntimeError as exc:
        return f"Error: {exc}"

    # Get message_id from sent message
    message_id = result["message_id"]

    # Poll for callback response
    try:
        selected = await poll_for_callback(telegram_client, message_id, timeout)
        return selected
    except TimeoutError:
        return f"Error: No se recibió respuesta en {timeout} segundos"
    except RuntimeError as exc:
        return f"Error: {exc}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
