# Generated by Django 2.2.13 on 2021-03-24 22:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0002_auto_20210324_1811'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comprehensioncheckresponse',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
