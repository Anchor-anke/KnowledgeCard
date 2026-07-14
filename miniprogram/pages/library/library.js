const api = require('../../utils/mock-api')

Page({
  data: {
    loading: true,
    decks: [],
    activeDeckId: 'all'
  },

  onShow() {
    this.load()
  },

  load() {
    this.setData({ loading: true })
    api.getLibrary().then((result) => {
      this.setData({
        loading: false,
        decks: result.decks,
        activeDeckId: result.activeDeckId
      })
    })
  },

  selectDeck(event) {
    const deckId = event.currentTarget.dataset.deckId
    if (!deckId) {
      return
    }
    api.setActiveDeck(deckId).then(() => {
      wx.switchTab({ url: '/pages/study/study' })
    }).catch(() => {
      wx.showToast({
        title: '暂时无法打开学习内容',
        icon: 'none'
      })
    })
  },

  openSettings() {
    wx.switchTab({ url: '/pages/settings/settings' })
  }
})
