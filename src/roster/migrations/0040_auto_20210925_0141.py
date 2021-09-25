# Generated by Django 2.2.24 on 2021-09-25 01:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('roster', '0039_clusiveuser_data_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clusiveuser',
            name='library_view',
            field=models.CharField(choices=[('all', 'All readings'), ('public', 'Public readings'), ('mine', 'My readings'), ('period', 'Period assignments')], default='period', max_length=10),
        ),
    ]
