function readWindowInfo() {
  let windowInfo = {}
  let systemInfo = {}
  try {
    if (wx.getWindowInfo) {
      windowInfo = wx.getWindowInfo() || {}
    }
  } catch (error) {
    windowInfo = {}
  }
  try {
    systemInfo = wx.getSystemInfoSync() || {}
  } catch (error) {
    systemInfo = {}
  }
  return {
    statusBarHeight:
      windowInfo.statusBarHeight || systemInfo.statusBarHeight || 20,
    windowWidth: windowInfo.windowWidth || systemInfo.windowWidth || 375,
    windowHeight:
      windowInfo.windowHeight ||
      systemInfo.windowHeight ||
      systemInfo.screenHeight ||
      667,
    screenHeight:
      windowInfo.screenHeight ||
      systemInfo.screenHeight ||
      windowInfo.windowHeight ||
      systemInfo.windowHeight ||
      667,
    safeArea: windowInfo.safeArea || systemInfo.safeArea || null,
    pixelRatio: windowInfo.pixelRatio || systemInfo.pixelRatio || 2
  }
}

function getSafeBottom(screenHeight, safeArea) {
  if (!safeArea || typeof safeArea.bottom !== 'number') {
    return 0
  }
  const raw = Math.max(0, screenHeight - safeArea.bottom)
  // Some Huawei builds return inflated inset values.
  if (raw > 48) {
    return 24
  }
  return raw
}

function getNavMetrics() {
  const info = readWindowInfo()
  let menuButton = null
  try {
    if (wx.getMenuButtonBoundingClientRect) {
      menuButton = wx.getMenuButtonBoundingClientRect()
    }
  } catch (error) {
    menuButton = null
  }

  if (
    !menuButton ||
    !menuButton.height ||
    !menuButton.width ||
    menuButton.top < 0 ||
    menuButton.left <= 0
  ) {
    return {
      statusBarHeight: info.statusBarHeight,
      navBarHeight: 44,
      navTotalHeight: info.statusBarHeight + 44,
      menuSideGap: 96,
      windowHeight: info.windowHeight,
      safeBottom: getSafeBottom(info.screenHeight, info.safeArea)
    }
  }

  const gap = Math.max(4, menuButton.top - info.statusBarHeight)
  const navBarHeight = Math.max(
    32,
    Math.round(menuButton.height + gap * 2)
  )
  const menuSideGap = Math.max(
    12,
    Math.round(info.windowWidth - menuButton.left + 8)
  )

  return {
    statusBarHeight: info.statusBarHeight,
    navBarHeight,
    navTotalHeight: info.statusBarHeight + navBarHeight,
    menuSideGap,
    windowHeight: info.windowHeight,
    safeBottom: getSafeBottom(info.screenHeight, info.safeArea)
  }
}

function getStudyViewportHeight(options) {
  const info = readWindowInfo()
  const navTotalHeight = options && options.navTotalHeight
    ? options.navTotalHeight
    : info.statusBarHeight + 44
  const measuredTop = options && typeof options.cardTop === 'number'
    ? options.cardTop
    : null
  const windowHeight =
    (options && options.windowHeight) || info.windowHeight
  const safeBottom = getSafeBottom(info.screenHeight, info.safeArea)

  let cardTop = measuredTop
  if (typeof cardTop !== 'number' || cardTop < navTotalHeight - 2) {
    cardTop = navTotalHeight + 8
  }

  // Reserve space for gesture hint + home indicator.
  const bottomReserve = Math.max(28, safeBottom + 18)
  let availableHeight = Math.floor(windowHeight - cardTop - bottomReserve)

  if (availableHeight < 240) {
    availableHeight = Math.floor(
      windowHeight - navTotalHeight - bottomReserve - 16
    )
  }

  availableHeight = Math.max(
    240,
    Math.min(availableHeight, Math.floor(windowHeight - navTotalHeight - 24))
  )

  return {
    availableHeight,
    minCardHeight: Math.floor(availableHeight * 0.8),
    windowHeight,
    safeBottom,
    cardTop
  }
}

module.exports = {
  getNavMetrics,
  getStudyViewportHeight,
  readWindowInfo
}
