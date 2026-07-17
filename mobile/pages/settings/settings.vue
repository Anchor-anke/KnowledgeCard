<template>
  <view class="page settings-page">
    <view class="custom-nav" :style="{ height: navTotalHeight + 'px' }">
      <view :style="{ height: statusBarHeight + 'px' }"></view>
      <view
        class="custom-nav-bar"
        :style="{ height: navBarHeight + 'px' }"
      >
        <view class="nav-title-wrap">
          <view class="nav-eyebrow">SETTINGS</view>
          <view class="nav-title">学习设置</view>
        </view>
      </view>
    </view>

    <view class="settings-body" :style="{ paddingTop: navTotalHeight + 'px' }">
      <text class="muted settings-intro">按自己的节奏调整学习量与提醒。</text>

      <view class="card-panel profile-panel" @tap="openLibrary">
        <view class="profile-top">
          <view>
            <text class="eyebrow">正在学习</text>
            <text class="goal">{{ activeDeckTitle }}</text>
          </view>
          <text class="profile-action">更换 →</text>
        </view>
        <text class="muted">
          每日新卡 {{ user.newCardLimit || 0 }} 张 · 每日复习 {{ user.reviewLimit || 0 }} 个知识点
        </text>
      </view>

      <view class="card-panel settings-panel">
        <text class="section-label">学习节奏</text>

        <view class="setting-row">
          <view>
            <text class="setting-title">每日新卡</text>
            <text class="muted">每天最多学习多少张新卡片</text>
          </view>
          <view class="limit-input-wrap">
            <input
              v-model="newCardInput"
              class="limit-input"
              type="number"
              @blur="saveNewCardLimit"
              @confirm="saveNewCardLimit"
            />
            <text class="limit-unit">张</text>
          </view>
        </view>

        <view class="setting-row">
          <view>
            <text class="setting-title">每日复习上限</text>
            <text class="muted">每天最多复习多少个知识点</text>
          </view>
          <view class="limit-input-wrap">
            <input
              v-model="reviewInput"
              class="limit-input"
              type="number"
              @blur="saveReviewLimit"
              @confirm="saveReviewLimit"
            />
            <text class="limit-unit">个</text>
          </view>
        </view>
      </view>

      <view class="card-panel settings-panel">
        <text class="section-label">复习提醒</text>

        <view class="setting-row">
          <view>
            <text class="setting-title">开启提醒</text>
            <text class="muted">到期复习时，通过 App 通知你</text>
          </view>
          <switch
            :checked="Boolean(user.subscriptionAuthorized)"
            color="#1976d2"
            @change="toggleSubscription"
          />
        </view>

        <picker mode="time" :value="user.reminderTime" @change="onReminderChange">
          <view class="setting-row">
            <view>
              <text class="setting-title">提醒时间</text>
              <text class="muted">建议选择你方便学习的时段</text>
            </view>
            <text class="setting-value">{{ user.reminderTime }}</text>
          </view>
        </picker>
      </view>

      <view class="card-panel settings-panel">
        <text class="section-label">关于</text>

        <view class="setting-row" @tap="sendFeedback">
          <view>
            <text class="setting-title">意见反馈</text>
            <text class="muted">告诉我们哪里可以更好</text>
          </view>
          <text class="setting-value">›</text>
        </view>

        <view class="about-block">
          <text class="about-name">知识卡</text>
          <text class="muted">把长资料变成短卡片，用间隔复习记住真正重要的知识。</text>
          <text class="privacy-note">你的学习资料与进度默认仅对自己可见。</text>
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
      user: {
        newCardLimit: 10,
        reviewLimit: 20,
        reminderTime: '20:00',
        subscriptionAuthorized: false
      },
      activeDeckTitle: 'CAPM · 全部知识',
      newCardInput: '10',
      reviewInput: '20',
      ...navMetrics
    }
  },
  onShow() {
    Object.assign(this, getNavMetrics())
    this.load()
  },
  methods: {
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
        this.user = user
        this.activeDeckTitle = activeDeckTitle
        this.newCardInput = String(user.newCardLimit || 10)
        this.reviewInput = String(user.reviewLimit || 20)
      }).catch((error) => {
        showError(error, '设置加载失败')
      })
    },
    openLibrary() {
      uni.switchTab({ url: '/pages/library/library' })
    },
    parseLimit(value, fallback) {
      const number = Number(String(value || '').trim())
      if (!Number.isFinite(number) || number < 1) {
        return fallback
      }
      return Math.min(200, Math.floor(number))
    },
    saveNewCardLimit() {
      const newCardLimit = this.parseLimit(this.newCardInput, this.user.newCardLimit || 10)
      this.newCardInput = String(newCardLimit)
      if (newCardLimit === this.user.newCardLimit) {
        return
      }
      api.updateSettings({ newCardLimit }).then((user) => {
        this.user = user
        this.newCardInput = String(user.newCardLimit)
        uni.showToast({ title: '已更新每日新卡', icon: 'none' })
      })
    },
    saveReviewLimit() {
      const reviewLimit = this.parseLimit(this.reviewInput, this.user.reviewLimit || 20)
      this.reviewInput = String(reviewLimit)
      if (reviewLimit === this.user.reviewLimit) {
        return
      }
      api.updateSettings({ reviewLimit }).then((user) => {
        this.user = user
        this.reviewInput = String(user.reviewLimit)
        uni.showToast({ title: '已更新每日复习', icon: 'none' })
      })
    },
    onReminderChange(event) {
      const reminderTime = event.detail.value
      api.updateSettings({ reminderTime }).then((user) => {
        this.user = user
        uni.showToast({ title: '提醒时间已更新', icon: 'none' })
      })
    },
    toggleSubscription(event) {
      const authorized = Boolean(event.detail.value)
      api.requestSubscription(authorized).then((user) => {
        this.user = user
        uni.showToast({
          title: authorized ? '已开启复习提醒' : '已关闭复习提醒',
          icon: 'none'
        })
      })
    },
    sendFeedback() {
      uni.showModal({
        title: '意见反馈',
        editable: true,
        placeholderText: '说说你想改进的地方',
        success: (result) => {
          if (!result.confirm) {
            return
          }
          const content = (result.content || '').trim()
          if (!content) {
            uni.showToast({ title: '请填写反馈内容', icon: 'none' })
            return
          }
          api.submitFeedback('settings', 'SUGGESTION', content).then(() => {
            uni.showToast({ title: '感谢你的反馈', icon: 'success' })
          })
        }
      })
    }
  }
}
</script>

<style>
.settings-page {
  padding: 0 32rpx 56rpx;
  background:
    radial-gradient(circle at 100% 0%, rgba(25, 118, 210, 0.08), transparent 34%),
    #f4f7fb;
}

.settings-intro {
  display: block;
  margin-top: 24rpx;
  font-size: 24rpx;
  line-height: 1.5;
}

.eyebrow {
  display: block;
  color: #1976d2;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.profile-panel,
.settings-panel {
  margin-top: 24rpx;
}

.profile-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.goal {
  display: block;
  margin-top: 12rpx;
  color: #102a43;
  font-size: 36rpx;
  font-weight: 700;
  line-height: 1.35;
}

.profile-action {
  flex-shrink: 0;
  margin-top: 8rpx;
  color: #1976d2;
  font-size: 24rpx;
  font-weight: 600;
}

.profile-panel > .muted {
  display: block;
  margin-top: 18rpx;
}

.section-label {
  display: block;
  margin-bottom: 8rpx;
  color: #829ab1;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  min-height: 108rpx;
  padding: 8rpx 0;
  border-bottom: 1rpx solid #e6eef5;
}

.setting-row:last-child {
  border-bottom: 0;
}

.setting-title {
  display: block;
  color: #102a43;
  font-size: 30rpx;
  font-weight: 700;
}

.setting-row .muted {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.4;
}

.setting-value {
  flex-shrink: 0;
  color: #1976d2;
  font-size: 26rpx;
  font-weight: 600;
}

.limit-input-wrap {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 10rpx;
  min-width: 140rpx;
  padding: 0 16rpx;
  border: 1rpx solid #d9eaf7;
  border-radius: 16rpx;
  background: #f7fbfe;
}

.limit-input {
  width: 88rpx;
  height: 64rpx;
  color: #1976d2;
  font-size: 28rpx;
  font-weight: 700;
  text-align: center;
}

.limit-unit {
  color: #829ab1;
  font-size: 22rpx;
}

.about-block {
  padding-top: 18rpx;
}

.about-name {
  display: block;
  color: #102a43;
  font-size: 28rpx;
  font-weight: 700;
}

.about-block .muted {
  display: block;
  margin-top: 12rpx;
  font-size: 23rpx;
  line-height: 1.6;
}

.privacy-note {
  display: block;
  margin-top: 16rpx;
  color: #9fb3c8;
  font-size: 21rpx;
  line-height: 1.5;
}
</style>
