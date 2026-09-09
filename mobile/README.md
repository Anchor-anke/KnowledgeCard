# 知识卡移动端

这是 KnowledgeCard 的跨平台移动端，使用 **uni-app + Vue 3** 重写，可从同一套页面代码构建：

- Android
- 华为 Android 手机
- iOS
- HarmonyOS NEXT（需要 uni-app 的鸿蒙构建链）

当前移动端保留原小程序的核心体验：欢迎页、新手引导、知识库、滑动学习和设置。知识库页已支持选择 PDF，调用本地 AI 后端生成可审核的卡片草稿，并在确认后保存到设备本地。

## 开发环境

### Android / iOS

1. 安装最新版 [HBuilderX](https://www.dcloud.io/hbuilderx.html)。
2. 在 HBuilderX 中打开仓库里的 `mobile/` 目录。
3. 运行到 Android 模拟器、Android 真机或 iOS 模拟器。
4. 真机发行时，在「发行 → 原生 App-云打包」中配置 Android 签名或 iOS 证书。

普通华为 Android 手机直接安装 Android APK / AAB 即可；如果接入华为推送、华为账号或 AppGallery 内购，再增加 HMS 原生配置。

### HarmonyOS NEXT

HarmonyOS NEXT 需要使用支持鸿蒙的 HBuilderX，并安装 DevEco Studio 与鸿蒙 SDK：

1. 使用 Vue 3 项目打开 `mobile/`。
2. 在 HBuilderX 中运行到鸿蒙设备。
3. 按 DevEco Studio 要求配置签名证书。
4. 通过鸿蒙构建流程生成并提交 App 包。

建议使用 HBuilderX 4.27 及以上；如果使用 uni-app x 项目能力，按当前官方文档使用 HBuilderX 4.61 及以上和对应 DevEco Studio 版本。

官方说明：[uni-app HarmonyOS NEXT](https://uniapp.dcloud.net.cn/tutorial/harmony.html)

## 页面与手势

- 欢迎页：查看产品价值并开始使用
- 新手引导：上滑下一步、下滑返回、左右跳过
- 知识库：选择 CAPM 全部知识或 Domain 分组
- 学习页：上滑下一张、下滑上一张、左右标记「没记住」，也可使用底部按钮；正文独立滚动，主动回忆保持全屏盲答
- 设置页：每组新卡、每组复习、提醒偏好和意见反馈；PDF 服务配置可展开查看

## PDF 制卡

1. 启动 `backend` 服务：`uvicorn app.main:app --host 0.0.0.0 --port 8000`。
2. 在 App 的「设置 → PDF 制卡服务」填写服务地址。Android 模拟器使用 `http://10.0.2.2:8000`，真机使用电脑局域网 IP。
3. 进入「知识库」，点击「上传 PDF」，选择不超过 10 MB、可提取文字的 PDF。
4. 等待 AI 草稿生成，确认预览后点击「保存到知识库」。卡片会保存在设备本地，并自动切换到新资料组。

## 当前边界

- `utils/mock-store.js` 使用本地存储，仅用于演示和端到端体验验证。
- 客户端同时保留内置 CAPM 演示卡组与用户导入的 PDF 卡组。
- 当前 PDF 任务和本地学习进度仍是本地原型；服务重启后未持久化任务，卡片保存后保留在设备本地。
- 真实账号、云端同步和推送服务尚未接入；部署到受信任用户前，应把 `ALLOW_INSECURE_DEV_IDENTITY` 关闭并接入真实身份签名网关。
- 上架 Android、AppGallery、App Store 或 HarmonyOS 应用市场前，还需要准备隐私政策、用户协议、应用图标、签名证书和真实服务地址。
