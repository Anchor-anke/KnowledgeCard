App({
  globalData: {
    sessionId: `mock-session-${Date.now()}`
  },
  onLaunch() {
    const updateManager = wx.getUpdateManager && wx.getUpdateManager()
    if (updateManager) {
      updateManager.onCheckForUpdate(() => {})
    }
  }
})

