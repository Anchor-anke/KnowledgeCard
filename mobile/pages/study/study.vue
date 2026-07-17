<template>
  <view class="page study-page">
    <view class="custom-nav" :style="{ height: navTotalHeight + 'px' }">
      <view :style="{ height: statusBarHeight + 'px' }"></view>
      <view
        class="custom-nav-bar"
        :style="{ height: navBarHeight + 'px' }"
      >
        <view class="nav-title-wrap">
          <view class="nav-eyebrow">STUDY</view>
          <view class="nav-title">学习卡流</view>
        </view>
      </view>
    </view>

    <view class="study-body" :style="{ paddingTop: navTotalHeight + 'px' }">
      <view v-if="loading" class="empty-panel card-panel">
        <text class="muted">正在加载学习任务…</text>
      </view>

      <view v-else-if="groupCompleted" class="completion-panel card-panel">
        <text class="completion-eyebrow">本组学习完成</text>
        <text class="completion-title">这组知识点已经记下来了</text>
        <text class="completion-summary">{{ lastFeedback }}</text>
        <button
          class="primary-button completion-button"
          :loading="committing"
          :disabled="committing"
          @tap="loadEntry(true)"
        >继续学习</button>
      </view>

      <view v-else-if="cards.length">
        <view
          class="card-viewport"
          :style="{ height: cardViewportHeight + 'px' }"
          @touchstart="onTouchStart"
          @touchend="onTouchEnd"
        >
          <view
            :class="['knowledge-card', cardAnimation]"
            :style="{
              minHeight: cardMinHeight + 'px',
              maxHeight: cardContentMaxHeight + 'px'
            }"
          >
            <scroll-view
              class="card-content"
              scroll-y
              :bounces="false"
              :show-scrollbar="false"
              :scroll-top="scrollTop"
              @scroll="onCardScroll"
            >
              <view class="card-meta">
                <text class="card-index">{{ current + 1 }} / {{ cards.length }}</text>
                <button class="feedback-button" @tap.stop="sendFeedback">反馈</button>
              </view>
              <text class="card-title">{{ currentCard.title }}</text>
              <view class="conclusion">
                <text class="label">一句话结论</text>
                <text class="conclusion-text">{{ currentCard.conclusion }}</text>
              </view>
              <view class="content-section">
                <text class="label">解释</text>
                <text class="body-text">{{ currentCard.explanation }}</text>
              </view>
              <view class="content-section">
                <text class="label">例子</text>
                <text class="body-text">{{ currentCard.example }}</text>
              </view>
              <view class="recall-section">
                <text class="label">回忆提示</text>
                <text class="body-text">{{ currentCard.recallPrompt }}</text>
              </view>
            </scroll-view>
            <view class="source">
              <text>
                来源：{{ currentCard.source }} · v{{ currentCard.version }} · {{ currentCard.sourceLocator }}
              </text>
            </view>
          </view>
          <view class="gesture-hint">
            <text>↑↓ 记住了</text>
            <text>←→ 没记住</text>
          </view>
        </view>
      </view>

      <view v-else class="empty-panel card-panel">
        <text class="empty-title">暂时没有更多卡片</text>
        <text class="muted">完成自评后，系统会在合适的时间安排复习。</text>
        <button class="secondary-button" @tap="loadEntry(true)">重新加载</button>
        <button class="secondary-button" @tap="resetDemo">重置演示数据</button>
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
      sessionId: `mobile-session-${Date.now()}`,
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
      ...navMetrics,
      cardMinHeight: 384,
      cardContentMaxHeight: 480,
      cardViewportHeight: 480,
      cardAnimation: '',
      loading: true,
      submitting: false,
      committing: false,
      groupCompleted: false,
      lastFeedback: '',
      cardContentMoved: false,
      cardScrollTop: 0,
      touchStartX: 0,
      touchStartY: 0
    }
  },
  computed: {
    currentCard() {
      return this.cards[this.current] || {}
    }
  },
  onShow() {
    Object.assign(this, getNavMetrics())
    this.skippedPointIds = []
    this.updateViewportHeight()
    this.loadEntry(true)
  },
  methods: {
    updateViewportHeight() {
      let windowHeight = 667
      try {
        const info = uni.getSystemInfoSync() || {}
        windowHeight = info.windowHeight || info.screenHeight || windowHeight
      } catch (error) {
        // Keep the safe fallback for preview environments.
      }
      const availableHeight = Math.max(
        360,
        Math.floor(windowHeight - this.navTotalHeight - 92)
      )
      this.cardViewportHeight = availableHeight
      this.cardContentMaxHeight = availableHeight - 24
      this.cardMinHeight = Math.floor(this.cardContentMaxHeight * 0.8)
    },
    loadEntry(resetSkipped = false) {
      if (resetSkipped) {
        this.skippedPointIds = []
      }
      // Keep the current card visible while refreshing a tab that has already
      // been opened. This prevents a brief loading-panel flash on iOS.
      this.loading = !this.cards.length
      this.groupCompleted = false
      api.getLearningEntry(this.skippedPointIds).then((entry) => {
        this.mode = entry.mode
        this.tasks = entry.tasks || []
        this.cards = entry.cards || []
        this.stats = entry.stats || this.stats
        this.current = 0
        this.pendingRememberedCardIds = []
        this.groupId = `${this.sessionId}:${Date.now()}`
        this.scrollTop = 0
        this.cardAnimation = ''
        this.loading = false
        this.groupCompleted = false
        this.lastFeedback = ''
        this.updateViewportHeight()
      }).catch((error) => {
        this.loading = false
        showError(error, '学习任务加载失败')
      })
    },
    onTouchStart(event) {
      const touch = event.touches && event.touches[0]
      if (!touch) {
        return
      }
      this.cardContentMoved = false
      this.touchStartX = touch.clientX
      this.touchStartY = touch.clientY
      this.cardScrollTop = 0
    },
    onCardScroll(event) {
      const scrollTop = event.detail && event.detail.scrollTop
      if (typeof scrollTop === 'number' && scrollTop !== this.cardScrollTop) {
        this.cardContentMoved = true
        this.cardScrollTop = scrollTop
      }
    },
    onTouchEnd(event) {
      if (this.submitting || this.committing || this.cardContentMoved) {
        this.cardContentMoved = false
        return
      }
      const touch = event.changedTouches && event.changedTouches[0]
      if (!touch) {
        return
      }
      const deltaX = touch.clientX - this.touchStartX
      const deltaY = touch.clientY - this.touchStartY
      if (Math.max(Math.abs(deltaX), Math.abs(deltaY)) < 45) {
        return
      }
      if (Math.abs(deltaX) > Math.abs(deltaY)) {
        this.submitNotRemembered(deltaX < 0 ? 'left' : 'right')
      } else if (deltaY < 0) {
        const pendingIds = this.rememberCurrentForGroup()
        this.nextCard(pendingIds)
      } else {
        this.previousCard()
      }
    },
    rememberCurrentForGroup() {
      const card = this.cards[this.current]
      if (!card) {
        return this.pendingRememberedCardIds
      }
      if (this.pendingRememberedCardIds.indexOf(card.id) < 0) {
        this.pendingRememberedCardIds = this.pendingRememberedCardIds.concat(card.id)
      }
      return this.pendingRememberedCardIds
    },
    nextCard(pendingIds) {
      const card = this.cards[this.current]
      if (!card) {
        return
      }
      this.skippedPointIds = this.skippedPointIds.concat(card.knowledgePointId)
      if (this.current < this.cards.length - 1) {
        this.current += 1
        this.scrollTop = 0
        this.cardAnimation = 'slide-next'
        setTimeout(() => {
          this.cardAnimation = ''
        }, 280)
        return
      }
      this.cardAnimation = ''
      this.finishGroup(pendingIds || this.pendingRememberedCardIds)
    },
    previousCard() {
      if (this.current <= 0) {
        return
      }
      const previousCard = this.cards[this.current - 1]
      this.skippedPointIds = this.skippedPointIds.filter(
        (pointId) => pointId !== previousCard.knowledgePointId
      )
      this.current -= 1
      this.scrollTop = 0
      this.cardAnimation = 'slide-previous'
      setTimeout(() => {
        this.cardAnimation = ''
      }, 280)
    },
    submitNotRemembered(direction) {
      const card = this.cards[this.current]
      if (!card || this.submitting || this.committing) {
        return
      }
      this.pendingRememberedCardIds = this.pendingRememberedCardIds.filter(
        (cardId) => cardId !== card.id
      )
      this.cardAnimation = `slide-not-remembered-${direction}`
      this.submitRating('NOT_REMEMBERED', () => {
        setTimeout(() => this.removeCurrentCard(), 320)
      })
    },
    removeCurrentCard() {
      const cards = this.cards.slice()
      cards.splice(this.current, 1)
      this.cards = cards
      this.current = Math.min(this.current, Math.max(0, cards.length - 1))
      this.scrollTop = 0
      this.cardAnimation = ''
      if (!cards.length) {
        this.finishGroup(this.pendingRememberedCardIds)
      }
    },
    finishGroup(pendingIds) {
      const cardIds = Array.from(new Set(pendingIds || []))
      if (!cardIds.length) {
        this.groupCompleted = true
        this.lastFeedback = '本组已完成，复习计划已安排'
        return
      }
      if (this.committing) {
        return
      }
      this.committing = true
      this.groupCompleted = true
      this.lastFeedback = '正在安排复习计划…'
      api.submitRememberedBatch(cardIds, this.sessionId, this.groupId).then(() => {
        this.committing = false
        this.pendingRememberedCardIds = []
        this.lastFeedback = `本组已完成 ${cardIds.length} 张，复习计划已安排`
      }).catch((error) => {
        this.committing = false
        this.groupCompleted = false
        showError(error, '复习计划保存失败')
      })
    },
    submitRating(rating, onComplete) {
      const card = this.cards[this.current]
      if (!card || this.submitting) {
        return
      }
      const key = `${this.sessionId}:${card.id}:${rating.toLowerCase()}:${Date.now()}`
      this.submitting = true
      api.completeCard(card.id, this.sessionId).then(() => {
        return api.submitRating(card.id, this.sessionId, rating, key)
      }).then((result) => {
        this.submitting = false
        this.lastFeedback = result.plan.reason
        if (onComplete) {
          onComplete()
        } else {
          setTimeout(() => this.loadEntry(true), 800)
        }
      }).catch((error) => {
        this.submitting = false
        this.cardAnimation = ''
        showError(error, '提交失败')
      })
    },
    sendFeedback() {
      const card = this.cards[this.current]
      if (!card) {
        return
      }
      uni.showModal({
        title: '反馈卡片问题',
        editable: true,
        placeholderText: '可填写具体问题',
        success: (result) => {
          if (result.confirm) {
            api.submitFeedback(card.id, 'ERROR', result.content).then(() => {
              uni.showToast({ title: '反馈已提交', icon: 'success' })
            })
          }
        }
      })
    },
    resetDemo() {
      api.reset().then(() => {
        uni.reLaunch({ url: '/pages/index/index' })
      })
    }
  }
}
</script>

<style>
.study-page {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  min-height: 100vh;
  max-height: 100vh;
  box-sizing: border-box;
  overflow: hidden;
  padding: 0 32rpx 24rpx;
  background:
    radial-gradient(circle at 100% 8%, rgba(25, 118, 210, 0.09), transparent 32%),
    radial-gradient(circle at 0% 82%, rgba(246, 173, 85, 0.08), transparent 28%),
    #f4f7fb;
}

.study-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  box-sizing: border-box;
}

.card-viewport {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 0;
  margin-top: 8rpx;
  overflow: hidden;
}

.knowledge-card {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  overflow: hidden;
  border: 1rpx solid rgba(217, 226, 236, 0.8);
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow:
    0 18rpx 42rpx rgba(16, 42, 67, 0.09),
    0 2rpx 6rpx rgba(16, 42, 67, 0.04);
}

.knowledge-card.slide-next {
  animation: card-slide-next 280ms ease-out;
}

.knowledge-card.slide-previous {
  animation: card-slide-previous 280ms ease-out;
}

.knowledge-card.slide-not-remembered-left {
  animation: card-swipe-left 320ms ease-out forwards;
}

.knowledge-card.slide-not-remembered-right {
  animation: card-swipe-right 320ms ease-out forwards;
}

@keyframes card-slide-next {
  from {
    opacity: 0;
    transform: translateY(64rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes card-slide-previous {
  from {
    opacity: 0;
    transform: translateY(-64rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes card-swipe-left {
  from {
    opacity: 1;
    transform: translateX(0) rotate(0);
  }
  to {
    opacity: 0.25;
    transform: translateX(-72rpx) rotate(-2deg);
  }
}

@keyframes card-swipe-right {
  from {
    opacity: 1;
    transform: translateX(0) rotate(0);
  }
  to {
    opacity: 0.25;
    transform: translateX(72rpx) rotate(2deg);
  }
}

.card-content {
  flex: 1;
  min-height: 0;
  height: auto;
  padding: 34rpx 34rpx 16rpx;
}

.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-index {
  color: #829ab1;
  font-size: 24rpx;
}

.card-title {
  display: block;
  margin-top: 18rpx;
  color: #102a43;
  font-size: 38rpx;
  font-weight: 700;
  line-height: 1.35;
}

.conclusion,
.content-section,
.recall-section {
  display: flex;
  flex-direction: column;
  margin-top: 28rpx;
}

.conclusion {
  padding: 22rpx;
  border-radius: 18rpx;
  background: #e6f6ff;
}

.label {
  color: #1976d2;
  font-size: 24rpx;
  font-weight: 700;
}

.conclusion-text {
  margin-top: 10rpx;
  color: #102a43;
  font-size: 30rpx;
  line-height: 1.55;
}

.body-text {
  margin-top: 10rpx;
  color: #334e68;
  font-size: 27rpx;
  line-height: 1.7;
}

.recall-section {
  padding: 20rpx;
  border-left: 8rpx solid #f6ad55;
  background: #fffaf0;
}

.source {
  flex-shrink: 0;
  margin-top: auto;
  padding: 12rpx 34rpx 28rpx;
  overflow: hidden;
  color: #829ab1;
  font-size: 18rpx;
  line-height: 1.3;
  text-align: left;
  white-space: nowrap;
}

.source text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gesture-hint {
  position: absolute;
  right: 0;
  bottom: 14rpx;
  left: 0;
  display: flex;
  justify-content: center;
  gap: 36rpx;
  color: #9fb3c8;
  font-size: 20rpx;
}

.feedback-button {
  margin: 0;
  padding: 0 18rpx;
  border: 1rpx solid #d9eaf7;
  border-radius: 26rpx;
  background: #f4f9fd;
  color: #627d98;
  font-size: 22rpx;
  line-height: 52rpx;
}

.feedback-button::after {
  border: 0;
}

.completion-panel {
  margin-top: 96rpx;
  text-align: center;
}

.completion-eyebrow {
  display: block;
  color: #1976d2;
  font-size: 26rpx;
}

.completion-title {
  display: block;
  margin-top: 20rpx;
  color: #102a43;
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.4;
}

.completion-summary {
  display: block;
  margin-top: 20rpx;
  color: #2f855a;
  font-size: 28rpx;
  line-height: 1.6;
}

.completion-button {
  margin-top: 36rpx;
}

.empty-panel {
  margin-top: 80rpx;
  text-align: center;
}

.empty-title {
  display: block;
  color: #102a43;
  font-size: 34rpx;
  font-weight: 700;
}
</style>
