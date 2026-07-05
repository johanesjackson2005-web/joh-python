document.addEventListener('DOMContentLoaded', function(){
  const chat = document.getElementById('chat');
  const input = document.getElementById('message');
  const send = document.getElementById('send');

  function appendMessage(text, cls){
    const d = document.createElement('div');
    d.className = 'msg '+cls;
    d.innerText = text;
    chat.appendChild(d);
    chat.scrollTop = chat.scrollHeight;
  }

  async function sendMessage(){
    const text = input.value.trim();
    if(!text) return;
    appendMessage(text, 'user');
    input.value = '';
    appendMessage('...', 'bot');
    const lastBot = chat.querySelectorAll('.msg.bot');
    const placeholder = lastBot[lastBot.length-1];

    try{
      const resp = await fetch('/ai-assistant/api/', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({message: text})
      });
      const j = await resp.json();
      if(j.answer){
        placeholder.innerText = j.answer;
        // notify parent window that assistant responded (so parent can show unread badge)
        try{ window.parent.postMessage({type:'ai-response', unread:true}, '*'); }catch(e){}
      } else if(j.error){
        placeholder.innerText = 'Error: '+j.error;
        try{ window.parent.postMessage({type:'ai-response', unread:true}, '*'); }catch(e){}
      } else {
        placeholder.innerText = 'No response';
        try{ window.parent.postMessage({type:'ai-response', unread:true}, '*'); }catch(e){}
      }
    }catch(e){
      placeholder.innerText = 'Request failed';
    }
  }

  send.addEventListener('click', sendMessage);
  input.addEventListener('keydown', function(e){ if(e.key==='Enter'){ e.preventDefault(); sendMessage(); } });
});