# Generated by Django 2.2.24 on 2022-03-16 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0048_paradata_starred'),
    ]

    operations = [
        migrations.AddField(
            model_name='booktrend',
            name='_user_count',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
