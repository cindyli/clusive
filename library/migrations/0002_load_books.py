# Generated by Django 2.2.4 on 2019-10-14 13:55
import json
import os

from django.contrib.staticfiles import finders
from django.db import migrations


def load_static_books(apps, schema_editor):
    Book = apps.get_model('library', 'Book')
    pubs_directory = finders.find('shared/pubs')
    book_dirs = os.scandir(pubs_directory)
    for book_dir in book_dirs:
        # Read the book manifest
        with open(os.path.join(book_dir, 'manifest.json'), 'r') as file:
            manifest = json.load(file)
            title = manifest['metadata']['headline']
            cover = find_cover(manifest)
            b = Book(path=book_dir.name, title=title, cover=cover)
            b.save()

def find_cover(manifest):
    for item in manifest['resources']:
        if item.get('rel') == 'cover':
            return item.get('href')
    return None

# Not sure if this is the best strategy.
# Fine for use while testing, but will fail if there are references to books in the DB.
def remove_all_books(apps, schema_editor):
    Book = apps.get_model('library', 'Book')
    Book.objects.all().delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('library', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_static_books, remove_all_books)
    ]
