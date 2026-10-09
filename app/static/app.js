const $ = (selector) => document.querySelector(selector);
const recordButton = $('#record-button');
const recordLabel = $('#record-label');
const recordStatus = $('#record-status');
const chatForm = $('#chat-form');
const messageInput = $('#message');
const languageSelect = $('#language');
const chatThread = $('#chat-thread');
const replyAudio = $('#reply-audio');
const remedies = $('#remedies');
const emergencyBanner = $('#emergency-banner');
const errorMessage = $('#error-message');
const chatList = $('#chat-list');
const CHATS_STORAGE_KEY = 'swasthai-chats';
let locale = 'en';
try { locale = localStorage.getItem('swasthai-language') || 'en'; } catch (_) {}
if (!window.SWASTHAI_I18N[locale]) locale = 'en';
let busy = false;
let recording = false;
let recorder;
let mediaStream;
let busyTimer;
let busyStartedAt = 0;
let statusKey = 'idle';
let errorKey = '';
let lastResult = null;
let chats = loadChats();
let activeChatId = chats[0]?.id || createChatId();
let conversation = chats[0]?.messages || [];

function t(key) { return window.SWASTHAI_I18N[locale][key] || window.SWASTHAI_I18N.en[key] || key; }
function createChatId() { return `chat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`; }
function escapeHtml(value) {
  return String(value || '').replace(/[&<>'"]/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;'}[c]));
}
function loadChats() {
  try {
    const saved = JSON.parse(localStorage.getItem(CHATS_STORAGE_KEY) || 'null');
    if (Array.isArray(saved)) return saved.filter(c => c && typeof c.id === 'string' && Array.isArray(c.messages));
    const legacy = JSON.parse(localStorage.getItem('swasthai-conversation') || '[]');
    if (Array.isArray(legacy) && legacy.length) return [{id:createChatId(), messages:legacy, updatedAt:Date.now()}];
  } catch (_) {}
  return [];
}
function saveConversation() {
  if (conversation.length) {
    let chat = chats.find(c => c.id === activeChatId);
    if (!chat) { chat = {id:activeChatId}; chats.unshift(chat); }
    Object.assign(chat, {messages:conversation, updatedAt:Date.now()});
    chats.sort((a,b) => b.updatedAt - a.updatedAt);
  }
  try {
    localStorage.setItem(CHATS_STORAGE_KEY, JSON.stringify(chats));
    localStorage.removeItem('swasthai-conversation');
  } catch (_) {}
  renderChatList();
}
function renderChatList() {
  chatList.innerHTML = chats.map(chat => {
    const title = chat.messages.find(e => e.role === 'user')?.text || t('newChat');
    return `<button class="chat-list-item${chat.id === activeChatId ? ' is-active' : ''}" type="button" data-chat-id="${escapeHtml(chat.id)}" ${busy || recording ? 'disabled' : ''}><span class="chat-list-icon" aria-hidden="true">•</span><span class="chat-list-title" dir="auto">${escapeHtml(title.slice(0,35))}</span></button>`;
  }).join('');
}
function updateStatus() {
  recordStatus.textContent = t(statusKey) + (busy ? ` ${t('elapsed').replace('{seconds}', Math.floor((Date.now()-busyStartedAt)/1000))}` : '');
}
function applyLanguage() {
  document.documentElement.lang = locale;
  document.documentElement.dir = locale === 'ur' ? 'rtl' : 'ltr';
  document.title = `SwasthAI | ${t('title')}`;
  languageSelect.value = locale;
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  $('.sidebar').setAttribute('aria-label', t('recent'));
  $('.brand').setAttribute('aria-label', `SwasthAI — ${t('title')}`);
  chatList.setAttribute('aria-label', t('recent'));
  $('#new-question').setAttribute('aria-label', t('newChat'));
  languageSelect.setAttribute('aria-label', t('language'));
  $('#composer-label').textContent = t(conversation.length ? 'reply' : 'composer');
  messageInput.placeholder = t(conversation.length ? 'continue' : 'placeholder');
  $('#send-label').textContent = t('send');
  $('.send-button').title = t('send');
  recordLabel.textContent = t(recording ? 'stop' : 'speak');
  recordButton.title = t(recording ? 'stop' : 'speak');
  recordButton.setAttribute('aria-label', recordButton.title);
  replyAudio.setAttribute('aria-label', t('reply'));
  if (errorKey) errorMessage.textContent = t(errorKey);
  updateStatus();
  renderChatList();
  if (lastResult) renderRemedies(lastResult);
}
function updateControls() {
  recordButton.disabled = busy;
  recordButton.classList.toggle('is-recording', recording);
  recordButton.setAttribute('aria-pressed', String(recording));
  $('.send-button').disabled = busy || recording;
  messageInput.disabled = busy || recording;
  $('#new-question').disabled = busy || recording;
  chatForm.setAttribute('aria-busy', String(busy));
  applyLanguage();
}
function setBusy(value, key='idle') {
  busy = value;
  statusKey = key;
  clearInterval(busyTimer);
  if (busy) { busyStartedAt = Date.now(); busyTimer = setInterval(updateStatus,1000); }
  updateControls();
}
function showError(key) { errorKey = key; errorMessage.textContent = t(key); errorMessage.hidden = false; }
function clearError() { errorKey=''; errorMessage.hidden=true; errorMessage.textContent=''; }
function addChatMessage(role,text) {
  const p = document.createElement('p');
  p.className = `chat-message ${role === 'user' ? 'user' : 'assistant'}`;
  p.dir = 'auto';
  p.textContent = text;
  chatThread.append(p);
}
function renderConversation() {
  chatThread.innerHTML='';
  conversation.forEach(entry => addChatMessage(entry.role,entry.text));
  $('#welcome').hidden = !!conversation.length;
  $('#result-section').hidden = !conversation.length;
  applyLanguage();
}
function renderRemedies(data) {
  const evidenceKeys = {'strong':'strong','moderate':'moderate','limited':'limited','traditional/anecdotal':'traditional'};
  const entries = ['allopathic','ayurvedic','unani','homeopathic'].filter(key => data[key] && typeof data[key] === 'object');
  $('#remedy-grid').innerHTML = entries.map(key => {
    const item = data[key];
    return `<article class="remedy-card"><h4>${t(key)}</h4><p dir="auto">${escapeHtml(item.summary)}</p><p dir="auto">${escapeHtml(item.precautions)}</p><span class="evidence">${t('evidence')}: ${t(evidenceKeys[item.evidence_level] || 'limited')}</span></article>`;
  }).join('');
  remedies.hidden = !entries.length || data.is_emergency === true;
  const sources = $('#sources');
  sources.replaceChildren();
  const urls = new Set();
  for (const source of data.sources || []) {
    try {
      const url = new URL(source.source_url);
      if (url.protocol !== 'https:' || urls.has(url.href)) continue;
      urls.add(url.href);
      const link = document.createElement('a');
      link.href = url.href; link.target='_blank'; link.rel='noopener noreferrer';
      link.textContent = `${t('sources')} ${urls.size} · ${url.hostname}`;
      sources.append(link);
    } catch (_) {}
  }
  sources.hidden = !urls.size;
}
function speakReply(text,language) {
  if (!window.speechSynthesis || !text) return;
  try {
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = language || locale;
  utterance.rate = 0.9;
  speechSynthesis.speak(utterance);
  } catch (_) { /* A missing device voice must not discard the text answer. */ }
}
async function readApiResponse(response) {
  if (!response.ok) throw new Error('request failed');
  const data = await response.json();
  if (!data || typeof data !== 'object' || typeof data.conversational_reply !== 'string') throw new Error('invalid response');
  return data;
}
function renderResult(data) {
  const reply = data.conversational_reply || t('errorResponse');
  conversation.push({role:'assistant',text:reply});
  saveConversation();
  lastResult = data;
  renderConversation();
  emergencyBanner.hidden = !data.is_emergency;
  renderRemedies(data);
  if (data.audio_url) { replyAudio.src = data.audio_url; replyAudio.hidden=false; }
  speakReply(reply,data.language || locale);
  chatThread.lastElementChild?.scrollIntoView({behavior:'smooth',block:'nearest'});
}
function history() { return conversation.slice(-12).map(entry => ({role:entry.role,content:entry.text})); }
async function submitChat(message) {
  if (busy || recording) return;
  clearError();
  const previousHistory = history();
  const requestLanguage = locale;
  conversation.push({role:'user',text:message});
  saveConversation();
  renderConversation();
  messageInput.value='';
  resizeComposer();
  setBusy(true,'preparing');
  const form = new FormData();
  form.append('message',message); form.append('language',requestLanguage); form.append('history',JSON.stringify(previousHistory));
  try {
    renderResult(await readApiResponse(await fetch('/chat',{method:'POST',body:form})));
  } catch (_) {
    // Roll back the unanswered turn so retrying does not duplicate history.
    conversation.pop(); saveConversation(); renderConversation();
    messageInput.value=message; resizeComposer(); showError('errorChat');
  } finally { setBusy(false); messageInput.focus(); }
}
async function submitVoice(blob, requestLanguage) {
  clearError(); setBusy(true,'transcribing');
  const form = new FormData();
  form.append('file',blob,'voice-question.webm');
  form.append('language',requestLanguage); form.append('history',JSON.stringify(history()));
  try {
    const data = await readApiResponse(await fetch('/voice-chat',{method:'POST',body:form}));
    conversation.push({role:'user',text:data.transcribed_text || t('voiceQuestion')});
    renderResult(data);
  } catch (_) { showError('errorVoice'); }
  finally { setBusy(false); }
}
recordButton.addEventListener('click',async () => {
  if (busy) return;
  clearError();
  if (recorder?.state === 'recording') { recorder.stop(); return; }
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { showError('errorUnsupported'); return; }
  // Lock while permission is pending, preventing concurrent capture sessions.
  setBusy(true,'preparing');
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({audio:true});
    recorder = new MediaRecorder(mediaStream);
    const chunks=[];
    const requestLanguage = locale;
    recorder.addEventListener('dataavailable',e => { if(e.data.size) chunks.push(e.data); });
    let failed = false;
    recorder.addEventListener('error',() => {
      failed=true; recording=false;
      mediaStream.getTracks().forEach(track => track.stop());
      setBusy(false); showError('errorVoice');
    });
    recorder.addEventListener('stop',() => {
      mediaStream.getTracks().forEach(track => track.stop());
      recording=false;
      if (!failed) submitVoice(new Blob(chunks,{type:recorder.mimeType || 'audio/webm'}),requestLanguage);
    });
    recorder.start(); recording=true; setBusy(false,'listening');
  } catch (_) {
    mediaStream?.getTracks().forEach(track => track.stop());
    recording=false; setBusy(false); showError('errorMic');
  }
});
function resizeComposer() { messageInput.style.height='auto'; messageInput.style.height=`${Math.min(messageInput.scrollHeight,140)}px`; }
messageInput.addEventListener('input',resizeComposer);
chatForm.addEventListener('submit',e => { e.preventDefault(); const text=messageInput.value.trim(); if(text) submitChat(text); });
messageInput.addEventListener('keydown',e => {
  if(e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); chatForm.requestSubmit(); }
});
function resetView() {
  lastResult=null; remedies.hidden=true; emergencyBanner.hidden=true;
  replyAudio.pause(); replyAudio.removeAttribute('src'); replyAudio.hidden=true;
  window.speechSynthesis?.cancel(); clearError(); renderConversation(); renderChatList();
}
$('#new-question').addEventListener('click',() => {
  if(busy || recording) return;
  activeChatId=createChatId(); conversation=[]; messageInput.value='';
  resetView(); resizeComposer(); messageInput.focus();
});
chatList.addEventListener('click',e => {
  if(busy || recording) return;
  const chat=chats.find(c => c.id === e.target.closest('[data-chat-id]')?.dataset.chatId);
  if(!chat) return;
  activeChatId=chat.id; conversation=chat.messages; resetView();
});
languageSelect.addEventListener('change',() => {
  locale=languageSelect.value;
  try { localStorage.setItem('swasthai-language',locale); } catch (_) {}
  applyLanguage();
});
renderConversation(); renderChatList(); updateControls();
