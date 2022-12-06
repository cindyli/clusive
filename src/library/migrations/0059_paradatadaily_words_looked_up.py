# Generated by Django 3.2.16 on 2022-11-28 19:30

import json
import logging

from django.db import migrations, models
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


# When the `words_looked_up` field is added, each ClusiveUser's Events are
# searched for 'lookup' events.  Each day's worth of Events are used to capture
# the words looked up that day and added to a ParadataDaily record
def batch_load_daily_word_lists(apps, schema_editor):
    # Relevant models
    ParadataDaily = apps.get_model('library', 'ParadataDaily')
    Book = apps.get_model('library', 'Book')
    Event = apps.get_model('eventlog', 'Event')
    ClusiveUser = apps.get_model('roster', 'ClusiveUser')

    for clusive_user in ClusiveUser.objects.all():
        # Get all the avents for the user that involve word lookup
        word_events = Event.objects.filter(
            actor=clusive_user,
            control__icontains='lookup'
        ).exclude(book_id=None)
        # Loop thru the word events and construct a dictionary mapping
        # (book, date) tuples to a set of words gathered from the events
        # for the book and date.
        book_date_map = dict()
        for word_event in word_events:
            date = word_event.event_time.date()
            try:
                book = Book.objects.get(pk=word_event.book_id)
            except Book.DoesNotExist:
                logger.debug(f"No book with book_id {word_event.book_id} for word look-up {word_event}/{word_event.control}/{word_event.value}; user {clusive_user.user.username}/{clusive_user.anon_id}")
                continue
            word_set = book_date_map.get((book, date))
            if word_set is not None:
                word_set.add(word_event.value)
            else:
                word_set = set()
                word_set.add(word_event.value)
                book_date_map[(book, date)] = word_set
        # Loop thru the dictionary keys and find the ParadataDaily records
        # for that book and date.
        for book_date in book_date_map.keys():
            try:
                paradata_daily = ParadataDaily.objects.get(
                    paradata__user=clusive_user,
                    paradata__book=book_date[0],
                    date=book_date[1]
                )
                paradata_daily.words_looked_up = json.dumps(list(book_date_map[book_date]))
                paradata_daily.save()
                logger.info(f"Saved words_looked_up {paradata_daily.words_looked_up} for {paradata_daily} for {book_date}, user {clusive_user.user.username}/{clusive_user.anon_id})")
            except ParadataDaily.DoesNotExist:
                logger.debug(f"No ParadataDaily found for {book_date}, words: {book_date_map[book_date]}, user {clusive_user.user.username}/{clusive_user.anon_id}")


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0058_educatorresourcecategory_feature_alt_format'),
    ]

    operations = [
        migrations.AddField(
            model_name='paradatadaily',
            name='words_looked_up',
            field=models.TextField(blank=True, null=True, verbose_name='JSON list of words looked up'),
        ),
        migrations.RunPython(batch_load_daily_word_lists, migrations.RunPython.noop),
    ]
