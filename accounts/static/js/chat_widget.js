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
    const targetRaw = qs('#chat-target') ? qs('#chat-target').value.trim() : '';
    // normalize function for usernames to make safe room tokens
    function normalizeName(s){ return String(s||'').trim().toLowerCase().replace(/[^a-z0-9_-]+/g, '_'); }
    const target = normalizeName(targetRaw);
    const meName = normalizeName(username);
    if(scope === 'public' || (!scope && !userId)) return 'public';
    if(scope === 'private'){
      if(meName && target && meName !== target){
        const parts = [meName, target].sort();
        return 'pm_' + parts[0] + '_' + parts[1];
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
  let unreadCount = 0;
  const badgeEl = qs('#chat-badge');

  // Notification helpers
  function ensureNotificationPermission(){
    if(!('Notification' in window)) return;
    if(Notification.permission === 'default') Notification.requestPermission().catch(()=>{});
  }

  function playBeep(){
    try{
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = 'sine'; o.frequency.value = 880;
      g.gain.value = 0.02;
      o.connect(g); g.connect(ctx.destination);
      o.start();
      setTimeout(function(){ o.stop(); ctx.close(); }, 120);
    }catch(e){}
  }

 function connect(){

 if(socket){
  try{ socket.close(); }catch(e){}
  socket = null;
}

// safisha messages za zamani kabla ya kupokea history mpya
const list = qs('#chat-messages');
 if(list){
    list.innerHTML = '';
}

roomName = computeRoomName();

wsUrl = protocol + '://' + location.host + '/ws/chat/' + roomName + '/';

console.log('Connecting to chat room', roomName);

socket = new WebSocket(wsUrl);
    socket.onopen = function(){ console.log('Chat connected to', wsUrl); qs('#chat-status') && (qs('#chat-status').innerText='online'); };
    socket.onclose = function(){ console.log('Chat disconnected'); qs('#chat-status') && (qs('#chat-status').innerText='offline'); setTimeout(connect, 3000); };
    socket.onerror = function(e){ console.error('Chat socket error', e); };
   socket.onmessage = function(e){

const data = JSON.parse(e.data);
if (data.type === "delete") {

    let messageBox = document.querySelector(
        `[data-message-id="${data.message_id}"]`
    );

    if (messageBox) {
        messageBox.remove();
    }

    return;
}

// Expand / Restore chat window
if(data.type === "message"){

appendMessage(
    data.user,
    data.message,
    data.user === username,
    data.id,
    data.avatar
);

}

// message ya kawaida + history ya database

};
 }

  function appendMessage(user, text, outgoing, id, avatar){
  const list = qs('#chat-messages');
  if(!list) return;

  const el = document.createElement('div');
  el.className = 'chat-line' + (outgoing ? ' outgoing' : ' incoming');

  // 🔥 muhimu sana kwa delete feature
  if(id) el.setAttribute('data-message-id', id);

  el.innerHTML = `
 <img src="${avatar || '/static/image/logo 1.png'}" alt="Avatar"
style="
width:35px;
height:35px;
border-radius:50%;
object-fit:cover;
margin-right:8px;
">

<strong>${escapeHtml(user)}:</strong> 
${escapeHtml(text)}

<button type="button" class="delete-btn">🗑</button>
`;

  list.appendChild(el);
  list.scrollTop = list.scrollHeight;

  // unread + notification logic (unchanged)
  const modal = qs('#chat-modal');

const modalHidden = !modal || window.getComputedStyle(modal).display === 'none';

if(!outgoing && modalHidden){

  unreadCount += 1;

  if(badgeEl){
    badgeEl.style.display = 'flex';
    badgeEl.classList.add('pulse');
    badgeEl.innerText = unreadCount;
  }

  try{
    if(window.Notification && Notification.permission === 'granted'){
      new Notification(user || 'Chat', {
        body: String(text).slice(0,120)
      });
    }
  }catch(e){}

  playBeep();
}
  }

  function escapeHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  function sendMessage(){
    const input = qs('#chat-input');
    const text = input && input.value.trim();
    if(!text) return;

    // If WS is open, send over socket
    if(socket && socket.readyState === WebSocket.OPEN){
  const payload = {
    type: "message",
    id: crypto.randomUUID(),
    message: text,
    username: username,
    room: roomName
  };

  socket.send(JSON.stringify(payload));
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
  // Emoji UI
  const emojiBtn = qs('#emoji-btn');
  const emojiPicker = qs('#emoji-picker');
  function insertEmoji(ch){ const input = qs('#chat-input'); if(!input) return; try{ const start = input.selectionStart || 0; const end = input.selectionEnd || 0; const v = input.value; input.value = v.slice(0,start) + ch + v.slice(end); input.selectionStart = input.selectionEnd = start + ch.length; input.focus(); }catch(e){ input.value = input.value + ch; } }
  if(emojiPicker){
    emojiPicker.addEventListener('click', function(e){ if(e.target && e.target.classList && e.target.classList.contains('emoji-swatch')){ insertEmoji(e.target.textContent); emojiPicker.style.display='none'; } });
    // keyboard navigation for emoji picker
    (function(){
      const swatches = Array.from(emojiPicker.querySelectorAll('.emoji-swatch'));
      if(!swatches.length) return;
      let active = -1;
      function setActive(i){
        if(active >= 0 && swatches[active]) swatches[active].classList.remove('emoji-active');
        active = i;
        if(active >= 0 && swatches[active]){
          swatches[active].classList.add('emoji-active');
          swatches[active].scrollIntoView({block:'nearest'});
        }
      }
      swatches.forEach((s, idx)=>{
        s.tabIndex = 0;
        s.setAttribute('role','button');
        s.addEventListener('keydown', function(ev){ if(ev.key === 'Enter' || ev.key === ' '){ ev.preventDefault(); s.click(); } });
        s.addEventListener('mouseover', ()=> setActive(idx));
      });

      function onKey(e){
        if(emojiPicker.style.display !== 'block') return;
        const cols = Math.max(1, Math.floor(emojiPicker.clientWidth / 32));
        if(e.key === 'ArrowRight'){
          e.preventDefault(); setActive(Math.min(active+1, swatches.length-1));
        } else if(e.key === 'ArrowLeft'){
          e.preventDefault(); setActive(Math.max(active-1, 0));
        } else if(e.key === 'ArrowDown'){
          e.preventDefault(); setActive(Math.min(active + cols, swatches.length-1));
        } else if(e.key === 'ArrowUp'){
          e.preventDefault(); setActive(Math.max(active - cols, 0));
        } else if(e.key === 'Enter' && active >= 0){
          e.preventDefault(); swatches[active].click();
        } else if(e.key === 'Escape'){
          emojiPicker.style.display = 'none';
        }
      }

      // when opening the picker via button, set focus to first swatch and enable key listener
      if(emojiBtn){
        emojiBtn.addEventListener('click', function(){ if(emojiPicker.style.display === 'block'){ setActive(0); document.addEventListener('keydown', onKey); } else { document.removeEventListener('keydown', onKey); } });
        // ensure we remove listener when picker is closed by outside click
        document.addEventListener('click', function(ev){ if(emojiPicker && emojiPicker.style.display === 'block' && ev.target !== emojiBtn && !emojiPicker.contains(ev.target)){ document.removeEventListener('keydown', onKey); } });
      }
    })();
  }
  if(emojiBtn){
    emojiBtn.addEventListener('click', function(e){ e.stopPropagation(); if(!emojiPicker) return; emojiPicker.style.display = (emojiPicker.style.display === 'block' ? 'none' : 'block'); });
    // hide picker when clicking outside
    document.addEventListener('click', function(e){ if(emojiPicker && e.target !== emojiBtn && !emojiPicker.contains(e.target)){ emojiPicker.style.display='none'; } });
  }
const expandBtn = document.getElementById("chat-expand");
const modal = document.getElementById("chat-modal");

if(expandBtn && modal){

    expandBtn.addEventListener("click", function(){

        modal.classList.toggle("chat-fullscreen");


        if(modal.classList.contains("chat-fullscreen")){

            expandBtn.innerHTML="🗗";

        }else{

            expandBtn.innerHTML="⛶";

        }

    });

}
  
     qs('#chat-open') && qs('#chat-open').addEventListener('click', function(){ 

    const modal = qs('#chat-modal');

    let willOpen = modal.style.display !== 'block';


    if(willOpen){

        const btnPosition = this.getBoundingClientRect();


        // kwanza ionyeshe ili tupate size yake
        modal.style.display = "block";

        modal.style.position = "fixed";
        modal.style.right = "auto";
        modal.style.bottom = "auto";


        const modalWidth = modal.offsetWidth;
        const modalHeight = modal.offsetHeight;


        let left = btnPosition.left;

        let top = btnPosition.top - modalHeight - 10;


        // kama itatoka nje juu
        if(top < 10){

            top = btnPosition.bottom + 10;

        }


        // kama itatoka nje kulia
        if(left + modalWidth > window.innerWidth){

            left = window.innerWidth - modalWidth - 10;

        }


        modal.style.left = left + "px";
        modal.style.top = top + "px";


    }else{

        modal.style.display = "none";

    }


    qs('#chat-input') && qs('#chat-input').focus();


 if(willOpen){ // clear unread count when opening
    unreadCount = 0; if(badgeEl){ badgeEl.style.display='none'; badgeEl.classList.remove('pulse'); badgeEl.innerText = ''; } }
  });
  qs('#chat-close') && qs('#chat-close').addEventListener('click', function(){ qs('#chat-modal').style.display='none'; });
  qs('#chat-send') && qs('#chat-send').addEventListener('click', sendMessage);
  // If UI controls exist to choose public/private, react to changes and reconnect
  document.addEventListener('click', function(e){

  if(!e.target.classList.contains('delete-btn')) return;

  e.preventDefault();
  e.stopPropagation();

  const msgEl = e.target.closest('.chat-line');
  const messageId = msgEl.getAttribute('data-message-id');

  if(socket && socket.readyState === WebSocket.OPEN){
    socket.send(JSON.stringify({
      type: "delete",
      message_id: messageId,
      room: roomName,
      username: username
    }));
  }

});
  const scopeEl = qs('#chat-scope');
  const targetEl = qs('#chat-target');
  if(scopeEl){
    scopeEl.addEventListener('change', function(){ connect(); });
  }
  if(targetEl){
      targetEl.addEventListener('blur', function(){ setTimeout(()=> dropdown.style.display='none', 150); connect(); });
        // autocomplete dropdown
        const dropdown = document.createElement('div');
        dropdown.style.position = 'absolute';
        dropdown.style.background = '#1ff10c';
        dropdown.style.color = '#000';
        dropdown.style.border = '1px solid rgba(0,0,0,0.08)';
        dropdown.style.zIndex = 9999;
        dropdown.style.display = 'none';
        dropdown.style.maxHeight = '180px';
        dropdown.style.overflow = 'auto';
        dropdown.style.minWidth = '160px';
        targetEl.parentElement.style.position = 'relative';
        targetEl.parentElement.appendChild(dropdown);

        let acTimer = null;
        targetEl.addEventListener('input', function(){
          const q = targetEl.value.trim();
          if(acTimer) clearTimeout(acTimer);
          if(!q){ dropdown.style.display='none'; return; }
          acTimer = setTimeout(()=>{
            fetch('/accounts/users/search/?q=' + encodeURIComponent(q))
              .then(r=>r.json())
              .then(data=>{
                dropdown.innerHTML='';
                (data.results||[]).forEach(name=>{
                  const item = document.createElement('div');
                  item.textContent = name;
                  item.style.padding = '6px 8px';
                  item.style.cursor = 'pointer';
                  item.addEventListener('click', ()=>{
                    targetEl.value = name;
                    dropdown.style.display='none';
                    connect();
                  });
                  dropdown.appendChild(item);
                });
                dropdown.style.display = dropdown.children.length ? 'block' : 'none';
              })
              .catch(()=>{ dropdown.style.display='none'; });
          }, 220);
        });
  }
  document.addEventListener('keydown', function(e){ if(e.key === 'Enter' && document.activeElement.id === 'chat-input'){ e.preventDefault(); sendMessage(); } });

  // Request notifications permission proactively
  ensureNotificationPermission();

  connect();
})();


     //for movable widgget
function makeButtonDraggable(button){

    let moving = false;
    let offsetX = 0;
    let offsetY = 0;


    button.addEventListener("mousedown", function(e){

        moving = true;

        let rect = button.getBoundingClientRect();

        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;


       button.style.position = "fixed";
       button.style.left = rect.left + "px";
       button.style.top = rect.top + "px";

        button.style.right = "auto";
        button.style.bottom = "auto";

    });


    document.addEventListener("mousemove", function(e){

        if(!moving) return;


        button.style.left =
            (e.clientX - offsetX) + "px";


        button.style.top =
            (e.clientY - offsetY) + "px";

    });


    document.addEventListener("mouseup", function(){

        moving = false;

    });

}


const chatButton = document.getElementById("chat-open");


if(chatButton){

    makeButtonDraggable(chatButton);

}