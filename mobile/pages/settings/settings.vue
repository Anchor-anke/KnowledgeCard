<template>
  <view class="page settings-page">
    <view class="custom-nav" :style="{ height: navTotalHeight + 'px' }">
      <view :style="{ height: statusBarHeight + 'px' }">
      </view>
      <view
        class="custom-nav-bar"
        :style="{ height: navBarHeight + 'px' }"
      >
        <view class="nav-title-wrap">
          <view class="nav-eyebrow">
            SETTINGS
          </view>
          <view class="nav-title">
            设置
          </view>
        </view>
      </view>
    </view>
    <view class="settings-body" :style="{ paddingTop: navTotalHeight + 'px' }">
      <text class="settings-intro">
        找到适合自己的学习节奏。
      </text>
      <text class="settings-caption">
        少一点负担，多一点积累。
      </text>
      <button role="button" class="card-panel profile-panel" @tap="openLibrary">
        <view class="profile-top">
          <view>
            <text class="eyebrow">
              正在学习
            </text>
            <text class="goal">
              {{ activeDeckTitle }}
            </text>
          </view>
          <text class="profile-action">
            更换 →
          </text>
        </view>
        <text class="muted">
          每组 {{ user.newCardLimit || 0 }} 张新卡 · {{ user.reviewLimit || 0 }} 个复习知识点
        </text>
      </button>
      <view class="card-panel settings-panel">
        <text class="section-label">
          学习节奏
        </text>
        <view class="setting-row">
          <view>
            <text class="setting-title">
              新卡数量
            </text>
            <text class="muted">
              每组呈现的新卡片数量
            </text>
          </view>
          <view class="limit-input-wrap">
            <input
              v-model="newCardInput"
              class="limit-input"
              aria-label="每组新卡数量"
              type="number"
              @blur="saveNewCardLimit"
              @confirm="saveNewCardLimit"
            />
            <text class="limit-unit">
              张
            </text>
          </view>
        </view>
        <view class="setting-row">
          <view>
            <text class="setting-title">
              复习数量
            </text>
            <text class="muted">
              每组呈现的到期知识点数量
            </text>
          </view>
          <view class="limit-input-wrap">
            <input
              v-model="reviewInput"
              class="limit-input"
              aria-label="每组复习数量"
              type="number"
              @blur="saveReviewLimit"
              @confirm="saveReviewLimit"
            />
            <text class="limit-unit">
              个
            </text>
          </view>
        </view>
      </view>
      <view class="card-panel settings-panel">
        <view class="section-heading">
          <text class="section-label">
            提醒偏好
          </text>
          <text class="local-badge">
            本地保存
          </text>
        </view>
        <view class="setting-row">
          <view>
            <text class="setting-title">
              保存提醒偏好
            </text>
            <text class="muted">
              通知功能尚未接入，当前仅保存偏好
            </text>
          </view>
          <switch
            :checked="Boolean(user.subscriptionAuthorized)"
            color="#3659d9"
            @change="toggleSubscription"
          />
        </view>
        <picker mode="time" :value="user.reminderTime" @change="onReminderChange">
          <view class="setting-row">
            <view>
              <text class="setting-title">
                提醒时间
              </text>
              <text class="muted">
                建议选择你方便学习的时段
              </text>
            </view>
            <text class="setting-value">
              {{ user.reminderTime }}
            </text>
          </view>
        </picker>
      </view>
      <view class="card-panel settings-panel">
        <button role="button" class="service-toggle" :aria-expanded="serviceExpanded" @tap="serviceExpanded = !serviceExpanded">
          <view>
            <text class="setting-title">
              PDF 制卡服务
            </text>
            <text class="muted">
              连接服务与本地身份设置
            </text>
          </view>
          <text class="setting-value">
            {{ serviceExpanded ? '收起' : '配置' }}
          </text>
        </button>
        <view v-if="serviceExpanded" class="service-details">
          <view class="api-setting-block">
            <text class="setting-title">
              服务地址
            </text>
            <input
            aria-label="制卡服务地址"
            v-model="apiBaseUrl"
            class="api-input"
            placeholder="例如 http://192.168.1.10:8000"
            @blur="saveApiConfig"
            @confirm="saveApiConfig"
          />
            <text class="muted api-hint">
              Android 模拟器默认使用 10.0.2.2；真机请填电脑的局域网 IP。
            </text>
          </view>
          <view class="api-setting-block">
            <text class="setting-title">
              本地用户标识
            </text>
            <input
            aria-label="本地用户标识"
            v-model="apiUserId"
            class="api-input"
            placeholder="mobile-user-1"
            @blur="saveApiConfig"
            @confirm="saveApiConfig"
          />
          </view>
        </view>
      </view>
      <view class="card-panel settings-panel">
        <text class="section-label">
          关于
        </text>
        <button role="button" class="setting-row feedback-row" @tap="sendFeedback">
          <view>
            <text class="setting-title">
              意见反馈
            </text>
            <text class="muted">
              告诉我们哪里可以更好
            </text>
          </view>
          <text class="setting-value" aria-hidden="true">
            →
          </text>
        </button>
        <view class="about-block">
          <text class="about-name">
            知识卡
          </text>
          <text class="muted">
            把长资料变成短卡片，用间隔复习记住真正重要的知识。
          </text>
          <text class="privacy-note">
            学习资料与进度保存在当前设备，请妥善保留。
          </text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { api } from '../../utils/mock-store'
import { getNavMetrics, showError } from '../../utils/layout'
import { getApiConfig, updateApiConfig } from '../../utils/api'

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
      serviceExpanded: false,
      activeDeckTitle: 'CAPM · 全部知识',
      newCardInput: '10',
      reviewInput: '20',
      apiBaseUrl: '',
      apiUserId: 'mobile-user-1',
      ...navMetrics
    }
  },
  onShow() {
    Object.assign(this, getNavMetrics())
    const apiConfig = getApiConfig()
    this.apiBaseUrl = apiConfig.baseUrl
    this.apiUserId = apiConfig.userId
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
        uni.showToast({ title: '已更新新卡数量', icon: 'none' })
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
    saveApiConfig() {
      const config = updateApiConfig({
        baseUrl: this.apiBaseUrl,
        userId: this.apiUserId
      })
      this.apiBaseUrl = config.baseUrl
      this.apiUserId = config.userId
      uni.showToast({ title: '制卡服务配置已保存', icon: 'none' })
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
          title: authorized ? '提醒偏好已保存' : '提醒偏好已关闭',
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

<style scoped>
.settings-page {
  padding: 0 36rpx 48rpx;
}
.settings-body {
  max-width: 600px;
  margin: 0 auto;
}
.settings-intro {
  display: block;
  margin-top: 28rpx;
  font-size: clamp(16px, 36rpx, 21px);
  font-weight: 650;
  line-height: 1.55;
}
.settings-caption {
  display: block;
  margin-top: 6rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 26rpx, 15px);
}
.profile-panel {
  display: block;
  width: 100%;
  margin: 30rpx 0 0;
  padding: 28rpx;
  background: var(--kc-primary-soft);
  border-color: #dce3f6;
  text-align: left;
  line-height: 1.5;
}
.profile-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}
.profile-top > view {
  flex: 1;
  min-width: 0;
}
.eyebrow {
  display: block;
  color: var(--kc-primary);
  font-size: clamp(12px, 24rpx, 14px);
}
.goal {
  display: block;
  margin-top: 12rpx;
  font-size: clamp(13px, 31rpx, 18px);
  font-weight: 650;
  line-height: 1.55;
  overflow-wrap: anywhere;
}
.profile-action {
  flex-shrink: 0;
  color: var(--kc-primary);
  font-size: clamp(12px, 25rpx, 15px);
}
.profile-panel > .muted {
  display: block;
  margin-top: 14rpx;
  color: #58677f;
  font-size: clamp(12px, 24rpx, 14px);
}
.settings-panel {
  margin-top: 26rpx;
  padding: 28rpx;
}
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}
.section-label {
  display: block;
  margin-bottom: 10rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 24rpx, 14px);
  font-weight: 500;
}
.local-badge {
  color: var(--kc-muted);
  padding: 4rpx 10rpx;
  border-radius: 8rpx;
  background: var(--kc-background);
  font-size: clamp(12px, 21rpx, 12px);
}
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  min-height: 112rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid var(--kc-line);
}
.setting-row > view:first-child {
  flex: 1;
  min-width: 0;
}
.setting-row:last-child {
  border-bottom: 0;
}
.setting-title {
  display: block;
  color: var(--kc-ink);
  font-size: clamp(13px, 29rpx, 17px);
  font-weight: 600;
  line-height: 1.5;
}
.setting-row .muted, .service-toggle .muted {
  display: block;
  margin-top: 8rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 24rpx, 14px);
  line-height: 1.6;
}
.setting-value {
  flex-shrink: 0;
  color: var(--kc-primary);
  font-size: clamp(12px, 27rpx, 16px);
  font-weight: 500;
}
.limit-input-wrap {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 6rpx;
  padding: 0 12rpx;
  border: 1rpx solid #c9d2e5;
  border-radius: 16rpx;
  background: #f8f9fc;
}
.limit-input {
  width: 68rpx;
  min-height: 48px;
  color: var(--kc-primary);
  font-size: clamp(13px, 31rpx, 18px);
  font-weight: 650;
  text-align: center;
}
.limit-unit {
  color: var(--kc-muted);
  font-size: clamp(12px, 24rpx, 14px);
}
.service-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  width: 100%;
  min-height: 48px;
  margin: 0;
  padding: 0;
  background: transparent;
  text-align: left;
  line-height: 1.5;
}
.service-details {
  margin-top: 26rpx;
  padding-top: 10rpx;
  border-top: 1rpx solid var(--kc-line);
}
.api-setting-block {
  padding: 16rpx 0;
}
.api-input {
  width: 100%;
  min-height: 48px;
  margin-top: 12rpx;
  padding: 12rpx 18rpx;
  border: 1rpx solid #c9d2e5;
  border-radius: 14rpx;
  background: #f8f9fc;
  color: var(--kc-ink);
  font-size: clamp(12px, 27rpx, 16px);
}
.api-hint {
  display: block;
  margin-top: 12rpx;
  font-size: clamp(12px, 24rpx, 14px);
  line-height: 1.7;
}
.feedback-row {
  width: 100%;
  margin: 0;
  background: transparent;
  text-align: left;
  border-radius: 0;
  line-height: 1.5;
}
.about-block {
  padding-top: 24rpx;
}
.about-name {
  display: block;
  color: var(--kc-ink);
  font-size: clamp(12px, 28rpx, 16px);
  font-weight: 650;
}
.about-block .muted {
  display: block;
  margin-top: 12rpx;
  font-size: clamp(12px, 25rpx, 15px);
  line-height: 1.7;
}
.privacy-note {
  display: block;
  margin-top: 18rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 23rpx, 13px);
  line-height: 1.7;
}
</style>
