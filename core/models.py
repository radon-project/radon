from django.db import models
from django.utils.timezone import now

class RN_Themes(models.Model):
    '''All themes are in this table.'''
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(default='radon_one', max_length=120)
    is_active = models.BooleanField(default=False)
    date = models.DateTimeField(default=now)

