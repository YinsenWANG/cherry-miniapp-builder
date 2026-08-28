const STATE_KEY = 'workspace'
const memory = { items: [] }
let state = memory
let saveTimer = null

const $ = (selector) => document.querySelector(selector)

function toast(message) {
  const node = $('#toast')
  node.textContent = message
  node.classList.add('visible')
  window.setTimeout(() => node.classList.remove('visible'), 2200)
}

function publicMessage(error) {
  const messages = {
    PermissionDenied: 'This feature is not permitted. You can review optional permissions in the app details.',
    QuotaExceeded: 'The app storage is full. Remove older items and try again.',
    RateLimited: 'That happened too quickly. Wait a moment and try again.',
    Unavailable: 'Cherry cannot complete that action right now. Your input is still here.',
    InvalidArgument: 'One of the values is not valid. Review it and try again.',
    Cancelled: 'The action was cancelled.',
    Internal: 'Something went wrong. Try again.'
  }
  return messages[error?.name] ?? 'Something went wrong. Try again.'
}

async function loadState() {
  if (!window.cherry) return memory
  try {
    const { value } = await cherry.storage.get(STATE_KEY)
    if (!value) return { items: [] }
    const envelope = JSON.parse(value)
    return envelope.schema === 1 && Array.isArray(envelope.data?.items) ? envelope.data : { items: [] }
  } catch (error) {
    toast(publicMessage(error))
    return { items: [] }
  }
}

async function saveState() {
  if (!window.cherry) return
  $('#save-status').textContent = 'Saving…'
  try {
    await cherry.storage.set(STATE_KEY, JSON.stringify({ schema: 1, updatedAt: new Date().toISOString(), data: state }))
    $('#save-status').textContent = 'Saved'
  } catch (error) {
    $('#save-status').textContent = 'Not saved'
    toast(publicMessage(error))
  }
}

function scheduleSave({ immediate = false } = {}) {
  window.clearTimeout(saveTimer)
  if (immediate) return saveState()
  saveTimer = window.setTimeout(saveState, 250)
}

function render() {
  const list = $('#item-list')
  const empty = $('#empty-state')
  list.replaceChildren()
  empty.hidden = state.items.length > 0
  state.items.forEach((item) => {
    const row = document.createElement('li')
    row.className = 'item'
    const title = document.createElement('strong')
    const notes = document.createElement('p')
    title.textContent = item.title
    notes.textContent = item.notes || 'No notes'
    row.append(title, notes)
    list.append(row)
  })
}

$('#item-form').addEventListener('submit', async (event) => {
  event.preventDefault()
  const form = new FormData(event.currentTarget)
  const title = String(form.get('title') ?? '').trim()
  const notes = String(form.get('notes') ?? '').trim()
  if (!title) return
  state = { ...state, items: [{ id: crypto.randomUUID(), title, notes, createdAt: Date.now() }, ...state.items] }
  event.currentTarget.reset()
  render()
  await scheduleSave({ immediate: true })
})

$('#clear-items').addEventListener('click', async () => {
  if (state.items.length === 0 || !confirm('Remove every item from this workspace?')) return
  state = { ...state, items: [] }
  render()
  await scheduleSave({ immediate: true })
})

$('#primary-action').addEventListener('click', () => $('#item-title').focus())

async function start() {
  state = await loadState()
  render()
  if (!window.cherry) {
    $('#save-status').textContent = 'Browser preview'
    return
  }
  cherry.on('app.visibilityChange', ({ visible }) => {
    if (!visible) scheduleSave({ immediate: true })
  })
  cherry.on('app.localeChange', () => {
    // Replace with the app's locale switch when the generated product is bilingual.
  })
}

start()
