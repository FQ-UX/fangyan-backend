# 方言互动 · Railway 部署指南

本文档详细介绍如何将方言互动后端部署到 Railway 平台。

## 目录

1. [前提条件](#前提条件)
2. [第一步：上传代码到 GitHub](#第一步上传代码到-github)
3. [第二步：创建 Railway 项目](#第二步创建-railway-项目)
4. [第三步：配置环境变量](#第三步配置环境变量)
5. [第四步：等待部署](#第四步等待部署)
6. [常见问题](#常见问题)

---

## 前提条件

- GitHub 账号
- Railway 账号（使用 GitHub 登录）
- 阿里云 DashScope API Key（如需 AI 对话功能）
- 讯飞开放平台 API（如需语音合成功能）

---

## 第一步：上传代码到 GitHub

### 1.1 创建 GitHub 仓库

1. 访问 https://github.com 并登录
2. 点击右上角 "+" → "New repository"
3. 填写仓库信息：
   - Repository name: `fangyan-backend`
   - Description: "方言互动 · 国风传承 后端服务"
   - 选择 "Private"（如需保持代码私密）
   - 不要勾选 "Add a README file"（我们已有项目文件）

### 1.2 初始化本地 Git 仓库

在项目根目录打开终端，执行以下命令：

```bash
# 初始化 Git 仓库
git init

# 添加所有文件（排除 .gitignore 中的文件）
git add .

# 提交
git commit -m "Initial commit: 方言互动后端服务"

# 添加远程仓库（将 YOUR_USERNAME 替换为您的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/fangyan-backend.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 1.3 验证上传成功

刷新 GitHub 仓库页面，确认所有文件已上传。

---

## 第二步：创建 Railway 项目

### 2.1 注册 Railway

1. 访问 https://railway.app 并点击 "Sign Up"
2. 选择 "Sign in with GitHub"（最简单的方式）
3. 授权 Railway 访问您的 GitHub 账号

### 2.2 创建新项目

1. 在 Railway 控制台，点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 选择您刚创建的 `fangyan-backend` 仓库
4. Railway 会自动检测为 Python 项目

### 2.3 配置项目

Railway 会自动配置以下内容：
- 检测到 `requirements.txt` → 自动安装依赖
- 检测到 FastAPI → 自动配置 Web 服务
- 分配一个公共域名

---

## 第三步：配置环境变量

### 3.1 访问项目设置

1. 在 Railway 项目页面，点击 "Settings"
2. 找到 "Environment Variables" 部分

### 3.2 添加必需的环境变量

需要添加以下环境变量（根据 `.env.example`）：

```
DASHSCOPE_API_KEY=your_dashscope_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_OMNI_MODEL=qwen3-omni-flash
QWEN_TTS_MODEL=qwen3-omni-flash

XFYUN_APPID=your_xfyun_appid
XFYUN_API_KEY=your_xfyun_api_key
XFYUN_API_SECRET=your_xfyun_api_secret

DEV_MODE=false
DATABASE_URL=sqlite:///./fangyan.db
AUDIO_CACHE_DIR=./audio_cache
```

### 3.3 获取 API 密钥

**阿里云 DashScope**：
1. 访问 https://dashscope.console.aliyun.com/apiKey
2. 创建 API Key 并复制

**讯飞开放平台**：
1. 访问 https://console.xfyun.cn
2. 创建应用，获取 AppID、API Key 和 API Secret

---

## 第四步：等待部署

1. 配置完环境变量后，Railway 会自动重新部署
2. 在 "Deployments" 页面可以看到部署状态
3. 等待几分钟后，部署完成
4. 点击生成的域名（如 `https://fangyan-backend.up.railway.app`）测试访问

---

## 常见问题

### Q1: 部署失败怎么办？

检查以下几点：
- 环境变量是否正确配置
- `requirements.txt` 是否包含所有依赖
- 查看 Railway 日志定位具体错误

### Q2: 如何查看日志？

在 Railway 项目页面，点击 "Deployments" → 选择当前部署 → "Logs"

### Q3: 如何更新代码？

只需将新代码推送到 GitHub，Railway 会自动检测并重新部署。

### Q4: 数据库如何持久化？

Railway 会自动持久化 SQLite 数据库，无需额外配置。

### Q5: 域名可以修改吗？

可以，在 Railway 项目设置中修改域名。

---

## 验证部署成功

部署完成后，访问以下地址验证：

- 主站：`https://your-app.up.railway.app/`
- API 文档：`https://your-app.up.railway.app/docs`
- 健康检查：`https://your-app.up.railway.app/api/health`

---

## 注意事项

1. **保持密钥安全**：不要将真实的 API Key 提交到 GitHub
2. **监控用量**：Railway 免费版有额度限制，注意监控使用量
3. **定期备份**：重要数据定期备份
4. **查看日志**：如遇问题，先查看 Railway 部署日志

---

如有问题，请参考 Railway 官方文档：https://docs.railway.app
