from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from users.models import UserChannelGroup
from friend.models import Friend
from users.models import User
import time, re, redis, threading
from django.conf import settings

matchmaking_redis = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
matchmaking_lock = threading.Lock()

def remove_from_all_queues(user_id):
    for matchmaking_redis_key in matchmaking_redis.scan_iter(match='*'):
        matchmaking_redis.zrem(matchmaking_redis_key, user_id)

# Helper functions
def user_disconnect(user_id):
    time.sleep(5)
    try:
        user = User.objects.get(id=user_id)
        main = UserChannelGroup.objects.get(user=user).main
        should_disconnect = main == '' and user.status != 'offline'
        if should_disconnect:
            user.status = 'offline'
            friends = Friend.objects.online_friends(user)
            if friends:
                channel_layer = get_channel_layer()
                for friend in friends:
                    notify_online(user, friend, 'offline', channel_layer)
            remove_from_all_queues(user_id)
            clear_user_channels(user)
            user.save()
    except User.DoesNotExist:
        print('User not found')
    except UserChannelGroup.DoesNotExist:
        print('User channel group not found')

def close_recipient_channel(user_id, group, channel_layer):
    if group.startswith('pong_'):
        group = group[5:]
    users = group.split('_')
    recipient_id = users[0] if users[0] != str(user_id) else users[1]
    
    try:
        send_to_websocket(channel_layer, UserChannelGroup.objects.get(user__id=recipient_id).get_channel_name(group), {
            'type': 'chat.message',
            'message': 'User is offline',
            'senderId': user_id,
            'closing': True
        })
    except User.DoesNotExist:
        print('Recipient not found')
        
def clear_user_channels(user):
    try:
        channel_groups = UserChannelGroup.objects.get(user=user)
        channel_layer = get_channel_layer()
        channel_groups_pairs = channel_groups.channel_groups
        channel_groups.remove_all_channel_groups()

        for channel, group in channel_groups_pairs.items():
            send_to_websocket(channel_layer, channel, {'type': 'websocket.close'})
            if group != 'global':
                close_recipient_channel(user.id, group, channel_layer)
    except Exception as e:
        print('Error:', e)

async def get_opponent_id(room, user_id):
    users = room.split('_')
    return users[0] if users[0] != str(user_id) else users[1]
        
def friend_request_notify(user_id, friend, friend_request_id):
    try:
        send_to_websocket(get_channel_layer(), UserChannelGroup.objects.get(user=friend).main, {
            'type': 'send.notification',
            'notification': 'friendRequest',
            'userId': user_id,
            'id': friend_request_id
        })
    except Exception as e:
        print('Error:', e)
        
def unfriend_notify(to_user, from_user):
    try:
        send_to_websocket(get_channel_layer(), UserChannelGroup.objects.get(user=to_user).main, {
            'type': 'send.notification',
            'notification': 'unfriend',
            'userId': from_user.id
        })
    except Exception as e:
        print('Error:', e)
        
def accept_friend_request_notify(user, friend):
    channel_layer = get_channel_layer()
    if friend.status != 'offline':
        notify_online(user, friend, 'online', channel_layer)
    if user.status != 'offline':
        notify_online(friend, user, 'online', channel_layer)
        
def notify_online(user, friend, status, channel_layer):
    try:
        send_to_websocket(channel_layer, UserChannelGroup.objects.get(user=friend).main, {
            'type': 'send.notification',
            'notification': 'connection',
            'status': status,
            'userId': user.id
        })
    except Exception as e:
        print('Error:', e)
        
def send_to_websocket(channel_layer, channel_name, event):
    if channel_name:
            async_to_sync(channel_layer.send)(channel_name, event)
    else:
        print('Channel name not found')
        
async def async_send_to_websocket(channel_layer, channel_name, event):
    if channel_name:
        await channel_layer.send(channel_name, event)
    else:
        print('Channel name not found')
        
# Convert special characters such as ?, &, /, <, > and spaces to their respective HTML or URL encoded equivalents.
def escape_html(text):
    return re.sub(r'[?&/<> ]', lambda x: '&#' + str(ord(x.group())) + ';', text)