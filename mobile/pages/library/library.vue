<template>
  <view class="page library-page">
    <view :aria-hidden="uploadVisible" class="custom-nav" :style="{ height: navTotalHeight + 'px' }">
      <view :style="{ height: statusBarHeight + 'px' }">
      </view>
      <view
        class="custom-nav-bar"
        :style="{ height: navBarHeight + 'px' }"
      >
        <view class="nav-title-wrap">
          <view class="nav-eyebrow">
            MY LIBRARY
          </view>
          <view class="nav-title">
            知识库
          </view>
        </view>
        <button role="button" class="nav-action" @tap="openSettings">
          设置
        </button>
      </view>
    </view>
    <view :aria-hidden="uploadVisible" class="library-body" :style="{ paddingTop: navTotalHeight + 'px' }">
      <view v-if="loading" class="library-loading card-panel">
        <text class="muted">
          正在整理你的知识库…
        </text>
      </view>
      <view v-else class="collection-list">
        <view class="library-intro">
          <text class="intro-kicker">
            一点积累，一点进步
          </text>
          <text class="intro-title">
            今天，也留下一点知识。
          </text>
          <view class="library-stats">
            <view>
              <text class="stat-value">
                {{ libraryStats.totalCards }}
              </text>
              <text class="stat-label">
                张知识卡
              </text>
            </view>
            <view>
              <text class="stat-value">
                {{ libraryStats.learnedCards }}
              </text>
              <text class="stat-label">
                张已学习
              </text>
            </view>
            <view>
              <text class="stat-value due-number">
                {{ libraryStats.dueCards }}
              </text>
              <text class="stat-label">
                张待复习
              </text>
            </view>
          </view>
        </view>
        <view v-if="activeDeck" class="continue-card">
          <view class="continue-heading">
            <text class="continue-label">
              接着上次的内容
            </text>
            <text class="continue-badge">
              {{ activeDeck.stats.dueCards ? '复习优先' : '按自己的节奏' }}
            </text>
          </view>
          <text class="continue-title">
            {{ activeDeck.title }}
          </text>
          <text class="continue-detail">
            已学 {{ activeDeck.stats.learnedCards }} / {{ activeDeck.stats.totalCards }} 张{{ activeDeck.stats.dueCards ? ' · ' + activeDeck.stats.dueCards + ' 张待复习' : '' }}
          </text>
          <button role="button" class="continue-button" @tap="selectDeck(activeDeckId)">
            {{ activeDeck.stats.dueCards ? '开始复习' : activeDeck.stats.learnedCards ? '继续学习' : '开始学习' }}
            <text aria-hidden="true">
              →
            </text>
          </button>
        </view>
        <view class="upload-source-card">
          <view class="upload-source-copy">
            <text class="upload-title">
              把资料变成自己的知识卡
            </text>
            <text class="upload-subtitle">
              上传 PDF，预览 AI 草稿后保存。
            </text>
          </view>
          <button role="button" class="upload-button" @tap="openUpload">
            ＋ 导入
          </button>
        </view>
        <view class="library-section-heading">
          <text>
            我的知识库
          </text>
          <text class="library-count">
            {{ collections.length }} 个知识库
          </text>
        </view>
        <view v-for="(item, index) in collections" :key="item.id" :class="['collection-card', { active: item.hasActiveDeck }]">
          <button role="button" class="collection-main" :aria-expanded="expandedCollectionId === item.id" @tap="toggleCollection(item.id)">
            <view :class="['deck-cover', 'deck-cover-' + (index % 3)]" aria-hidden="true">
              <text class="cover-mark">
                {{ item.coverMark }}
              </text>
              <view class="cover-line">
              </view>
            </view>
            <view class="deck-info">
              <view class="deck-heading">
                <text class="deck-title">
                  {{ item.title }}
                </text>
                <text class="expand-mark">
                  {{ expandedCollectionId === item.id ? '收起' : '展开' }}
                </text>
              </view>
              <text class="deck-subtitle">
                {{ item.id === 'capm' ? '内置示例 · 5 个学习分组' : item.subtitle }}
              </text>
              <view class="deck-progress-summary">
                <text>
                  {{ item.stats.learnedCards }} / {{ item.stats.totalCards }} 张已学
                </text>
                <text>
                  {{ item.stats.completionPercent }}%
                </text>
              </view>
              <view class="deck-progress-track">
                <view class="deck-progress-fill" :style="{ width: item.stats.completionPercent + '%' }">
                </view>
              </view>
              <text v-if="item.stats.dueCards" class="due-hint">
                {{ item.stats.dueCards }} 张到期，等你复习
              </text>
            </view>
          </button>
          <view v-if="expandedCollectionId === item.id" class="subdeck-list">
            <button role="button" v-for="deck in item.decks" :key="deck.id" :class="['subdeck-row', { active: deck.id === activeDeckId }]" @tap.stop="selectDeck(deck.id)">
              <view class="subdeck-copy">
                <view class="subdeck-heading">
                  <text class="subdeck-label">
                    {{ deck.label }}
                  </text>
                  <text v-if="deck.id === activeDeckId" class="active-badge">
                    当前内容
                  </text>
                </view>
                <text class="subdeck-title">
                  {{ deck.title }}
                </text>
                <text class="subdeck-subtitle">
                  {{ deck.subtitle }}
                </text>
              </view>
              <view class="subdeck-meta">
                <text class="subdeck-progress">
                  {{ deck.stats.learnedCards }}/{{ deck.stats.totalCards }}
                </text>
                <text v-if="deck.stats.dueCards" class="subdeck-due">
                  {{ deck.stats.dueCards }} 待复习
                </text>
                <text v-else class="subdeck-enter" aria-hidden="true">
                  →
                </text>
              </view>
            </button>
          </view>
        </view>
        <text class="library-footnote">
          资料与学习进度保存在当前设备
        </text>
      </view>
    </view>
    <view v-if="uploadVisible" class="upload-mask" @tap="closeUpload">
      <view class="upload-sheet" role="dialog" aria-modal="true" aria-label="从 PDF 制作知识卡" @tap.stop>
        <view class="upload-sheet-header">
          <view>
            <text class="upload-sheet-eyebrow">
              从阅读，到记住
            </text>
            <text class="upload-sheet-title">
              从 PDF 制作知识卡
            </text>
          </view>
          <button role="button" v-if="!uploading" class="upload-close" @tap="closeUpload">
            关闭
          </button>
        </view>
        <view v-if="!draft" class="upload-form">
          <text class="form-label">
            资料标题（可选）
          </text>
          <input aria-label="资料标题" v-model="uploadTitle" class="upload-text-input" placeholder="例如：产品设计入门" />
          <text class="form-label">
            PDF 文件
          </text>
          <view class="file-picker" @tap="choosePdf">
            <text class="file-picker-icon">
              ＋
            </text>
            <text class="file-picker-text">
              {{ selectedFileName || '选择一个不超过 10 MB 的 PDF' }}
            </text>
          </view>
          <input
            ref="pdfInput"
            class="native-file-input"
            type="file"
            accept=".pdf,application/pdf"
            @change="onFileChange"
          />
          <view v-if="uploadStatusDetail" class="upload-status">
            <text class="upload-status-label">
              {{ uploadStatusLabel }}
            </text>
            <text class="upload-status-detail">
              {{ uploadStatusDetail }}
            </text>
          </view>
          <button role="button"
            class="primary-button upload-submit"
            :loading="uploading"
            :disabled="uploading || !selectedFile" :aria-disabled="uploading || !selectedFile"
            @tap="startUpload"
          >
            {{ uploading ? '正在制作…' : '上传并生成草稿' }}
          </button>
        </view>
        <view v-else class="draft-preview">
          <view class="draft-ready-badge">
            草稿已生成 · {{ draft.cards.length }} 张
          </view>
          <text class="draft-title">
            {{ draft.title }}
          </text>
          <text class="draft-summary">
            {{ draft.summary }}
          </text>
          <view class="draft-card-list">
            <view v-for="(card, index) in draft.cards" :key="index" class="draft-card-item">
              <text class="draft-card-index">
                {{ String(index + 1).padStart(2, '0') }}
              </text>
              <view>
                <text class="draft-card-title">
                  {{ card.title }}
                </text>
                <text class="draft-card-conclusion">
                  {{ card.conclusion }}
                </text>
                <text v-if="card.explanation" class="draft-card-detail">
                  {{ card.explanation }}
                </text>
                <text v-if="card.source_locator" class="draft-card-source">
                  来源：{{ card.source_locator }}
                </text>
              </view>
            </view>
          </view>
          <text v-if="draft.quality_warnings && draft.quality_warnings.length" class="draft-warning">
            提示：{{ draft.quality_warnings[0] }}
          </text>
          <view class="draft-actions">
            <button role="button" class="secondary-button" @tap="openUpload">
              重新上传
            </button>
            <button role="button" class="primary-button" @tap="saveDraft">
              保存到知识库
            </button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { api } from '../../utils/mock-store'
import { getNavMetrics, showError } from '../../utils/layout'
import { uploadPdfFile, waitForSummary } from '../../utils/api'

export default {
  data() {
    const navMetrics = getNavMetrics()
    return {
      loading: true,
      collections: [],
      activeDeckId: 'capm-all',
      expandedCollectionId: 'capm',
      uploadVisible: false,
      uploading: false,
      selectedFile: null,
      selectedFileName: '',
      uploadTitle: '',
      uploadStatus: '',
      uploadStatusDetail: '',
      draft: null,
      ...navMetrics
    }
  },
  computed: {
    uploadStatusLabel() {
      return { UPLOADING: '正在上传', EXTRACTED: '文字已提取', GENERATING: '正在制作知识卡', DRAFT_READY: '草稿已就绪', FAILED: '暂时未能完成' }[this.uploadStatus] || '处理中'
    },
    activeDeck() {
      return this.collections.reduce((decks, item) => decks.concat(item.decks || []), []).find((deck) => deck.id === this.activeDeckId)
    },
    libraryStats() {
      return this.collections.reduce((total, item) => ({
        totalCards: total.totalCards + item.stats.totalCards,
        learnedCards: total.learnedCards + item.stats.learnedCards,
        dueCards: total.dueCards + item.stats.dueCards
      }), { totalCards: 0, learnedCards: 0, dueCards: 0 })
    }
  },
  onShow() {
    if (this.uploadVisible) uni.hideTabBar({ animation: false })
    Object.assign(this, getNavMetrics())
    this.load()
  },
  onHide() {
    if (this.uploadVisible) uni.showTabBar({ animation: false })
  },
  onBackPress() {
    if (!this.uploadVisible) return false
    this.closeUpload()
    return true
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
    },
    openUpload() {
      this.uploadVisible = true
      uni.hideTabBar({ animation: false })
      this.uploading = false
      this.selectedFile = null
      this.selectedFileName = ''
      this.uploadTitle = ''
      this.uploadStatus = ''
      this.uploadStatusDetail = ''
      this.draft = null
    },
    closeUpload() {
      if (this.uploading) {
        return
      }
      this.uploadVisible = false
      uni.showTabBar({ animation: false })
    },
    choosePdf() {
      if (this.uploading) {
        return
      }
      const ref = this.$refs.pdfInput
      const input = Array.isArray(ref) ? ref[0] : ref
      if (input && typeof input.click === 'function') {
        input.click()
        return
      }
      uni.showToast({ title: '当前环境无法打开文件选择器', icon: 'none' })
    },
    onFileChange(event) {
      const target = event && event.target
      const files = target && target.files
        ? target.files
        : event && event.detail && event.detail.files
      const file = files && files[0]
      if (!file) {
        return
      }
      const name = String(file.name || '').trim()
      if (!/\.pdf$/i.test(name)) {
        this.selectedFile = null
        this.selectedFileName = ''
        uni.showToast({ title: '请选择 PDF 文件', icon: 'none' })
        return
      }
      this.selectedFile = file
      this.selectedFileName = name
      if (!this.uploadTitle) {
        this.uploadTitle = name.replace(/\.pdf$/i, '')
      }
    },
    startUpload() {
      if (!this.selectedFile || this.uploading) {
        uni.showToast({ title: '请先选择 PDF 文件', icon: 'none' })
        return
      }
      this.uploading = true
      this.draft = null
      this.uploadStatus = 'UPLOADING'
      this.uploadStatusDetail = '正在上传 PDF…'
      uploadPdfFile(this.selectedFile, this.uploadTitle).then((created) => {
        if (!created || !created.task_id) {
          throw new Error('服务没有返回制卡任务')
        }
        this.uploadStatus = 'GENERATING'
        this.uploadStatusDetail = 'PDF 已上传，AI 正在提取重点并制作卡片…'
        return waitForSummary(created.task_id, (task) => {
          this.uploadStatus = task.status || 'GENERATING'
          if (task.status === 'EXTRACTED') {
            this.uploadStatusDetail = '文字已提取，正在生成知识卡…'
          } else if (task.status === 'GENERATING') {
            this.uploadStatusDetail = 'AI 正在生成知识卡草稿…'
          }
        })
      }).then((finished) => {
        const result = finished.result || {}
        this.draft = {
          title: finished.title || this.uploadTitle || this.selectedFileName,
          sourceName: finished.source_name || this.selectedFileName,
          summary: result.summary || '',
          key_points: result.key_points || [],
          cards: result.cards || [],
          quality_warnings: result.quality_warnings || []
        }
        this.uploadStatus = 'DRAFT_READY'
        this.uploadStatusDetail = `已生成 ${this.draft.cards.length} 张卡片草稿，请确认后保存。`
        this.uploading = false
      }).catch((error) => {
        this.uploading = false
        this.uploadStatus = 'FAILED'
        this.uploadStatusDetail = error && error.message ? error.message : '上传或制卡失败'
      })
    },
    saveDraft() {
      if (!this.draft || this.uploading) {
        return
      }
      api.saveImportedDeck(this.draft).then((deck) => {
        this.uploadVisible = false
        uni.showTabBar({ animation: false })
        this.load()
        uni.showToast({ title: `已保存 ${deck.cardCount} 张知识卡`, icon: 'success' })
      }).catch((error) => {
        showError(error, '知识卡保存失败')
      })
    }
  }
}
</script>

<style scoped>
.library-page {
  padding: 0 36rpx 48rpx;
}
.library-body {
  max-width: 600px;
  margin: 0 auto;
}
.collection-list {
  padding-top: 28rpx;
}
.library-intro {
  margin-bottom: 30rpx;
}
.intro-kicker, .intro-title {
  display: block;
}
.intro-kicker {
  color: var(--kc-muted);
  font-size: clamp(12px, 25rpx, 15px);
}
.intro-title {
  margin-top: 8rpx;
  font-size: clamp(17px, 39rpx, 22px);
  font-weight: 700;
  letter-spacing: -1rpx;
  line-height: 1.45;
}
.library-stats {
  display: flex;
  gap: 48rpx;
  margin-top: 30rpx;
}
.library-stats > view {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}
.stat-value {
  font-size: clamp(18px, 42rpx, 24px);
  font-weight: 700;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}
.stat-label {
  color: var(--kc-muted);
  font-size: clamp(12px, 23rpx, 13px);
}
.due-number {
  color: var(--kc-primary);
}
.continue-card {
  padding: 30rpx;
  border-radius: 28rpx;
  background: #293d79;
  color: #ffffff;
}
.continue-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}
.continue-label {
  color: #d7e0fb;
  font-size: clamp(12px, 25rpx, 15px);
}
.continue-badge {
  padding: 5rpx 12rpx;
  border-radius: 8rpx;
  background: #3c508b;
  color: #eef2ff;
  font-size: clamp(12px, 21rpx, 12px);
}
.continue-title {
  display: block;
  margin-top: 18rpx;
  font-size: clamp(16px, 36rpx, 21px);
  font-weight: 650;
  line-height: 1.45;
}
.continue-detail {
  display: block;
  margin-top: 8rpx;
  font-size: clamp(12px, 25rpx, 15px);
  color: #d7e0fb;
}
.continue-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 48px;
  margin: 26rpx 0 0;
  padding: 16rpx 24rpx;
  border-radius: 16rpx;
  background: #ffffff;
  color: #293d79;
  font-size: clamp(12px, 28rpx, 16px);
  font-weight: 600;
  line-height: 1.5;
}
.continue-button text {
  font-size: clamp(15px, 34rpx, 20px);
}
.upload-source-card {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin: 22rpx 0 36rpx;
  padding: 24rpx;
  border: 1rpx dashed #c3cce0;
  border-radius: 24rpx;
  background: #eef1f8;
}
.upload-source-copy {
  flex: 1;
  min-width: 0;
}
.upload-title, .upload-subtitle {
  display: block;
}
.upload-title {
  font-size: clamp(12px, 27rpx, 16px);
  font-weight: 600;
}
.upload-subtitle {
  margin-top: 5rpx;
  font-size: clamp(12px, 23rpx, 13px);
  color: var(--kc-muted);
}
.upload-button {
  display: flex;
  align-items: center;
  min-height: 48px;
  flex-shrink: 0;
  margin: 0;
  padding: 12rpx 18rpx;
  border-radius: 14rpx;
  background: #ffffff;
  color: var(--kc-primary);
  font-size: clamp(12px, 27rpx, 16px);
  font-weight: 600;
  line-height: 1.4;
}
.library-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18rpx;
  font-size: clamp(13px, 31rpx, 18px);
  font-weight: 650;
}
.library-count {
  color: var(--kc-muted);
  font-size: clamp(12px, 24rpx, 14px);
  font-weight: 400;
}
.collection-card {
  margin-bottom: 24rpx;
  padding: 26rpx;
  border: 1rpx solid var(--kc-line);
  border-radius: 26rpx;
  background: var(--kc-surface);
}
.collection-main {
  display: flex;
  align-items: center;
  gap: 24rpx;
  width: 100%;
  margin: 0;
  padding: 0;
  background: transparent;
  text-align: left;
  line-height: 1.5;
}
.deck-cover {
  position: relative;
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 116rpx;
  height: 152rpx;
  overflow: hidden;
  border-radius: 12rpx 18rpx 18rpx 12rpx;
  background: #dfe6fa;
  color: #334879;
  border-left: 8rpx solid #c5d0ee;
}
.deck-cover-1 {
  background: #e1eee7;
  border-left-color: #c6ddd0;
  color: #306b54;
}
.deck-cover-2 {
  background: #f4eada;
  border-left-color: #e6d4b5;
  color: #785b32;
}
.cover-mark {
  font-size: clamp(12px, 27rpx, 16px);
  font-weight: 700;
  letter-spacing: 1rpx;
}
.cover-line {
  position: absolute;
  left: 24rpx;
  bottom: 24rpx;
  width: 38rpx;
  height: 3rpx;
  background: currentColor;
  opacity: .45;
}
.deck-info {
  flex: 1;
  min-width: 0;
}
.deck-heading, .deck-progress-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}
.deck-title {
  font-size: clamp(14px, 32rpx, 18px);
  font-weight: 700;
  overflow-wrap: anywhere;
}
.expand-mark {
  flex-shrink: 0;
  font-size: clamp(12px, 23rpx, 13px);
  color: var(--kc-muted);
}
.deck-subtitle {
  display: block;
  margin-top: 7rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 23rpx, 13px);
  overflow-wrap: anywhere;
}
.deck-progress-summary {
  margin-top: 18rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 22rpx, 13px);
}
.deck-progress-track {
  height: 6rpx;
  margin-top: 10rpx;
  overflow: hidden;
  border-radius: 8rpx;
  background: #edf0f6;
}
.deck-progress-fill {
  height: 100%;
  background: var(--kc-primary);
  border-radius: inherit;
}
.due-hint {
  display: block;
  margin-top: 12rpx;
  color: var(--kc-warning);
  font-size: clamp(12px, 23rpx, 13px);
}
.subdeck-list {
  margin-top: 26rpx;
  border-top: 1rpx solid var(--kc-line);
  padding-top: 12rpx;
}
.subdeck-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  width: 100%;
  min-height: 104rpx;
  margin: 0;
  padding: 22rpx 14rpx;
  border-bottom: 1rpx solid #eff1f5;
  border-radius: 0;
  background: transparent;
  text-align: left;
  line-height: 1.5;
}
.subdeck-row:last-child {
  border-bottom: 0;
}
.subdeck-row.active {
  border-radius: 18rpx;
  border-bottom-color: transparent;
  background: var(--kc-primary-soft);
}
.subdeck-copy {
  flex: 1;
  min-width: 0;
}
.subdeck-heading {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12rpx;
}
.subdeck-label {
  color: var(--kc-muted);
  font-size: clamp(12px, 22rpx, 13px);
}
.active-badge {
  color: var(--kc-primary);
  font-size: clamp(12px, 21rpx, 12px);
}
.subdeck-title {
  display: block;
  margin-top: 5rpx;
  font-size: clamp(12px, 28rpx, 16px);
  font-weight: 600;
}
.subdeck-subtitle {
  display: block;
  margin-top: 5rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 23rpx, 13px);
}
.subdeck-meta {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  align-items: flex-end;
  gap: 6rpx;
}
.subdeck-progress {
  font-size: clamp(12px, 24rpx, 14px);
  color: var(--kc-muted);
}
.subdeck-enter {
  color: var(--kc-primary);
  font-size: clamp(13px, 29rpx, 17px);
}
.subdeck-due {
  font-size: clamp(12px, 22rpx, 13px);
  color: var(--kc-warning);
}
.library-footnote {
  display: block;
  margin-top: 30rpx;
  text-align: center;
  color: var(--kc-muted);
  font-size: clamp(12px, 23rpx, 13px);
}
.upload-mask {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 20;
  display: flex;
  align-items: flex-end;
  background: rgba(16, 42, 67, 0.48);
}
.upload-sheet {
  width: 100%;
  box-sizing: border-box;
  max-height: 88vh;
  overflow-y: auto;
  padding: 32rpx 32rpx 42rpx;
  border-radius: 30rpx 30rpx 0 0;
  background: #ffffff;
}
.upload-sheet-header,
.draft-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}
.upload-sheet-title {
  display: block;
  margin-top: 8rpx;
  color: #102a43;
  font-size: clamp(17px, 38rpx, 22px);
  font-weight: 700;
}
.upload-close {
  flex-shrink: 0;
  color: #1976d2;
  font-size: clamp(12px, 24rpx, 14px);
}
.upload-form {
  margin-top: 30rpx;
}
.form-label {
  display: block;
  margin: 18rpx 0 10rpx;
  color: #486581;
  font-size: clamp(12px, 22rpx, 13px);
  font-weight: 700;
}
.upload-text-input {
  width: 100%;
  height: 78rpx;
  box-sizing: border-box;
  padding: 0 22rpx;
  border: 1rpx solid #d9eaf7;
  border-radius: 16rpx;
  background: #f7fbfe;
  color: #102a43;
  font-size: clamp(12px, 26rpx, 15px);
}
.file-picker {
  display: flex;
  align-items: center;
  gap: 16rpx;
  min-height: 96rpx;
  box-sizing: border-box;
  padding: 18rpx 22rpx;
  border: 2rpx dashed #9ac8ec;
  border-radius: 18rpx;
  background: #f4f9fd;
}
.file-picker-icon {
  flex-shrink: 0;
  color: #1976d2;
  font-size: clamp(18px, 42rpx, 24px);
  line-height: 1;
}
.file-picker-text {
  overflow: hidden;
  color: #486581;
  font-size: clamp(12px, 24rpx, 14px);
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.native-file-input {
  position: absolute;
  width: 2rpx;
  height: 2rpx;
  opacity: 0;
}
.upload-status {
  margin-top: 22rpx;
  padding: 18rpx 20rpx;
  border-radius: 16rpx;
  background: #f4f9fd;
}
.upload-status-label,
.upload-status-detail {
  display: block;
}
.upload-status-label {
  color: #1976d2;
  font-size: clamp(12px, 20rpx, 12px);
  font-weight: 700;
  letter-spacing: 1rpx;
}
.upload-status-detail {
  margin-top: 6rpx;
  color: #486581;
  font-size: clamp(12px, 23rpx, 13px);
  line-height: 1.45;
}
.upload-submit {
  width: 100%;
  margin-top: 26rpx;
}
.draft-preview {
  margin-top: 28rpx;
}
.draft-ready-badge {
  display: inline-block;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: #e6f6ff;
  color: #1976d2;
  font-size: clamp(12px, 20rpx, 12px);
  font-weight: 700;
}
.draft-title {
  display: block;
  margin-top: 18rpx;
  color: #102a43;
  font-size: clamp(15px, 34rpx, 20px);
  font-weight: 700;
}
.draft-summary {
  display: block;
  margin-top: 12rpx;
  color: #486581;
  font-size: clamp(12px, 24rpx, 14px);
  line-height: 1.55;
}
.draft-card-list {
  margin-top: 22rpx;
}
.draft-card-item {
  display: flex;
  gap: 16rpx;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #e8eef5;
}
.draft-card-index {
  flex-shrink: 0;
  color: #9ac8ec;
  font-size: clamp(12px, 22rpx, 13px);
  font-weight: 700;
}
.draft-card-title,
.draft-card-conclusion {
  display: block;
}
.draft-card-title {
  color: #102a43;
  font-size: clamp(12px, 25rpx, 15px);
  font-weight: 700;
}
.draft-card-conclusion {
  margin-top: 6rpx;
  color: #627d98;
  font-size: clamp(12px, 22rpx, 13px);
  line-height: 1.4;
}
.draft-warning {
  display: block;
  margin-top: 16rpx;
  color: #c05621;
  font-size: clamp(12px, 21rpx, 12px);
  line-height: 1.45;
}
.draft-actions {
  margin-top: 28rpx;
}
.draft-actions button {
  flex: 1;
  margin: 0;
}
.upload-mask {
  z-index: 50;
  padding-bottom: var(--window-bottom, 0px);
  background: rgba(24, 34, 56, .44);
}
.upload-sheet {
  max-width: 600px;
  margin: 0 auto;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
}
.upload-sheet-eyebrow {
  display: block;
  color: var(--kc-muted);
  font-size: clamp(12px, 24rpx, 14px);
}
.upload-sheet-title {
  font-size: clamp(15px, 35rpx, 20px);
}
.upload-close {
  min-height: 48px;
  min-width: 48px;
  margin: 0;
  padding: 12rpx;
  background: transparent;
  color: var(--kc-primary);
  line-height: 1.5;
}
.upload-text-input {
  min-height: 48px;
  font-size: clamp(12px, 28rpx, 16px);
}
.form-label, .file-picker-text {
  font-size: clamp(12px, 26rpx, 15px);
}
.file-picker {
  min-height: 112rpx;
}
.draft-card-detail {
  display: block;
  margin-top: 10rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 25rpx, 15px);
  line-height: 1.65;
}
.draft-card-source {
  display: block;
  margin-top: 10rpx;
  color: var(--kc-muted);
  font-size: clamp(12px, 23rpx, 13px);
}
.draft-card-title {
  font-size: clamp(12px, 28rpx, 16px);
}
.draft-card-conclusion {
  font-size: clamp(12px, 26rpx, 15px);
  color: var(--kc-ink);
}
.draft-actions {
  position: sticky;
  bottom: -1rpx;
  padding: 22rpx 0 0;
  background: #fff;
}
@media (max-width: 360px) {
  .library-stats {
    gap: 24rpx;
  }
  .intro-title {
    font-size: clamp(15px, 35rpx, 20px);
  }
}
</style>
