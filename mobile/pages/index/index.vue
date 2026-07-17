<template>
  <view class="page index-page">
    <view class="index-glow index-glow-one"></view>
    <view class="index-glow index-glow-two"></view>

    <view class="custom-nav" :style="{ height: navTotalHeight + 'px' }">
      <view :style="{ height: statusBarHeight + 'px' }"></view>
      <view
        class="custom-nav-bar"
        :style="{ height: navBarHeight + 'px' }"
      >
        <view class="brand-lockup">
          <view class="brand-mark">KC</view>
          <view>
            <text class="brand-name">KnowledgeCard</text>
            <text class="brand-caption">PERSONAL LEARNING</text>
          </view>
        </view>
      </view>
    </view>

    <view class="index-body" :style="{ paddingTop: navTotalHeight + 'px' }">
      <view class="index-hero">
        <text class="hero-eyebrow">把长资料，变成会记住的知识</text>
        <text class="title">每一次滑动，<text class="title-accent">都算数。</text></text>
        <text class="hero-description">
          用短卡片理解重点，用间隔复习把知识留在脑海里。
        </text>
      </view>

      <view class="value-list">
        <view class="value-item">
          <text class="value-number">01</text>
          <view>
            <text class="value-title">一张卡，一个重点</text>
            <text class="value-description">把复杂资料拆成轻松可读的知识卡</text>
          </view>
        </view>
        <view class="value-item">
          <text class="value-number">02</text>
          <view>
            <text class="value-title">复习有节奏</text>
            <text class="value-description">在合适的时间重新遇见重要内容</text>
          </view>
        </view>
        <view class="value-item">
          <text class="value-number">03</text>
          <view>
            <text class="value-title">只为你保留</text>
            <text class="value-description">你的资料和学习进度默认只属于你</text>
          </view>
        </view>
      </view>

      <view class="index-footer">
        <button
          v-if="!loading"
          class="index-start"
          hover-class="index-start-hover"
          @tap="start"
        >
          <text>开始使用</text>
          <text class="button-arrow">→</text>
        </button>
        <view v-else class="loading-placeholder">正在准备学习空间…</view>
        <text class="index-note">先从一张卡开始，慢慢建立自己的知识库</text>
      </view>
    </view>
  </view>
</template>

<script>
import { api } from '../../utils/mock-store'
import { getNavMetrics } from '../../utils/layout'

export default {
  data() {
    const navMetrics = getNavMetrics()
    return {
      loading: true,
      onboardingCompleted: false,
      ...navMetrics
    }
  },
  onShow() {
    Object.assign(this, getNavMetrics())
    api.getSession().then((user) => {
      this.loading = false
      this.onboardingCompleted = user.onboardingCompleted
    })
  },
  methods: {
    start() {
      if (this.loading) {
        return
      }
      if (this.onboardingCompleted) {
        uni.switchTab({ url: '/pages/library/library' })
        return
      }
      uni.redirectTo({ url: '/pages/onboarding/onboarding' })
    }
  }
}
</script>

<style>
.index-page {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 0 32rpx 56rpx;
  background: #f6f8fb;
}

.index-glow {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.index-glow-one {
  top: 120rpx;
  right: -140rpx;
  width: 420rpx;
  height: 420rpx;
  background: rgba(25, 118, 210, 0.08);
}

.index-glow-two {
  bottom: 160rpx;
  left: -180rpx;
  width: 360rpx;
  height: 360rpx;
  background: rgba(246, 173, 85, 0.08);
}

.brand-lockup {
  display: flex;
  align-items: center;
  gap: 16rpx;
  min-width: 0;
}

.brand-mark {
  width: 56rpx;
  height: 56rpx;
  border-radius: 16rpx;
  background: #102a43;
  color: #ffffff;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 56rpx;
  letter-spacing: 1rpx;
  text-align: center;
}

.brand-name,
.brand-caption {
  display: block;
}

.brand-name {
  color: #102a43;
  font-size: 26rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
  line-height: 1.2;
}

.brand-caption {
  margin-top: 4rpx;
  color: #829ab1;
  font-size: 15rpx;
  letter-spacing: 2rpx;
  line-height: 1.2;
}

.index-body {
  position: relative;
  z-index: 1;
  display: flex;
  flex: 1;
  flex-direction: column;
  box-sizing: border-box;
  min-height: 0;
}

.index-hero {
  margin-top: 72rpx;
}

.hero-eyebrow {
  display: block;
  color: #1976d2;
  font-size: 25rpx;
  font-weight: 600;
}

.title {
  display: block;
  margin-top: 20rpx;
  color: #102a43;
  font-size: 56rpx;
  font-weight: 700;
  line-height: 1.25;
}

.title-accent {
  color: #1976d2;
}

.hero-description {
  display: block;
  max-width: 560rpx;
  margin-top: 28rpx;
  color: #627d98;
  font-size: 28rpx;
  line-height: 1.7;
}

.value-list {
  margin-top: 72rpx;
  padding: 28rpx 0;
  border-top: 1rpx solid #d9e2ec;
  border-bottom: 1rpx solid #d9e2ec;
}

.value-item {
  display: flex;
  align-items: flex-start;
  gap: 24rpx;
}

.value-item + .value-item {
  margin-top: 28rpx;
}

.value-number {
  color: #1976d2;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

.value-title,
.value-description {
  display: block;
}

.value-title {
  color: #243b53;
  font-size: 27rpx;
  font-weight: 700;
}

.value-description {
  margin-top: 6rpx;
  color: #829ab1;
  font-size: 23rpx;
}

.index-footer {
  margin-top: auto;
  padding-top: 56rpx;
}

.index-start {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin: 0;
  padding: 0 28rpx 0 34rpx;
  border: 0;
  border-radius: 20rpx;
  background: #1976d2;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 600;
  line-height: 92rpx;
  text-align: left;
  box-shadow: 0 14rpx 28rpx rgba(25, 118, 210, 0.2);
}

.index-start::after {
  border: 0;
}

.index-start-hover {
  opacity: 0.88;
}

.button-arrow {
  font-size: 38rpx;
  font-weight: 300;
}

.loading-placeholder {
  height: 92rpx;
  border-radius: 20rpx;
  background: #e8eef5;
  color: #829ab1;
  font-size: 26rpx;
  line-height: 92rpx;
  text-align: center;
}

.index-note {
  display: block;
  margin-top: 22rpx;
  color: #9fb3c8;
  font-size: 21rpx;
  text-align: center;
}
</style>
