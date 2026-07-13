/*
 * Mock API for WeChat DevTools verification.
 *
 * The functions have the same shape as the future HTTPS API adapter. Replace
 * this file with request() calls after the FastAPI layer is available.
 */

const STORAGE_KEY = 'knowledge_card_mock_state_v1'

const INITIAL_CARDS = [
  {
    id: 'mock-card-1-v1',
    cardId: 'mock-card-1',
    knowledgePointId: 'mock-kp-1',
    version: 1,
    title: '项目与运营有什么区别？',
    conclusion: '项目是临时性的，运营是持续性的。',
    explanation: '项目有明确的开始和结束，运营持续产生重复性结果。',
    example: '实施一次系统升级是项目，日常客服支持是运营。',
    recallPrompt: '请回忆：项目和运营最关键的区别是什么？',
    referenceAnswer: '项目是临时性工作，运营是持续性工作。',
    source: 'PMI CAPM ECO（Mock）',
    sourceLocator: 'Domain 1 / Foundations'
  },
  {
    id: 'mock-card-2-v1',
    cardId: 'mock-card-2',
    knowledgePointId: 'mock-kp-2',
    version: 1,
    title: '项目生命周期是什么？',
    conclusion: '项目生命周期是项目从开始到结束所经历的一组阶段。',
    explanation: '不同项目的阶段名称可能不同，但都需要明确阶段目标、交付物和决策点。',
    example: '一个产品项目可以拆分为启动、规划、执行、交付和收尾。',
    recallPrompt: '项目生命周期阶段需要明确哪些内容？',
    referenceAnswer: '阶段目标、交付物和决策点。',
    source: 'PMI CAPM ECO（Mock）',
    sourceLocator: 'Domain 2 / Life cycle'
  },
  {
    id: 'mock-card-3-v1',
    cardId: 'mock-card-3',
    knowledgePointId: 'mock-kp-3',
    version: 1,
    title: '相关方为什么重要？',
    conclusion: '相关方的态度和影响力会影响项目结果。',
    explanation: '项目团队需要识别相关方，理解其期望，并持续沟通和参与管理。',
    example: '关键用户没有参与评审，可能导致交付物无法被接受。',
    recallPrompt: '管理相关方的第一步是什么？',
    referenceAnswer: '识别相关方并理解其影响力、期望和参与方式。',
    source: 'PMI CAPM ECO（Mock）',
    sourceLocator: 'Domain 3 / Stakeholders'
  }
]

function createInitialState() {
  return {
    user: {
      id: 'mock-user-1',
      onboardingCompleted: false,
      goal: null,
      subscriptionAuthorized: false,
      newCardLimit: 10,
      reviewLimit: 20,
      reminderTime: '20:00'
    },
    cards: INITIAL_CARDS,
    plans: {},
    completed: {},
    ratingByIdempotency: {},
    records: [],
    feedback: []
  }
}

function loadState() {
  let state = wx.getStorageSync(STORAGE_KEY)
  if (!state || !state.user) {
    state = createInitialState()
    saveState(state)
  }
  return state
}

function saveState(state) {
  wx.setStorageSync(STORAGE_KEY, state)
}

function now() {
  return new Date()
}

function isoNow() {
  return now().toISOString()
}

function addMinutes(date, minutes) {
  return new Date(date.getTime() + minutes * 60 * 1000).toISOString()
}

function addDays(date, days) {
  return new Date(date.getTime() + days * 24 * 60 * 60 * 1000).toISOString()
}

function nextRememberedDate(plan, reviewedAt) {
  const intervals = [3, 7, 14, 30, 60]
  const consecutive = (plan ? plan.consecutiveRemembered : 0) + 1
  const interval = intervals[Math.min(consecutive - 1, intervals.length - 1)]
  return {
    nextReviewAt: addDays(reviewedAt, interval),
    intervalDays: interval,
    consecutiveRemembered: consecutive
  }
}

function getLearningEntry(excludedKnowledgePointIds) {
  const state = loadState()
  const current = now()
  const excluded = excludedKnowledgePointIds || []
  const duePlans = Object.keys(state.plans)
    .map((pointId) => state.plans[pointId])
    .filter(
      (plan) =>
        new Date(plan.nextReviewAt) <= current &&
        excluded.indexOf(plan.knowledgePointId) < 0
    )
    .sort((a, b) => new Date(a.nextReviewAt) - new Date(b.nextReviewAt))
    .slice(0, state.user.reviewLimit)

  if (duePlans.length > 0) {
    const duePointIds = duePlans.map((plan) => plan.knowledgePointId)
    return Promise.resolve({
      mode: 'REVIEW',
      tasks: duePlans,
      cards: state.cards.filter(
        (card) => duePointIds.indexOf(card.knowledgePointId) >= 0
      )
    })
  }

  const newCards = state.cards.filter(
    (card) =>
      !state.plans[card.knowledgePointId] &&
      excluded.indexOf(card.knowledgePointId) < 0
  )
  return Promise.resolve({
    mode: 'NEW',
    tasks: [],
    cards: newCards.slice(0, state.user.newCardLimit)
  })
}

function completeCard(cardVersionId, sessionId) {
  const state = loadState()
  const key = `${sessionId}:${cardVersionId}`
  state.completed[key] = true
  saveState(state)
  return Promise.resolve({ completed: true })
}

function submitRating(cardVersionId, sessionId, rating, idempotencyKey, correctionOf) {
  const state = loadState()
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

  const reviewedAt = now()
  const previousPlan = state.plans[card.knowledgePointId]
  let schedule = {
    nextReviewAt: addMinutes(reviewedAt, 10),
    intervalDays: 0,
    consecutiveRemembered: 0,
    stage: 'LEARNING'
  }
  let reason = '忘了：10 分钟后再次复习'
  if (rating === 'VAGUE') {
    schedule = {
      nextReviewAt: addDays(reviewedAt, 1),
      intervalDays: 1,
      consecutiveRemembered: 0,
      stage: 'CONSOLIDATING'
    }
    reason = '模糊：1 天后复习'
  } else if (rating === 'REMEMBERED') {
    const remembered = nextRememberedDate(previousPlan, reviewedAt)
    schedule = {
      nextReviewAt: remembered.nextReviewAt,
      intervalDays: remembered.intervalDays,
      consecutiveRemembered: remembered.consecutiveRemembered,
      stage: remembered.consecutiveRemembered >= 3 ? 'STABLE' : 'CONSOLIDATING'
    }
    reason = `记住了：${remembered.intervalDays} 天后复习`
  }

  const record = {
    id: `mock-record-${Date.now()}`,
    cardVersionId,
    knowledgePointId: card.knowledgePointId,
    sessionId,
    rating,
    occurredAt: reviewedAt.toISOString(),
    idempotencyKey,
    correctionOf: correctionOf || null
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
}

module.exports = {
  getSession() {
    return Promise.resolve(loadState().user)
  },
  completeOnboarding(goal) {
    const state = loadState()
    state.user.goal = goal
    state.user.onboardingCompleted = true
    saveState(state)
    return Promise.resolve(state.user)
  },
  getLearningEntry,
  completeCard,
  submitRating,
  requestSubscription(authorized) {
    const state = loadState()
    state.user.subscriptionAuthorized = authorized
    saveState(state)
    return Promise.resolve(state.user)
  },
  getSettings() {
    const state = loadState()
    return Promise.resolve(state.user)
  },
  updateSettings(settings) {
    const state = loadState()
    state.user = Object.assign({}, state.user, settings)
    saveState(state)
    return Promise.resolve(state.user)
  },
  submitFeedback(cardVersionId, type, description) {
    const state = loadState()
    const existing = state.feedback.find(
      (item) => item.cardVersionId === cardVersionId && item.type === type
    )
    if (existing) {
      return Promise.resolve(existing)
    }
    const feedback = {
      id: `mock-feedback-${Date.now()}`,
      cardVersionId,
      type,
      description: description || '',
      createdAt: isoNow(),
      status: 'OPEN'
    }
    state.feedback.push(feedback)
    saveState(state)
    return Promise.resolve(feedback)
  },
  makeReviewDue() {
    const state = loadState()
    const pointIds = Object.keys(state.plans)
    pointIds.forEach((pointId) => {
      state.plans[pointId].nextReviewAt = new Date(Date.now() - 60 * 1000).toISOString()
    })
    saveState(state)
    return Promise.resolve()
  },
  reset() {
    const state = createInitialState()
    saveState(state)
    return Promise.resolve(state)
  }
}

