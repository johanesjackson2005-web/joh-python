// Simple WebSocket-based chat widget client
(function(){
  function qs(sel, ctx){ return (ctx||document).querySelector(sel); }
  const widget = qs('#chat-widget');
  if(!widget) return;
  const userId = widget.dataset.user || '';
  const username = widget.dataset.username || 'Anonymous';
  // choose a room name: allow 'public' for site-wide chat or 'pm_<id1>_<id2>' for private
  function computeRoomName(){
    const scope = qs('#chat-scope') ? qs('#chat-scope').value : null;
    const target = qs('#chat-target') ? qs('#chat-target').value.trim() : '';
    if(scope === 'public' || (!scope && !userId)) return 'public';
    if(scope === 'private'){
      const me = parseInt(userId)||null;
      const other = parseInt(target)||null;
      if(me && other && me !== other){
        const ids = [me, other].sort((a,b)=>a-b);
        return 'pm_' + ids[0] + '_' + ids[1];
      }
      // invalid private target -> fallback to public
      return 'public';
    }
    // default per-user room for backwards compatibility
    return userId ? ('user_' + userId) : 'public';
  }
  let roomName = computeRoomName();
  const protocol = (location.protocol === 'https:') ? 'wss' : 'ws';
  let wsUrl = protocol + '://' + location.host + '/ws/chat/' + roomName + '/';
  let socket;

  function connect(){
    if(socket){
      try{ socket.close(); }catch(e){}
      socket = null;
    }
    roomName = computeRoomName();
    wsUrl = protocol + '://' + location.host + '/ws/chat/' + roomName + '/';
    console.log('Connecting to chat room', roomName);
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
  // If UI controls exist to choose public/private, react to changes and reconnect
  const scopeEl = qs('#chat-scope');
  const targetEl = qs('#chat-target');
  if(scopeEl){
    scopeEl.addEventListener('change', function(){ connect(); });
  }
  if(targetEl){
    targetEl.addEventListener('blur', function(){ connect(); });
  }
  document.addEventListener('keydown', function(e){ if(e.key === 'Enter' && document.activeElement.id === 'chat-input'){ e.preventDefault(); sendMessage(); } });

  connect();
})();
