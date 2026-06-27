# 企业微信销售 AI 副驾驶 MVP

这是一个可运行的 MVP 工程骨架，包含 FastAPI 后端、Vue 3 企业微信侧边栏 H5、MySQL/Redis/Docker 部署配置，以及企业微信官方接口和会话存档 Finance SDK 的预留适配点。

## 当前能力

- 企业微信 AccessToken 缓存刷新。
- JS-SDK 签名接口。
- 外部联系人同步接口。
- 会话存档客户端抽象，默认 `stub`，生产可替换为官方 Finance SDK 实现。
- 单聊文本消息结构化存储模型。
- 客户画像标签和意向等级计算。
- OpenAI 兼容大模型实时话术分析，失败时自动返回规则兜底话术。
- 侧边栏 H5：话术推荐、画像详情、跟进记录。

## 本地配置

复制环境变量模板：

```bash
cp .env.example .env
```

后端依赖：

```bash
cd backend
pip install -r requirements.txt
python -m app.core.init_db
uvicorn app.main:app --reload --port 8000
```

前端依赖：

```bash
cd frontend
npm install
npm run dev
```

开发模式下，前端会使用：

- `VITE_DEV_SALES_USERID=sales-dev-001`
- `VITE_DEV_EXTERNAL_USERID=external-dev-001`

在企业微信侧边栏环境中，前端会调用 `ww.invoke('getCurExternalContact')` 获取当前客户 ID。

## 生产部署

```bash
docker compose up -d --build
```

如果服务器已有面板占用 `80/443`，默认 Compose 会把项目 Nginx 映射到 `18080`，本地服务端口为：

- 后端：`8000`
- 前端：`5173`
- 项目 Nginx：`18080`

正式上线前需要完成：

- 企业微信可信域名与可信 IP 配置。
- HTTPS 证书配置。
- 自建应用 Secret、会话存档 Secret、RSA 私钥、公钥版本号配置。
- Linux 服务器挂载 `libWeWorkFinanceSdk_C.so`。
- 在 `FinanceSdkArchiveClient` 中接入官方 C SDK 的 `GetChatData` 和 `DecryptData` ctypes 绑定。

## 关键接口

- `POST /api/auth/login`
- `GET /api/wecom/js-config`
- `POST /api/sync/external-contacts`
- `GET /api/customer/info`
- `GET /api/analysis/realtime`
- `POST /api/analysis/summary`
- `GET /api/chat/history`
- `GET /api/follow/list`
- `POST /api/follow/add`

## 合规边界

MVP 不自动发送消息，不处理群聊和非文本消息，不做朋友圈自动运营。会话存档上线前必须配置客户告知话术，并按企业微信和当地监管要求控制数据范围、权限和留痕。
