# 知识卡移动端

这是 KnowledgeCard 的跨平台移动端，使用 **uni-app + Vue 3** 重写，可从同一套页面代码构建：

- Android
- 华为 Android 手机
- iOS
- HarmonyOS NEXT（需要 uni-app 的鸿蒙构建链）

当前移动端保留原小程序的核心体验：欢迎页、新手引导、知识库、滑动学习和设置。演示数据保存在设备本地，仍然是 Mock，不调用真实后端。

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
- 学习页：上滑下一张、下滑上一张、左右标记「没记住」
- 设置页：每日新卡、每日复习、提醒时间和意见反馈

## 当前边界

- `utils/mock-store.js` 使用本地存储，仅用于演示和端到端体验验证。
- 当前客户端仍使用内置 CAPM 演示卡组。
- 用户 PDF 上传、解析、AI 制卡、真实账号、云端同步和推送服务尚未接入。
- 上架 Android、AppGallery、App Store 或 HarmonyOS 应用市场前，还需要准备隐私政策、用户协议、应用图标、签名证书和真实服务地址。
