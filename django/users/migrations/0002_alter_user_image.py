# Generated by Django 4.2.9 on 2024-02-14 22:29

from django.db import migrations, models
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='image',
            field=models.URLField(default=users.models.random_default_image),
        ),
    ]
