const api = require('../../utils/mock-api')

Page({
  data: {
    user: {}
  },

  onShow() {
    this.load()
  },

  load() {
    api.getSettings().then((user) => {
      this.setData({ user })
    })
  },

  toggleSubscription() {
    const authorized = !this.data.user.subscriptionAuthorized
    api.requestSubscription(authorized).then(() => {
      this.load()
      wx.showToast({
        title: authorized ? '已模拟授权' : '已拒绝授权',
        icon: 'none'
      })
    })
  },

  makeReviewDue() {
    api.makeReviewDue().then(() => {
      wx.showToast({
        title: '已模拟到期任务',
        icon: 'success'
      })
      setTimeout(() => {
        wx.switchTab({ url: '/pages/study/study' })
      }, 500)
    })
  },

  resetDemo() {
    api.reset().then(() => {
      wx.reLaunch({ url: '/pages/index/index' })
    })
  }
})

