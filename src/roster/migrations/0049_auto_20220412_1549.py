# Generated by Django 2.2.24 on 2022-04-12 15:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('roster', '0048_auto_20220412_1541'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clusiveuser',
            old_name='simplification_tool',
            new_name='transform_tool',
        ),
    ]