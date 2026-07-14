const api = require('../../utils/mock-api')
const { getNavMetrics } = require('../../utils/layout')

Page({
  data: {
    user: {},
    activeDeckTitle: 'CAPM · 全部知识',
    newCardInput: '10',
    reviewInput: '20',
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
    this.load()
  },

  load() {
    Promise.all([api.getSettings(), api.getLibrary()]).then(([user, library]) => {
      let activeDeckTitle = 'CAPM · 全部知识'
      ;(library.collections || []).forEach((collection) => {
        const activeDeck = (collection.decks || []).find(
          (deck) => deck.id === library.activeDeckId
        )
        if (activeDeck) {
          activeDeckTitle = `${collection.title} · ${activeDeck.title}`
        }
      })
      this.setData({
        user,
        activeDeckTitle,
        newCardInput: String(user.newCardLimit || 10),
        reviewInput: String(user.reviewLimit || 20)
      })
    })
  },

  openLibrary() {
    wx.switchTab({ url: '/pages/library/library' })
  },

  parseLimit(value, fallback) {
    const number = Number(String(value || '').trim())
    if (!Number.isFinite(number) || number < 1) {
      return fallback
    }
    return Math.min(200, Math.floor(number))
  },

  onNewCardInput(event) {
    this.setData({ newCardInput: event.detail.value })
  },

  onReviewInput(event) {
    this.setData({ reviewInput: event.detail.value })
  },

  saveNewCardLimit() {
    const newCardLimit = this.parseLimit(this.data.newCardInput, this.data.user.newCardLimit || 10)
    this.setData({ newCardInput: String(newCardLimit) })
    if (newCardLimit === this.data.user.newCardLimit) {
      return
    }
    api.updateSettings({ newCardLimit }).then((user) => {
      this.setData({
        user,
        newCardInput: String(user.newCardLimit)
      })
      wx.showToast({ title: '已更新每日新卡', icon: 'none' })
    })
  },

  saveReviewLimit() {
    const reviewLimit = this.parseLimit(this.data.reviewInput, this.data.user.reviewLimit || 20)
    this.setData({ reviewInput: String(reviewLimit) })
    if (reviewLimit === this.data.user.reviewLimit) {
      return
    }
    api.updateSettings({ reviewLimit }).then((user) => {
      this.setData({
        user,
        reviewInput: String(user.reviewLimit)
      })
      wx.showToast({ title: '已更新每日复习', icon: 'none' })
    })
  },

  onReminderChange(event) {
    const reminderTime = event.detail.value
    api.updateSettings({ reminderTime }).then((user) => {
      this.setData({ user })
      wx.showToast({ title: '提醒时间已更新', icon: 'none' })
    })
  },

  toggleSubscription() {
    const authorized = !this.data.user.subscriptionAuthorized
    api.requestSubscription(authorized).then((user) => {
      this.setData({ user })
      wx.showToast({
        title: authorized ? '已开启复习提醒' : '已关闭复习提醒',
        icon: 'none'
      })
    })
  },

  sendFeedback() {
    wx.showModal({
      title: '意见反馈',
      editable: true,
      placeholderText: '说说你想改进的地方',
      success: (result) => {
        if (!result.confirm) {
          return
        }
        const content = (result.content || '').trim()
        if (!content) {
          wx.showToast({ title: '请填写反馈内容', icon: 'none' })
          return
        }
        api.submitFeedback('settings', 'SUGGESTION', content).then(() => {
          wx.showToast({ title: '感谢你的反馈', icon: 'success' })
        })
      }
    })
  }
})
