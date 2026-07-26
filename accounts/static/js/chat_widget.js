// Simple WebSocket-based chat widget client


const isChatPage = document.querySelector(".chat-container") !== null;

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
  
  const scopeEl = isChatPage
    ? qs('#page-chat-scope')
    : qs('#chat-scope');

const targetEl = isChatPage
    ? qs('#page-chat-target')
    : qs('#chat-target');
  const widget = qs('#chat-widget');


if(!widget && !isChatPage){
    return;
}


let username = "Anonymous";


if(widget){

    username = widget.dataset.username || "Anonymous";

}
else{

    const currentUser = qs('#current-user');

    if(currentUser){

        username = currentUser.value;

    }

}
  // choose a room name: allow 'public' for site-wide chat or 'pm_<id1>_<id2>' for private
 

    // fallback kwa widget popup
    function computeRoomName(){

    const pageRoom = qs('#chat-room');

    if(pageRoom && pageRoom.value){

        if(pageRoom.value.startsWith("pm_")){

            return pageRoom.value;

        }

        if(pageRoom.value === "public"){

            return "public";

        }

    }


    const scope = scopeEl ? scopeEl.value : "public";


    if(scope === "public"){

        return "public";

    }


    if(!targetEl || !targetEl.value){

        return "public";

    }


    let names=[
        username.toLowerCase(),
        targetEl.value.toLowerCase()
    ].sort();


    return "pm_"+names[0]+"_"+names[1];

}
let roomName = computeRoomName();

console.log("FIRST ROOM:", roomName);
const protocol = window.location.protocol === "https:"
    ? "wss"
    : "ws";

const CHAT_SOCKET_HOST = window.location.host;

let wsUrl = protocol + '://' + CHAT_SOCKET_HOST + '/ws/chat/' + roomName + '/';
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
function showDMNotification(username, sender_id){


    const userBox = document.querySelector(
        `[data-user-id="${sender_id}"]`
    );


    if(userBox){


        let badge = userBox.querySelector(
            ".dm-counter"
        );


        if(!badge){

            badge = document.createElement("span");

            badge.className="dm-counter";

            badge.innerText="1";

            userBox.appendChild(badge);


        }else{


            badge.innerText =
            parseInt(badge.innerText)+1;


        }

    }


    playBeep();


}
function updateUserStatus(username, status){

    const users = document.querySelectorAll(".user");


    users.forEach(user => {

        const name = user.querySelector(".user-name");


        if(name && name.innerText.trim() === username){

            const statusBox = user.querySelector(".last-message");


            if(statusBox){

                if(status === "online"){

                    statusBox.innerHTML = `
                    <span style="color:#00ff66">
                    ● Online
                    </span>
                    `;

                }else{

                    statusBox.innerHTML = `
                    <span style="color:red">
                    ● Offline
                    </span>
                    `;

                }

            }

        }

    });

}
 function connect(){

 if(socket){
  try{ socket.close(); }catch(e){}
  socket = null;
}
const messagesEl = isChatPage
    ? qs('#page-chat-messages')
    : qs('#chat-messages');
// safisha messages za zamani kabla ya kupokea history mpya
const list = messagesEl;
 if(list){
    list.innerHTML = '';
}

roomName = computeRoomName();


console.log("CONNECTING ROOM:", roomName);


wsUrl = protocol + '://' + CHAT_SOCKET_HOST + '/ws/chat/' + roomName + '/';

console.log("WEBSOCKET URL:", wsUrl);

socket = new WebSocket(wsUrl);
    socket.onopen = function(){ console.log('Chat connected to', wsUrl); qs('#chat-status') && (qs('#chat-status').innerText='online'); };
    socket.onclose = function(){
    console.log('Chat disconnected');
    qs('#chat-status') && (qs('#chat-status').innerText='offline');
}; socket.onerror = function(e){ console.error('Chat socket error', e); };
   socket.onmessage = function(e){

const data = JSON.parse(e.data);

console.log(data.type);
console.log(data.from);
console.log(data.sender_id);
// DM NOTIFICATION

if(data.type==="dm_notification"){
console.log("DM Notification", data);
    const activeRoom = computeRoomName();

    const sender = data.from.toLowerCase();

    const current = username.toLowerCase();

    const expectedRoom = [
        sender,
        current
    ].sort();

    const room = "pm_"+expectedRoom[0]+"_"+expectedRoom[1];

    if(room===activeRoom){
        return;
    }
const userBox = [...document.querySelectorAll(".user-info")]
.find(el => 
    el.querySelector(".user-name")?.innerText.trim().toLowerCase()
    === data.from.toLowerCase()
);
if(userBox){

    let counter = userBox.querySelector(".dm-counter");


if(!counter){

    counter = document.createElement("span");

    counter.className = "dm-counter";

    counter.innerText = "0";

    userBox.appendChild(counter);

}


let count = parseInt(counter.innerText || "0");


counter.innerText = count + 1;

counter.style.display = "inline-flex";
}
   
    playBeep();

    return;
}
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


if(data.file_type &&
data.file_type.startsWith("audio")){


appendVoice(
    data.id,
    data.url
);


}else{


appendFile(
    data.id,
    data.name,
    data.url
);


}


}



if (data.type === "user_status") {

    console.log(
        data.username + " is " + data.status
    );

    updateUserStatus(
        data.username,
        data.status
    );

    return;
}
// message ya kawaida + history ya database

};
 }

  function appendMessage(user, text, outgoing, id, avatar){

    const list = isChatPage
        ? qs('#page-chat-messages')
        : qs('#chat-messages');

    if(!list) return;
  const el = document.createElement('div');
  el.className = 'chat-line' + (outgoing ? ' outgoing' : ' incoming');

  // 🔥 muhimu sana kwa delete feature
  if(id) el.setAttribute('data-message-id', id);

  el.innerHTML = `
 <img src="${avatar || '/static/image/logo1.png'}" alt="Avatar"
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

    const list = isChatPage
        ? qs('#page-chat-messages')
        : qs('#chat-messages');

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
    name.match(/\.(webm|mp3|wav|ogg|m4a)$/i)
    ||
    url.includes("video/upload")
){

      content = `

<audio controls preload="metadata">
    <source src="${url}" type="audio/webm">
    Your browser does not support audio.
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
    const input = isChatPage
    ? qs('#page-chat-input')
    : qs('#chat-input');
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
const chatInput = isChatPage
    ? qs('#page-chat-input')
    : qs('#chat-input');

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
  function insertEmoji(ch){const input = isChatPage
    ? qs('#page-chat-input')
    : qs('#chat-input'); ; if(!input) return; try{ const start = input.selectionStart || 0; const end = input.selectionEnd || 0; const v = input.value; input.value = v.slice(0,start) + ch + v.slice(end); input.selectionStart = input.selectionEnd = start + ch.length; input.focus(); }catch(e){ input.value = input.value + ch; } }
  if(emojiPicker){
    emojiPicker.addEventListener('click', function(e){ if(e.target && e.target.classList && e.target.classList.contains('emoji-swatch')){ insertEmoji(e.target.textContent); emojiPicker.classList.remove("show"); } });
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
          emojiPicker.classList.remove("show");
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

    emojiBtn.addEventListener('click', function(e){
        

        e.stopPropagation();
        console.log("EMOJI BUTTON CLICKED");


        if(!emojiPicker) return;


        emojiPicker.classList.toggle("show");


    });
 
// hide picker when clicking outside
    document.addEventListener('click', function(e){ if(emojiPicker && e.target !== emojiBtn && !emojiPicker.contains(e.target)){emojiPicker.classList.remove("show"); } });
  }
const expandBtn = document.getElementById("chat-expand");

if(expandBtn){

    expandBtn.addEventListener("click", function(){

        window.location.href = "/chat/?room=" + roomName;

    });

}
  
     qs('#chat-open') && qs('#chat-open').addEventListener('click', function(){ 

    const modal = qs('#chat-modal');

    let willOpen = modal.style.display !== 'block';


    if(willOpen){
      modal.classList.remove("chat-fullscreen");
const btnPosition = widget.getBoundingClientRect();
console.log(btnPosition.top, btnPosition.left);

modal.style.display = "block";

modal.style.position = "fixed";
modal.style.right = "auto";
modal.style.bottom = "auto";

// GET REAL SIZE AFTER DISPLAY
const rect = modal.getBoundingClientRect();

let modalWidth = rect.width;
let modalHeight = rect.height;

const screenWidth = window.innerWidth;
const screenHeight = window.innerHeight;


// default position karibu na widget
let left = btnPosition.left;
let top = btnPosition.top - modalHeight - 15;


// kama hakuna nafasi juu
if(top < 10){

    top = btnPosition.bottom + 15;

}


// kama bado imezidi chini
if(top + modalHeight > screenHeight){

    top = screenHeight - modalHeight - 10;

}


// zuia kulia kutoka nje
if(left + modalWidth > screenWidth){

    left = screenWidth - modalWidth - 10;

}


// zuia kushoto kutoka nje
if(left < 10){

    left = 10;

}


// mwisho wa usalama
if(top < 10){

    top = 10;

}


modal.style.left = left + "px";
modal.style.top = top + "px";
// final safety check

const finalRect = modal.getBoundingClientRect();


if(finalRect.right > window.innerWidth){

    modal.style.left =
    (window.innerWidth - finalRect.width - 10) + "px";

}


if(finalRect.left < 0){

    modal.style.left = "10px";

}


if(finalRect.bottom > window.innerHeight){

    modal.style.top =
    (window.innerHeight - finalRect.height - 10) + "px";

}


if(finalRect.top < 0){

    modal.style.top = "10px";

}
modal.style.setProperty("left", left + "px", "important");
modal.style.setProperty("top", top + "px", "important");


    }else{

        modal.style.display = "none";

    }


    qs('#chat-input') && qs('#chat-input').focus();


 if(willOpen){ // clear unread count when opening
    unreadCount = 0; if(badgeEl){ badgeEl.style.display='none'; badgeEl.classList.remove('pulse'); badgeEl.innerText = ''; } }
  });
  const chatClose = qs('#chat-close');

if(chatClose){

    chatClose.addEventListener('click', function(e){

        e.preventDefault();

        const modal = qs('#chat-modal');

        if(modal){
            modal.style.display = "none";
        }

    });


    chatClose.addEventListener('touchend', function(e){

        e.preventDefault();

        const modal = qs('#chat-modal');

        if(modal){
            modal.style.display = "none";
        }

    });

}
  const sendBtn = isChatPage
    ? qs('#page-chat-send')
    : qs('#chat-send');

if(sendBtn){
    sendBtn.addEventListener("click", sendMessage);
}
const chatForm = isChatPage
    ? qs('#page-chat-form')
    : qs('#chat-form');
if(chatForm){

chatForm.addEventListener(
"submit",
function(e){

e.preventDefault();

sendMessage();

});

}
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


function updateDMState(){

    if(!scopeEl || !targetEl) return;

    if(scopeEl.value === "private"){

        targetEl.disabled = false;

    }else{

        targetEl.disabled = true;

    }

}


// hali ya mwanzo
updateDMState();


if(scopeEl){

    scopeEl.addEventListener("change", function(){

        updateDMState();
if(this.value === "public"){

            connect();

        }


    });
}   

if(targetEl){

    targetEl.addEventListener("change", function(){
        const activeUser = document.querySelector(
    '.user[data-username="' + this.value.toLowerCase() + '"]'
);

if(activeUser){

    const badge = activeUser.querySelector(".dm-counter");

    if(badge){

        badge.textContent = "0";
        badge.style.display = "none";

    }

}

        connect();

    });

}

document.addEventListener("keydown", function(e){

    const input = document.activeElement;

    if(
        input &&
        (
            input.id === "chat-input" ||
            input.id === "page-chat-input"
        )
    ){

        // Enter = Send
        if(e.key === "Enter" && !e.shiftKey){

            e.preventDefault();
            sendMessage();

        }

        // Shift + Enter = New line
        if(e.key === "Enter" && e.shiftKey){

            // textarea itaongeza newline yenyewe
            return;

        }

    }

});




const imageUpload = isChatPage
    ? document.getElementById("page-image-upload")
    : document.getElementById("image-upload");

const fileUpload = isChatPage
    ? document.getElementById("page-file-upload")
    : document.getElementById("file-upload");
const recordBtn = isChatPage
    ? document.getElementById("page-voice-record")
    : document.getElementById("voice-record");

let mediaRecorder;
let audioChunks = [];
let audioStream;


if(recordBtn){

recordBtn.addEventListener("click", async function(){

    // kama tayari recording inaendelea
    if(mediaRecorder && mediaRecorder.state === "recording"){

        mediaRecorder.stop();

        recordBtn.innerHTML = "🎤";

        return;
    }


    try{

        audioStream = await navigator.mediaDevices.getUserMedia({
            audio:true
        });


        mediaRecorder = new MediaRecorder(audioStream);


        audioChunks = [];


        mediaRecorder.ondataavailable = function(e){

            if(e.data.size > 0){

                audioChunks.push(e.data);

            }

        };


        mediaRecorder.onstop = function(){


            const audioBlob = new Blob(
                audioChunks,
                {
                    type:"audio/webm"
                }
            );


            const voiceFile = new File(
                [audioBlob],
                "voice.webm",
                {
                    type:"audio/webm"
                }
            );


            sendFile(voiceFile);



            // zima microphone
            audioStream.getTracks().forEach(
                track=>track.stop()
            );


        };


        mediaRecorder.start();


        recordBtn.innerHTML="⏹";


        console.log(
            "Voice recording started"
        );


    }
    catch(error){

        console.error(
            "Microphone error:",
            error
        );


        alert(
            "Please allow microphone permission"
        );

    }


});


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
roomName
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

if(
    data.url &&
    socket &&
    socket.readyState===WebSocket.OPEN
){

socket.send(JSON.stringify({

type:"file",

id:data.id,

url:data.url,

name:data.name,

file_type:data.type,

room:roomName

}));

}else{

console.error(
"Upload failed:",
data
);

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
function toggleMenu(){
    document.getElementById("navLinks").classList.toggle("active");
}
window.addEventListener("resize", function(){

    const modal = qs('#chat-modal');

    if(!modal) return;

    if(modal.style.display === "block"){

        const rect = modal.getBoundingClientRect();

        if(rect.right > window.innerWidth){

            modal.style.left =
            (window.innerWidth - rect.width - 10)+"px";

        }

        if(rect.bottom > window.innerHeight){

            modal.style.top =
            (window.innerHeight - rect.height - 10)+"px";

        }

    }

});




// Request notifications permission proactively
ensureNotificationPermission();

connect();

})();

let moved = false;
     //for movable widgget
function makeButtonDraggable(button){

    let moving = false;
    let offsetX = 0;
    let offsetY = 0;
    

    function startDrag(e){

        moving = true;
        moved = false;

        const point = e.touches ? e.touches[0] : e;

        let rect = button.getBoundingClientRect();


        offsetX = point.clientX - rect.left;
        offsetY = point.clientY - rect.top;


        button.style.position = "fixed";

        button.style.left = rect.left + "px";
        button.style.top = rect.top + "px";

        button.style.right = "auto";
        button.style.bottom = "auto";


        e.preventDefault();

    }



    function moveDrag(e){
       
        if(!moving) return;

         moved = true;
        const point = e.touches ? e.touches[0] : e;


        let x = point.clientX - offsetX;
        let y = point.clientY - offsetY;



        // Zuia widget isitoke nje ya screen

        x = Math.max(
            0,
            Math.min(
                x,
                window.innerWidth - button.offsetWidth
            )
        );


        y = Math.max(
            0,
            Math.min(
                y,
                window.innerHeight - button.offsetHeight
            )
        );



        button.style.left = x + "px";

        button.style.top = y + "px";

    }
function stopDrag(){

    moving = false;

    setTimeout(function(){

        moved = false;

    },150);

}


    


    // PC mouse

    button.addEventListener(
        "mousedown",
        startDrag
    );


    document.addEventListener(
        "mousemove",
        moveDrag
    );


    document.addEventListener(
        "mouseup",
        stopDrag
    );



    // Mobile touch

    button.addEventListener(
        "touchstart",
        startDrag,
        {passive:false}
    );


    document.addEventListener(
        "touchmove",
        moveDrag,
        {passive:false}
    );


    document.addEventListener(
        "touchend",
        stopDrag
    );


}

const chatOpen = document.getElementById("chat-open");

if(chatOpen){

    chatOpen.addEventListener("click",function(e){

        if(moved){

            e.preventDefault();

            return;

        }

    });

}
const plusBtn = isChatPage
    ? document.getElementById("page-plus-btn")
    : document.getElementById("plus-btn");

const uploadMenu = isChatPage
    ? document.getElementById("page-upload-menu")
    : document.getElementById("upload-menu");

if (plusBtn && uploadMenu) {

    plusBtn.addEventListener("click", function(e){

        e.preventDefault();
        e.stopPropagation();

        uploadMenu.classList.toggle("show");

    });

}



const backPopup = document.getElementById("back-popup");


if(backPopup){

    backPopup.addEventListener("click",function(){

        const previous =
        document.getElementById("previous-page").value;


        if(backPopup){

    backPopup.addEventListener("click",function(){

        window.history.back();

    });

}

    });

}


