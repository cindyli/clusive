# Generated by Django 3.2.14 on 2022-10-07 14:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tips', '0006_tiptype_kind'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tiptype',
            name='kind',
        ),
    ]
