import os
import time
import tempfile
import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig, logger
import astrbot.api.message_components as Comp


@register(
    "astrbot_plugin_voxcpm_tts",
    "liumouzs",
    "将 Colab 部署的 VoxCPM2 语音克隆 API 接入 AstrBot",
    "1.0.0",
    "https://github.com/liumouzs/astrbot_plugin_voxcpm_tts",
)
class VoxCPMTTSPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.temp_dir = os.path.join(tempfile.gettempdir(), "astrbot_voxcpm_tts")
        os.makedirs(self.temp_dir, exist_ok=True)

    @filter.command("vox_url")
    async def set_vox_url(self, event: AstrMessageEvent, new_url: str = ""):
        """热更新 Colab 临时公网地址，用法：/vox_url https://xxxx.trycloudflare.com/v1"""
        new_url = new_url.strip().rstrip("/")
        if not new_url.startswith("http"):
            yield event.plain_result("请输入有效的地址，例如：/vox_url https://xxxx.trycloudflare.com/v1")
            return

        if not new_url.endswith("/v1"):
            new_url += "/v1"

        self.config["api_base_url"] = new_url
        self.config.save_config()
        yield event.plain_result(f"✅ VoxCPM2 接口地址已更新为：\n{new_url}")

    @filter.command("vox")
    async def vox_tts(self, event: AstrMessageEvent):
        """将文本转为克隆语音，用法：/vox 你好，这是测试语音"""
        raw_msg = event.message_str.strip()
        text = raw_msg[len("vox"):].strip() if raw_msg.startswith("vox") else raw_msg
        if text.startswith("/vox"):
            text = text[len("/vox"):].strip()

        if not text:
            yield event.plain_result("请输入要合成的文本，例如：/vox 你好，这是测试语音")
            return

        base_url = self.config.get("api_base_url", "").strip().rstrip("/")
        if not base_url:
            yield event.plain_result("❌ 尚未配置 api_base_url，请在 WebUI 或使用 /vox_url 设置。")
            return

        endpoint = f"{base_url}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.config.get('api_key', 'sk-voxcpm2')}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.get("model", "voxcpm2"),
            "voice": self.config.get("voice", "default"),
            "input": text,
            "response_format": "wav",
        }
        timeout = aiohttp.ClientTimeout(total=int(self.config.get("timeout", 60)))

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(endpoint, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        logger.error(f"VoxCPM2 API 请求失败: {resp.status} - {err_text}")
                        yield event.plain_result(f"❌ 语音合成失败（HTTP {resp.status}），请检查 Colab 隧道是否在线。")
                        return

                    audio_bytes = await resp.read()
                    wav_path = os.path.join(self.temp_dir, f"vox_{int(time.time() * 1000)}.wav")
                    with open(wav_path, "wb") as f:
                        f.write(audio_bytes)

            yield event.chain_result([Comp.Record.fromFileSystem(wav_path)])
        except Exception as e:
            logger.error(f"VoxCPM2 语音合成异常: {e}")
            yield event.plain_result(f"❌ 请求异常：{e}")
