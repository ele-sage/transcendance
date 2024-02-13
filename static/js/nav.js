function updateNav(connect) {
    var connected = document.querySelectorAll('.connected');
    var notconnected = document.querySelectorAll('.anonymous');
    if(connect) {
        connected.forEach(function(connected) {
            connected.style.display = 'block';
        });
        notconnected.forEach(function(notconnected) {
            notconnected.style.display = 'none';
        });
    }
    else {
        connected.forEach(function(connected) {
            connected.style.display = 'none';
        });
        notconnected.forEach(function(notconnected) {
            notconnected.style.display = 'block';
        });
    }
}
// function getCookie(name) {
//     let cookieValue = null;
//     if (document.cookie && document.cookie !== '') {
//         const cookies = document.cookie.split(';');
//         for (let i = 0; i < cookies.length; i++) {
//             const cookie = cookies[i].trim();
//             // Does this cookie string begin with the name we want?
//             if (cookie.substring(0, name.length + 1) === (name + '=')) {
//                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                 break;
//             }
//         }
//     }
//     return cookieValue;
// }

function displayAuthContainer(display="block")
{
    document.querySelector("#authentication-container").style.display = display;
    document.querySelector("#shadow").style.display = display;
}

function hideAuthContainer()
{
    displayAuthContainer("none");
}

function displayLogin()
{
    const loginElement = document.querySelector("#login");
    loginElement.style.display = "flex";
    const registerElement = document.querySelector("#register");
    registerElement.style.display = "none";
    displayAuthContainer();
}

function displayRegister()
{
    const loginElement = document.querySelector("#login");
    loginElement.style.display = "none";
    const registerElement = document.querySelector("#register");
    registerElement.style.display = "flex";
    displayAuthContainer();  
}


// function Show(login, first) {
//     var loginElement = document.getElementById('login');
//     var register = document.getElementById('register');
//     if(first === true) {
//         var overlay = document.getElementById("shadow");
//         var box = document.getElementById("authentification");
//         box.style.display = "flex";
//         overlay.style.display = "flex";
//     }
//     if(login === true) {
//         loginElement.style.display = "flex";
//         register.style.display = "none";
//     }
//     else {
//         register.style.display = "flex";
//         loginElement.style.display = "none";
//     }
// }

// function logout() {
//     var token = getCookie('csrftoken');
//     console.log(token);
//     fetch("/logout/", {
//         method: 'POST',
//         headers: {
//             'X-CSRFToken': token,
//         },
//     })
//     .then(response => response.text())
//     .then(data => {
//         data = JSON.parse(data);
//         if (data.success) {
//             updateNav(false);
//         }
//         if (data.error) {
//             // Handle logout error
//         }
//     })
//     .catch(error => {
//         console.error('Error:', error);
//     }); 
// }

export {updateNav, displayLogin, displayRegister, hideAuthContainer};