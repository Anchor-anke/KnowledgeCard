<template>
  <view class="page onboarding-page">
    <view class="custom-nav" :style="{ height: navTotalHeight + 'px' }">
      <view :style="{ height: statusBarHeight + 'px' }"></view>
      <view
        class="custom-nav-bar"
        :style="{ height: navBarHeight + 'px' }"
      >
        <view class="nav-brand">
          <view class="mini-brand">KC</view>
          <text class="nav-title">认识 KnowledgeCard</text>
        </view>
        <button
          v-if="currentStep < steps.length - 1"
          class="nav-action muted"
          @tap="start"
        >跳过</button>
      </view>
    </view>

    <view class="onboarding-body" :style="{ paddingTop: navTotalHeight + 'px' }">
      <view class="card-progress">
        <text>知识卡教学</text>
        <text>{{ currentStep + 1 }} / {{ steps.length }}</text>
      </view>

      <view
        :class="['onboarding-card', demoAnimation]"
        @touchstart="onTouchStart"
        @touchend="onTouchEnd"
      >
        <view class="card-header">
          <text>KnowledgeCard</text>
          <text>0{{ currentStep + 1 }}</text>
        </view>

        <view class="card-body">
          <view class="card-symbol">
            <text>{{ steps[currentStep].visual }}</text>
          </view>
          <text class="tour-eyebrow">{{ steps[currentStep].eyebrow }}</text>
          <text class="tour-title">{{ steps[currentStep].title }}</text>
          <text class="tour-description">{{ steps[currentStep].description }}</text>
        </view>

        <view class="card-footer">
          <text v-if="currentStep === 0">上滑开始　左右跳过</text>
          <text v-else-if="currentStep === 2">上滑下一张　下滑上一张　左右跳过</text>
          <text v-else-if="currentStep === steps.length - 1">上滑完成学习　下滑返回</text>
          <text v-else>上滑下一张　下滑上一张　左右跳过</text>
          <text class="card-footer-arrow">↑</text>
        </view>
      </view>

      <view
        v-if="gestureResult"
        :class="['gesture-result', gestureResultType]"
      >{{ gestureResult }}</view>
      <text class="onboarding-note">像学习一样滑动卡片</text>
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
      submitting: false,
      currentStep: 0,
      demoAnimation: '',
      gestureResult: '',
      gestureResultType: '',
      touchStartX: 0,
      touchStartY: 0,
      ...navMetrics,
      steps: [
        {
          eyebrow: 'STEP 01',
          title: '把长资料，变成短卡片',
          description: '上传你的学习资料，AI 会帮你提取重点，整理成一张张轻量知识卡。',
          visual: 'PDF',
          visualCaption: '资料 → 知识卡'
        },
        {
          eyebrow: 'STEP 02',
          title: '一张卡，只讲一个重点',
          description: '每张卡都只解决一个知识目标，让你在碎片时间也能快速理解。',
          visual: '30s',
          visualCaption: '短时间 · 高专注'
        },
        {
          eyebrow: 'STEP 03',
          title: '用滑动告诉我们',
          description: '上下滑动表示记住了，左右滑动表示没记住。简单的动作就是你的学习反馈。',
          visual: '↕',
          visualCaption: '滑动 · 反馈'
        },
        {
          eyebrow: 'STEP 04',
          title: '在合适的时间再次复习',
          description: '系统会根据你的学习反馈安排复习，让知识从“看过”变成“记得住”。',
          visual: '03',
          visualCaption: '间隔复习 · 长期记忆'
        }
      ]
    }
  },
  onShow() {
    Object.assign(this, getNavMetrics())
  },
  methods: {
    onTouchStart(event) {
      const touch = event.touches && event.touches[0]
      if (!touch) {
        return
      }
      this.touchStartX = touch.clientX
      this.touchStartY = touch.clientY
    },
    onTouchEnd(event) {
      const touch = event.changedTouches && event.changedTouches[0]
      if (!touch) {
        return
      }
      const deltaX = touch.clientX - this.touchStartX
      const deltaY = touch.clientY - this.touchStartY
      const distanceX = Math.abs(deltaX)
      const distanceY = Math.abs(deltaY)

      if (Math.max(distanceX, distanceY) < 45) {
        uni.showToast({ title: '试着滑动卡片', icon: 'none' })
        return
      }

      const isVertical = distanceY >= distanceX
      const remembered = isVertical
      const animation = isVertical
        ? (deltaY < 0 ? 'demo-swipe-up' : 'demo-swipe-down')
        : (deltaX < 0 ? 'demo-swipe-left' : 'demo-swipe-right')
      const movingBack = isVertical && deltaY > 0

      if (movingBack && this.currentStep === 0) {
        return
      }

      this.demoAnimation = animation
      this.gestureResult = remembered ? '记住了' : '没记住'
      this.gestureResultType = remembered ? 'remembered' : 'not-remembered'

      clearTimeout(this.demoAnimationTimer)
      this.demoAnimationTimer = setTimeout(() => {
        if (!movingBack && this.currentStep >= this.steps.length - 1) {
          this.start()
          return
        }
        this.currentStep = movingBack
          ? this.currentStep - 1
          : this.currentStep + 1
        this.demoAnimation = ''
        this.gestureResult = ''
        this.gestureResultType = ''
      }, 320)
    },
    start() {
      if (this.submitting) {
        return
      }
      this.submitting = true
      api.completeOnboarding('CAPM').then(() => {
        uni.switchTab({
          url: '/pages/library/library',
          fail: () => {
            this.submitting = false
            uni.showToast({ title: '无法打开学习页', icon: 'none' })
          }
        })
      }).catch((error) => {
        this.submitting = false
        showError(error, '保存学习目标失败')
      })
    }
  }
}
</script>

<style>
.onboarding-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 0 32rpx 52rpx;
  background: #f6f8fb;
}

.onboarding-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  box-sizing: border-box;
  min-height: 0;
}

.nav-brand {
  display: flex;
  flex: 1;
  align-items: center;
  min-width: 0;
  gap: 16rpx;
}

.mini-brand {
  width: 48rpx;
  height: 48rpx;
  border-radius: 14rpx;
  background: #102a43;
  color: #ffffff;
  font-size: 18rpx;
  font-weight: 700;
  line-height: 48rpx;
  letter-spacing: 1rpx;
  text-align: center;
}

.card-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24rpx;
  color: #829ab1;
  font-size: 23rpx;
}

.card-progress text:last-child {
  color: #1976d2;
  font-weight: 700;
}

.onboarding-card {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 720rpx;
  margin-top: 24rpx;
  padding: 30rpx;
  border: 1rpx solid #d9e2ec;
  border-radius: 32rpx;
  background: #ffffff;
  box-shadow: 0 18rpx 42rpx rgba(16, 42, 67, 0.1);
}

.card-header,
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #829ab1;
  font-size: 22rpx;
}

.card-header {
  padding-bottom: 24rpx;
  border-bottom: 1rpx solid #e8eef5;
  font-size: 21rpx;
  letter-spacing: 1rpx;
}

.card-header text:last-child,
.card-footer-arrow {
  color: #1976d2;
  font-weight: 700;
}

.card-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  justify-content: center;
  padding: 48rpx 12rpx;
}

.card-symbol {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 168rpx;
  height: 168rpx;
  margin-bottom: 62rpx;
  border-radius: 48rpx;
  background: #e8f3fb;
  color: #1976d2;
  font-size: 48rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.tour-eyebrow {
  display: block;
  color: #1976d2;
  font-size: 24rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.tour-title {
  display: block;
  margin-top: 18rpx;
  color: #102a43;
  font-size: 44rpx;
  font-weight: 700;
  line-height: 1.35;
}

.tour-description {
  display: block;
  margin-top: 22rpx;
  color: #627d98;
  font-size: 28rpx;
  line-height: 1.75;
}

.card-footer {
  padding-top: 24rpx;
  border-top: 1rpx solid #e8eef5;
}

.card-footer-arrow {
  font-size: 34rpx;
}

.gesture-result {
  position: relative;
  z-index: 1;
  margin-top: 14rpx;
  font-size: 22rpx;
  font-weight: 700;
}

.gesture-result.remembered {
  color: #2f855a;
}

.gesture-result.not-remembered {
  color: #c53030;
}

.onboarding-note {
  display: block;
  margin-top: 18rpx;
  color: #9fb3c8;
  font-size: 21rpx;
  text-align: center;
}

.demo-swipe-left,
.demo-swipe-right,
.demo-swipe-up,
.demo-swipe-down {
  animation-duration: 320ms;
  animation-fill-mode: forwards;
  animation-timing-function: ease-out;
}

.demo-swipe-left {
  animation-name: demo-swipe-left;
}

.demo-swipe-right {
  animation-name: demo-swipe-right;
}

.demo-swipe-up {
  animation-name: demo-swipe-up;
}

.demo-swipe-down {
  animation-name: demo-swipe-down;
}

@keyframes demo-swipe-left {
  50% {
    transform: translateX(-60rpx) rotate(-3deg);
    opacity: 0.72;
  }
}

@keyframes demo-swipe-right {
  50% {
    transform: translateX(60rpx) rotate(3deg);
    opacity: 0.72;
  }
}

@keyframes demo-swipe-up {
  50% {
    transform: translateY(-46rpx);
    opacity: 0.72;
  }
}

@keyframes demo-swipe-down {
  50% {
    transform: translateY(46rpx);
    opacity: 0.72;
  }
}
</style>
