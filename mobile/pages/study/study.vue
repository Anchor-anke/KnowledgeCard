<template>
  <view class="page study-page" :style="{ height: viewportHeight + 'px' }">
    <view v-show="!activeRecall" class="custom-nav" :style="{ height: navTotalHeight + 'px' }">
      <view :style="{ height: statusBarHeight + 'px' }">
      </view>
      <view
        class="custom-nav-bar"
        :style="{ height: navBarHeight + 'px' }"
      >
        <view class="nav-title-wrap">
          <view class="nav-eyebrow">
            STUDY
          </view>
          <view class="nav-title">
            专注学习
          </view>
        </view>
      </view>
    </view>
    <view v-show="!activeRecall" class="study-body" :style="{ paddingTop: navTotalHeight + 'px' }">
      <view v-if="loading" class="empty-panel card-panel">
        <text class="muted">
          正在加载学习任务…
        </text>
      </view>
      <view v-else-if="groupCompleted" class="completion-panel card-panel">
        <text class="completion-eyebrow">
          本组学习完成
        </text>
        <text class="completion-title">
          完成一组，积累一点。
        </text>
        <text class="completion-summary">
          {{ lastFeedback }}
        </text>
        <button role="button"
          class="primary-button completion-button"
          :loading="committing"
          :disabled="committing" :aria-disabled="committing"
          @tap="loadEntry(true)"
        >
          继续学习
        </button>
      </view>
      <view v-else-if="cards.length" class="study-session">
        <view class="session-heading">
          <text class="session-mode">
            {{ mode === 'REVIEW' ? '到期复习' : '新卡学习' }}
          </text>
          <text class="session-position">
            第 {{ current + 1 }} 张
            <text class="position-total">
              / 共 {{ cards.length }} 张
            </text>
          </text>
        </view>
        <view class="session-progress" aria-hidden="true">
          <view :style="{ width: ((current + 1) / cards.length * 100) + '%' }">
          </view>
        </view>
        <view
          class="card-viewport"
          @touchstart="onTouchStart"
          @touchend="onTouchEnd"
        >
          <view
            :class="['knowledge-card', cardAnimation]"
          >
            <view class="card-meta">
                <text class="card-index">
                  知识卡
                </text>
                <view class="card-actions">
                  <button role="button" class="recall-open-button" @tap.stop="openActiveRecall">
                    主动回忆
                  </button>
                  <button role="button" class="feedback-button" @tap.stop="sendFeedback">
                    反馈
                  </button>
                </view>
              </view>
            <scroll-view
              :key="currentCard.id"
              class="card-content"
              scroll-y
              :bounces="false"
              :show-scrollbar="false"
              :scroll-top="scrollTop"
              @scroll="onCardScroll"
            >
              <text class="card-title">
                {{ currentCard.title }}
              </text>
              <view class="conclusion">
                <text class="label">
                  一句话结论
                </text>
                <text class="conclusion-text">
                  {{ currentCard.conclusion }}
                </text>
              </view>
              <view class="content-section">
                <text class="label">
                  解释
                </text>
                <text class="body-text">
                  {{ currentCard.explanation }}
                </text>
              </view>
              <view class="content-section">
                <text class="label">
                  例子
                </text>
                <text class="body-text">
                  {{ currentCard.example }}
                </text>
              </view>
              <view class="recall-section">
                <text class="label">
                  回忆提示
                </text>
                <text class="body-text">
                  {{ currentCard.recallPrompt }}
                </text>
              </view>
            </scroll-view>
            <view class="source">
              <text>
                来源：{{ currentCard.source }} · v{{ currentCard.version }} · {{ currentCard.sourceLocator }}
              </text>
            </view>
          </view>
        </view>
        <view class="study-controls">
          <button role="button" class="study-control previous-control" :disabled="current === 0 || interactionBusy" :aria-disabled="current === 0 || interactionBusy" @tap="previousCard">
            上一张
          </button>
          <button role="button" class="study-control forgot-control" :disabled="interactionBusy" :aria-disabled="interactionBusy" @tap="submitNotRemembered('left')">
            没记住
          </button>
          <button role="button" class="study-control next-control" :disabled="interactionBusy" :aria-disabled="interactionBusy" @tap="advanceCard">
            {{ current === cards.length - 1 ? '完成本组' : '下一张' }}
            <text aria-hidden="true">
              →
            </text>
          </button>
        </view>
        <text class="gesture-hint">
          上下滑动切卡 · 整组完成后保存已读卡片的自评
        </text>
      </view>
      <view v-else class="empty-panel card-panel">
        <text class="empty-title">
          这一轮，先学到这里
        </text>
        <text class="muted">
          可以换一组内容继续，也可以休息一下，等待下一次复习。
        </text>
        <button role="button" class="secondary-button" @tap="loadEntry(true)">
          重新加载
        </button>
        <button role="button" class="secondary-button" @tap="openLibrary">
          返回知识库
        </button>
      </view>
    </view>
    <view v-if="activeRecall" class="recall-mask" @tap="closeActiveRecall">
      <view
        class="recall-sheet"
        :style="{ paddingTop: (statusBarHeight + 20) + 'px' }"
        @tap.stop
      >
        <view class="recall-header">
          <view>
            <text class="recall-eyebrow">
              留一点时间，独立想一想
            </text>
            <text class="recall-title">
              主动回忆
            </text>
          </view>
          <button role="button" v-if="!recallSubmitting" class="recall-close" @tap="closeActiveRecall">
            关闭
          </button>
        </view>
        <scroll-view class="recall-content" scroll-y :show-scrollbar="false">
          <text class="recall-question-label">
            先回忆，再看答案
          </text>
          <text class="recall-question">
            {{ currentCard.title }}
          </text>
          <text v-if="currentCard.recallPrompt" class="recall-prompt">
            提示：{{ currentCard.recallPrompt }}
          </text>
          <view v-if="!recallSubmitted" class="recall-answer-form">
            <textarea
              v-model="recallAnswer"
              class="recall-input"
              aria-label="我的回忆答案"
              maxlength="2000"
              auto-height
              placeholder="把你记得的结论、原因或例子写下来…"
            />
            <text class="recall-input-hint">
              先独立回忆，再点击提交查看标准答案
            </text>
            <button role="button"
              class="primary-button recall-submit-button"
              :disabled="!recallAnswer.trim() || recallSubmitting" :aria-disabled="!recallAnswer.trim() || recallSubmitting"
              :loading="recallSubmitting"
              @tap="submitRecallAnswer"
            >
              提交答案
            </button>
          </view>
          <view v-else class="recall-comparison">
            <view class="comparison-block my-answer-block">
              <text class="comparison-label">
                我的回答
              </text>
              <text class="comparison-text">
                {{ recallAnswer }}
              </text>
            </view>
            <view class="comparison-block correct-answer-block">
              <text class="comparison-label">
                标准答案
              </text>
              <text class="comparison-text correct-answer-text">
                {{ currentCard.conclusion }}
              </text>
              <text v-if="currentCard.referenceAnswer" class="comparison-detail">
                {{ currentCard.referenceAnswer }}
              </text>
              <text v-if="currentCard.explanation" class="comparison-detail">
                {{ currentCard.explanation }}
              </text>
            </view>
            <text class="recall-rating-title">
              对比后，你觉得自己掌握得怎么样？
            </text>
            <view class="recall-rating-list">
              <button role="button"
                class="recall-rating recall-rating-remembered"
                :disabled="recallSubmitting" :aria-disabled="recallSubmitting"
                @tap="rateActiveRecall('REMEMBERED')"
              >
                记住了
              </button>
              <button role="button"
                class="recall-rating recall-rating-partial"
                :disabled="recallSubmitting" :aria-disabled="recallSubmitting"
                @tap="rateActiveRecall('PARTIAL')"
              >
                部分记住
              </button>
              <button role="button"
                class="recall-rating recall-rating-forgot"
                :disabled="recallSubmitting" :aria-disabled="recallSubmitting"
                @tap="rateActiveRecall('FORGOT')"
              >
                没记住
              </button>
            </view>
          </view>
        </scroll-view>
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
      viewportHeight: 667,
      cardAnimation: '',
      loading: true,
      submitting: false,
      committing: false,
      groupCompleted: false,
      lastFeedback: '',
      cardContentMoved: false,
      cardScrollTop: 0,
      touchStartX: 0,
      touchStartY: 0,
      activeRecall: false,
      recallAnswer: '',
      recallSubmitted: false,
      recallSubmitting: false
    }
  },
  computed: {
    interactionBusy() {
      return this.submitting || this.committing || Boolean(this.cardAnimation)
    },
    currentCard() {
      return this.cards[this.current] || {}
    }
  },
  onShow() {
    Object.assign(this, getNavMetrics())
    uni.showTabBar({ animation: false })
    this.skippedPointIds = []
    this.updateViewportHeight()
    this.loadEntry(true)
  },
  onResize() {
    Object.assign(this, getNavMetrics())
    this.updateViewportHeight()
  },
  onBackPress() {
    if (!this.activeRecall) return false
    this.closeActiveRecall()
    return true
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
      this.viewportHeight = windowHeight
    },
    openLibrary() {
      uni.switchTab({ url: '/pages/library/library' })
    },
    advanceCard() {
      if (this.interactionBusy) return
      this.nextCard(this.rememberCurrentForGroup())
    },
    loadEntry(resetSkipped = false) {
      if (resetSkipped) {
        this.skippedPointIds = []
      }
      // Keep the current card visible while refreshing a tab that has already
      // been opened. This prevents a brief loading-panel flash on iOS.
      this.loading = !this.cards.length
      this.groupCompleted = false
      this.activeRecall = false
      this.recallAnswer = ''
      this.recallSubmitted = false
      this.recallSubmitting = false
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
    openActiveRecall() {
      if (!this.currentCard.id || this.submitting || this.committing) {
        return
      }
      this.activeRecall = true
      this.recallAnswer = ''
      this.recallSubmitted = false
      this.recallSubmitting = false
      uni.hideTabBar({ animation: false })
    },
    closeActiveRecall() {
      if (this.recallSubmitting) {
        return
      }
      this.activeRecall = false
      this.recallAnswer = ''
      this.recallSubmitted = false
      uni.showTabBar({ animation: false })
    },
    submitRecallAnswer() {
      if (!this.recallAnswer.trim() || this.recallSubmitting) {
        return
      }
      this.recallSubmitted = true
    },
    rateActiveRecall(rating) {
      const card = this.currentCard
      const answer = this.recallAnswer.trim()
      if (!card.id || !answer || !this.recallSubmitted || this.recallSubmitting) {
        return
      }
      const key = `${this.sessionId}:${card.id}:active-recall:${rating.toLowerCase()}:${Date.now()}`
      this.recallSubmitting = true
      api.submitRecall(card.id, this.sessionId, rating, answer, key).then((result) => {
        this.recallSubmitting = false
        this.activeRecall = false
        this.recallAnswer = ''
        this.recallSubmitted = false
        uni.showTabBar({ animation: false })
        this.lastFeedback = result.plan.reason
        this.loadEntry(true)
      }).catch((error) => {
        this.recallSubmitting = false
        showError(error, '主动回忆结果保存失败')
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
      if (this.submitting || this.committing || this.cardAnimation || this.cardContentMoved) {
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
      if (this.interactionBusy || this.current <= 0) {
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
      if (!card || this.submitting || this.committing || this.cardAnimation) {
        return
      }
      this.pendingRememberedCardIds = this.pendingRememberedCardIds.filter(
        (cardId) => cardId !== card.id
      )
      this.cardAnimation = `slide-not-remembered-${direction}`
      this.submitRating('FORGOT', () => {
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
    }
  }
}
</script>

<style scoped>
.study-page {
  display: flex;
  flex-direction: column;
  min-height: 0;
  box-sizing: border-box;
  overflow: hidden;
  padding: 0 32rpx;
}
.study-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  padding-bottom: 12rpx;
}
.study-session {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  padding-top: 16rpx;
}
.session-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  gap: 16rpx;
  font-size: clamp(12px, 25rpx, 15px);
}
.session-mode {
  color: var(--kc-primary);
  font-weight: 600;
}
.session-position {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.position-total {
  color: var(--kc-muted);
  font-weight: 400;
}
.session-progress {
  flex-shrink: 0;
  height: 5rpx;
  margin-top: 15rpx;
  overflow: hidden;
  border-radius: 8rpx;
  background: #e2e7f1;
}
.session-progress > view {
  height: 100%;
  border-radius: inherit;
  background: var(--kc-primary);
}
.card-viewport {
  display: flex;
  flex: 1;
  min-height: 0;
  margin: 22rpx 0;
}
.knowledge-card {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1rpx solid var(--kc-line);
  border-radius: 28rpx;
  background: var(--kc-surface);
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
  height: 0;
  min-height: 0;
  padding: 16rpx 30rpx 24rpx;
}
.card-meta {
  flex-shrink: 0;
  padding: 16rpx 30rpx 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10rpx;
}
.card-index {
  color: var(--kc-muted);
  font-size: clamp(12px, 24rpx, 14px);
}
.card-actions {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.feedback-button, .recall-open-button {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  margin: 0;
  padding: 10rpx 16rpx;
  border: 0;
  border-radius: 14rpx;
  font-size: clamp(12px, 25rpx, 15px);
  line-height: 1.4;
}
.feedback-button {
  min-width: 48px;
  color: var(--kc-muted);
  background: transparent;
}
.recall-open-button {
  color: var(--kc-primary);
  background: var(--kc-primary-soft);
  font-weight: 600;
}
.card-title {
  display: block;
  margin: 0;
  color: var(--kc-ink);
  font-size: clamp(17px, 39rpx, 22px);
  font-weight: 700;
  line-height: 1.5;
  overflow-wrap: anywhere;
}
.conclusion, .content-section, .recall-section {
  display: flex;
  flex-direction: column;
  margin-top: 30rpx;
}
.conclusion {
  padding: 24rpx;
  border-radius: 18rpx;
  background: var(--kc-primary-soft);
}
.label {
  color: var(--kc-muted);
  font-size: clamp(12px, 24rpx, 14px);
  font-weight: 600;
}
.conclusion .label {
  color: var(--kc-primary);
}
.conclusion-text {
  margin-top: 12rpx;
  color: var(--kc-ink);
  font-size: clamp(14px, 32rpx, 18px);
  font-weight: 500;
  line-height: 1.75;
}
.body-text {
  display: block;
  margin-top: 10rpx;
  color: #354158;
  font-size: clamp(13px, 30rpx, 17px);
  line-height: 1.85;
  overflow-wrap: anywhere;
}
.recall-section {
  margin-bottom: 20rpx;
  padding: 22rpx;
  border-radius: 18rpx;
  background: #faf4e9;
}
.recall-section .label {
  color: #8c5d25;
}
.source {
  flex-shrink: 0;
  padding: 18rpx 30rpx;
  border-top: 1rpx solid #edf0f5;
  color: var(--kc-muted);
  font-size: clamp(12px, 22rpx, 13px);
  line-height: 1.55;
}
.source text {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow-wrap: anywhere;
}
.study-controls {
  display: flex;
  flex-shrink: 0;
  gap: 12rpx;
}
.study-control {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  min-height: 48px;
  margin: 0;
  padding: 16rpx 12rpx;
  border-radius: 18rpx;
  font-size: clamp(12px, 27rpx, 16px);
  line-height: 1.4;
  font-weight: 600;
}
.previous-control {
  flex: .9;
  background: #e8ecf4;
  color: #536078;
}
.forgot-control {
  flex: 1;
  background: #f4e9e7;
  color: #944c3e;
}
.next-control {
  flex: 1.25;
  color: #ffffff;
  background: var(--kc-primary);
}
.gesture-hint {
  display: block;
  flex-shrink: 0;
  padding: 16rpx 0 4rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 22rpx, 13px);
  line-height: 1.45;
  text-align: center;
}
.recall-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  background: var(--kc-surface);
}
.recall-sheet {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 600px;
  height: 100%;
  margin: 0 auto;
  min-height: 0;
  overflow: hidden;
  padding: 28rpx 36rpx calc(28rpx + env(safe-area-inset-bottom));
  background: var(--kc-surface);
}
.recall-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  gap: 18rpx;
}
.recall-eyebrow {
  display: block;
  color: var(--kc-muted);
  font-size: clamp(12px, 23rpx, 13px);
}
.recall-title {
  display: block;
  margin-top: 6rpx;
  font-size: clamp(17px, 39rpx, 22px);
  font-weight: 700;
}
.recall-close {
  flex-shrink: 0;
  min-height: 48px;
  min-width: 48px;
  margin: 0;
  padding: 14rpx;
  border-radius: 16rpx;
  background: var(--kc-background);
  color: var(--kc-muted);
  font-size: clamp(12px, 26rpx, 15px);
  line-height: 1.4;
}
.recall-content {
  flex: 1;
  height: 0;
  min-height: 0;
  margin-top: 34rpx;
}
.recall-question-label, .recall-question, .recall-prompt, .recall-input-hint, .recall-rating-title {
  display: block;
}
.recall-question-label {
  color: var(--kc-primary);
  font-size: clamp(12px, 25rpx, 15px);
  font-weight: 600;
}
.recall-question {
  margin-top: 16rpx;
  font-size: clamp(16px, 37rpx, 21px);
  font-weight: 700;
  line-height: 1.6;
}
.recall-prompt {
  margin-top: 20rpx;
  padding: 22rpx;
  border-radius: 18rpx;
  background: #faf4e9;
  color: #785b32;
  font-size: clamp(12px, 27rpx, 16px);
  line-height: 1.7;
}
.recall-answer-form {
  margin-top: 26rpx;
}
.recall-input {
  width: 100%;
  min-height: 260rpx;
  padding: 24rpx;
  border: 1rpx solid #bdc7db;
  border-radius: 20rpx;
  background: #f8f9fc;
  color: var(--kc-ink);
  font-size: clamp(13px, 30rpx, 17px);
  line-height: 1.8;
}
.recall-input-hint {
  margin-top: 16rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 24rpx, 14px);
}
.recall-submit-button {
  width: 100%;
  margin-bottom: 20rpx;
}
.recall-comparison {
  margin-top: 28rpx;
}
.comparison-block {
  padding: 26rpx;
  border-radius: 20rpx;
}
.my-answer-block {
  background: var(--kc-background);
}
.correct-answer-block {
  margin-top: 20rpx;
  background: #edf5f0;
}
.comparison-label {
  display: block;
  color: var(--kc-muted);
  font-size: clamp(12px, 25rpx, 15px);
  font-weight: 600;
}
.comparison-text, .comparison-detail {
  display: block;
  margin-top: 12rpx;
  color: var(--kc-ink);
  font-size: clamp(13px, 29rpx, 17px);
  line-height: 1.8;
  white-space: pre-wrap;
}
.correct-answer-text {
  color: #24654e;
  font-weight: 600;
}
.comparison-detail {
  color: #4d6057;
  font-size: clamp(12px, 27rpx, 16px);
}
.recall-rating-title {
  margin-top: 30rpx;
  font-size: clamp(12px, 28rpx, 16px);
  font-weight: 600;
}
.recall-rating-list {
  display: flex;
  gap: 12rpx;
  margin: 20rpx 0;
}
.recall-rating {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 48px;
  margin: 0;
  padding: 16rpx 8rpx;
  border: 0;
  border-radius: 16rpx;
  font-size: clamp(12px, 27rpx, 16px);
  line-height: 1.4;
}
.recall-rating-remembered {
  background: #e2f0e8;
  color: #24654e;
}
.recall-rating-partial {
  background: #f6eedc;
  color: #805c21;
}
.recall-rating-forgot {
  background: #f4e9e7;
  color: #944c3e;
}
.completion-panel, .empty-panel {
  margin: auto 0;
  padding: 46rpx 32rpx;
}
.completion-eyebrow {
  display: block;
  color: var(--kc-primary);
  font-size: clamp(12px, 27rpx, 16px);
}
.completion-title, .empty-title {
  display: block;
  margin-top: 16rpx;
  font-size: clamp(17px, 38rpx, 22px);
  font-weight: 700;
  line-height: 1.5;
}
.completion-summary, .empty-panel .muted {
  display: block;
  margin-top: 20rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 28rpx, 16px);
  line-height: 1.75;
}
.completion-button {
  margin-top: 32rpx;
}
@media (max-height: 500px) and (min-width: 600px) {
  .study-session {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 132px;
    grid-template-rows: auto 3px minmax(0, 1fr);
    column-gap: 16px;
    row-gap: 8px;
    padding-top: 4px;
  }
  .session-heading, .session-progress {
    grid-column: 1 / -1;
    margin: 0;
  }
  .card-viewport {
    grid-column: 1;
    grid-row: 3;
    margin: 0;
  }
  .study-controls {
    grid-column: 2;
    grid-row: 3;
    flex-direction: column;
    justify-content: center;
    gap: 10px;
  }
  .study-control {
    flex: none;
  }
  .gesture-hint {
    display: none;
  }
  .knowledge-card {
    border-radius: 18px;
  }
  .card-meta {
    padding: 6px 16px 0;
  }
  .card-content {
    padding: 8px 16px 16px;
  }
  .source {
    padding: 6px 16px;
  }
  .source text {
    -webkit-line-clamp: 1;
  }
}
</style>
