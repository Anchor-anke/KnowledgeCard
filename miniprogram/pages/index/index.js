const api = require('../../utils/mock-api')

Page({
  data: {
    loading: true,
    onboardingCompleted: false
  },

  onShow() {
    api.getSession().then((user) => {
      this.setData({
        loading: false,
        onboardingCompleted: user.onboardingCompleted
      })
    })
  },

  start() {
    if (this.data.loading) {
      return
    }
    if (this.data.onboardingCompleted) {
      wx.switchTab({ url: '/pages/library/library' })
      return
    }
    wx.redirectTo({ url: '/pages/onboarding/onboarding' })
  }
})

