# Generated by Django 2.2.4 on 2019-08-07 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('roster', '0012_remove_site_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clusiveuser',
            name='role',
            field=models.CharField(choices=[('GU', 'Guest'), ('ST', 'Student'), ('PA', 'Parent'), ('TE', 'Teacher'), ('RE', 'Researcher'), ('AD', 'Admin')], default='GU', max_length=2),
        ),
    ]
