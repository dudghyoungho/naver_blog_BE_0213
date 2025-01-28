# Generated by Django 5.1 on 2025-01-28 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_profile_intro'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='postimage',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='posttext',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='postimage',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='posttext',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
