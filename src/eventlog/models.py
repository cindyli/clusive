import logging
from datetime import timedelta
from uuid import uuid4

import caliper
from django.db import models
from django.utils import timezone

from library.models import BookVersion
from roster.models import Period, ClusiveUser, Roles
from tips.models import TipType

logger = logging.getLogger(__name__)

# Keys for data we store in the session
PERIOD_KEY = 'current_period'
SESSION_ID_KEY = 'db_session_id'

# A user session
class LoginSession(models.Model):
    id = models.CharField(primary_key=True, default=uuid4, max_length=36)
    user = models.ForeignKey(to=ClusiveUser, on_delete=models.SET_NULL, null=True)
    started_at_time = models.DateTimeField(auto_now_add=True)
    ended_at_time = models.DateTimeField(null=True)  # time stamp when session ended (logout or timeout)
    # TODO appVersion: the current version of the Clusive application that the user is interacting with
    user_agent = models.CharField(max_length=256)
    active_duration = models.DurationField(null=True) # Total of active_duration of all events in this session

    def add_active_time(self, duration):
        if self.active_duration is None:
            self.active_duration = timedelta()
        self.active_duration += duration
        self.save()

    def __str__(self):
        anon_id = "nouser" if not self.user else self.user.anon_id
        return '%s [%s - %s] (%s)' % (anon_id, self.started_at_time, self.ended_at_time, self.id)


class Event(models.Model):
    id = models.CharField(primary_key=True, default=uuid4, max_length=36)
    session = models.ForeignKey(to=LoginSession, on_delete=models.PROTECT)
    actor = models.ForeignKey(to=ClusiveUser, on_delete=models.SET_NULL, null=True)
    group = models.ForeignKey(to=Period, null=True, on_delete=models.PROTECT)
    membership = models.CharField(
        max_length=2,
        choices=Roles.ROLE_CHOICES,
        default=Roles.GUEST
    )
    # Optional ID for a related event to this event (typically, a PageView)
    parent_event_id = models.CharField(null=True, max_length=36)
    # Date and time the event started
    event_time = models.DateTimeField(default=timezone.now)
    # (VIEW events:) time for the browser to retrieve and render the content
    load_time = models.DurationField(null=True)
    # (VIEW events:) total time from when the page was loaded to when it was exited
    duration = models.DurationField(null=True)
    # (VIEW events:) time that this page was focused, computer was awake, and no timeout dialog was in play.
    active_duration = models.DurationField(null=True)
    # type of the event, based on Caliper spec
    type = models.CharField(max_length=32, choices=[(k,v) for k,v in caliper.constants.EVENT_TYPES.items()])
    # action of the event, based on Caliper spec
    action = models.CharField(max_length=32, choices=[(k,v) for k, v in caliper.constants.CALIPER_ACTIONS.items()])
    # What Book was connected to the interaction; null if none
    # This is not a ForeignKey because Books can be deleted, but we want to keep the info here regardless.
    book_id = models.BigIntegerField(null=True)
    # What BookVersion the user was looking at; null if none (eg, the library page)
    # This is not a ForeignKey because BookVersions can be deleted, but we want to keep the info here regardless.
    book_version_id = models.BigIntegerField(null=True)
    # Resource href (specific resource within an ebook); null if none
    resource_href = models.CharField(max_length=512, null=True)
    # Resource progression, if relevant; null if none
    resource_progression = models.FloatField(null=True)
    # The name of the application page (Library, Reading, etc)
    page = models.CharField(max_length=128, null=True)
    # for TOOL_USE_EVENT, records what tool was used; for preferences, which preference
    control = models.CharField(max_length=64, null=True)
    # For assessment events, the question being answered. For translation, the language.
    object = models.CharField(max_length=128, null=True)
    # For events that operate on text (lookup, highlight, translate), the actual text looked up or highlighted
    # For preferences, the new value chosen for the preference
    value = models.CharField(max_length=128, null=True)
    # If this is a page-view event that included a Tip, that is recorded here.
    tip_type = models.ForeignKey(to=TipType, null=True, on_delete=models.PROTECT)
    # TODO log source of glossary definitions?
    # TODO context (current settings, version of text (eg lexile level), list of glossary words highlighted)

    @classmethod
    def build(cls, type, action,
              session=None, login_session=None, group=None, parent_event_id=None,
              book_version=None, book_id=None, book_version_id=None,
              resource_href=None, resource_progression=None, page=None,
              control=None, object=None, value=None, event_time=None):
        """Create an event based on the data provided."""
        if not session and not login_session:
            logger.error("Either a session object or a login_session must be provided")
            return None
        try:
            if session and not login_session:
                login_session_id = session.get(SESSION_ID_KEY, None)
                login_session = LoginSession.objects.get(id=login_session_id)
            if session and not group:
                period_id = session.get(PERIOD_KEY, None)
                group = Period.objects.filter(id=period_id).first()
            if event_time == None:
                event_time = timezone.now()
            clusive_user = login_session.user
            if object and len(object) > 128:
                obj = object[:126] + '…'
            if value and len(value) > 128:
                value = value[:126] + '…'
            if not book_version_id and book_version:
                book_version_id = book_version.id
            # If we don't have a book_id but we do have book_version / book_version_id,
            # try to look up the related book
            if not book_id and book_version:
                book_id = book_version.book.id
            if not book_id and book_version_id:
                try:
                    bv = BookVersion.objects.get(pk=book_version_id)
                    book_id = bv.book.id
                except BookVersion.DoesNotExist:
                    logger.warning("Tried to look up book_id for book_version_id %s, but BookVersion does not exist", book_version_id)
            event = cls(type=type,
                        action=action,
                        actor=clusive_user,
                        membership=clusive_user.role,
                        session=login_session,
                        group=group,
                        parent_event_id=parent_event_id,
                        book_id=book_id,
                        book_version_id = book_version_id,
                        resource_href=resource_href,
                        resource_progression=resource_progression,
                        page=page,
                        control=control,
                        object=object,
                        value=value,
                        event_time=event_time)
            return event
        except ClusiveUser.DoesNotExist:
            logger.warning("Event could not be stored - no Clusive user found: %s/%s", type, action)
        except LoginSession.DoesNotExist:
            logger.warning("Event could not be stored - no LoginSession: %s/%s", type, action)
        except Period.DoesNotExist:
            logger.warning("Event could not be stored - period id %s not found", period_id)
        return None


    def __str__(self):
        anon_id = "noactor" if not self.actor else self.actor.anon_id
        return '%s:%s (%s)' % (anon_id, self.action, self.id)
