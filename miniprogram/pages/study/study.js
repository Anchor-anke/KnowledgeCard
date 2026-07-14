const api = require('../../utils/mock-api')
const { getNavMetrics, getStudyViewportHeight } = require('../../utils/layout')

Page({
  data: {
    sessionId: '',
    mode: 'NEW',
    tasks: [],
    cards: [],
    stats: {
      totalCards: 0,
      learnedCards: 0,
      completionPercent: 0
    },
    current: 0,
    skippedPointIds: [],
    pendingRememberedCardIds: [],
    groupId: '',
    scrollTop: 0,
    statusBarHeight: 20,
    navBarHeight: 44,
    navTotalHeight: 64,
    menuSideGap: 96,
    cardMinHeight: 384,
    cardContentMaxHeight: 480,
    cardViewportHeight: 480,
    cardAnimation: '',
    loading: true,
    submitting: false,
    committing: false,
    groupCompleted: false,
    lastFeedback: ''
  },

  onLoad() {
    const app = getApp()
    const nav = getNavMetrics()
    this.setData({
      sessionId: app.globalData.sessionId,
      statusBarHeight: nav.statusBarHeight,
      navBarHeight: nav.navBarHeight,
      navTotalHeight: nav.navTotalHeight,
      menuSideGap: nav.menuSideGap
    })
    this.updateCardContentHeight()
    if (wx.onWindowResize) {
      this.windowResizeHandler = (result) => {
        const nextNav = getNavMetrics()
        this.setData({
          statusBarHeight: nextNav.statusBarHeight,
          navBarHeight: nextNav.navBarHeight,
          navTotalHeight: nextNav.navTotalHeight,
          menuSideGap: nextNav.menuSideGap
        })
        this.updateCardContentHeight(result && result.size && result.size.windowHeight)
      }
      wx.onWindowResize(this.windowResizeHandler)
    }
  },

  onShow() {
    const nav = getNavMetrics()
    this.setData({
      statusBarHeight: nav.statusBarHeight,
      navBarHeight: nav.navBarHeight,
      navTotalHeight: nav.navTotalHeight,
      menuSideGap: nav.menuSideGap,
      skippedPointIds: []
    }, () => {
      this.updateCardContentHeight()
      this.loadEntry()
    })
  },

  onUnload() {
    if (wx.offWindowResize && this.windowResizeHandler) {
      wx.offWindowResize(this.windowResizeHandler)
    }
  },

  applyViewportHeight(cardTop, windowHeight) {
    const result = getStudyViewportHeight({
      navTotalHeight: this.data.navTotalHeight,
      cardTop,
      windowHeight
    })
    if (
      result.availableHeight !== this.data.cardContentMaxHeight ||
      result.availableHeight !== this.data.cardViewportHeight ||
      result.minCardHeight !== this.data.cardMinHeight
    ) {
      this.setData({
        cardMinHeight: result.minCardHeight,
        cardContentMaxHeight: result.availableHeight,
        cardViewportHeight: result.availableHeight
      })
    }
  },

  updateCardContentHeight(windowHeight) {
    const measure = () => {
      if (!this.data.loading && this.data.cards.length) {
        wx.createSelectorQuery()
          .in(this)
          .select('.card-viewport')
          .boundingClientRect((rect) => {
            this.applyViewportHeight(
              rect && typeof rect.top === 'number' ? rect.top : null,
              windowHeight
            )
          })
          .exec()
        return
      }
      this.applyViewportHeight(null, windowHeight)
    }

    measure()
    // Huawei layout often settles one frame later.
    setTimeout(measure, 64)
  },

  loadEntry() {
    this.setData({
      loading: true,
      groupCompleted: false
    })
    api.getLearningEntry(this.data.skippedPointIds).then((entry) => {
      this.setData({
        mode: entry.mode,
        tasks: entry.tasks,
        cards: entry.cards,
        stats: entry.stats,
        current: 0,
        pendingRememberedCardIds: [],
        groupId: `${this.data.sessionId}:${Date.now()}`,
        scrollTop: 0,
        cardAnimation: '',
        loading: false,
        groupCompleted: false,
        lastFeedback: ''
      }, () => {
        this.updateCardContentHeight()
      })
    })
  },

  onTouchStart(event) {
    const touch = event.touches[0]
    this.cardContentMoved = false
    this.cardScrollTop = this.cardScrollTop || 0
    this.touchStart = {
      x: touch.clientX,
      y: touch.clientY
    }
  },

  onCardScroll(event) {
    const scrollTop = event.detail && event.detail.scrollTop
    if (this.touchStart && scrollTop !== this.cardScrollTop) {
      this.cardContentMoved = true
    }
    if (typeof scrollTop === 'number') {
      this.cardScrollTop = scrollTop
    }
  },

  onTouchEnd(event) {
    if (this.data.submitting || this.data.committing) {
      this.touchStart = null
      this.cardContentMoved = false
      return
    }
    if (!this.touchStart || !event.changedTouches.length) {
      return
    }
    const cardContentMoved = this.cardContentMoved
    const touch = event.changedTouches[0]
    const deltaX = touch.clientX - this.touchStart.x
    const deltaY = touch.clientY - this.touchStart.y
    this.touchStart = null
    this.cardContentMoved = false
    if (cardContentMoved) {
      return
    }
    if (Math.max(Math.abs(deltaX), Math.abs(deltaY)) < 45) {
      return
    }
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      this.submitNotRemembered(deltaX < 0 ? 'left' : 'right')
    } else if (deltaY < 0) {
      const pendingIds = this.rememberCurrentForGroup()
      this.nextCard(pendingIds)
    } else if (this.data.current <= 0) {
      this.previousCard()
    } else {
      this.rememberCurrentForGroup()
      this.previousCard()
    }
  },

  rememberCurrentForGroup() {
    const card = this.data.cards[this.data.current]
    if (!card) {
      return this.data.pendingRememberedCardIds
    }
    const pendingIds = this.data.pendingRememberedCardIds.indexOf(card.id) >= 0
      ? this.data.pendingRememberedCardIds
      : this.data.pendingRememberedCardIds.concat(card.id)
    this.setData({ pendingRememberedCardIds: pendingIds })
    return pendingIds
  },

  nextCard(pendingIds) {
    const card = this.data.cards[this.data.current]
    if (!card) {
      return
    }
    const skippedPointIds = this.data.skippedPointIds.concat(card.knowledgePointId)
    if (this.data.current < this.data.cards.length - 1) {
      this.setData({
        current: this.data.current + 1,
        skippedPointIds,
        scrollTop: 0,
        cardAnimation: 'slide-next'
      })
      setTimeout(() => this.setData({ cardAnimation: '' }), 280)
      return
    }
    this.setData({
      skippedPointIds,
      scrollTop: 0,
      cardAnimation: ''
    })
    this.finishGroup(pendingIds || this.data.pendingRememberedCardIds)
  },

  previousCard() {
    if (this.data.current <= 0) {
      return
    }
    const previousCard = this.data.cards[this.data.current - 1]
    const skippedPointIds = this.data.skippedPointIds.filter(
      (pointId) => pointId !== previousCard.knowledgePointId
    )
    this.setData({
      current: this.data.current - 1,
      skippedPointIds,
      scrollTop: 0,
      cardAnimation: 'slide-previous'
    })
    setTimeout(() => this.setData({ cardAnimation: '' }), 280)
  },

  submitNotRemembered(direction) {
    const card = this.data.cards[this.data.current]
    if (!card || this.data.submitting || this.data.committing) {
      return
    }
    const pendingIds = this.data.pendingRememberedCardIds.filter(
      (cardId) => cardId !== card.id
    )
    this.setData({
      cardAnimation: `slide-not-remembered-${direction}`,
      pendingRememberedCardIds: pendingIds
    })
    this.submitRating('NOT_REMEMBERED', () => {
      setTimeout(() => this.removeCurrentCard(), 320)
    })
  },

  removeCurrentCard() {
    const cards = this.data.cards.slice()
    cards.splice(this.data.current, 1)
    if (!cards.length) {
      this.setData({
        cards: [],
        current: 0,
        scrollTop: 0,
        cardAnimation: ''
      })
      this.finishGroup(this.data.pendingRememberedCardIds)
      return
    }
    this.setData({
      cards,
      current: Math.min(this.data.current, cards.length - 1),
      scrollTop: 0,
      cardAnimation: 'slide-next'
    })
    setTimeout(() => this.setData({ cardAnimation: '' }), 280)
  },

  finishGroup(pendingIds) {
    const cardIds = Array.from(new Set(pendingIds || []))
    if (!cardIds.length) {
      this.setData({
        groupCompleted: true,
        lastFeedback: '本组已完成，复习计划已安排'
      })
      return
    }
    if (this.data.committing) {
      return
    }
    this.setData({
      committing: true,
      groupCompleted: true,
      lastFeedback: '正在安排复习计划…'
    })
    api.submitRememberedBatch(cardIds, this.data.sessionId, this.data.groupId).then(() => {
      this.setData({
        committing: false,
        pendingRememberedCardIds: [],
        lastFeedback: `本组已完成 ${cardIds.length} 张，复习计划已安排`
      })
    }).catch((error) => {
      this.setData({
        committing: false,
        groupCompleted: false
      })
      wx.showToast({
        title: error.message || '复习计划保存失败',
        icon: 'none'
      })
    })
  },

  submitRating(rating, onComplete) {
    const card = this.data.cards[this.data.current]
    if (!card || this.data.submitting) {
      return
    }
    const key = `${this.data.sessionId}:${card.id}:${rating.toLowerCase()}:${Date.now()}`
    this.setData({ submitting: true })
    api.completeCard(card.id, this.data.sessionId).then(() => {
      return api.submitRating(card.id, this.data.sessionId, rating, key)
    }).then((result) => {
      this.setData({
        submitting: false,
        lastFeedback: result.plan.reason
      })
      if (onComplete) {
        onComplete()
      } else {
        setTimeout(() => this.loadEntry(), 800)
      }
    }).catch((error) => {
      this.setData({
        submitting: false,
        cardAnimation: ''
      })
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
