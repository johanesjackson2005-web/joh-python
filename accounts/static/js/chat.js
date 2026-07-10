let socket = null;

const currentUser =
document.getElementById("current-user").value;


function openChat(username){


    // Funga connection ya zamani
    if(socket){

        socket.close();

    }


    // Safisha messages za zamani
    document.getElementById("messages").innerHTML = "";



    // Tengeneza private room
    const room =
    "pm_" +
    [currentUser, username]
    .sort()
    .join("_");



    const protocol =
    window.location.protocol === "https:"
    ? "wss"
    : "ws";



    socket = new WebSocket(

        protocol +
        "://" +
        window.location.host +
        "/ws/chat/" +
        room +
        "/"

    );



    socket.onopen=function(){

        console.log(
            "Connected:",
            room
        );

    };



    socket.onmessage=function(e){


        const data =
        JSON.parse(e.data);



        if(data.type === "message"){

            addMessage(
                data.user,
                data.message
            );

        }


    };



    socket.onclose=function(){

        console.log(
            "Disconnected:",
            room
        );

    };



}



function addMessage(user,text){


    const box =
    document.getElementById("messages");



    const div =
    document.createElement("div");



    if(user === currentUser){

        div.className="outgoing";

    }else{

        div.className="incoming";

    }



    div.innerText=text;



    box.appendChild(div);



    box.scrollTop =
    box.scrollHeight;


}




// Sidebar click

document
.querySelectorAll(".user")
.forEach(item=>{


    item.onclick=function(){


        const username =
        this.dataset.username;


        openChat(username);


    };


});





// Send message

document
.getElementById("chat-form")
?.addEventListener(
"submit",
function(e){


    e.preventDefault();



    const input =
    document.getElementById("message");



    if(!socket){

        alert("Select user first");

        return;

    }



    if(input.value.trim()===""){

        return;

    }



    socket.send(JSON.stringify({

        type:"message",

        message:input.value


    }));



    input.value="";


});
document.addEventListener("DOMContentLoaded", function(){


const plusBtn = document.getElementById("plus-btn");
const uploadMenu = document.getElementById("upload-menu");

const emojiBtn = document.getElementById("emoji-btn");
const emojiPicker = document.getElementById("emoji-picker");

const chatInput = document.getElementById("chat-input");



/* =====================
   PLUS MENU
===================== */


if(plusBtn){

plusBtn.addEventListener("click", function(e){

    e.stopPropagation();

    uploadMenu.classList.toggle("show");

    emojiPicker.style.display="none";

});

}



/* =====================
   EMOJI MENU
===================== */


if(emojiBtn){

emojiBtn.addEventListener("click", function(e){

    e.stopPropagation();

    if(emojiPicker.style.display==="block"){

        emojiPicker.style.display="none";

    }else{

        emojiPicker.style.display="block";

        uploadMenu.classList.remove("show");

    }


});

}



/* =====================
   SELECT EMOJI
===================== */


document.querySelectorAll(".emoji-swatch")
.forEach(function(emoji){


emoji.addEventListener("click",function(){


    chatInput.value += this.textContent;


    chatInput.focus();


    emojiPicker.style.display="none";


});


});



/* =====================
 CLICK OUTSIDE CLOSE
===================== */


document.addEventListener("click",function(e){


if(!e.target.closest("#upload-menu")
&& !e.target.closest("#plus-btn")){


    uploadMenu.classList.remove("show");


}



if(!e.target.closest("#emoji-picker")
&& !e.target.closest("#emoji-btn")){


    emojiPicker.style.display="none";


}


});



});
