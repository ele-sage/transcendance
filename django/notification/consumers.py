from channels.generic.websocket import AsyncWebsocketConsumer
from users.models import UserChannelGroup
from channels.layers import get_channel_layer
import time, threading, redis, json
from django.conf import settings
from notification.utils import get_opponent_id, user_disconnect, send_to_websocket
from notification.utils_db import change_status, set_main_channel, get_group_list, get_main_channel, get_online_friends, friend_request_count, get_user, is_recipient_online


TOURNAMENT_NB_PLAYERS = 4

matchmaking_redis = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
matchmaking_lock = redis.lock.Lock(matchmaking_redis, 'matchmaking_lock', timeout=1)

def matchmaker(room):
    if not matchmaking_lock.locked():
        matchmaking_lock.acquire()
        min_players = TOURNAMENT_NB_PLAYERS if room == 'tournament' else 2
        try:
            while True:
                print('In Queue...')
                if matchmaking_redis.zcard(room) >= min_players:
                    print('Match found')
                    users = matchmaking_redis.zrange(room, 0, min_players - 1)
                    channel_layer = get_channel_layer()
                    for i in range(0, min_players, 2):
                        room_name = '_'.join(sorted([users[i].decode('utf-8'), users[i+1].decode('utf-8')]))
                        try:
                            send_to_websocket(channel_layer, UserChannelGroup.objects.get(user_id=users[i]).main, {
                                'type': 'send.notification', 'notification': 'pong', 'description': 'matchFound', 'room': room_name
                            })
                            send_to_websocket(channel_layer, UserChannelGroup.objects.get(user_id=users[i+1]).main, {
                                'type': 'send.notification', 'notification': 'pong', 'description': 'matchFound', 'room': room_name
                            })
                        except UserChannelGroup.DoesNotExist:
                            break
                    matchmaking_redis.zremrangebyrank(room, 0, min_players - 1)
                else:
                    print('Not enough players')
                    break
        finally:
            matchmaking_lock.release()

async def async_send_to_websocket(channel_layer, channel_name, event):
    if channel_name:
        await channel_layer.send(channel_name, event)
    else:
        print('Channel name not found')

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.in_queue = False
        self.current_queue = ''

        if not self.user.is_authenticated:
            await self.close()
        else:
            if self.user.status == 'offline':
                await change_status(self.user, 'online')
                await self.notify_online_status_to_friends(True)
            await set_main_channel(self.user, self.channel_name)
            await self.accept()
            await self.send(text_data=json.dumps({
                'type': 'onlineFriends',
                'userIds': await get_online_friends(self.user, ids_only=True)
            }))
            await self.send(text_data=json.dumps({
                'type': 'friendRequests',
                'count': await friend_request_count(self.user)
            }))
            await self.reconnect_chats()
    
    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await set_main_channel(self.user, '')
            self.cancel_search()
            disconnect_thread = threading.Thread(target=user_disconnect, args=(self.user,))
            disconnect_thread.start()
  
    async def receive(self, text_data):
        data = json.loads(text_data)
        type = data['type']

        if type == 'matchmaking':
            await self.handle_matchmaking(data)
        
    async def handle_matchmaking(self, data):
        room = data.get('room', 'global')
        
        if data.get('cancel', False):
            if not await self.is_refusing_match(room) and self.in_queue:
                await self.cancel_search()
        else:
            if self.current_queue != room:
                await self.cancel_search()
            await self.search_match(room)
            
    async def websocket_close(self, event):
        await self.close()
    
    async def send_notification(self, event):
        params = event
        params['type'] = params.pop('notification')

        await self.send(text_data=json.dumps(params))
        if params['type'] == 'matchFound':
            self.in_queue = False
        elif params['type'] == 'matchRefused':
            await self.cancel_search()
    
    async def reconnect_chats(self):
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'room': 'global'
        }))
        group_list = await get_group_list(self.user)
        if group_list:
            for group in group_list:
                if group != 'global' and is_recipient_online(group, self.user.id):
                    await self.send(text_data=json.dumps({
                        'type': 'chat',
                        'room': group
                    }))
    
    async def notify_online_status_to_friends(self, connected):
        friends = await get_online_friends(self.user)
        if friends:
            for friend in friends:
                await async_send_to_websocket(self.channel_layer, await get_main_channel(friend), {
                    'type': 'send.notification', 'notification': 'connection', 'connected': connected, 'userId': self.user.id
                })

    async def search_match(self, room):
        if room != 'global' and room != 'tournament':
            if not await self.send_match_request(room):
                return
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'description': 'searchingMatch',
            'room': room
        }))
        matchmaking_redis.zadd(room, {self.user.id: time.time()})
        self.in_queue = True
        self.current_queue = room
        matchmaker_thread = threading.Thread(target=matchmaker, args=(room,))
        matchmaker_thread.start()

    async def cancel_search(self):
        matchmaking_redis.zrem(self.current_queue, self.user.id)
        self.in_queue = False
        self.current_queue = ''
        
    async def is_refusing_match(self, room):
        if room != 'global' and room != 'tournament':
            opponent_id = await get_opponent_id(room, self.user.id)
            if opponent_id and matchmaking_redis.zrank(room, opponent_id) is not None:
                await async_send_to_websocket(self.channel_layer, await get_main_channel(opponent_id, True), {
                    'type': 'send.notification', 'notification': 'pong', 'description': 'matchRefused', 'room': room
                })
                return True
        return False
    
    async def send_match_request(self, room):
        opponent_id = await get_opponent_id(room, self.user.id)
        opponent = await get_user(opponent_id)
        if opponent:
            if opponent.status == 'online':
                if matchmaking_redis.zrank(room, opponent_id) is None:
                    await async_send_to_websocket(self.channel_layer, await get_main_channel(opponent_id, True), {
                        'type': 'send.notification', 'notification': 'pong', 'description': 'matchRequest', 'room': room, 'userId': self.user.id
                    })
                return True
            elif opponent.status == 'in-game':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'description': 'opponentInGame',
                    'userId': opponent_id
                }))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'description': 'opponentOffline',
                    'userId': opponent_id
                }))
        return False