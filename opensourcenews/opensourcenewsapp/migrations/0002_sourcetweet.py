from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("opensourcenewsapp", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SourceTweet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("raw", models.JSONField(default=dict)),
                ("excluded", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="source_tweets",
                        to="opensourcenewsapp.post",
                    ),
                ),
            ],
        ),
    ]
