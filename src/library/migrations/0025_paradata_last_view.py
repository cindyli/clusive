# Generated by Django 2.2.13 on 2021-03-16 13:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0024_bookversion_non_dict_words'),
    ]

    operations = [
        migrations.AddField(
            model_name='paradata',
            name='last_view',
            field=models.DateTimeField(null=True),
        ),
    ]
