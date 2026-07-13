const api = require('../../utils/mock-api')

Page({
  data: {
    sessionId: '',
    mode: 'NEW',
    tasks: [],
    cards: [],
    current: 0,
    skippedPointIds: [],
    cardAnimation: '',
    loading: true,
    submitting: false,
    lastFeedback: ''
  },

  onLoad() {
    const app = getApp()
    this.setData({
      sessionId: app.globalData.sessionId
    })
  },

  onShow() {
    this.loadEntry()
  },

  loadEntry() {
    this.setData({ loading: true })
    api.getLearningEntry(this.data.skippedPointIds).then((entry) => {
      this.setData({
        mode: entry.mode,
        tasks: entry.tasks,
        cards: entry.cards,
        current: 0,
        cardAnimation: '',
        loading: false,
        lastFeedback: ''
      })
    })
  },

  onTouchStart(event) {
    const touch = event.touches[0]
    this.touchStart = {
      x: touch.clientX,
      y: touch.clientY
    }
  },

  onTouchEnd(event) {
    if (!this.touchStart || !event.changedTouches.length) {
      return
    }
    const touch = event.changedTouches[0]
    const deltaX = touch.clientX - this.touchStart.x
    const deltaY = touch.clientY - this.touchStart.y
    this.touchStart = null
    if (Math.max(Math.abs(deltaX), Math.abs(deltaY)) < 45) {
      return
    }
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      this.submitVague()
    } else if (deltaY < 0) {
      this.nextCard()
    } else {
      this.previousCard()
    }
  },

  nextCard() {
    const card = this.data.cards[this.data.current]
    if (!card) {
      return
    }
    const skippedPointIds = this.data.skippedPointIds.concat(card.knowledgePointId)
    if (this.data.current < this.data.cards.length - 1) {
      this.setData({
        current: this.data.current + 1,
        skippedPointIds,
        cardAnimation: 'slide-next'
      })
      setTimeout(() => this.setData({ cardAnimation: '' }), 280)
      return
    }
    this.setData({
      skippedPointIds,
      cardAnimation: 'slide-next'
    })
    setTimeout(() => this.loadEntry(), 280)
  },

  previousCard() {
    if (this.data.current <= 0) {
      wx.showToast({
        title: '已经是第一张',
        icon: 'none'
      })
      return
    }
    const previousCard = this.data.cards[this.data.current - 1]
    const skippedPointIds = this.data.skippedPointIds.filter(
      (pointId) => pointId !== previousCard.knowledgePointId
    )
    this.setData({
      current: this.data.current - 1,
      skippedPointIds,
      cardAnimation: 'slide-previous'
    })
    setTimeout(() => this.setData({ cardAnimation: '' }), 280)
  },

  submitVague() {
    this.submitRating('VAGUE')
  },

  submitExplicitRating(event) {
    this.submitRating(event.currentTarget.dataset.rating)
  },

  submitRating(rating) {
    const card = this.data.cards[this.data.current]
    if (!card || this.data.submitting) {
      return
    }
    const key = `${this.data.sessionId}:${card.id}:${rating.toLowerCase()}:${Date.now()}`
    this.setData({ submitting: true })
    api.completeCard(card.id, this.data.sessionId).then(() => {
      return api.submitRating(card.id, this.data.sessionId, 'VAGUE', key)
    }).then((result) => {
      this.setData({
        submitting: false,
        lastFeedback: result.plan.reason
      })
      setTimeout(() => this.loadEntry(), 800)
    }).catch((error) => {
      this.setData({ submitting: false })
      wx.showToast({
        title: error.message || '提交失败',
        icon: 'none'
      })
    })
  },

  sendFeedback() {
    const card = this.data.cards[this.data.current]
    if (!card) {
      return
    }
    wx.showModal({
      title: '反馈卡片问题',
      editable: true,
      placeholderText: '可填写具体问题',
      success: (result) => {
        if (result.confirm) {
          api.submitFeedback(card.id, 'ERROR', result.content).then(() => {
            wx.showToast({ title: '反馈已提交', icon: 'success' })
          })
        }
      }
    })
  },

  openSettings() {
    wx.switchTab({ url: '/pages/settings/settings' })
  },

  resetDemo() {
    api.reset().then(() => {
      wx.reLaunch({ url: '/pages/index/index' })
    })
  }
})

