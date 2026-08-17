const CONFIG_KEY = 'knowledge_card_api_config_v1'
const DEFAULT_API_PORT = 8000
const MAX_PDF_BYTES = 10 * 1024 * 1024

function getPlatform() {
  try {
    return uni.getSystemInfoSync().platform || ''
  } catch (error) {
    return ''
  }
}

function defaultBaseUrl() {
  const platform = getPlatform()
  if (platform === 'android') {
    // Android emulator uses 10.0.2.2 to reach the host machine.
    return `http://10.0.2.2:${DEFAULT_API_PORT}`
  }
  return `http://127.0.0.1:${DEFAULT_API_PORT}`
}

function cleanBaseUrl(value) {
  return String(value || '').trim().replace(/\/+$/, '')
}

function readConfig() {
  const stored = typeof uni !== 'undefined' ? uni.getStorageSync(CONFIG_KEY) : null
  return Object.assign(
    {
      baseUrl: defaultBaseUrl(),
      userId: 'mobile-user-1'
    },
    stored || {}
  )
}

function saveConfig(config) {
  const next = {
    baseUrl: cleanBaseUrl(config.baseUrl) || defaultBaseUrl(),
    userId: String(config.userId || '').trim() || 'mobile-user-1'
  }
  if (typeof uni !== 'undefined') {
    uni.setStorageSync(CONFIG_KEY, next)
  }
  return next
}

function parseResponseBody(raw) {
  if (raw && typeof raw === 'object') {
    return raw
  }
  try {
    return JSON.parse(raw || '{}')
  } catch (error) {
    throw new Error('服务返回了无法识别的内容')
  }
}

function responseError(body, fallback) {
  const detail = body && (body.detail || body.message || body.error)
  return new Error(typeof detail === 'string' ? detail : fallback)
}

function uploadWithUni(filePath, title, config) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${config.baseUrl}/api/v1/summaries/pdf`,
      filePath,
      name: 'file',
      formData: { title: title || '' },
      header: { 'X-User-ID': config.userId },
      success(response) {
        const body = parseResponseBody(response.data)
        if (Number(response.statusCode || 200) >= 400) {
          reject(responseError(body, 'PDF 上传失败'))
          return
        }
        resolve(body)
      },
      fail(error) {
        reject(new Error(error && error.errMsg ? error.errMsg : 'PDF 上传失败'))
      }
    })
  })
}

async function uploadWithFetch(file, title, config) {
  const formData = new FormData()
  formData.append('file', file, file.name || 'document.pdf')
  formData.append('title', title || '')
  const response = await fetch(`${config.baseUrl}/api/v1/summaries/pdf`, {
    method: 'POST',
    headers: { 'X-User-ID': config.userId },
    body: formData
  })
  const body = parseResponseBody(await response.text())
  if (!response.ok) {
    throw responseError(body, 'PDF 上传失败')
  }
  return body
}

export function getApiConfig() {
  return readConfig()
}

export function updateApiConfig(config) {
  return saveConfig(Object.assign({}, readConfig(), config || {}))
}

export function uploadPdfFile(file, title) {
  const config = readConfig()
  if (!config.baseUrl) {
    return Promise.reject(new Error('请先配置 AI 服务地址'))
  }
  if (!file) {
    return Promise.reject(new Error('请选择 PDF 文件'))
  }
  if (typeof file !== 'string' && file.size && file.size > MAX_PDF_BYTES) {
    return Promise.reject(new Error('PDF 文件不能超过 10 MB'))
  }
  if (typeof file === 'string') {
    return uploadWithUni(file, title, config)
  }
  return uploadWithFetch(file, title, config)
}

export function getSummaryTask(taskId) {
  const config = readConfig()
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${config.baseUrl}/api/v1/summaries/${encodeURIComponent(taskId)}`,
      method: 'GET',
      header: { 'X-User-ID': config.userId },
      success(response) {
        const body = parseResponseBody(response.data)
        if (Number(response.statusCode || 200) >= 400) {
          reject(responseError(body, '读取制卡任务失败'))
          return
        }
        resolve(body)
      },
      fail(error) {
        reject(new Error(error && error.errMsg ? error.errMsg : '读取制卡任务失败'))
      }
    })
  })
}

export async function waitForSummary(taskId, onProgress) {
  const startedAt = Date.now()
  const timeoutMs = 2 * 60 * 1000
  while (Date.now() - startedAt < timeoutMs) {
    const task = await getSummaryTask(taskId)
    if (onProgress) {
      onProgress(task)
    }
    if (task.status === 'DRAFT_READY') {
      return task
    }
    if (task.status === 'FAILED') {
      throw new Error(task.error || 'AI 制卡失败')
    }
    await new Promise((resolve) => setTimeout(resolve, 1200))
  }
  throw new Error('AI 制卡超时，请稍后在服务正常时重试')
}

export { MAX_PDF_BYTES }
