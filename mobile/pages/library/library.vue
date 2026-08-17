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
        <view class="upload-source-card">
          <view class="upload-source-copy">
            <text class="upload-eyebrow">PDF → KNOWLEDGE CARDS</text>
            <text class="upload-title">上传资料，自动生成知识卡</text>
            <text class="upload-subtitle">AI 先生成草稿，你确认后再保存到本地知识库。</text>
          </view>
          <button class="upload-button" @tap="openUpload">上传 PDF</button>
        </view>
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

    <view v-if="uploadVisible" class="upload-mask" @tap="closeUpload">
      <view class="upload-sheet" @tap.stop>
        <view class="upload-sheet-header">
          <view>
            <text class="upload-sheet-eyebrow">AI IMPORT</text>
            <text class="upload-sheet-title">从 PDF 制作知识卡</text>
          </view>
          <text v-if="!uploading" class="upload-close" @tap="closeUpload">关闭</text>
        </view>

        <view v-if="!draft" class="upload-form">
          <text class="form-label">资料标题（可选）</text>
          <input v-model="uploadTitle" class="upload-text-input" placeholder="例如：产品设计入门" />
          <text class="form-label">PDF 文件</text>
          <view class="file-picker" @tap="choosePdf">
            <text class="file-picker-icon">＋</text>
            <text class="file-picker-text">{{ selectedFileName || '选择一个不超过 10 MB 的 PDF' }}</text>
          </view>
          <input
            ref="pdfInput"
            class="native-file-input"
            type="file"
            accept=".pdf,application/pdf"
            @change="onFileChange"
          />
          <view v-if="uploadStatusDetail" class="upload-status">
            <text class="upload-status-label">{{ uploadStatus }}</text>
            <text class="upload-status-detail">{{ uploadStatusDetail }}</text>
          </view>
          <button
            class="primary-button upload-submit"
            :loading="uploading"
            :disabled="uploading || !selectedFile"
            @tap="startUpload"
          >{{ uploading ? '正在制作…' : '上传并生成草稿' }}</button>
        </view>

        <view v-else class="draft-preview">
          <view class="draft-ready-badge">草稿已生成 · {{ draft.cards.length }} 张</view>
          <text class="draft-title">{{ draft.title }}</text>
          <text class="draft-summary">{{ draft.summary }}</text>
          <view class="draft-card-list">
            <view v-for="(card, index) in draft.cards.slice(0, 3)" :key="index" class="draft-card-item">
              <text class="draft-card-index">0{{ index + 1 }}</text>
              <view>
                <text class="draft-card-title">{{ card.title }}</text>
                <text class="draft-card-conclusion">{{ card.conclusion }}</text>
              </view>
            </view>
          </view>
          <text v-if="draft.quality_warnings && draft.quality_warnings.length" class="draft-warning">
            提示：{{ draft.quality_warnings[0] }}
          </text>
          <view class="draft-actions">
            <button class="secondary-button" @tap="openUpload">重新上传</button>
            <button class="primary-button" @tap="saveDraft">保存到知识库</button>
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
    },
    openUpload() {
      this.uploadVisible = true
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
        this.load()
        uni.showToast({ title: `已保存 ${deck.cardCount} 张知识卡`, icon: 'success' })
      }).catch((error) => {
        showError(error, '知识卡保存失败')
      })
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

.upload-source-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 22rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: #102a43;
  box-shadow: 0 14rpx 32rpx rgba(16, 42, 67, 0.16);
}

.upload-source-copy {
  flex: 1;
  min-width: 0;
}

.upload-eyebrow,
.upload-sheet-eyebrow {
  display: block;
  color: #9ac8ec;
  font-size: 18rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.upload-title,
.upload-subtitle {
  display: block;
}

.upload-title {
  margin-top: 8rpx;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.35;
}

.upload-subtitle {
  margin-top: 8rpx;
  color: #d9eaf7;
  font-size: 20rpx;
  line-height: 1.45;
}

.upload-button {
  flex-shrink: 0;
  min-width: 140rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 0;
  border-radius: 999rpx;
  background: #ffffff;
  color: #1976d2;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 72rpx;
}

.upload-button::after,
.upload-submit::after,
.draft-actions button::after {
  border: 0;
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
  font-size: 38rpx;
  font-weight: 700;
}

.upload-close {
  flex-shrink: 0;
  color: #1976d2;
  font-size: 24rpx;
}

.upload-form {
  margin-top: 30rpx;
}

.form-label {
  display: block;
  margin: 18rpx 0 10rpx;
  color: #486581;
  font-size: 22rpx;
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
  font-size: 26rpx;
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
  font-size: 42rpx;
  line-height: 1;
}

.file-picker-text {
  overflow: hidden;
  color: #486581;
  font-size: 24rpx;
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
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

.upload-status-detail {
  margin-top: 6rpx;
  color: #486581;
  font-size: 23rpx;
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
  font-size: 20rpx;
  font-weight: 700;
}

.draft-title {
  display: block;
  margin-top: 18rpx;
  color: #102a43;
  font-size: 34rpx;
  font-weight: 700;
}

.draft-summary {
  display: block;
  margin-top: 12rpx;
  color: #486581;
  font-size: 24rpx;
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
  font-size: 22rpx;
  font-weight: 700;
}

.draft-card-title,
.draft-card-conclusion {
  display: block;
}

.draft-card-title {
  color: #102a43;
  font-size: 25rpx;
  font-weight: 700;
}

.draft-card-conclusion {
  margin-top: 6rpx;
  color: #627d98;
  font-size: 22rpx;
  line-height: 1.4;
}

.draft-warning {
  display: block;
  margin-top: 16rpx;
  color: #c05621;
  font-size: 21rpx;
  line-height: 1.45;
}

.draft-actions {
  margin-top: 28rpx;
}

.draft-actions button {
  flex: 1;
  margin: 0;
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
