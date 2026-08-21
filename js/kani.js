
document.addEventListener('DOMContentLoaded', () => {
  // Only inject if it doesn't already exist
  if (document.getElementById('floatingChatWidget')) return;

  const kaniHTML = `
  <!-- FLOATING CHATBOT BUTTON (DESKTOP) -->
  <div class="floating-chat-btn" id="floatingChatWidget" onclick="toggleKaniChat()" title="Kani AI Assistant (Coming Soon)">
    <div class="floating-chat-icon">
      <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/></svg>
    </div>
    <div class="floating-chat-text">
      <span class="floating-chat-title">Kani AI Assistant</span>
      <span class="floating-chat-status" style="color:#00c97a;">● Online</span>
    </div>
  </div>

  <!-- POP-UP FLOATING CHAT OVERLAY WINDOW -->
  <div class="floating-chat-window" id="floatingChatWindow">
    <div class="window-header">
      <div class="window-title">
        <div class="window-mini-hud">KANI</div>
        <div>
          <div style="font-family:'Orbitron',sans-serif; font-size:0.85rem; font-weight:700; color:#fff;">Kani AI Assistant</div>
          <div style="font-family:'Space Mono',monospace; font-size:0.68rem; color:#00c97a;"><span class="pulse-dot" style="background:#00c97a; box-shadow:0 0 8px #00c97a;"></span> Online</div>
        </div>
      </div>
      <button class="window-close-btn" onclick="toggleKaniChat()" aria-label="Close Chat">✕</button>
    </div>

    <div class="chat-card-body" id="popupChatBody">
      <div class="chat-message bot-msg">
        <div class="msg-bubble">
          <b>[KANI]</b><br>Hello! I am Kani, your NgenAI Intelligent Assistant. How can I help you today?
        </div>
      </div>
      <div class="chat-chips" id="popupChatChips">
        <button class="chip-btn" onclick="sendPopupQuickPrompt('Tell me about Agentic AI Automation & Integrations')">⚡ Agentic AI Services</button>
        <button class="chip-btn" onclick="sendPopupQuickPrompt('Tell me about RAG Pipelines')">📄 RAG Pipelines</button>
        <button class="chip-btn" onclick="sendPopupQuickPrompt('Do you help with M.Tech & PhD projects?')">🎓 PhD & M.Tech</button>
        <button class="chip-btn" onclick="sendPopupQuickPrompt('How do I contact NgenAI?')">📞 Contact Kani</button>
      </div>
    </div>

    <div class="chat-card-input">
      <input type="text" id="popupChatInput" placeholder="Ask Kani AI anything..." onkeypress="handlePopupKeyPress(event)">
      <button class="chat-send-btn" onclick="sendPopupMessage()" aria-label="Send">
        <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
      </button>
    </div>
  </div>
  `;

  document.body.insertAdjacentHTML('beforeend', kaniHTML);
});

// Global functions so onclick handlers work
window.toggleKaniChat = function() {
  const win = document.getElementById('floatingChatWindow');
  if(win) {
    win.classList.toggle('active');
    if (win.classList.contains('active')) {
      setTimeout(() => {
        const input = document.getElementById('popupChatInput');
        if (input) input.focus();
      }, 100);
    }
  }
};

window.kaniChatMessages = [];

window.sendPopupQuickPrompt = function(promptText) {
  const input = document.getElementById('popupChatInput');
  if(input) {
    input.value = promptText;
    window.sendPopupMessage();
  }
};

window.handlePopupKeyPress = function(e) {
  if (e.key === 'Enter') {
    window.sendPopupMessage();
  }
};

window.sendPopupMessage = async function() {
  const input = document.getElementById('popupChatInput');
  if(!input) return;
  const query = input.value.trim();
  if (!query) return;

  const chatBody = document.getElementById('popupChatBody');
  const chips = document.getElementById('popupChatChips');
  if (chips) chips.remove();

  const userDiv = document.createElement('div');
  userDiv.className = 'chat-message user-msg';
  userDiv.innerHTML = `<div class="msg-bubble">${escapeKaniHTML(query)}</div>`;
  chatBody.appendChild(userDiv);
  
  window.kaniChatMessages.push({ role: 'user', content: query });
  input.value = '';
  chatBody.scrollTop = chatBody.scrollHeight;

  const typingDiv = document.createElement('div');
  typingDiv.className = 'chat-message bot-msg';
  typingDiv.innerHTML = `<div class="msg-bubble" style="font-style:italic; color:var(--muted);">Kani is typing...</div>`;
  typingDiv.id = 'typingIndicator';
  chatBody.appendChild(typingDiv);
  chatBody.scrollTop = chatBody.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        messages: window.kaniChatMessages,
        context: window.location.pathname
      })
    });
    
    const data = await res.json();
    
    const typing = document.getElementById('typingIndicator');
    if(typing) typing.remove();
    
    if (data.error) {
      throw new Error(data.error);
    }

    const botReply = data.message.content;
    window.kaniChatMessages.push(data.message);

    const botDiv = document.createElement('div');
    botDiv.className = 'chat-message bot-msg';
    
    // Simple markdown parser
    function parseMarkdown(text) {
      return text
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') // bold
        .replace(/\*(.*?)\*/g, '<i>$1</i>')   // italic
        .replace(/\n- (.*?)(?=\n|$)/g, '<br>• $1') // bullet points
        .replace(/\n/g, '<br>'); // newlines
    }
    
    const formattedReply = parseMarkdown(botReply);

    botDiv.innerHTML = `<div class="msg-bubble"><b>[KANI]</b><br>${formattedReply}</div>`;
    chatBody.appendChild(botDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

  } catch (err) {
    console.error(err);
    const typing = document.getElementById('typingIndicator');
    if(typing) typing.remove();
    const errorDiv = document.createElement('div');
    errorDiv.className = 'chat-message bot-msg';
    errorDiv.innerHTML = `<div class="msg-bubble" style="color:#ff4444;">Error connecting to Kani API.</div>`;
    chatBody.appendChild(errorDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
  }
};

function escapeKaniHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag));
}
