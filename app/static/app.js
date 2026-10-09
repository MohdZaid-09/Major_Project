const recordButton = document.querySelector('#record-button');
const recordLabel = document.querySelector('#record-label');
const recordStatus = document.querySelector('#record-status');
const chatForm = document.querySelector('#chat-form');
const messageInput = document.querySelector('#message');
const welcome = document.querySelector('#welcome');
const composerLabel = document.querySelector('#composer-label');
const sendLabel = document.querySelector('#send-label');
const languageSelect = document.querySelector('#language');
const resultSection = document.querySelector('#result-section');
const chatThread = document.querySelector('#chat-thread');
const replyAudio = document.querySelector('#reply-audio');
const remedies = document.querySelector('#remedies');
const remedyGrid = document.querySelector('#remedy-grid');
const emergencyBanner = document.querySelector('#emergency-banner');
const errorMessage = document.querySelector('#error-message');
const newQuestionButton = document.querySelector('#new-question');
const chatList = document.querySelector('#chat-list');
const STORAGE_KEY = 'swasthai-conversation';
const CHATS_STORAGE_KEY = 'swasthai-chats';

let recorder;
let chunks = [];
let busyTimer;
let busyStartedAt;
let chats = loadChats();
let activeChatId = chats[0]?.id || createChatId();
let conversation = getActiveConversation();

function createChatId() {
  return `chat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function loadChats() {
  try {
    const savedChats = JSON.parse(window.localStorage.getItem(CHATS_STORAGE_KEY) || 'null');
    if (Array.isArray(savedChats)) {
      return savedChats.filter((chat) => chat && chat.id && Array.isArray(chat.messages));
    }

    const legacyMessages = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '[]');
    if (Array.isArray(legacyMessages) && legacyMessages.length) {
      const migratedChat = {
        id: createChatId(),
        title: getChatTitle(legacyMessages),
        messages: legacyMessages,
        updatedAt: Date.now()
      };
      window.localStorage.setItem(CHATS_STORAGE_KEY, JSON.stringify([migratedChat]));
      return [migratedChat];
    }
  } catch (error) {
    return [];
  }
  return [];
}

function getActiveConversation() {
  return chats.find((chat) => chat.id === activeChatId)?.messages || [];
}

function getChatTitle(messages) {
  const firstUserMessage = messages.find((entry) => entry.role === 'user');
  const title = firstUserMessage?.text?.trim() || 'New conversation';
  return title.length > 35 ? `${title.slice(0, 35).trim()}...` : title;
}

function saveChats() {
  try {
    window.localStorage.setItem(CHATS_STORAGE_KEY, JSON.stringify(chats));
    window.localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    // The in-memory archive still works when browser storage is unavailable.
  }
}

function saveActiveChat() {
  const existingChat = chats.find((chat) => chat.id === activeChatId);
  if (conversation.length) {
    const chat = existingChat || { id: activeChatId, title: getChatTitle(conversation), messages: [] };
    chat.messages = conversation;
    chat.title = getChatTitle(conversation);
    chat.updatedAt = Date.now();
    if (!existingChat) chats.unshift(chat);
    chats.sort((first, second) => second.updatedAt - first.updatedAt);
  } else if (existingChat) {
    chats = chats.filter((chat) => chat.id !== activeChatId);
  }
  saveChats();
  renderChatList();
}

function renderChatList() {
  chatList.innerHTML = chats.map((chat) => `
    <button class="chat-list-item${chat.id === activeChatId ? ' is-active' : ''}" type="button" data-chat-id="${escapeHtml(chat.id)}">
      <span class="chat-list-icon" aria-hidden="true">•</span>
      <span class="chat-list-title">${escapeHtml(chat.title)}</span>
    </button>
  `).join('');
}

function saveConversation() {
  saveActiveChat();
}

function renderConversation() {
  chatThread.innerHTML = '';
  conversation.forEach((entry) => addChatMessage(entry.role, entry.text));
  if (conversation.length) {
    welcome.hidden = true;
    resultSection.hidden = false;
    composerLabel.textContent = 'Reply to the assistant';
    messageInput.placeholder = 'Continue the conversation...';
    sendLabel.textContent = 'Send reply';
  }
}

function openChat(chatId) {
  const selectedChat = chats.find((chat) => chat.id === chatId);
  if (!selectedChat || selectedChat.id === activeChatId) return;
  activeChatId = selectedChat.id;
  conversation = selectedChat.messages;
  renderConversation();
  renderChatList();
  remedies.hidden = true;
  emergencyBanner.hidden = true;
  replyAudio.pause();
  replyAudio.removeAttribute('src');
  replyAudio.hidden = true;
  resultSection.hidden = !conversation.length;
}

function setBusy(isBusy, text) {
  recordButton.disabled = isBusy;
  chatForm.querySelector('button').disabled = isBusy;
  window.clearInterval(busyTimer);
  if (!isBusy) {
    if (text) recordStatus.textContent = text;
    return;
  }

  busyStartedAt = Date.now();
  recordStatus.textContent = `${text} 0 seconds elapsed.`;
  busyTimer = window.setInterval(() => {
    const seconds = Math.floor((Date.now() - busyStartedAt) / 1000);
    recordStatus.textContent = `${text} ${seconds} seconds elapsed.`;
  }, 1000);
}

function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
}

function clearError() {
  errorMessage.hidden = true;
  errorMessage.textContent = '';
}

function renderRemedies(data) {
  const labels = {
    allopathic: 'Modern medicine',
    ayurvedic: 'Ayurvedic care',
    unani: 'Unani care',
    homeopathic: 'Homeopathic view'
  };
  const entries = Object.entries(labels)
    .filter(([key]) => data[key])
    .map(([key, label]) => {
      const remedy = data[key];
      return `<article class="remedy-card">
        <h4>${label}</h4>
        <p>${escapeHtml(remedy.summary)}</p>
        <p>${escapeHtml(remedy.precautions)}</p>
        <span class="evidence">Evidence: ${escapeHtml(remedy.evidence_level)}</span>
      </article>`;
    });

  remedyGrid.innerHTML = entries.join('');
  remedies.hidden = entries.length < 4;
}

function escapeHtml(value) {
  return String(value || '').replace(/[&<>'"]/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[character]));
}

function speakReply(text, language) {
  if (!('speechSynthesis' in window) || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = language || 'en';
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
}

function addChatMessage(role, text) {
  const message = document.createElement('p');
  message.className = `chat-message ${role}`;
  message.textContent = text;
  chatThread.appendChild(message);
  chatThread.scrollTop = chatThread.scrollHeight;
}

async function readApiResponse(response, fallbackMessage) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || data.error || fallbackMessage);
    return data;
  }

  const body = await response.text();
  if (!response.ok) {
    throw new Error(`${fallbackMessage} (server error ${response.status})`);
  }
  throw new Error(body || fallbackMessage);
}

function renderResult(data) {
  const reply = data.conversational_reply || 'I could not prepare a response. Please try again.';
  welcome.hidden = true;
  addChatMessage('assistant', reply);
  conversation.push({ role: 'assistant', text: reply });
  saveConversation();
  emergencyBanner.hidden = !data.is_emergency;
  renderRemedies(data);
  if (remedies.hidden) {
    composerLabel.textContent = 'Reply to the assistant';
    messageInput.placeholder = 'For example: The pain is mild and I have no vomiting';
    sendLabel.textContent = 'Send reply';
  }
  if (data.audio_url) {
    replyAudio.src = data.audio_url;
    replyAudio.hidden = false;
  } else {
    replyAudio.removeAttribute('src');
    replyAudio.hidden = true;
  }
  speakReply(data.conversational_reply, data.detected_language || data.language);
  resultSection.hidden = false;
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function submitChat(message) {
  clearError();
  addChatMessage('user', message);
  const history = conversation.map((entry) => ({
    role: entry.role,
    content: entry.text
  }));
  conversation.push({ role: 'user', text: message });
  saveConversation();
  setBusy(true, 'Preparing your answer. Please wait...');
  const formData = new FormData();
  formData.append('message', message);
  formData.append('language', languageSelect.value);
  formData.append('history', JSON.stringify(history));

  try {
    const response = await fetch('/chat', { method: 'POST', body: formData });
    const data = await readApiResponse(response, 'The assistant could not answer right now.');
    renderResult(data);
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy(false, 'You can speak for as long as you need.');
  }
}

async function submitVoice(blob) {
  clearError();
  setBusy(true, 'Understanding your recording. Please wait...');
  const formData = new FormData();
  formData.append('file', blob, 'voice-question.webm');
  formData.append('history', JSON.stringify(conversation.map((entry) => ({
    role: entry.role,
    content: entry.text
  }))));

  try {
    const response = await fetch('/voice-chat', { method: 'POST', body: formData });
    const data = await readApiResponse(response, 'I could not process the recording.');
    const spokenText = data.transcribed_text || 'Voice question';
    addChatMessage('user', spokenText);
    conversation.push({ role: 'user', text: spokenText });
    saveConversation();
    renderResult(data);
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy(false, 'You can speak for as long as you need.');
  }
}

recordButton.addEventListener('click', async () => {
  clearError();
  if (recorder && recorder.state === 'recording') {
    recorder.stop();
    return;
  }

  if (!navigator.mediaDevices || !window.MediaRecorder) {
    showError('Voice recording is not supported in this browser. Please type your question below.');
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = [];
    recorder = new MediaRecorder(stream);
    recorder.addEventListener('dataavailable', (event) => chunks.push(event.data));
    recorder.addEventListener('stop', () => {
      stream.getTracks().forEach((track) => track.stop());
      submitVoice(new Blob(chunks, { type: recorder.mimeType || 'audio/webm' }));
    });
    recorder.start();
    recordButton.classList.add('is-recording');
    recordButton.setAttribute('aria-pressed', 'true');
    recordLabel.textContent = 'Press to finish';
    recordStatus.textContent = 'I am listening. Press the button when you are finished.';
  } catch (error) {
    showError('Microphone access was not available. Please type your question below.');
  }
});

chatForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (message) submitChat(message);
});

newQuestionButton.addEventListener('click', () => {
  saveActiveChat();
  activeChatId = createChatId();
  conversation = [];
  chatThread.innerHTML = '';
  remedies.hidden = true;
  emergencyBanner.hidden = true;
  replyAudio.pause();
  replyAudio.removeAttribute('src');
  replyAudio.hidden = true;
  resultSection.hidden = true;
  welcome.hidden = false;
  composerLabel.textContent = 'What would you like help with?';
  messageInput.placeholder = 'Message SwasthAI...';
  sendLabel.textContent = 'Send message';
  messageInput.focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
  renderChatList();
});

renderConversation();
renderChatList();

chatList.addEventListener('click', (event) => {
  const chatButton = event.target.closest('[data-chat-id]');
  if (chatButton) openChat(chatButton.dataset.chatId);
});

setInterval(() => {
  if (recorder && recorder.state !== 'recording') {
    recordButton.classList.remove('is-recording');
    recordButton.setAttribute('aria-pressed', 'false');
    recordLabel.textContent = 'Press to speak';
  }
}, 250);
