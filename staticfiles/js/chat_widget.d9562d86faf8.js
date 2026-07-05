// Simple WebSocket-based chat widget client
(function(){
  function qs(sel, ctx){ return (ctx||document).querySelector(sel); }
  const widget = qs('#chat-widget');
  if(!widget) return;
  const userId = widget.dataset.user || '';
  const username = widget.dataset.username || 'Anonymous';
  // choose a room name: per-user room if logged in, else 'public'
  const roomName = userId ? ('user_' + userId) : 'public';
  const protocol = (location.protocol === 'https:') ? 'wss' : 'ws';
  const wsUrl = protocol + '://' + location.host + '/ws/chat/' + roomName + '/';
  let socket;

  function connect(){
    socket = new WebSocket(wsUrl);
    socket.onopen = function(){ console.log('Chat connected to', wsUrl); qs('#chat-status') && (qs('#chat-status').innerText='online'); };
    socket.onclose = function(){ console.log('Chat disconnected'); qs('#chat-status') && (qs('#chat-status').innerText='offline'); setTimeout(connect, 3000); };
    socket.onerror = function(e){ console.error('Chat socket error', e); };
    socket.onmessage = function(e){ try{ const data = JSON.parse(e.data); appendMessage(data.user, data.message, false); }catch(err){ console.error(err); } };
  }

  function appendMessage(user, text, outgoing){
    const list = qs('#chat-messages');
    if(!list) return;
    const el = document.createElement('div');
    el.className = 'chat-line' + (outgoing? ' outgoing':'');
    el.innerHTML = '<strong>'+escapeHtml(user)+':</strong> '+escapeHtml(text);
    list.appendChild(el);
    list.scrollTop = list.scrollHeight;
  }

  function escapeHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  function sendMessage(){
    const input = qs('#chat-input');
    const text = input && input.value.trim();
    if(!text) return;

    // If WS is open, send over socket
    if(socket && socket.readyState === WebSocket.OPEN){
      const payload = {message: text, username: username};
      socket.send(JSON.stringify(payload));
      appendMessage(username, text, true);
      input.value = '';
      return;
    }

    // Fallback: send via HTTP POST to persist the message
    try{
      const csrftoken = (function(){
        const match = document.cookie.match(/(^|;)\s*csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[2]) : '';
      })();

      fetch('/chat/send/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({message: text, room: roomName, username: username})
      }).then(resp=>resp.json()).then(data=>{
        if(data && !data.error){
          appendMessage(data.user||username, data.message||text, true);
        } else {
          console.error('Chat send error', data);
        }
      }).catch(err=>{ console.error('Chat POST error', err); });

      input.value = '';
    }catch(err){
      console.error(err);
    }
  }

  // UI wiring
  qs('#chat-open') && qs('#chat-open').addEventListener('click', function(){ const modal = qs('#chat-modal'); modal.style.display = modal.style.display === 'block' ? 'none' : 'block'; qs('#chat-input') && qs('#chat-input').focus(); });
  qs('#chat-close') && qs('#chat-close').addEventListener('click', function(){ qs('#chat-modal').style.display='none'; });
  qs('#chat-send') && qs('#chat-send').addEventListener('click', sendMessage);
  document.addEventListener('keydown', function(e){ if(e.key === 'Enter' && document.activeElement.id === 'chat-input'){ e.preventDefault(); sendMessage(); } });

  connect();
})();
