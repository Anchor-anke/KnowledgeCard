const api = require('../../utils/mock-api')
const { getNavMetrics } = require('../../utils/layout')

Page({
  data: {
    submitting: false,
    currentStep: 0,
    demoAnimation: '',
    gestureResult: '',
    gestureResultType: '',
    touchStartX: 0,
    touchStartY: 0,
    statusBarHeight: 20,
    navBarHeight: 44,
    navTotalHeight: 64,
    menuSideGap: 96,
    steps: [
      {
        eyebrow: 'STEP 01',
        title: '把长资料，变成短卡片',
        description: '上传你的学习资料，AI 会帮你提取重点，整理成一张张轻量知识卡。',
        visual: 'PDF',
        visualCaption: '资料 → 知识卡'
      },
      {
        eyebrow: 'STEP 02',
        title: '一张卡，只讲一个重点',
        description: '每张卡都只解决一个知识目标，让你在碎片时间也能快速理解。',
        visual: '30s',
        visualCaption: '短时间 · 高专注'
      },
      {
        eyebrow: 'STEP 03',
        title: '用滑动告诉我们',
        description: '上下滑动表示记住了，左右滑动表示没记住。简单的动作就是你的学习反馈。',
        visual: '↕',
        visualCaption: '滑动 · 反馈'
      },
      {
        eyebrow: 'STEP 04',
        title: '在合适的时间再次复习',
        description: '系统会根据你的学习反馈安排复习，让知识从“看过”变成“记得住”。',
        visual: '03',
        visualCaption: '间隔复习 · 长期记忆'
      }
    ]
  },

  onLoad() {
    this.setData(getNavMetrics())
  },

  onShow() {
    this.setData(getNavMetrics())
  },

  onTouchStart(event) {
    const touch = event.touches[0]
    this.setData({
      touchStartX: touch.clientX,
      touchStartY: touch.clientY
    })
  },

  onTouchMove() {},

  onTouchEnd(event) {
    const touch = event.changedTouches[0]
    const deltaX = touch.clientX - this.data.touchStartX
    const deltaY = touch.clientY - this.data.touchStartY
    const distanceX = Math.abs(deltaX)
    const distanceY = Math.abs(deltaY)

    if (Math.max(distanceX, distanceY) < 45) {
      wx.showToast({ title: '试着滑动卡片', icon: 'none' })
      return
    }

    const isVertical = distanceY >= distanceX
    const remembered = isVertical
    const animation = isVertical
      ? (deltaY < 0 ? 'demo-swipe-up' : 'demo-swipe-down')
      : (deltaX < 0 ? 'demo-swipe-left' : 'demo-swipe-right')
    const movingBack = isVertical && deltaY > 0

    if (movingBack && this.data.currentStep === 0) {
      return
    }

    this.setData({
      demoAnimation: animation,
      gestureResult: remembered ? '记住了' : '没记住',
      gestureResultType: remembered ? 'remembered' : 'not-remembered'
    })

    clearTimeout(this.demoAnimationTimer)
    this.demoAnimationTimer = setTimeout(() => {
      if (
        !movingBack &&
        this.data.currentStep >= this.data.steps.length - 1
      ) {
        this.start()
        return
      }
      this.setData({
        currentStep: movingBack
          ? this.data.currentStep - 1
          : this.data.currentStep + 1,
        demoAnimation: '',
        gestureResult: '',
        gestureResultType: ''
      })
    }, 320)
  },

  start() {
    if (this.data.submitting) {
      return
    }
    this.setData({ submitting: true })
    api.completeOnboarding('CAPM').then(() => {
      wx.switchTab({
        url: '/pages/library/library',
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
