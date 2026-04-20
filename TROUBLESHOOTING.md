# Troubleshooting Guide

## 问题 1: 启动时大量乱码、"不是内部或外部命令"

**原因**：`.bat` 文件编码不对，Windows cmd 默认用 GBK 读取。

**解决**：新版本的 `.bat` 已经全部改为纯英文（ASCII），不会再出现这个问题。如果仍然出现，请：

1. 右键 `start.bat` → 用 记事本 打开
2. 另存为 → 编码选 **ANSI**（不是 UTF-8）→ 保存覆盖

## 问题 2: `No module named uvicorn`

**原因**：依赖没装，或者装到了虚拟环境外/错误的 Python 下。

**解决方案（按顺序试）**：

### 方案 A：用 install_direct.bat + run_direct.bat（最简单）

不使用虚拟环境，直接装到系统 Python：
```
1. 双击 install_direct.bat（等 2-5 分钟）
2. 安装完成后双击 run_direct.bat
```

### 方案 B：手动激活 venv 再装

在项目目录打开 cmd：
```cmd
.venv\Scripts\activate.bat
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 方案 C：Python 3.14 兼容问题

Python 3.14 太新，部分依赖可能没 wheel。建议：

**方法 1**：装一个稳定的 Python 3.11 或 3.12（推荐）
- 去 python.org/downloads 下载 Python 3.11.x
- 安装时勾选 "Add to PATH"
- 删掉已有的 `.venv` 文件夹
- 重新双击 `start.bat`

**方法 2**：强制用 3.14（若上面不行）
```cmd
py -3.14 -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 问题 3: pip 安装很慢 / 卡住

默认 PyPI 在国内慢。已在 `start.bat` 里配置了清华镜像。若还卡：

```cmd
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## 问题 4: 服务启动后浏览器打不开

- 确认 cmd 窗口显示了 `Uvicorn running on http://127.0.0.1:8000`
- 如果提示端口占用，改 `.env` 里的 `PORT=8001`
- Windows 防火墙可能拦截，点"允许访问"
- 访问 `http://localhost:8000/api/health`，应返回 `{"status":"ok"}`

## 问题 5: 点 AI 对话没响应

按 F12 打开浏览器控制台，看 Network 标签下 `/api/chat` 的响应。常见：

- **CORS error**：访问地址不是 `http://127.0.0.1:8000` 而是 `file://...`（用了文件直接打开）
  → 必须通过后端地址访问：`http://127.0.0.1:8000/`
- **500 错误**：后端 DeepSeek key 无效 → 检查 `.env` 里的 `DEEPSEEK_API_KEY`
- **超时**：DeepSeek 网络不通 → 稍等或重试

## 问题 6: 讯飞 TTS/ASR 报错

讯飞的 WebSocket 签名很严格，几个常见错误码：

- `10105 license error`：应用未授权该功能，去讯飞控制台开通对应服务
- `10106 invalid parameter`：参数错误，通常是文本太长或发音人不存在
- `10114 ws connect time out`：网络问题，重试
- `10700 engine error`：发音人名不对（方言发音人需额外开通）

## 诊断工具

双击 `diagnose.bat`，把输出完整截图/复制发给我，我能快速定位问题。
