# astrbot_plugin_voxcpm_tts

将基于 **Google Colab** 云端 GPU 部署的 **`openbmb/VoxCPM2`** 语音克隆模型接入 **AstrBot**，通过 OpenAI 兼容 TTS API 实现在 QQ 中直接调用并发送克隆语音条。

## 工作原理

1. **云端模型推理（Google Colab）**：在 Google Colab GPU 环境中部署 `openbmb/VoxCPM2` 语音克隆服务，使用 FastAPI 封装 OpenAI 兼容接口：
   - `POST {api_base_url}/audio/speech`：接收 JSON 请求体（`model`、`voice`、`input`、`response_format: "wav"`），返回 `audio/wav` 二进制音频流。
   - `GET {api_base_url}/models`：提供模型列表与服务可用性探测。
2. **公网隧道穿透（cloudflared）**：通过 `cloudflared` 将 Colab 本地 FastAPI 服务暴露为临时公网 HTTPS 地址（`*.trycloudflare.com`）。
3. **AstrBot 插件调用**：用户在 QQ 发送 `/vox <文本>` 后，插件异步请求远程 `/v1/audio/speech` 接口获取 WAV 音频，落盘临时文件后以 QQ 语音条形式发送；当 Colab 重连 GPU 导致 `trycloudflare.com` 域名变更时，可通过 `/vox_url <新地址>` 在 QQ 内直接热更新并持久化保存，无需反复登录 AstrBot 后台修改配置。

## 功能指令

- `/vox <文本>`：调用远程 VoxCPM2 API 合成 48kHz 克隆语音并发送为 QQ 语音条。
- `/vox_url <新地址>`：热更新并持久化保存 Colab 新的 `trycloudflare.com` 接口地址（自动补全 `/v1` 后缀）。

## 安装方式

在 **AstrBot WebUI -> 插件管理 -> 通过 Git 仓库安装** 中填入本仓库地址：

```text
https://github.com/liumouzs/astrbot_plugin_voxcpm_tts
```

## 配置项说明

可在 AstrBot WebUI 插件配置中设置以下参数：

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `api_base_url` | string | `https://your-tunnel.trycloudflare.com/v1` | VoxCPM2 OpenAI 兼容接口地址（填到 `/v1` 为止） |
| `api_key` | string | `sk-voxcpm2` | 请求鉴权 Key（自建 Colab 接口可任意填写） |
| `model` | string | `voxcpm2` | 请求的模型名称 |
| `voice` | string | `default` | 音色标识 |
| `timeout` | int | `60` | HTTP 请求超时时间（秒） |

## 注意事项

- 请确保 QQ 协议端（如 NapCat / Lagrange / LLOneBot）宿主机已安装 `ffmpeg`，以支持 `.wav` 自动转码为 QQ 所需的 `.silk` 语音格式。
- Google Colab 免费 GPU 实例存在闲置回收机制，重连后仅需复制新的 `trycloudflare.com` 地址并在 QQ 发送 `/vox_url <新地址>` 即可恢复使用。
