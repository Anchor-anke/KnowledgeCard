export function getNavMetrics() {
  let info = {}
  try {
    info = uni.getSystemInfoSync() || {}
  } catch (error) {
    info = {}
  }

  const statusBarHeight = Number.isFinite(info.statusBarHeight) ? info.statusBarHeight : 20
  const navBarHeight = 44
  return {
    statusBarHeight,
    navBarHeight,
    navTotalHeight: statusBarHeight + navBarHeight
  }
}

export function showError(error, fallback = '操作失败') {
  uni.showToast({
    title: (error && error.message) || fallback,
    icon: 'none'
  })
}
