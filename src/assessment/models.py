import logging

from django.db import models
from django.utils import timezone

from library.models import Book
from roster.models import ClusiveUser

logger = logging.getLogger(__name__)


class ComprehensionCheck:
    scale_response_key = "scale_response"
    free_response_key = "free_response"

    class ComprehensionScale:
        NOTHING = 0
        LITTLE = 1
        LOT = 2

        COMPREHENSION_SCALE_CHOICES = [
            (NOTHING, 'Nothing'),
            (LITTLE, 'A little'),
            (LOT, 'A lot')
        ]


# Generic comprehension check responses
class ComprehensionCheckResponse(models.Model):    
    user = models.ForeignKey(to=ClusiveUser, on_delete=models.PROTECT)
    book = models.ForeignKey(to=Book, on_delete=models.PROTECT)       
    comprehension_scale_response = models.IntegerField(        
        choices=ComprehensionCheck.ComprehensionScale.COMPREHENSION_SCALE_CHOICES,
        null=True
    )    
    comprehension_free_response = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '<CCResp %s/%d>' % (self.user.anon_id, self.book.id)

