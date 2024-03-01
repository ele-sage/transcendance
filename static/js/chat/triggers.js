import * as chat from "/js/chat/chat.js";
import * as chatFriends from "/js/chat/friends.js";
import * as chatMessages from "/js/chat/messages.js";
import * as util from "/js/util.js";
import { GLOBAL_ROOM_ID, MATCH_ROOM_ID } from "/js/chat/chat.js";


const chatIcon = document.getElementById('chat-icon'); //add connected check
const chatBox = document.getElementById('chat-box');
function toggleChat() {
	util.toggleClass(chatIcon, 'chat-active')
	util.toggleClass(chatBox, 'chat-active')
}

// -- tabs ----
const gameTab = document.getElementById('tab-game');
function activateGameTab() {
	activateTab(gameTab, MATCH_ROOM_ID);
};

const globalTab = document.getElementById('tab-global');
function activateGlobalTab() {
	activateTab(globalTab, GLOBAL_ROOM_ID);
}

const friendsTab = document.getElementById('tab-friends');
function activateFriendsTab(target) {
	const roomId = target.getAttribute('data-room-id');
	if (!(roomId in chat.chatSockets)) {
		chat.start(roomId);
	}
	activateTab(friendsTab, roomId);
}

function activateTab(target, roomId) {
	if (chat.currRoomId == roomId) {
		return;
	}
	chat.updateRoomId(roomId);
	document.querySelector('.tab-active').classList.remove('tab-active');
	target.classList.add('tab-active');
	chatMessages.loadMessages();
}

const friendsList = document.getElementById('friendlist-tab');
function activateFriendsList() {
	chatFriends.generateFriendsList(friendsList);
	util.toggleClass(friendsList, 'show');
};

// -- image ----
const menu = document.getElementById('chat-menu');
function activateMenu(target) {
	console.log("profile-picture-chat");
	updateMenu(target.getAttribute('data-id'));
	const imageRect = target.getBoundingClientRect();
	var imageX = imageRect.left + window.scrollX;
	var imageY = imageRect.top + window.scrollY;

	menu.style.left = imageX + 'px';
	menu.style.top = (imageY - menu.offsetHeight) + 'px';
	menu.style.display = 'block';
};

const chatbody = document.querySelector('.chat-box-body');
document.addEventListener('click', function(event) {
	if (!chatbody.contains(event.target)) {
		menu.style.display = 'none';
	}
});

function updateMenu(id) {
	var menuOptions = ['stats', 'block', 'invite'];
	menu.innerHTML = '';
	var ul = document.createElement('ul');
	menuOptions.forEach(function(option) {
		var li = document.createElement('li');
		var a = document.createElement('a');
		a.href = '#';
		a.setAttribute('id', id);
		a.textContent = option;
		li.appendChild(a);
		ul.appendChild(li);
	});
	menu.appendChild(ul);
}

export { toggleChat }
export { activateGlobalTab, activateFriendsList, activateFriendsTab, activateGameTab };
export { activateMenu };