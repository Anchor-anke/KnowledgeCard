# 微信开发者工具 Mock 验证

当前仓库已经增加一个原生微信小程序 Mock 客户端，用于先验证用户流程。它不调用真实微信登录、真实 API 或真实订阅消息，数据保存于开发者工具本地缓存。

## 导入项目

1. 安装并打开微信开发者工具。
2. 选择“导入项目”。
3. 项目目录选择仓库根目录：

   `/Users/anchorxia/KnowledgeCard`

4. 开发者工具会读取根目录的 `project.config.json`，并将 `miniprogram/` 作为小程序根目录。
5. AppID 可以先使用测试号；正式接入时替换为真实小程序 AppID。

## 推荐验证流程

1. 首次打开进入“开始学习”页。
2. 点击“确认 CAPM 学习目标”。
3. 在学习页查看第一张卡。
4. 左右滑动卡片，确认自动提交“模糊”，并安排 1 天后复习。
5. 手指从下往上滑，确认进入下一个知识点并出现滑入动效；手指从上往下滑，确认返回上一个知识点。
6. 通过“忘了”或“记住了”按钮提交另外两种自评。
7. 在设置页点击“模拟产生到期复习”。
8. 返回学习页，确认“到期复习”优先于新卡。
9. 点击“发现内容问题”，确认反馈可以提交。
10. 切换订阅消息开关，确认拒绝授权不会阻断学习。
11. 点击“重置 Mock 学习数据”，重新开始流程。

## Mock 与真实服务的边界

Mock API 位于 `miniprogram/utils/mock-api.js`。它保持了未来 HTTP API 的主要方法边界：

- `getSession`
- `completeOnboarding`
- `getLearningEntry`
- `completeCard`
- `submitRating`
- `requestSubscription`
- `submitFeedback`

接入真实后端时，只需要将这些方法替换为 `wx.request` 调用，不应在页面中直接修改学习计划或卡片数据。

