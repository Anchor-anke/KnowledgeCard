const { getNavMetrics } = require('../../utils/layout')
const api = require('../../utils/mock-api')

Page({
  data: {
    loading: true,
    collections: [],
    activeDeckId: 'capm-all',
    expandedCollectionId: 'capm',
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
    this.setData({ loading: true })
    api.getLibrary().then((result) => {
      const activeCollection = (result.collections || []).find(
        (collection) => collection.hasActiveDeck
      )
      this.setData({
        loading: false,
        collections: result.collections,
        activeDeckId: result.activeDeckId,
        expandedCollectionId: activeCollection
          ? activeCollection.id
          : this.data.expandedCollectionId || 'capm'
      })
    })
  },

  toggleCollection(event) {
    const collectionId = event.currentTarget.dataset.collectionId
    if (!collectionId) {
      return
    }
    this.setData({
      expandedCollectionId:
        this.data.expandedCollectionId === collectionId ? '' : collectionId
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
