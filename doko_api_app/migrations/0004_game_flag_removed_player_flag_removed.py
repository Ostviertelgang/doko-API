# Generated by Django 5.0.6 on 2024-06-20 16:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doko_api_app', '0003_round_bock_multiplier'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='flag_removed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='player',
            name='flag_removed',
            field=models.BooleanField(default=False),
        ),
    ]