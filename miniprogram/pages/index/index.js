const api = require('../../utils/mock-api')
const { getNavMetrics } = require('../../utils/layout')

Page({
  data: {
    loading: true,
    onboardingCompleted: false,
    statusBarHeight: 20,
    navBarHeight: 44,
    navTotalHeight: 64,
    menuSideGap: 96
  },

  onLoad() {
    this.setData(getNavMetrics())
  },

  onShow() {
    this.setData(getNavMetrics())
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
