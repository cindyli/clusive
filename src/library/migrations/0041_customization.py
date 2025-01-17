# Generated by Django 2.2.24 on 2022-01-20 18:30

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('roster', '0044_clusiveuser_student_activity_sort'),
        ('library', '0040_auto_20220120_1517'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256)),
                ('question', models.CharField(max_length=256)),
                ('vocabulary_words', models.TextField(default='[]')),
                ('mod_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.Book')),
                ('periods', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='roster.Period')),
            ],
            options={
                'ordering': ['title'],
            },
        ),
    ]
