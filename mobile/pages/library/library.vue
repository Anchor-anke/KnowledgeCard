<template>
  <view class="page library-page">
    <view class="custom-nav" :style="{ height: navTotalHeight + 'px' }">
      <view :style="{ height: statusBarHeight + 'px' }"></view>
      <view
        class="custom-nav-bar"
        :style="{ height: navBarHeight + 'px' }"
      >
        <view class="nav-title-wrap">
          <view class="nav-eyebrow">MY LIBRARY</view>
          <view class="nav-title">选择学习内容</view>
        </view>
        <view class="nav-action" @tap="openSettings">设置</view>
      </view>
    </view>

    <view class="library-body" :style="{ paddingTop: navTotalHeight + 'px' }">
      <view v-if="loading" class="library-loading card-panel">
        <text class="muted">正在整理你的学习内容…</text>
      </view>

      <view v-else class="collection-list">
        <view
          v-for="(item, index) in collections"
          :key="item.id"
          :class="['collection-card', { active: item.hasActiveDeck }]"
        >
          <view class="collection-main" @tap="toggleCollection(item.id)">
            <view :class="['deck-cover', `deck-cover-${index}`]">
              <text class="cover-label">{{ item.label }}</text>
              <text class="cover-mark">{{ item.coverMark }}</text>
              <view class="cover-line"></view>
            </view>
            <view class="deck-info">
              <view class="deck-heading">
                <text class="deck-title">{{ item.title }}</text>
                <text class="expand-mark">
                  {{ expandedCollectionId === item.id ? '收起' : '展开' }}
                </text>
              </view>
              <text class="deck-subtitle">{{ item.subtitle }}</text>
              <view class="deck-progress-summary">
                <text>{{ item.stats.learnedCards }} / {{ item.stats.totalCards }} 张已学</text>
                <text>{{ item.stats.completionPercent }}%</text>
              </view>
              <view class="deck-progress-track">
                <view
                  class="deck-progress-fill"
                  :style="{ width: item.stats.completionPercent + '%' }"
                ></view>
              </view>
              <text v-if="item.stats.dueCards" class="due-hint">
                {{ item.stats.dueCards }} 张待复习
              </text>
              <text v-else class="deck-action">
                {{ item.decks.length }} 个知识点分组
              </text>
            </view>
          </view>

          <view v-if="expandedCollectionId === item.id" class="subdeck-list">
            <view
              v-for="deck in item.decks"
              :key="deck.id"
              :class="['subdeck-row', { active: deck.id === activeDeckId }]"
              @tap.stop="selectDeck(deck.id)"
            >
              <view class="subdeck-copy">
                <view class="subdeck-heading">
                  <text class="subdeck-label">{{ deck.label }}</text>
                  <text v-if="deck.id === activeDeckId" class="active-badge">正在学习</text>
                </view>
                <text class="subdeck-title">{{ deck.title }}</text>
                <text class="subdeck-subtitle">{{ deck.subtitle }}</text>
              </view>
              <view class="subdeck-meta">
                <text class="subdeck-progress">
                  {{ deck.stats.learnedCards }}/{{ deck.stats.totalCards }}
                </text>
                <text v-if="deck.stats.dueCards" class="subdeck-due">
                  {{ deck.stats.dueCards }} 待复习
                </text>
                <text v-else class="subdeck-enter">进入 →</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { api } from '../../utils/mock-store'
import { getNavMetrics, showError } from '../../utils/layout'

export default {
  data() {
    const navMetrics = getNavMetrics()
    return {
      loading: true,
      collections: [],
      activeDeckId: 'capm-all',
      expandedCollectionId: 'capm',
      ...navMetrics
    }
  },
  onShow() {
    Object.assign(this, getNavMetrics())
    this.load()
  },
  methods: {
    load() {
      // Keep the current list visible while the tab is refreshed. This avoids
      // a loading-panel flash when returning to the library on iOS.
      if (!this.collections.length) {
        this.loading = true
      }
      api.getLibrary().then((result) => {
        const activeCollection = (result.collections || []).find(
          (collection) => collection.hasActiveDeck
        )
        this.loading = false
        this.collections = result.collections || []
        this.activeDeckId = result.activeDeckId
        this.expandedCollectionId = activeCollection
          ? activeCollection.id
          : this.expandedCollectionId || 'capm'
      }).catch((error) => {
        this.loading = false
        showError(error, '暂时无法打开知识库')
      })
    },
    toggleCollection(collectionId) {
      if (!collectionId) {
        return
      }
      this.expandedCollectionId =
        this.expandedCollectionId === collectionId ? '' : collectionId
    },
    selectDeck(deckId) {
      if (!deckId) {
        return
      }
      api.setActiveDeck(deckId).then(() => {
        uni.switchTab({ url: '/pages/study/study' })
      }).catch((error) => {
        showError(error, '暂时无法打开学习内容')
      })
    },
    openSettings() {
      uni.switchTab({ url: '/pages/settings/settings' })
    }
  }
}
</script>

<style>
.library-page {
  padding: 0 32rpx 56rpx;
}

.library-loading {
  margin-top: 28rpx;
  text-align: center;
}

.collection-list {
  margin-top: 28rpx;
}

.collection-card {
  margin-bottom: 22rpx;
  padding: 22rpx;
  border: 1rpx solid transparent;
  border-radius: 26rpx;
  background: #ffffff;
  box-shadow: 0 12rpx 32rpx rgba(16, 42, 67, 0.07);
}

.collection-card.active {
  border-color: #9ac8ec;
  box-shadow: 0 14rpx 34rpx rgba(25, 118, 210, 0.12);
}

.collection-main {
  display: flex;
  gap: 24rpx;
}

.deck-cover {
  position: relative;
  flex-shrink: 0;
  width: 154rpx;
  height: 204rpx;
  overflow: hidden;
  padding: 20rpx 18rpx;
  border-radius: 18rpx;
  color: #ffffff;
}

.deck-cover::after {
  position: absolute;
  right: -44rpx;
  bottom: -44rpx;
  width: 150rpx;
  height: 150rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  content: "";
}

.deck-cover-0 {
  background: #102a43;
}

.deck-cover-1 {
  background: #1976d2;
}

.deck-cover-2 {
  background: #486581;
}

.cover-label,
.cover-mark {
  position: relative;
  z-index: 1;
  display: block;
}

.cover-label {
  font-size: 18rpx;
  letter-spacing: 1rpx;
  opacity: 0.78;
}

.cover-mark {
  margin-top: 54rpx;
  font-size: 30rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

.cover-line {
  position: absolute;
  bottom: 24rpx;
  left: 18rpx;
  z-index: 1;
  width: 56rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.72);
}

.deck-info {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
}

.deck-heading,
.deck-progress-summary,
.subdeck-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10rpx;
}

.deck-title {
  color: #102a43;
  font-size: 32rpx;
  font-weight: 700;
  line-height: 1.35;
}

.expand-mark {
  flex-shrink: 0;
  color: #1976d2;
  font-size: 22rpx;
  font-weight: 600;
}

.deck-subtitle,
.subdeck-subtitle {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
}

.deck-subtitle {
  margin-top: 12rpx;
  color: #627d98;
  font-size: 22rpx;
  line-height: 1.5;
  -webkit-line-clamp: 2;
}

.deck-progress-summary {
  margin-top: 22rpx;
  color: #829ab1;
  font-size: 20rpx;
}

.deck-progress-track {
  height: 8rpx;
  margin-top: 10rpx;
  overflow: hidden;
  border-radius: 999rpx;
  background: #e8eef5;
}

.deck-progress-fill {
  height: 100%;
  border-radius: inherit;
  background: #1976d2;
  transition: width 240ms ease-out;
}

.due-hint,
.deck-action {
  display: block;
  margin-top: 16rpx;
  font-size: 21rpx;
}

.due-hint,
.subdeck-due {
  color: #c05621;
  font-weight: 600;
}

.deck-action,
.subdeck-enter {
  color: #1976d2;
}

.subdeck-list {
  margin-top: 22rpx;
  padding-top: 8rpx;
  border-top: 1rpx solid #e8eef5;
}

.subdeck-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 22rpx 8rpx;
  border-bottom: 1rpx solid #eef3f8;
}

.subdeck-row:last-child {
  padding-bottom: 4rpx;
  border-bottom: 0;
}

.subdeck-row.active {
  margin: 0 -8rpx;
  padding-right: 16rpx;
  padding-left: 16rpx;
  border-radius: 18rpx;
  background: #f4f9fd;
  border-bottom-color: transparent;
}

.subdeck-copy {
  flex: 1;
  min-width: 0;
}

.subdeck-heading {
  align-items: center;
  justify-content: flex-start;
  gap: 12rpx;
}

.subdeck-label {
  color: #1976d2;
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

.active-badge {
  flex-shrink: 0;
  padding: 4rpx 10rpx;
  border-radius: 999rpx;
  background: #e6f6ff;
  color: #1976d2;
  font-size: 18rpx;
}

.subdeck-title {
  display: block;
  margin-top: 8rpx;
  color: #102a43;
  font-size: 27rpx;
  font-weight: 700;
}

.subdeck-subtitle {
  margin-top: 6rpx;
  color: #829ab1;
  font-size: 21rpx;
  line-height: 1.45;
  -webkit-line-clamp: 1;
}

.subdeck-meta {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  align-items: flex-end;
  gap: 8rpx;
}

.subdeck-progress {
  color: #486581;
  font-size: 22rpx;
  font-weight: 600;
}

.subdeck-due,
.subdeck-enter {
  font-size: 20rpx;
}
</style>
