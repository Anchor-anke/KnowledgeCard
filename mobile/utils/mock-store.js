import { INITIAL_CARDS } from './mock-cards'

const STORAGE_KEY = 'knowledge_card_mobile_state_v1'

const COLLECTION_DEFINITIONS = [
  {
    id: 'capm',
    title: 'CAPM',
    subtitle: '项目管理助理认证，覆盖基础到商业分析',
    label: '考试认证',
    coverMark: 'CAPM',
    decks: [
      {
        id: 'capm-all',
        title: '全部知识',
        subtitle: '一次学习 CAPM 全部知识点',
        label: '完整',
        matcher: (card) => card.imported !== true
      },
      {
        id: 'foundations',
        title: '项目管理基础',
        subtitle: '项目、治理、角色与核心管理概念',
        label: 'Domain 1',
        matcher: (card) => card.imported !== true && card.sourceLocator.indexOf('Domain 1') === 0
      },
      {
        id: 'predictive',
        title: '预测型项目管理',
        subtitle: '范围、进度、成本与传统项目管理方法',
        label: 'Domain 2',
        matcher: (card) => card.imported !== true && card.sourceLocator.indexOf('Domain 2') === 0
      },
      {
        id: 'agile',
        title: '敏捷与混合方法',
        subtitle: '敏捷原则、迭代交付与混合型项目实践',
        label: 'Domain 3',
        matcher: (card) => card.imported !== true && card.sourceLocator.indexOf('Domain 3') === 0
      },
      {
        id: 'business-analysis',
        title: '商业分析',
        subtitle: '需求、交付成果与项目价值实现',
        label: 'Domain 4',
        matcher: (card) => card.imported !== true && card.sourceLocator.indexOf('Domain 4') === 0
      }
    ]
  }
]

const DECK_DEFINITIONS = COLLECTION_DEFINITIONS.reduce(
  (result, collection) => result.concat(collection.decks),
  []
)

function createInitialState() {
  return {
    user: {
      id: 'mobile-user-1',
      onboardingCompleted: false,
      goal: null,
      subscriptionAuthorized: false,
      newCardLimit: 10,
      reviewLimit: 20,
      reminderTime: '20:00',
      activeDeckId: 'capm-all'
    },
    cards: INITIAL_CARDS,
    importedDecks: [],
    plans: {},
    completed: {},
    ratingByIdempotency: {},
    records: [],
    feedback: []
  }
}

function readState() {
  const stored = typeof uni !== 'undefined' ? uni.getStorageSync(STORAGE_KEY) : null
  if (!stored || !stored.user || !Array.isArray(stored.cards)) {
    const fresh = createInitialState()
    saveState(fresh)
    return fresh
  }
  if (!Array.isArray(stored.importedDecks)) {
    stored.importedDecks = []
  }
  if (!stored.plans || typeof stored.plans !== 'object') stored.plans = {}
  if (!stored.completed || typeof stored.completed !== 'object') stored.completed = {}
  if (!stored.ratingByIdempotency || typeof stored.ratingByIdempotency !== 'object') {
    stored.ratingByIdempotency = {}
  }
  if (!Array.isArray(stored.records)) stored.records = []
  if (!Array.isArray(stored.feedback)) stored.feedback = []
  return stored
}

function saveState(state) {
  if (typeof uni !== 'undefined') {
    uni.setStorageSync(STORAGE_KEY, state)
  }
}

function getImportedCollections(state) {
  return (state.importedDecks || []).map((deck) => ({
    id: `collection-${deck.id}`,
    title: deck.title,
    subtitle: deck.subtitle || '来自 PDF 的 AI 知识卡草稿',
    label: 'AI 制卡',
    coverMark: 'PDF',
    decks: [
      {
        id: deck.id,
        title: deck.title,
        subtitle: `${deck.cardCount || 0} 张知识卡 · ${deck.sourceName || 'PDF'}`,
        label: 'PDF',
        matcher: (card) => card.importedDeckId === deck.id
      }
    ]
  }))
}

function getAllCollections(state) {
  return COLLECTION_DEFINITIONS.concat(getImportedCollections(state))
}

function getDeckDefinition(deckId, state) {
  const normalizedId = deckId === 'all' ? 'capm-all' : deckId
  return (
    getAllCollections(state)
      .reduce((result, collection) => result.concat(collection.decks), [])
      .find((deck) => deck.id === normalizedId) || DECK_DEFINITIONS[0]
  )
}

function getCardsForDeck(state, deckId) {
  const deck = getDeckDefinition(deckId || state.user.activeDeckId, state)
  return state.cards.filter((card) => deck.matcher(card))
}

function getStatsForCards(state, cards) {
  const cardIds = new Set(cards.map((card) => card.id))
  const learnedCardIds = Array.from(
    new Set(
      state.records
        .filter((record) => cardIds.has(record.cardVersionId))
        .map((record) => record.cardVersionId)
    )
  )
  const now = new Date()
  const dueCards = cards.filter((card) => {
    const plan = state.plans[card.knowledgePointId]
    return plan && new Date(plan.nextReviewAt) <= now
  }).length
  return {
    totalCards: cards.length,
    learnedCards: learnedCardIds.length,
    dueCards,
    completionPercent: cards.length
      ? Math.min(100, Math.round((learnedCardIds.length / cards.length) * 100))
      : 0
  }
}

function addMinutes(date, minutes) {
  return new Date(date.getTime() + minutes * 60 * 1000).toISOString()
}

function addDays(date, days) {
  return new Date(date.getTime() + days * 24 * 60 * 60 * 1000).toISOString()
}

function getLearningStats(state) {
  return getStatsForCards(state, getCardsForDeck(state))
}

function nextRememberedDate(plan, reviewedAt) {
  const intervals = [3, 7, 14, 30, 60]
  const consecutive =
    (plan && plan.lastRating === 'REMEMBERED'
      ? plan.consecutiveRemembered
      : 0) + 1
  const interval = intervals[Math.min(consecutive - 1, intervals.length - 1)]
  return {
    nextReviewAt: addDays(reviewedAt, interval),
    intervalDays: interval,
    consecutiveRemembered: consecutive
  }
}

export const api = {
  getSession() {
    return Promise.resolve(readState().user)
  },

  completeOnboarding(goal) {
    const state = readState()
    state.user.goal = goal
    state.user.onboardingCompleted = true
    saveState(state)
    return Promise.resolve(state.user)
  },

  getLibrary() {
    const state = readState()
    const activeDeckId = getDeckDefinition(state.user.activeDeckId, state).id
    const collections = getAllCollections(state).map((collection) => {
      const decks = collection.decks.map((deck) => ({
        id: deck.id,
        title: deck.title,
        subtitle: deck.subtitle,
        label: deck.label,
        stats: getStatsForCards(state, getCardsForDeck(state, deck.id))
      }))
      const rootDeck = decks[0]
      return {
        id: collection.id,
        title: collection.title,
        subtitle: collection.subtitle,
        label: collection.label,
        coverMark: collection.coverMark,
        stats: rootDeck.stats,
        decks,
        hasActiveDeck: decks.some((deck) => deck.id === activeDeckId)
      }
    })
    return Promise.resolve({ activeDeckId, collections })
  },

  setActiveDeck(deckId) {
    const state = readState()
    state.user.activeDeckId = getDeckDefinition(deckId, state).id
    saveState(state)
    return Promise.resolve(state.user)
  },

  getLearningEntry(excludedKnowledgePointIds = []) {
    const state = readState()
    const deckCards = getCardsForDeck(state)
    const deckPointIds = new Set(deckCards.map((card) => card.knowledgePointId))
    const now = new Date()
    const duePlans = Object.keys(state.plans)
      .map((pointId) => state.plans[pointId])
      .filter(
        (plan) =>
          new Date(plan.nextReviewAt) <= now &&
          deckPointIds.has(plan.knowledgePointId) &&
          excludedKnowledgePointIds.indexOf(plan.knowledgePointId) < 0
      )
      .sort((a, b) => new Date(a.nextReviewAt) - new Date(b.nextReviewAt))
      .slice(0, state.user.reviewLimit)

    if (duePlans.length) {
      const duePointIds = duePlans.map((plan) => plan.knowledgePointId)
      return Promise.resolve({
        mode: 'REVIEW',
        tasks: duePlans,
        stats: getLearningStats(state),
        cards: deckCards.filter((card) => duePointIds.indexOf(card.knowledgePointId) >= 0)
      })
    }

    const newCards = deckCards.filter(
      (card) =>
        !state.plans[card.knowledgePointId] &&
        excludedKnowledgePointIds.indexOf(card.knowledgePointId) < 0
    )
    return Promise.resolve({
      mode: 'NEW',
      tasks: [],
      stats: getLearningStats(state),
      cards: newCards.slice(0, state.user.newCardLimit)
    })
  },

  saveImportedDeck(draft) {
    const state = readState()
    const sourceName = String(draft && draft.sourceName ? draft.sourceName : '').trim()
    const title = String(draft && draft.title ? draft.title : '').trim() || sourceName || 'PDF 知识卡'
    const deckId = `pdf-${Date.now()}`
    const rawCards = Array.isArray(draft && draft.cards) ? draft.cards.slice(0, 20) : []
    const cards = rawCards.map((item, index) => ({
      id: `pdf-card-${Date.now()}-${index}-v1`,
      cardId: `pdf-card-${Date.now()}-${index}`,
      knowledgePointId: `pdf-kp-${deckId}-${index}`,
      version: 1,
      title: String(item.title || `知识点 ${index + 1}`),
      conclusion: String(item.conclusion || ''),
      explanation: String(item.explanation || ''),
      example: String(item.example || '资料中未提供例子。'),
      recallPrompt: String(item.recall_prompt || item.recallPrompt || '请回忆这个知识点的核心结论。'),
      referenceAnswer: String(item.reference_answer || item.referenceAnswer || item.conclusion || ''),
      source: sourceName || 'PDF AI 制卡',
      sourceLocator: String(item.source_locator || item.sourceLocator || 'PDF'),
      imported: true,
      importedDeckId: deckId
    }))
    if (!cards.length) {
      return Promise.reject(new Error('AI 没有生成可保存的知识卡'))
    }
    state.cards = cards.concat(state.cards || [])
    state.importedDecks = [
      {
        id: deckId,
        title,
        subtitle: String(draft.summary || '由 PDF 内容生成的可复习知识卡'),
        sourceName: sourceName || 'document.pdf',
        cardCount: cards.length,
        createdAt: new Date().toISOString()
      },
      ...(state.importedDecks || [])
    ]
    state.user.activeDeckId = deckId
    saveState(state)
    return Promise.resolve(state.importedDecks[0])
  },

  completeCard(cardVersionId, sessionId) {
    const state = readState()
    state.completed[`${sessionId}:${cardVersionId}`] = true
    saveState(state)
    return Promise.resolve({ completed: true })
  },

  submitRecall(cardVersionId, sessionId, rating, answer, idempotencyKey) {
    return this.completeCard(cardVersionId, sessionId).then(() =>
      this.submitRating(
        cardVersionId,
        sessionId,
        rating,
        idempotencyKey,
        null,
        answer
      )
    )
  },

  submitRating(
    cardVersionId,
    sessionId,
    rating,
    idempotencyKey,
    correctionOf,
    selfAnswer
  ) {
    const state = readState()
    if (state.ratingByIdempotency[idempotencyKey]) {
      return Promise.resolve(state.ratingByIdempotency[idempotencyKey])
    }
    const completionKey = `${sessionId}:${cardVersionId}`
    if (!state.completed[completionKey] && !correctionOf) {
      return Promise.reject(new Error('请先完成卡片，再提交记忆自评'))
    }
    const card = state.cards.find((item) => item.id === cardVersionId)
    if (!card) {
      return Promise.reject(new Error('卡片不存在'))
    }

    const reviewedAt = new Date()
    const previousPlan = state.plans[card.knowledgePointId]
    let schedule = {
      nextReviewAt: addMinutes(reviewedAt, 10),
      intervalDays: 0,
      consecutiveRemembered: 0,
      stage: 'LEARNING'
    }
    let reason = '没记住：10 分钟后再次复习'
    if (rating === 'REMEMBERED') {
      const remembered = nextRememberedDate(previousPlan, reviewedAt)
      schedule = {
        nextReviewAt: remembered.nextReviewAt,
        intervalDays: remembered.intervalDays,
        consecutiveRemembered: remembered.consecutiveRemembered,
        stage: remembered.consecutiveRemembered >= 3 ? 'STABLE' : 'CONSOLIDATING'
      }
      reason = `记住了：${remembered.intervalDays} 天后复习`
    } else if (rating === 'PARTIAL') {
      schedule = {
        nextReviewAt: addDays(reviewedAt, 1),
        intervalDays: 1,
        consecutiveRemembered: 0,
        stage: 'CONSOLIDATING'
      }
      reason = '部分记住：1 天后再次复习'
    }

    const record = {
      id: `mobile-record-${Date.now()}`,
      cardVersionId,
      knowledgePointId: card.knowledgePointId,
      sessionId,
      rating,
      occurredAt: reviewedAt.toISOString(),
      idempotencyKey,
      correctionOf: correctionOf || null,
      reviewMode: selfAnswer ? 'ACTIVE_RECALL' : 'CARD_SWIPE',
      selfAnswer: selfAnswer || ''
    }
    state.records.push(record)
    state.ratingByIdempotency[idempotencyKey] = record
    state.plans[card.knowledgePointId] = {
      userId: state.user.id,
      knowledgePointId: card.knowledgePointId,
      nextReviewAt: schedule.nextReviewAt,
      lastReviewedAt: reviewedAt.toISOString(),
      lastRating: rating,
      consecutiveRemembered: schedule.consecutiveRemembered,
      intervalDays: schedule.intervalDays,
      stage: schedule.stage,
      algorithmVersion: 'mvp-v1',
      overdue: false,
      reason
    }
    saveState(state)
    return Promise.resolve({ record, plan: state.plans[card.knowledgePointId] })
  },

  submitRememberedBatch(cardVersionIds, sessionId, batchId) {
    return (cardVersionIds || []).reduce(
      (promise, cardVersionId) =>
        promise
          .then(() => this.completeCard(cardVersionId, sessionId))
          .then(() =>
            this.submitRating(
              cardVersionId,
              sessionId,
              'REMEMBERED',
              `${batchId}:${cardVersionId}:remembered`
            )
          ),
      Promise.resolve()
    )
  },

  getSettings() {
    return Promise.resolve(readState().user)
  },

  updateSettings(settings) {
    const state = readState()
    state.user = Object.assign({}, state.user, settings)
    saveState(state)
    return Promise.resolve(state.user)
  },

  requestSubscription(authorized) {
    return this.updateSettings({ subscriptionAuthorized: authorized })
  },

  submitFeedback(cardVersionId, type, description) {
    const state = readState()
    const existing = state.feedback.find(
      (item) => item.cardVersionId === cardVersionId && item.type === type
    )
    if (existing) {
      return Promise.resolve(existing)
    }
    const feedback = {
      id: `mobile-feedback-${Date.now()}`,
      cardVersionId,
      type,
      description: description || '',
      createdAt: new Date().toISOString(),
      status: 'OPEN'
    }
    state.feedback.push(feedback)
    saveState(state)
    return Promise.resolve(feedback)
  },

  reset() {
    const state = createInitialState()
    saveState(state)
    return Promise.resolve(state)
  }
}
