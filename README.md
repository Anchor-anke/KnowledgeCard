# KnowledgeCard

把长资料变成短知识卡，用主动回忆和间隔复习把“看过”变成“记住”。

KnowledgeCard 的目标是让用户上传自己的 PDF，经过 AI 提取重点并生成可审核的知识卡，然后在移动端通过滑动学习、主动回忆和间隔复习巩固知识。

当前仓库是一个可运行的产品原型，包含：

- `mobile/`：基于 uni-app + Vue 3 的 Android / iOS / HarmonyOS NEXT 跨平台客户端；
- `backend/`：FastAPI 本地 AI 制卡服务，支持文本和 PDF 输入；
- `miniprogram/`：微信小程序 Mock 客户端；
- `src/knowledge_card/`：Python 标准库实现的领域核心 MVP；
- `docs/`：产品需求、模块设计和验证文档。

## 产品流程

```text
用户选择 PDF
    ↓
移动端上传到 FastAPI
    ↓
后端提取 PDF 文本并调用 OpenAI-compatible AI API
    ↓
返回总结、重点和 USER_DRAFT 知识卡
    ↓
用户在移动端预览并确认
    ↓
保存到本地知识库
    ↓
滑动学习 / 主动回忆 / 间隔复习
```

AI 生成的内容先进入草稿状态，不会绕过用户确认直接进入学习流。

## 当前功能

### 移动端

- 欢迎页和新手引导；
- 知识库与学习内容分组；
- 选择 PDF、上传并轮询 AI 制卡任务；
- 草稿预览、质量提醒和保存到本地知识库；
- 学习卡片上下滑动切换，左右滑动表示“没记住”；
- 主动回忆模式：
  - 打开后进入全屏、不透明的盲答页面；
  - 原知识卡片的结论、解释、例子和底部导航都会被隐藏；
  - 用户先输入自己的回答，再查看标准答案、参考答案和解释；
  - 通过“记住了 / 部分记住 / 没记住”完成自评；
- 每日新卡数量、每日复习上限、提醒时间和 PDF 服务地址设置；
- Android 模拟器默认通过 `10.0.2.2` 访问宿主机服务。

移动端的学习进度、导入卡片和设置当前保存在设备本地，适合受信任用户测试。

### AI 制卡后端

- `POST /api/v1/summaries/text`：提交文本总结任务；
- `POST /api/v1/summaries/pdf`：上传 PDF 并创建制卡任务；
- `GET /api/v1/summaries/{task_id}`：轮询任务状态；
- `GET /health`：服务健康检查；
- 支持 OpenAI-compatible Chat Completions 接口；
- PDF 解析限制为可提取文字的 PDF，当前不包含 OCR；
- 任务使用内存存储，服务重启后任务会清空；
- 使用 `X-User-ID` 做开发期用户隔离，生产或共享环境应使用签名身份。

### 领域核心 MVP

`src/knowledge_card/` 将身份、内容、卡片交付、学习记录、复习计划、反馈、通知和埋点拆成独立服务，并通过 `KnowledgeCardApplication` 统一编排。

核心约束包括：

- 学习端只读取已发布卡片版本；
- 内容经过草稿、审核、发布和下线状态流转；
- 学习自评使用幂等键，避免重复写入；
- 复习计划按知识点合并并优先处理到期内容；
- 用户反馈和领域事件可被独立记录。

## 目录结构

```text
KnowledgeCard/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 路由、身份和 CORS
│   │   ├── ai_client.py     # OpenAI-compatible AI 客户端
│   │   ├── jobs.py          # 内存任务和后台处理
│   │   └── pdf_parser.py    # PDF 文字提取
│   ├── tests/               # 后端接口测试
│   └── README.md            # 后端接口说明
├── mobile/
│   ├── pages/               # 欢迎、引导、知识库、学习、设置
│   ├── utils/api.js         # PDF 上传和任务轮询客户端
│   ├── utils/mock-store.js  # 本地知识库和学习状态
│   ├── manifest.json        # 跨平台应用配置，不包含签名密码
│   └── README.md            # 移动端和 HarmonyOS 说明
├── miniprogram/             # 微信小程序 Mock 客户端
├── src/knowledge_card/      # 领域模型和应用服务
├── tests/                   # 领域单元测试
├── docs/                    # 需求、设计和验证文档
├── .gitignore               # 忽略环境、签名和构建产物
└── README.md
```

本地生成的 `mobile/unpackage/`、`mobile/pack/`、签名材料、虚拟环境和 `.env` 不提交到 Git。安装包应通过本地构建或 GitHub Release 分发，而不是放进源码提交。

## 环境要求

- Python 3.9 或更高版本；
- Node.js 与 npm（仅在需要使用 uni-app CLI 时使用）；
- HBuilderX 4.27 或更高版本；
- Android：Android SDK、Android Emulator 或 Android 真机；
- HarmonyOS NEXT：DevEco Studio、鸿蒙 SDK 和支持鸿蒙的 HBuilderX；
- 微信小程序：微信开发者工具；
- 一个可访问的 OpenAI-compatible AI 服务及其 API Key。

## 启动 AI 制卡后端

在仓库根目录执行：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate       # Windows 使用 .venv\Scripts\activate
python -m pip install -r requirements.txt
cp .env.example .env
```

编辑 `backend/.env`：

```dotenv
AI_BASE_URL=https://api.xiaomimimo.com/v1
AI_MODEL=mimo-v2.5-pro
AI_API_KEY=替换成自己的本地密钥

# 仅限本地测试；共享环境必须关闭并配置签名身份
ALLOW_INSECURE_DEV_IDENTITY=true
USER_ID_SIGNING_SECRET=
```

启动服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

接口文档：<http://127.0.0.1:8000/docs>

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## API 示例

### 文本制卡

```bash
curl -X POST http://127.0.0.1:8000/api/v1/summaries/text \
  -H 'X-User-ID: demo-user' \
  -H 'Content-Type: application/json' \
  -d '{"title":"项目管理基础","text":"项目是临时性的工作，运营是持续性的工作。"}'
```

### PDF 制卡

```bash
curl -X POST http://127.0.0.1:8000/api/v1/summaries/pdf \
  -H 'X-User-ID: demo-user' \
  -F 'title=我的学习资料' \
  -F 'file=@/absolute/path/to/document.pdf'
```

两个接口都会返回任务 ID。使用任务 ID 轮询：

```bash
curl http://127.0.0.1:8000/api/v1/summaries/<task_id> \
  -H 'X-User-ID: demo-user'
```

成功任务中的卡片草稿包含标题、结论、解释、例子、回忆提示、参考答案和来源页码，并带有 `USER_DRAFT` 状态。

## 运行移动端

### HBuilderX

1. 安装 HBuilderX。
2. 用 HBuilderX 打开仓库中的 `mobile/` 目录。
3. 选择运行到 Android 模拟器、Android 真机、iOS 或 HarmonyOS NEXT。
4. 如果只验证本地 UI，可以直接运行，客户端会使用内置 Mock 卡片。

Android 模拟器访问宿主机后端时，在 App 的「设置 → PDF 制卡服务」中使用：

```text
http://10.0.2.2:8000
```

Android 真机或 HarmonyOS 真机应填写电脑与手机处于同一局域网时的电脑 IP，例如：

```text
http://192.168.1.100:8000
```

### PDF 上传验证

1. 启动后端并确认 `/health` 返回 `status: ok`。
2. 在 App 设置中填写服务地址和本地用户标识。
3. 进入「知识库」，点击「上传 PDF」。
4. 选择不超过 10 MB 且可以提取文字的 PDF。
5. 等待任务完成，检查 AI 草稿和质量提醒。
6. 确认后点击「保存到知识库」。
7. 进入学习页验证卡片和主动回忆流程。

### HarmonyOS NEXT

HarmonyOS NEXT 需要使用对应版本的 HBuilderX、DevEco Studio 和鸿蒙 SDK：

1. 在 HBuilderX 中打开 `mobile/`。
2. 配置 `com.knowledgecard.app` 对应的本地签名证书。
3. 运行到鸿蒙设备进行测试。
4. 发行前在本机完成签名、隐私说明和权限检查。

仓库中的 `mobile/manifest.json` 只保留包名等非敏感配置。证书、`.p12`、`.p7b`、`.cer` 和密码必须通过本机 HBuilderX / DevEco Studio 配置，不要写回 Git。

## 运行测试

领域核心测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v
```

后端测试：

```bash
cd backend
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

提交前建议至少执行：

```bash
git diff --check
```

当前测试覆盖新用户闭环、内容审核隔离、PDF / 文本任务、用户身份隔离、自评幂等、复习计划、反馈和提醒等场景。

## 安全与部署边界

当前版本定位为本地或受信任用户测试版，不是生产部署版本：

- 不要提交 `backend/.env`、AI API Key、用户签名密钥或任何证书密码；
- `ALLOW_INSECURE_DEV_IDENTITY=true` 只适用于本机调试；
- 共享环境应设置 `USER_ID_SIGNING_SECRET`，并由已认证网关生成 `X-User-Signature`；
- 后端任务目前保存在内存，重启会丢失任务和结果；
- PDF 当前仅支持文字提取，不支持扫描件 OCR；
- 尚未接入正式登录、数据库、对象存储、异步队列、云端同步和正式通知；
- 上架 Android、AppGallery、App Store 或 HarmonyOS 应用市场前，还需要准备隐私政策、用户协议、图标、签名和正式服务地址。

## 相关文档

| 文档 | 内容 |
| --- | --- |
| [mobile/README.md](mobile/README.md) | 移动端、PDF 上传、Android 和 HarmonyOS 构建说明 |
| [backend/README.md](backend/README.md) | AI 制卡后端启动和接口示例 |
| [docs/proposal.md](docs/proposal.md) | 产品需求与用户流程 |
| [docs/user-pdf-import.md](docs/user-pdf-import.md) | PDF 上传、解析、AI 制卡和用户审核流程 |
| [docs/module-design.md](docs/module-design.md) | 模块边界、数据对象和接口设计 |
| [docs/wechat-mock-verification.md](docs/wechat-mock-verification.md) | 微信小程序 Mock 验证清单 |

## 后续计划

1. 将移动端本地 Mock 学习状态替换为正式 API 和云端持久化。
2. 增加登录、用户身份签名、数据库、对象存储和任务队列。
3. 增加扫描 PDF 的 OCR 处理和更严格的卡片质量检查。
4. 完善草稿编辑、审核历史、卡片版本和跨设备同步。
5. 完成 Android、HarmonyOS NEXT 和 iOS 的正式发布准备。

## License

当前仓库尚未声明开源许可证。如需公开分发或接受外部贡献，请先补充明确的 License 文件。
