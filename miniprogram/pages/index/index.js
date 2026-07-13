const api = require('../../utils/mock-api')

Page({
  data: {
    loading: true
  },

  onShow() {
    api.getSession().then((user) => {
      if (user.onboardingCompleted) {
        wx.switchTab({ url: '/pages/study/study' })
      } else {
        wx.redirectTo({ url: '/pages/onboarding/onboarding' })
      }
    })
  }
})

