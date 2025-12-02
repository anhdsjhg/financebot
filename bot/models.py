from django.db import models

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=200, blank=True)
    score = models.IntegerField(default=0)   

    def __str__(self):
        return str(self.telegram_id)


class GameState(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    money = models.IntegerField(default=10000)
    day = models.IntegerField(default=1)
    active = models.BooleanField(default=False)
