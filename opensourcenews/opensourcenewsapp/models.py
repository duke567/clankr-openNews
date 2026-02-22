from django.db import models

# Create your models here.
class Post(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    article = models.TextField()
    score = models.IntegerField(default=0)
    media = models.URLField(blank=True)
    
    def __str__(self):
        return self.title