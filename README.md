# astrbot_plugin_voxcpm_tts

将基于 **Google Colab** 云端 GPU 部署的 **`openbmb/VoxCPM2`** 语音克隆模型接入 **AstrBot**，通过 OpenAI 兼容 `/v1/audio/speech` 接口在 QQ 中直接合成并发送 48kHz 克隆语音条，支持固定云盘音色持久化、QQ 内热更新临时隧道地址及长文本超时控制。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/liumouzs/astrbot_plugin_voxcpm_tts/blob/main/colab/VoxCPM2_AstrBot_Server.ipynb)

## 1. 启动 Colab 服务端

1. 点击上方 **Open in Colab** 按钮打开 `colab/VoxCPM2_AstrBot_Server.ipynb`，连接 **GPU**（推荐 T4 或 L4）。
2. **首次使用**：运行「单元格 0」，上传 4~9 秒干净参考音频并写入对应文字稿，系统会自动持久化保存到 Google Drive 的 `VoxCPM2_Cache/`。
3. **每次重连 GPU**：按顺序运行 **单元格 1 → 单元格 2 → 单元格 3**，复制最后打印出的 `https://xxxx.trycloudflare.com/v1` 地址。

## 2. 工作原理

- **云端模型推理（Google Colab）**：在 Colab GPU 中加载 `openbmb/VoxCPM2` 并缓存在本地高速盘，通过 FastAPI 暴露 OpenAI 兼容接口（`POST /v1/audio/speech` 与 `GET /v1/models`）。
- **公网隧道穿透（cloudflared）**：通过 `cloudflared` 将本地 FastAPI 服务暴露为临时公网 HTTPS 地址（`*.trycloudflare.com`）。
- **AstrBot 插件调用**：用户在 QQ 发送 `/vox <文本>` 后，插件异步请求远程 `/v1/audio/speech` 获取 WAV 音频并发送为 QQ 语音条；Colab 重连域名变化时，直接用 `/vox_url <新地址>` 在 QQ 内热更新并持久化保存。

## 3. 安装 AstrBot 插件

在 **AstrBot WebUI → 插件管理 → 通过 Git 仓库安装** 中填入本仓库地址：

```text
https://github.com/liumouzs/astrbot_plugin_voxcpm_tts
```

## 4. 指令说明

- `/vox_url <新BaseURL>`：在 QQ 内直接热更新 Colab 隧道地址（例如 `/vox_url https://xxxx.trycloudflare.com/v1`，自动补全 `/v1`）。
- `/vox <文本>`：调用远程 VoxCPM2 合成 48kHz 克隆语音并发送为 QQ 语音条。
- `/vox_timeout <秒数>`：查看或热更新语音合成超时时间（填 `0` 表示不限制推理等待时间，适合超长文本合成）。

> 提示：你也可以直接把该 `/v1` 地址填入 AstrBot 自带的 **OpenAI TTS** 服务商，实现全自动语音回复。

## 5. 配置项说明

可在 AstrBot WebUI 插件配置中设置以下参数：

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `api_base_url` | string | `https://your-tunnel.trycloudflare.com/v1` | VoxCPM2 OpenAI 兼容接口地址（填到 `/v1` 为止） |
| `api_key` | string | `sk-voxcpm2` | 请求鉴权 Key（自建 Colab 接口可任意填写） |
| `model` | string | `voxcpm2` | 请求的模型名称 |
| `voice` | string | `default` | 音色标识 |
| `timeout` | int | `180` | 语音合成请求超时时间（秒）。长文本建议设为 `120~300`，填 `0` 表示不限制推理等待超时（仅保留 15 秒连接超时） |

## 6. 注意事项

- 请确保 QQ 协议端（如 NapCat / Lagrange / LLOneBot）宿主机已安装 `ffmpeg`，以支持 `.wav` 自动转码为 QQ 所需的 `.silk` 语音格式。
- Google Colab 免费 GPU 实例存在闲置回收机制，重连后依次运行单元格 1~3，复制新的 `trycloudflare.com` 地址并在 QQ 发送 `/vox_url <新地址>` 即可恢复使用。
