# Generated by Django 2.2.13 on 2021-03-16 15:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eventlog', '0024_event_book_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='eventTime',
            new_name='event_time',
        ),
    ]
