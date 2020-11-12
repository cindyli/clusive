# Generated by Django 2.2.13 on 2020-10-31 21:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('roster', '0024_auto_20200904_2000'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
                ('priority', models.PositiveSmallIntegerField(unique=True)),
                ('max', models.PositiveSmallIntegerField(verbose_name='Maximum times to show')),
                ('interval', models.DurationField(verbose_name='Interval between shows')),
            ],
        ),
        migrations.CreateModel(
            name='TipHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('show_count', models.PositiveSmallIntegerField(default=0)),
                ('last_show', models.DateTimeField(null=True)),
                ('last_action', models.DateTimeField(null=True)),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tips.TipType')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='roster.ClusiveUser')),
            ],
        ),
    ]