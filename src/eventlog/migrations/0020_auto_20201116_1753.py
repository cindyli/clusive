# Generated by Django 2.2.13 on 2020-11-16 17:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eventlog', '0019_auto_20201116_1642'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='book_version',
            new_name='book_version_id',
        ),
    ]
