# KnowledgeCard

把长资料变成短知识卡，用上下滑动学习、用间隔复习记住。

KnowledgeCard 是一款面向碎片时间的微信小程序学习工具。产品方向是：用户上传自己的 PDF，由 AI 整理成可确认的知识卡，再进入滑动学习与间隔复习。当前仓库已交付**领域核心 MVP**与**微信小程序 Mock 客户端**；演示内容仍使用内置 CAPM 卡组，用户 PDF 上传与真实 AI 生成见后续文档。

## 当前版本包含什么

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

## 仓库结构

```text
KnowledgeCard/
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

- 当前小程序为 **Mock**：无真实微信登录、HTTP API、生产库或真实 AI。
- **用户 PDF 上传 / 解析 / AI 制卡**已在需求与流程文档中定义，尚未接入客户端。
- CAPM 为演示与可选学习场景，不是唯一内容来源。
- 领域服务通过 `KnowledgeCardApplication` 与 repositories / adapters 扩展；不要绕过领域层直接改业务状态。

## 下一步

- 接入用户 PDF 导入与 AI 草稿生成（见 `docs/user-pdf-import.md`）
- 用真实 HTTP API 替换 `mock-api.js`
- 接入微信登录、订阅消息与持久化存储
