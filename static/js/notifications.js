import * as chat from "/js/chat/chat.js";
import * as chatFriends from "/js/chat/friends.js";
import * as friends from "/js/account/friends.js";
import * as match from "/js/pong/match.js";
import * as nav from "/js/nav.js";
import * as util from "/js/util.js";
import { getCurrUser } from "/js/user/currUser.js";
import { setUserStatus, getUser } from "/js/user/user.js";

var ws;

function start() {
	var userId = getCurrUser().id;
	ws = new WebSocket(
		'wss://'
		+ window.location.host
		+ '/ws/notifications/'
		+ userId + '/'
	);

	ws.onmessage = async (event) => {
		const data = JSON.parse(event.data);
		switch (data.type) {
			case "chat":
				chat.start(data.room);
				break;
			case "connection":
				friends.incrOnlineFriendsCount(data.connected ? 1 : -1);
				chatFriends.update(data.userId, data.connected);
				setUserStatus(data.userId, data.connected);
				util.showAlert({
					text: `${(await getUser(data.userId)).username} just ${data.connected ? "": "dis"}connected.`,
					timeout: 2,
				});
				break;
			case "onlineFriends":
				chatFriends.set(data.userIds);
				break;
			case "friendRequests":
				nav.updateFriendRequestCount(data.count);
				break;
			case "friendRequest":
				friends.receiveFriendRequest(data);
				break;
			case "pong":
				pongNotifications(data);
				break;
			default:
				console.log("Unknown notification:", data);
				break;
		}
    }

	ws.onclose = (_) => {
		console.log("Notifications socket closed.");
		stop();
	};
}

function pongNotifications(data) {
	console.log("pong notifications:", data);
	switch (data.description) {
		case "searchingMatch":
			match.setSearchingMatch({roomId: data.room});
			break;
		case "matchRequest":
			match.receiveInvite(data);
			break;
		case "matchRefused":
			match.setSearchingMatch({searching: false});
			util.showAlert({text: "Opponent refused to play."});
			break;
		case "opponentIngame":
			util.showAlert({text: "Opponent is already in game."});
			break;
		case "opponentOffline":
			util.showAlert({text: "Opponent is offline."});
			break;
		case "matchFound":
			match.setSearchingMatch({searching: false});
			match.start(data);
			break;
		default:
			console.log("Unknown notification:", data);
			break;			
	}

}

function stop() {
    if (!ws || ws.readyState === WebSocket.CLOSED) {
		console.log("notifications.stop: notifications websocket already closed.");
		return;
	}
	console.log('Notifications websocket closed.');
	ws.close();
}

function matchMaking(roomId, cancel=false) {
	if (!ws) {
		throw new Error("notifications.matchMaking: notifications websocket not started");
	}
	ws.send(JSON.stringify({
		type: "matchmaking",
		room: roomId,
		cancel: cancel,
	}));
}

export { start, stop, matchMaking };