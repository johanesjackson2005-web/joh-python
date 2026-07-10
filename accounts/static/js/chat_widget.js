// Simple WebSocket-based chat widget client




(function(){
    function getCookie(name){

    let cookieValue = null;

    const cookies = document.cookie.split(';');

    for(let cookie of cookies){

        cookie = cookie.trim();

        if(cookie.startsWith(name + '=')){

            cookieValue = decodeURIComponent(
                cookie.substring(name.length + 1)
            );

            break;
        }
    }

    return cookieValue;
}
 
  function qs(sel, ctx){ return (ctx||document).querySelector(sel); }
  const widget = qs('#chat-widget');
  if(!widget) return;
  const userId = widget.dataset.user || '';
  const username = widget.dataset.username || 'Anonymous';
  // choose a room name: allow 'public' for site-wide chat or 'pm_<id1>_<id2>' for private
  function computeRoomName(){

    const scope = qs('#chat-scope') 
        ? qs('#chat-scope').value 
        : 'public';

    const targetRaw = qs('#chat-target') 
        ? qs('#chat-target').value 
        : '';

    function normalizeName(s){
        return String(s || '')
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9_-]+/g, '_');
    }


    const me = normalizeName(username);
    const target = normalizeName(targetRaw);

    console.log("ROOM DATA:", {
        scope: scope,
        me: me,
        target: target
    });


    if(scope === "private"){

        if(me && target && me !== target){

            const users = [me, target].sort();

            return "pm_" + users[0] + "_" + users[1];

        }

        return "public";
    }


    return "public";
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
    socket.onclose = function(){
    console.log('Chat disconnected');
    qs('#chat-status') && (qs('#chat-status').innerText='offline');
}; socket.onerror = function(e){ console.error('Chat socket error', e); };
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


if(data.type==="file"){
    console.log("file received",data);

appendFile(
    data.id,
    data.name,
    data.url
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

${'<button type="button" class="delete-btn">🗑delete</button>'}
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
  function appendFile(id, name, url){

    const list = qs('#chat-messages');

    if(!list) return;


    const el = document.createElement("div");

    el.className = "chat-line incoming";


    // muhimu kwa delete
    el.setAttribute(
        "data-message-id",
        id
    );
console.log("file created", id)

    let content = "";


    if(
        url.match(/\.(jpg|jpeg|png|gif|webp)$/i)
    ){

        content = `

        <img src="${url}"
        style="
        max-width:220px;
        border-radius:10px;
        display:block;
        ">

        `;

    }


    else if(
        url.match(/\.(webm|mp3|wav)$/i)
    ){

        content = `

        <audio controls>
            <source src="${url}">
        </audio>

        `;

    }


    else{

        content = `

        📎 ${name}

        `;

    }


    // download + delete button kwa kila file
    content += `

    <br>

    <a href="${url}" download>
        ⬇ Download ${name}
    </a>


    <button 
    type="button"
    class="delete-btn">
        🗑 Delete
    </button>

    `;


    el.innerHTML = content;


    list.appendChild(el);

    list.scrollTop = list.scrollHeight;

}

  function escapeHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  function sendMessage(){

function uploadFile(file){

    if(!file) return;


    let formData = new FormData();

    formData.append(
        "file",
        file
    );


    fetch("/chat/upload/",{

        method:"POST",

        headers:{
            "X-CSRFToken":getCookie("csrftoken")
        },

        body:formData

    })

   .then(async res=>{

    const text = await res.text();

    console.log("SERVER RESPONSE:", text);

    let data;

    try{
        data = JSON.parse(text);
    }
    catch(error){
        console.error("NOT JSON RESPONSE");
        return;
    }

    console.log("UPLOAD RESULT:", data);


    if(data.url && socket && socket.readyState === WebSocket.OPEN){

        socket.send(JSON.stringify({

    type:"file",

    id:data.id,

    url:data.url,

    name:data.name

}));
    }

})

    .catch(error=>{

        console.error(
            "UPLOAD ERROR",
            error
        );

    });


}
    const input = qs('#chat-input');
    const text = input && input.value.trim();
    if(!text) return;
    if(
    scopeEl &&
    scopeEl.value === "private" &&
    targetEl &&
    !targetEl.value
){
    alert("Please select a user for DM");
    return;
}

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

input.style.height = "50px";
    }catch(err){
      console.error(err);
    }
  }
// Auto resize message textarea like WhatsApp
const chatInput = qs('#chat-input');

if(chatInput){

    chatInput.addEventListener("input", function(){

        this.style.height = "auto";

        this.style.height = Math.min(
            this.scrollHeight,
            120
        ) + "px";

    });

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

let oldChatPosition = {};

if(expandBtn && modal){

    expandBtn.addEventListener("click", function(){

        if(!modal.classList.contains("chat-fullscreen")){

            oldChatPosition = {
                left: modal.style.left,
                top: modal.style.top,
                width: modal.style.width,
                height: modal.style.height
            };

          
modal.classList.add("chat-fullscreen");

            expandBtn.innerHTML="🗗";

        }else{

            modal.classList.remove("chat-fullscreen");
            modal.removeAttribute("style");

            modal.style.left = oldChatPosition.left;
            modal.style.top = oldChatPosition.top;
            modal.style.width = oldChatPosition.width;
            modal.style.height = oldChatPosition.height;

            expandBtn.innerHTML="⛶";

        }

    });

}
  
     qs('#chat-open') && qs('#chat-open').addEventListener('click', function(){ 

    const modal = qs('#chat-modal');

    let willOpen = modal.style.display !== 'block';


    if(willOpen){
      modal.classList.remove("chat-fullscreen");

        const widget = document.getElementById("chat-widget");

const btnPosition = widget.getBoundingClientRect();
console.log(btnPosition.top, btnPosition.left);

modal.style.display = "block";

modal.style.position = "fixed";
modal.style.right = "auto";
modal.style.bottom = "auto";

const modalWidth = modal.offsetWidth;
const modalHeight = modal.offsetHeight;


// nafasi juu na chini
const spaceTop = btnPosition.top;
const spaceBottom = window.innerHeight - btnPosition.bottom;


let top;


// Fungua juu kama kuna nafasi
if(spaceTop >= modalHeight + 15){

    top = btnPosition.top - modalHeight - 15;

}


// Kama hakuna nafasi juu fungua chini
else if(spaceBottom >= modalHeight + 15){

    top = btnPosition.bottom + 15;

}


// Kama hakuna nafasi ya kutosha upande wowote

else{

    top = 10;

    modal.style.height = "85vh";

}


// horizontal position
let left = btnPosition.left;


// Zuia kutoka kulia
if(left + modalWidth > window.innerWidth){

    left = window.innerWidth - modalWidth - 10;

}


// Zuia kutoka kushoto
if(left < 10){

    left = 10;

}

console.log("POPUP POSITION:", left, top);

modal.style.setProperty("left", left + "px", "important");
modal.style.setProperty("top", top + "px", "important");


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


function updateDMState(){

    if(!scopeEl || !targetEl) return;

    if(scopeEl.value === "private"){

        targetEl.disabled = false;

    }else{

        targetEl.disabled = true;
        targetEl.value = "";

    }

}


// hali ya mwanzo
updateDMState();



if(scopeEl){

    scopeEl.addEventListener('change', function(){

        updateDMState();

        connect();

    });

}



if(targetEl){

    targetEl.addEventListener('change', function(){

        if(scopeEl.value === "private"){

            connect();

        }

    });

}





document.addEventListener('keydown', function(e){

    if(
        e.key === "Enter" &&
        document.activeElement.id === "chat-input" &&
        e.ctrlKey
    ){
        sendMessage();
    }

});
const imageUpload =
document.getElementById("image-upload");


const fileUpload =
document.getElementById("file-upload");

const recordBtn = document.getElementById("voice-record");

if(recordBtn){

recordBtn.onclick = async()=>{

let stream = await navigator.mediaDevices.getUserMedia({
    audio:true
});

let recorder = new MediaRecorder(stream);

let audioChunks=[];

recorder.ondataavailable=e=>{
    audioChunks.push(e.data);
};

recorder.onstop=()=>{

let audioBlob = new Blob(audioChunks,{
    type:"audio/webm"
});

sendFile(
    new File(
        [audioBlob],
        "voice.webm"
    )
);

};

recorder.start();

setTimeout(()=>{
    recorder.stop();
},10000);

};

}
function sendFile(file){

if(!file) return;
if(file.size > 10 * 1024 * 1024){

    alert("Maximum file size is 10 MB.");

    return;
}

let formData=new FormData();

formData.append(
"file",
file
);


formData.append(
"room",
"public" || roomName
);


fetch("/chat/upload/",{

method:"POST",

headers:{
"X-CSRFToken":getCookie("csrftoken")
},

body:formData

})

.then(res=>res.json())

.then(data=>{


console.log("UPLOAD RESULT",data);


if(socket && socket.readyState===WebSocket.OPEN){


socket.send(JSON.stringify({

type:"file",

url:data.url,

name:data.name

}));

}


});


}



if(imageUpload){

    imageUpload.addEventListener("change", function(){

        sendFile(this.files[0]);

        // reset input ili file ile ile iweze kuchaguliwa tena
        this.value = "";

    });

}


if(fileUpload){

    fileUpload.addEventListener("change", function(){

        sendFile(this.files[0]);

        this.value = "";

    });

}



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



