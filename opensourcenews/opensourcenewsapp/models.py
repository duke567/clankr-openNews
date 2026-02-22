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


class SourceTweet(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="source_tweets")
    raw = models.JSONField(default=dict)
    excluded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        text = (self.raw or {}).get("text", "")
        return text[:80]
