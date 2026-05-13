import asyncio
from typing import Optional
import discord
from .base import BaseChannel
from .reset_policy import ExactMatchResetPolicy, RegexResetPolicy


class DiscordChannel(BaseChannel):
    RESET_ACK_MESSAGE = "New session started."

    def __init__(self, config: dict):
        super().__init__(config)
        self.token = config["discord_token"]
        channel_id = str(config.get("channel_id", "")).strip()
        if not channel_id:
            raise ValueError("channel_id is required")
        self.target_channel_id = int(channel_id)

        source_bot_id = str(config.get("source_bot_id", "")).strip()
        self.source_bot_id = int(source_bot_id) if source_bot_id else None
        self.proxy = str(config.get("proxy", "")).strip() or None

        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True

        self.client = discord.Client(intents=intents, proxy=self.proxy)
        self._client_task: Optional[asyncio.Task] = None

        self._setup_events()

    def _setup_events(self):

        @self.client.event
        async def on_message(message: discord.Message):
            if message.channel.id != self.target_channel_id:
                return
            if self.source_bot_id is not None and message.author.id != self.source_bot_id:
                return
            if self.client.user and message.author.id == self.client.user.id:
                return

            self.logger.info(
                f"[Discord] 收到频道消息 channel={message.channel.id} author={message.author.id}: {message.content}"
            )
            await self._recv(message.content)

    async def connect(self):
        self.logger.info("[Discord] 正在初始化登录...")
        if self.proxy:
            self.logger.info(f"[Discord] 已启用代理: {self.proxy}")
        await self.client.login(self.token)

        self.logger.info("[Discord] 建立 WebSocket 连接...")
        self._client_task = asyncio.create_task(self.client.connect())

        await self.client.wait_until_ready()
        self.logger.info(f"[Discord] 已登录为 {self.client.user}")

    async def send(self, message: str):
        try:
            channel = self.client.get_channel(self.target_channel_id)
            if channel is None:
                self.logger.debug(
                    f"[Discord] 缓存未找到频道，正在通过 API 获取 ID: {self.target_channel_id}"
                )
                channel = await self.client.fetch_channel(self.target_channel_id)

            self.logger.debug(f"[Discord] 发送频道消息 channel={self.target_channel_id}: {message}")
            await channel.send(message)

        except discord.NotFound:
            self.logger.error(f"[Discord] 找不到目标频道 ID: {self.target_channel_id}")
        except discord.Forbidden:
            self.logger.error("[Discord] 无法发送频道消息 (可能缺少频道可见性或发送权限)")
        except Exception as e:
            self.logger.error(f"[Discord] 发送消息失败: {e}")

    def build_reset_response_policies(self):
        policies = [
            ExactMatchResetPolicy(
                target=self.RESET_ACK_MESSAGE,
                max_absorb=int(self.config.get("reset_ack_max_absorb", 1)),
            )
        ]
        for message in self.config.get("reset_ack_messages", []):
            policies.append(ExactMatchResetPolicy(target=str(message), max_absorb=1))
        for pattern in self.config.get("reset_ack_regexes", []):
            policies.append(RegexResetPolicy(pattern=str(pattern), max_absorb=1))
        return policies

    async def disconnect(self):
        self.logger.info("[Discord] 正在断开连接...")
        if not self.client.is_closed():
            await self.client.close()

        if self._client_task and not self._client_task.done():
            self._client_task.cancel()
            try:
                await self._client_task
            except asyncio.CancelledError:
                pass
        self.logger.info("[Discord] 已断开连接。")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
