# Generated by Django 2.2.20 on 2021-06-02 01:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('roster', '0034_auto_20210602_0100'),
        ('assessment', '0008_auto_20210428_1039'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClusiveRatingResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('star_rating', models.PositiveSmallIntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='roster.ClusiveUser')),
            ],
        ),
    ]