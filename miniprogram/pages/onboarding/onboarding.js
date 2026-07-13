const api = require('../../utils/mock-api')

Page({
  data: {
    submitting: false
  },

  start() {
    if (this.data.submitting) {
      return
    }
    this.setData({ submitting: true })
    api.completeOnboarding('CAPM').then(() => {
      wx.switchTab({
        url: '/pages/study/study',
        fail: () => {
          this.setData({ submitting: false })
          wx.showToast({ title: '无法打开学习页', icon: 'none' })
        }
      })
    }).catch(() => {
      this.setData({ submitting: false })
      wx.showToast({ title: '保存学习目标失败', icon: 'none' })
    })
  }
})

