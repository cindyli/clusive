from django.db import models
from uuid import uuid4
from django.contrib.auth.models import User
from datetime import datetime
import caliper

# A user session
class Session(models.Model):
    id = models.CharField(unique=True, primary_key=True, default=uuid4, max_length=36)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    startedAtTime = models.DateTimeField(default=datetime.now)
    endedAtTime = models.DateTimeField()  # time stamp when session ended (logout or timeout)
    # TODO appVersion: the current version of the Clusive application that the user is interacting with
    # TODO userAgent: the user-agent string that the browser identifies itself with - gives us browser type, version, operating system, etc.

    def __str__(self):
        return '%s (%s)' % (self.user, self.startedAtTime)

class Event(models.Model):
    id = models.CharField(unique=True, primary_key=True, default=uuid4, max_length=36)
    # TODO session
    actor = models.ForeignKey(to=User, on_delete=models.CASCADE)
    # TODO group
    # TODO membership
    eventTime = models.DateTimeField(default=datetime.now)
    # TODO eventEndTime
    type = models.CharField(max_length=8, choices=[(k,v) for k,v in caliper.constants.EVENT_TYPES.items()])
    action = models.CharField(max_length=32, choices=[(k,v) for k, v in caliper.constants.CALIPER_ACTIONS.items()])
    # TODO page
    # TODO article
    # TODO preference
    # TODO context (current settings, version of text (eg lexile level), list of glossary words highlighted)
