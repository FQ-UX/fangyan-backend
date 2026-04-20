# 方言互动 · 国风传承 — 后端服务

> 计算机设计大赛作品 · 方言文化传承平台
> 前端：单页 HTML · 后端：FastAPI + SQLite · AI：DeepSeek + 讯飞

---

## 🚀 快速开始（Windows）

### 第 1 步：准备 API 凭证

打开 `.env` 文件，确认以下字段已填写：
```ini
DEEPSEEK_API_KEY=sk-xxxxxxxxxx          # 从 https://platform.deepseek.com/ 获取
XFYUN_APPID=eeaea8ce                    # 从 https://console.xfyun.cn/ 获取
XFYUN_API_KEY=xxxxxxxxxx
XFYUN_API_SECRET=xxxxxxxxxx
```

> ⚠️ **重要安全提示**：你之前在聊天中发过的 key 已经暴露，务必去 DeepSeek 和讯飞平台**重新生成新 key**，并填到 `.env`。不要再在聊天中粘贴新 key。

### 第 2 步：双击启动

双击 `start.bat`，脚本会：
1. 自动创建 Python 虚拟环境
2. 安装依赖
3. 启动 FastAPI 服务

首次启动需要几分钟下载依赖，之后秒开。

### 第 3 步：打开浏览器

```
前端:      http://127.0.0.1:8000/
API 文档:  http://127.0.0.1:8000/docs
```

---

## 🗂️ 项目结构

```
fangyan_backend/
├── .env                        # 配置文件（API Keys）
├── requirements.txt            # Python 依赖
├── start.bat                   # Windows 一键启动
├── fangyan.db                  # SQLite 数据库（首次运行自动创建）
├── audio_cache/                # TTS 生成的音频缓存
├── static/
│   └── index.html              # 前端（已集成后端 API）
└── app/
    ├── main.py                 # FastAPI 入口
    ├── db.py                   # SQLite 连接
    ├── models.py               # 数据模型（5 张表）
    ├── data/                   # 静态数据（109词+103题+6故事）
    ├── services/
    │   ├── deepseek.py         # DeepSeek 对话
    │   ├── rag.py              # 词典 RAG 检索
    │   ├── xfyun_tts.py        # 讯飞语音合成
    │   └── xfyun_ise.py        # 讯飞发音评测
    └── routers/
        ├── progress.py         # 进度/积分/日历
        ├── achievements.py     # 成就
        ├── dict.py             # 词典
        ├── stories.py          # 故事
        ├── game.py             # 题库/发音测评
        ├── chat.py             # AI 对话
        ├── tts.py              # 语音合成
        └── asr.py              # 语音评测
```

---

## 🔌 API 端点一览

打开 `http://127.0.0.1:8000/docs` 可以看到交互式文档，可直接调试。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/progress` | 获取用户进度 |
| PATCH | `/api/progress` | 更新进度 |
| POST | `/api/progress/pts` | 加积分 |
| GET | `/api/progress/calendar` | 本月学习日历 |
| GET | `/api/achievements` | 所有成就 |
| POST | `/api/achievements/unlock` | 解锁一个成就 |
| GET | `/api/dict/words` | 词典列表（支持搜索/筛选） |
| GET | `/api/dict/word/{id}` | 单个词条详情 |
| GET | `/api/dict/compare` | 方言对照表 |
| GET | `/api/stories` | 故事列表 |
| GET | `/api/stories/{id}/text` | 故事全文 |
| GET | `/api/game/quiz` | 随机抽题 |
| GET | `/api/game/speech` | 发音测评题库 |
| POST | `/api/game/record` | 保存游戏记录 |
| POST | **`/api/chat`** | **AI 方言对话** ⭐ |
| GET | `/api/chat/quick-phrases` | 方言快捷短语 |
| POST | **`/api/tts`** | **方言语音合成** ⭐ |
| POST | **`/api/asr/evaluate`** | **发音评测** ⭐ |

---

## 🧩 技术亮点（答辩可用）

### 1. DeepSeek + RAG 增强对话
- 用户问话 → 从 109 词方言词典中检索相关词条
- 把词条 + 方言风格 Prompt 一起送给 DeepSeek
- 多轮上下文（最近 8 条）让对话连贯
- 响应失败自动降级到本地应答

### 2. 讯飞真实语音能力
- **TTS**：发音人按方言选（粤语/四川话/东北话 等），缓存到磁盘避免重复调用
- **ISE 发音评测**：用户录音上传 → 真实声学模型打分 0-100

### 3. 完整持久化
- SQLite 存储 5 张表（用户/成就/聊天/游戏/日历）
- 前端状态变更自动 debounce 保存（300ms）
- 重启后进度不丢失

### 4. 零配置单机跑
- SQLite 数据库文件化，无需安装 MySQL/Postgres
- Windows 双击 start.bat 即可启动
- CORS 开放模式，前端用 file:// 打开也能连

---

## 🔧 常见问题

### 依赖安装慢？
用清华镜像：
```cmd
.venv\Scripts\activate.bat
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 启动报端口占用？
在 `.env` 里改 `PORT=8001`，或找到占用 8000 的进程关掉。

### DeepSeek 调用失败？
在浏览器打开 `http://127.0.0.1:8000/docs`，找到 `/api/chat` 直接测试一条消息。
- 若返回 "API Key 无效" → `.env` 里的 key 写错了
- 若卡住超时 → 检查网络（DeepSeek 国内直连，基本没问题）

### 讯飞 TTS 没声音？
- 讯飞的方言发音人需要在控制台**单独购买/开通**（通用版默认只有普通话）
- 未开通时后端会兜底使用普通话发音人
- 打开 F12 看 Network → `/api/tts` 返回码

### 讯飞发音评测方言不准？
讯飞的 ISE 接口**官方只支持普通话和英语**，方言评测目前全行业都还做不到真正准确。
我们现在的方案：
- 对于普通话 → 使用讯飞真实评测
- 对于方言 → 使用兜底算法给出合理分数和建议
答辩时可以把这个作为"未来迭代方向"来讲。

---

## 🚢 部署到公网（可选）

### 最简方案：腾讯云轻量 / 阿里云 ECS（学生机 ~10元/月）
1. 购买 1核2G Linux 云服务器
2. 安装 Python 3.9+、nginx
3. 把整个项目目录 scp 上去
4. 运行：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
   ```
5. nginx 反代 80 → 8000，申请免费 SSL 证书（certbot）

---

## 📝 License

大赛作品 · 仅供学习交流使用
