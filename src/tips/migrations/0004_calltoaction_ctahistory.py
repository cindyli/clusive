# Generated by Django 2.2.24 on 2021-07-26 21:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('roster', '0035_userstats_logins'),
        ('tips', '0003_auto_20201109_1851'),
    ]

    operations = [
        migrations.CreateModel(
            name='CallToAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
                ('priority', models.PositiveSmallIntegerField(unique=True)),
                ('enabled', models.BooleanField(default=False)),
                ('max', models.PositiveSmallIntegerField(null=True, verbose_name='Maximum times to show')),
            ],
        ),
        migrations.CreateModel(
            name='CTAHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('show_count', models.PositiveSmallIntegerField(default=0)),
                ('first_show', models.DateTimeField(blank=True, null=True)),
                ('last_show', models.DateTimeField(blank=True, null=True)),
                ('completed', models.DateTimeField(blank=True, null=True)),
                ('completion_type', models.CharField(blank=True, choices=[('T', 'Action Taken'), ('D', 'Declined'), ('M', 'Max shows')], max_length=8, null=True)),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tips.CallToAction')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='roster.ClusiveUser')),
            ],
            options={
                'verbose_name': 'CTA history',
                'verbose_name_plural': 'CTA histories',
                'unique_together': {('type', 'user')},
            },
        ),
    ]
