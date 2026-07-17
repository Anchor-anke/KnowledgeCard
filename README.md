# KnowledgeCard

把长资料变成短知识卡，用上下滑动学习、用间隔复习记住。

KnowledgeCard 是一款面向碎片时间的学习工具。产品方向是：用户上传自己的 PDF，由 AI 整理成可确认的知识卡，再进入滑动学习与间隔复习。当前仓库包含**跨平台移动端**、**微信小程序 Mock 客户端**、**本地 AI 总结后端**与**领域核心 MVP**；移动端演示内容仍使用内置 CAPM 卡组，真实 AI 制卡可通过本地后端验证。

## 当前版本包含什么

### 跨平台移动端（`mobile/`）

使用 **uni-app + Vue 3** 重写，一套页面代码面向 Android、华为 Android、iOS 和 HarmonyOS NEXT。移动端当前使用本地 Mock 数据，适合先在真机上验证产品体验。

详细的 HBuilderX、Android/iOS 签名和 HarmonyOS 构建说明见 [`mobile/README.md`](mobile/README.md)。

### AI 总结测试后端（`backend/`）

使用 **FastAPI + MiMo OpenAI-compatible API** 构建的本地原型，支持：

- 提交文本或可复制文字的 PDF；
- 生成资料总结、重点和知识卡草稿；
- 保留 PDF 页码来源；
- 通过任务状态轮询查看处理结果；
- 将卡片标记为 `USER_DRAFT`，不会绕过审核直接进入学习流。

后端当前用于效果验证，使用内存任务存储，不包含正式登录、数据库或对象存储。完整启动和接口说明见 [`backend/README.md`](backend/README.md)。

### 微信小程序 Mock（`miniprogram/`）

可在微信开发者工具中直接运行，数据保存在本地缓存，不依赖真实后端。

| 页面 | 说明 |
| --- | --- |
| 欢迎页 | 品牌介绍与开始使用入口 |
| 新手引导 | 卡片式教学，对齐真实学习手势 |
| 知识库 | CAPM 集合 → 全部知识 / Domain 1–4，展示进度并选择学习内容 |
| 学习 | 上下滑切换知识点，左右滑标记「没记住」 |
| 设置 | 每日新卡/复习量、提醒、反馈与关于 |

手势约定：

- **上滑**：下一张（组结束时批量确认「记住了」）
- **下滑**：上一张
- **左右滑**：标记「没记住」，并安排短期复习

顶部导航为自定义自适应栏，按状态栏与胶囊按钮位置适配不同机型。

### 领域核心（`src/knowledge_card/`）

Python 标准库实现的可运行领域 MVP，用适配器隔离存储、微信与 AI，便于后续替换真实实现：

- 身份与用户引导、学习量与订阅设置
- 内容工作流：草稿、审核、发布、版本与审计
- 卡片交付：用户端只读已发布版本
- 学习记录、自评幂等与修正
- 复习计划：逾期识别、知识点级合并
- 内容反馈、提醒门禁与埋点事件

### 文档（`docs/`）

| 文档 | 内容 |
| --- | --- |
| [proposal.md](docs/proposal.md) | 产品需求：用户 PDF → AI 制卡 → 学习复习 |
| [user-pdf-import.md](docs/user-pdf-import.md) | PDF 上传、解析、AI 生成与用户审核流程 |
| [module-design.md](docs/module-design.md) | 模块边界、数据对象与接口设计 |
| [wechat-mock-verification.md](docs/wechat-mock-verification.md) | 小程序 Mock 导入与验证清单 |

## 快速开始：移动端

1. 安装最新版 [HBuilderX](https://www.dcloud.io/hbuilderx.html)。
2. 在 HBuilderX 中打开 `mobile/` 目录。
3. 选择运行到 Android、iOS 或 HarmonyOS NEXT 设备。
4. 真机发行前，配置对应平台的签名证书和隐私说明。

普通华为 Android 手机使用 Android 包即可；HarmonyOS NEXT 按 [`mobile/README.md`](mobile/README.md) 的鸿蒙构建说明操作。

## 快速开始：AI 总结后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

编辑 `backend/.env`，填写自己的 `AI_API_KEY`。默认配置使用 MiMo：

```dotenv
AI_BASE_URL=https://api.xiaomimimo.com/v1
AI_MODEL=mimo-v2.5-pro
AI_API_KEY=your-local-api-key
```

启动服务并打开接口文档：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

访问 <http://127.0.0.1:8000/docs>，可测试文本总结和 PDF 转知识卡片。

## 快速开始：微信小程序

1. 安装并打开[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)。
2. 选择「导入项目」，目录选仓库根目录（读取 `project.config.json`，小程序根目录为 `miniprogram/`）。
3. AppID 可先用测试号。
4. 按 [wechat-mock-verification.md](docs/wechat-mock-verification.md) 走通欢迎 → 引导 → 知识库 → 学习 → 设置。

Mock API 位于 `miniprogram/utils/mock-api.js`。接入真实后端时，将这些方法换成 `wx.request` 即可，页面内不应直接改学习计划或卡片数据。

## 运行领域测试

需要 Python 3.9+，无第三方依赖：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

覆盖新用户闭环、未发布内容隔离、自评与幂等、到期复习优先、逾期合并、内容状态机、反馈与提醒等场景。

后端原型测试：

```bash
PYTHONPATH=backend backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

## 仓库结构

```text
KnowledgeCard/
├── backend/              # FastAPI AI 总结与 PDF 转卡片测试后端
│   ├── app/              # API、AI 客户端、任务和 PDF 解析
│   └── tests/            # 后端接口与 Fake AI 测试
├── mobile/               # uni-app 跨平台移动端
│   ├── pages/            # 欢迎 / 引导 / 知识库 / 学习 / 设置
│   ├── utils/            # 本地 Mock 数据与布局
│   └── static/           # 图标资源
├── miniprogram/          # 微信小程序 Mock 客户端
│   ├── pages/            # 欢迎 / 引导 / 知识库 / 学习 / 设置
│   ├── utils/            # mock-api、自适应布局
│   └── assets/           # TabBar 图标
├── src/knowledge_card/   # Python 领域核心
├── tests/                # 领域单元测试
├── docs/                 # 需求与设计文档
└── project.config.json   # 微信开发者工具项目配置
```

## 边界说明

- 当前移动端和小程序仍为 **Mock**：尚未接入真实登录、HTTP API 或后端审核页面。
- `backend/` 是用于本地效果验证的原型：使用内存任务存储，尚未接入生产数据库、对象存储、正式鉴权和队列。
- **用户 PDF 上传 / 解析 / AI 制卡**已在后端原型和需求文档中定义，移动端上传与审核页面尚未接入。
- CAPM 为演示与可选学习场景，不是唯一内容来源。
- 领域服务通过 `KnowledgeCardApplication` 与 repositories / adapters 扩展；不要绕过领域层直接改业务状态。

## 下一步

- 将移动端和小程序的资料上传、处理进度、草稿审核页面接入 `backend/`
- 将后端内存任务替换为正式鉴权、对象存储、数据库和异步队列
- 接入微信登录、订阅消息与持久化存储
