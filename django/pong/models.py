from django.db import models
from users.models import User
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField

class GameManager(models.Manager):
    def get_games(self, user, from_game_id=0, size=10):
        if from_game_id > 0:
            return self.filter(models.Q(winner=user) | models.Q(loser=user), id__lt=from_game_id).order_by('-date')[:size]
        return self.filter(models.Q(winner=user) | models.Q(loser=user)).order_by('-date')[:size]

    def get_wins(self, user):
        return self.filter(winner=user)

    def get_losses(self, user):
        return self.filter(loser=user)
    
    def get_last_game(self, user_id, how_many=1):
        if how_many == 1:
            return self.filter(models.Q(winner=user_id) | models.Q(loser=user_id)).latest('date')
        return self.filter(models.Q(winner=user_id) | models.Q(loser=user_id)).order_by('-date')[:how_many]

    def get_penultimate_game(self, user_id):
        return self.filter(models.Q(winner=user_id) | models.Q(loser=user_id)).order_by('-date')[1]
    
    def get_stats(self, user):
        games = self.filter(models.Q(winner=user) | models.Q(loser=user))
        opponents = {}
        stats = {
            'swear_count': user.swear_count,
            'games': 0,
            'totals': {
                'wins': 0,
                'losses': 0,
                'time_played': 0,
                'longest_exchange': 0,
                'total_exchanges': 0,
                'total_distance': 0,
                'total_hits': 0,
            },
            'averages': {
                'longest_exchange': 0,
                'total_exchanges': 0,
                'distance': 0,
                'hits': 0,
                'duration': 0
            },
            'win_rate': 0,
            'most_played_opponent': {
                'opponent': None,
                'games': 0
            },
        }
        if games.count() == 0:
            return stats
        
        for game in games:
            if game.winner == user:
                stats['totals']['wins'] += 1
                if game.loser not in opponents:
                    opponents[game.loser] = 1
                else:
                    opponents[game.loser] += 1
            else:
                stats['totals']['losses'] += 1
                if game.winner not in opponents:
                    opponents[game.winner] = 1
                else:
                    opponents[game.winner] += 1
            stats['totals']['time_played'] += game.duration
            stats['totals']['total_exchanges'] += game.total_exchanges
            stats['totals']['total_distance'] += game.total_distance
            stats['totals']['total_hits'] += game.total_hits
            if game.longest_exchange > stats['totals']['longest_exchange']:
                stats['totals']['longest_exchange'] = game.longest_exchange
            
        if games.count() > 0:
            stats['averages']['total_exchanges'] = round(stats['totals']['total_exchanges'] / games.count())
            stats['averages']['duration'] = round(stats['totals']['time_played'] / games.count())
            stats['averages']['longest_exchange'] = round(stats['totals']['longest_exchange'] / games.count())
            stats['averages']['hits'] = round(stats['totals']['total_hits'] / games.count())
            stats['averages']['distance'] = round(stats['totals']['total_distance'] / games.count())
            stats['win_rate'] = round(stats['totals']['wins'] / games.count() * 100)
        # get opponent username with most games
        stats['most_played_opponent']['opponent'] = max(opponents, key=opponents.get).username
        stats['most_played_opponent']['games'] = opponents[max(opponents, key=opponents.get)]
        stats['games'] = games.count()
        return stats
                
    
# Pong Game Model
class Game(models.Model):
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='winner')
    loser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loser')
    score = ArrayField(models.IntegerField(), size=2)
    date = models.DateTimeField(auto_now_add=True)
    duration = models.IntegerField(default=0)
    longest_exchange = models.IntegerField(default=0)
    total_exchanges = models.IntegerField(default=0)
    total_distance = models.IntegerField(default=0)
    total_hits = models.IntegerField(default=0)
    objects = GameManager()

    def __str__(self):
        return f'{self.winner} vs {self.loser} ({self.score[0]}-{self.score[1]})'
    
    class Meta:
        db_table = 'games'
        verbose_name = 'Game'
        verbose_name_plural = 'Games'