# Generated by Django 2.2.24 on 2022-04-07 01:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('roster', '0046_auto_20220318_1817'),
    ]

    operations = [
        migrations.AddField(
            model_name='clusiveuser',
            name='simplification_tool',
            field=models.CharField(choices=[('simplify', 'simplify'), ('translate', 'translate')], default='simplify', max_length=10),
        ),
    ]
