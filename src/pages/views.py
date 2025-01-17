import json
import logging
from datetime import date, timedelta
from os.path import exists

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Q
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, RedirectView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import BaseCreateView

import flaticon.util
import nounproject.util
import translation
from assessment.forms import ClusiveRatingForm
from assessment.models import ClusiveRatingResponse, AffectiveUserTotal, ComprehensionCheckResponse, \
    AffectiveCheckResponse
from eventlog.models import Event
from eventlog.signals import star_rating_completed
from eventlog.views import EventMixin
from glossary.models import WordModel
from glossary.views import choose_words_to_cue
from library.models import Book, BookVersion, Paradata, Annotation, BookTrend, Customization
from roster.models import ClusiveUser, Period, Roles, UserStats, Preference
from tips.models import TipHistory, CTAHistory, CompletionType
from translation.util import TranslateApiManager

logger = logging.getLogger(__name__)


class ThemedPageMixin(ContextMixin):
    """
    Set up for the correct color theme to be applied to the page.
    This mixin provides a theme_class context variable to the view, according to user's preference,
    which is used by base.html to set a class attribute on the body tag.
    """

    def dispatch(self, request, *args, **kwargs):
        self.clusive_user = request.clusive_user
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['theme_class'] = 'clusive-theme-' + Preference.get_theme_for_user(self.clusive_user)
        return data


class SettingsPageMixin(ContextMixin):
    """
    Set up context variables needed by the settings panel.
    This mixin should be added to all page views that include settings.
    """

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['translation_languages'] = TranslateApiManager.get_translate_language_list()
        return data


class PeriodChoiceMixin(ContextMixin):
    """
    Add this to Views that allow users to select one of their Periods to be active.
    Sets context variables "periods" (a list) and current_period (the selected one).
    If a kwarg called "period_id" is received, updates the current_period.
    """
    periods = None
    current_period = None

    def get_current_period(self, request, **kwargs):
        """Return the current period for this user, setting it if necessary."""
        if not self.current_period:
            clusive_user = request.clusive_user
            if self.periods is None:
                self.periods = clusive_user.periods.all().order_by(Lower('name'))
            if kwargs.get('period_id'):
                # User is setting a new period
                self.current_period = get_object_or_404(Period, pk=kwargs.get('period_id'))
                if self.current_period not in self.periods:
                    self.handle_no_permission()   # attempted to access a Period the user is not in
                logger.debug('Set current period to %s', self.current_period)
            if self.current_period is None:
                # Set user's default Period
                if clusive_user.current_period:
                    self.current_period = clusive_user.current_period
                elif self.periods:
                    self.current_period = self.periods[0]
            if self.current_period != clusive_user.current_period and self.current_period != None:
                # Update user's default period to current
                clusive_user.current_period = self.current_period
                clusive_user.save()
        return self.current_period

    def get(self, request, *args, **kwargs):
        self.get_current_period(request, **kwargs)
        result = super().get(request, *args, **kwargs)
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['periods'] = self.periods
        context['current_period'] = self.current_period
        return context


class DashboardView(LoginRequiredMixin, ThemedPageMixin, SettingsPageMixin, EventMixin, PeriodChoiceMixin, TemplateView):
    template_name='pages/dashboard.html'

    def __init__(self):
        super().__init__()

    def get(self, request, *args, **kwargs):
        # Redirect administrators who mistakenly logged in with a link that goes here.
        if request.user.is_staff:
            return HttpResponseRedirect('/admin')

        self.clusive_user = request.clusive_user
        self.teacher = self.clusive_user.can_manage_periods
        self.current_period = self.get_current_period(request, **kwargs)
        self.panels = {} # This will hold info on which panels are to be displayed.
        self.data = {} # This will hold panel-specific data

        self.tip_shown = TipHistory.get_tip_to_show(self.clusive_user, page='Dashboard')

        # Decision-making data
        user_stats = UserStats.objects.get(user=request.clusive_user)

        # Welcome panel
        self.panels['welcome'] = user_stats.reading_views == 0

        # Calls to Action
        cta_name = None
        if request.GET.get('cta'):
            # Manual override, for testing. Named CTA will be shown, but not recorded in history.
            cta_name = request.GET.get('cta')
        else:
            histories = CTAHistory.available_ctas(user=self.clusive_user, page='Dashboard')
            if histories:
                logger.debug('CTAs: %s', repr(histories))
                histories[0].show()  # Record the fact that it was displayed.
                cta_name = histories[0].type.name
        if cta_name:
            self.panels['cta'] = True
            self.data['cta'] = {
                'type': cta_name,
            }
            if cta_name == 'star_rating':
                self.data['cta']['form'] = ClusiveRatingForm(initial={'star_rating': 0})
        else:
            self.panels['cta'] = False

        # Affect panel (for student)
        self.panels['affect'] = not self.teacher and user_stats.reading_views > 0
        if self.panels['affect']:
            totals = AffectiveUserTotal.objects.filter(user=request.clusive_user).first()
            self.data['affect'] = {
                'totals':  AffectiveUserTotal.scale_values(totals),
                'empty': totals is None,
            }

        # Class Affect panel (for parent/teacher)
        self.panels['class_affect'] = self.teacher and self.current_period
        if self.panels['class_affect']:
            sa = AffectiveUserTotal.objects.filter(user__periods=self.current_period, user__role=Roles.STUDENT)
            scaled = AffectiveUserTotal.aggregate_and_scale(sa)
            logger.debug('scaled: %s', scaled)
            self.data['class_affect'] = {
                'totals': scaled,
                'empty': not any([item['value'] for item in scaled]),
            }
            logger.debug("Scaled: %s", scaled)

        # Star results panel
        self.panels['star_results'] = self.should_show_star_results(request)
        if self.panels['star_results']:
            self.data['star_results'] = {
                'form': ClusiveRatingForm(initial={'star_rating': self.star_rating.star_rating}),
                'results': ClusiveRatingResponse.get_graphable_results(),
            }

        # Popular Reads panel (teacher)
        self.panels['popular_reads'] = self.teacher
        if self.panels['popular_reads']:
            self.data['popular_reads'] = get_popular_reads_data(self.clusive_user, self.periods, self.current_period,
                                                                assigned_only=False)

        # Getting Started panel
        if not self.teacher:
            last_reads = Paradata.latest_for_user(request.clusive_user)[:3]
            self.panels['getting_started'] = not last_reads or len(last_reads) == 0
            if self.panels['getting_started']:
                self.data['getting_started'] = {
                    'featured': list(Book.get_featured_books()[:2])
                }

            # Recent Reads panel
            self.panels['recent_reads'] = len(last_reads) > 0
            if self.panels['recent_reads']:
                if len(last_reads) < 3:
                    # Add featured books to the list
                    features = list(Book.get_featured_books()[:3])
                    # Remove any featured books that are in the user's last-read list.
                    for para in last_reads:
                        if para.book in features:
                            features.remove(para.book)
                else:
                    features = []
                self.data['recent_reads'] = {
                    'last_reads': last_reads,
                    'featured': features,
                }

        # Student Activity panel
        self.panels['student_activity'] = self.teacher
        sa_days = self.clusive_user.student_activity_days
        sa_sort = self.clusive_user.student_activity_sort
        if self.panels['student_activity']:
            self.data['student_activity'] = {
                'days': sa_days,
                'sort': sa_sort,
                'reading_data':
                    Paradata.reading_data_for_period(self.current_period, days=sa_days, sort=sa_sort)
                    if self.current_period else None
            }

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['period_name'] = self.current_period.name if self.current_period else None
        context['query'] = None
        context['panels'] = self.panels
        context['data'] = self.data
        context['tip_name'] = self.tip_shown.name if self.tip_shown else None
        return context

    def should_show_star_results(self, request):
        # Put 'starresults=1' in URL for debugging
        if request.GET.get('starresults'):
            return True

        # Otherwise, only shown via AJAX request after rating.
        return False

    def configure_event(self, event: Event):
        event.page = 'Dashboard'
        event.tip_type = self.tip_shown


class PopularReadsPanelView(LoginRequiredMixin, TemplateView):
    """Used for AJAX request to switch between Popular and Assigned views of the student reading panel."""
    template_name = 'pages/partial/dashboard_panel_popular_reads_data.html'

    def get(self, request, *args, **kwargs):
        self.clusive_user = request.clusive_user
        self.view = kwargs['view']
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        periods = list(self.clusive_user.periods.all())
        current_period = self.clusive_user.current_period
        assigned = self.view == 'assigned'
        context.update({
            'current_period': current_period,
            'period_name': current_period.name,
            'query': None,
            'data': get_popular_reads_data(self.clusive_user, periods, current_period, assigned_only=assigned),
        })
        return context


def get_popular_reads_data(clusive_user, periods, current_period, assigned_only):
    # Gather data about books that are trending for dashboard view
    if assigned_only:
        trends = BookTrend.top_assigned(current_period)[:3]
    else:
        trends = BookTrend.top_trends(current_period)[:3]
    trend_data = [{'trend': t} for t in trends]

    for td in trend_data:
        t = td['trend']
        book = td['trend'].book
        # Look up paradata, assignments & customizations for books so they can be shown in the cards.
        book.paradata_list = list(Paradata.objects.filter(book=book, user=clusive_user))
        book.add_teacher_extra_info(periods)
        # Check if there is a customization for the current period.
        for c in book.custom_list:
            if current_period in list(c.periods.all()):
                td['customization'] = c
        # Get comp check statistics
        td['comp_check'] = ComprehensionCheckResponse.get_counts(t.book, t.period)
        td['unauthorized'] = not t.book.is_visible_to(clusive_user)

    return {
        'all': trend_data,
        'view': 'assigned' if assigned_only else 'popular',
    }


class DashboardActivityPanelView(TemplateView):
    """Shows just the activity panel, for AJAX updates"""
    template_name = 'pages/partial/dashboard_panel_student_activity.html'

    def get(self, request, *args, **kwargs):
        self.clusive_user = request.clusive_user
        self.current_period = request.clusive_user.current_period

        if 'days' in kwargs:
            self.days = kwargs.get('days')
            logger.debug('Setting student activity days = %d', self.days)
            self.clusive_user.student_activity_days = self.days
            self.clusive_user.save()
        else:
            self.days = self.clusive_user.student_activity_days

        if 'sort' in kwargs:
            self.sort = kwargs.get('sort')
            logger.debug('Setting student activity sort = %s', self.sort)
            self.clusive_user.student_activity_sort = self.sort
            self.clusive_user.save()
        else:
            self.sort = self.clusive_user.student_activity_sort

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = {
            'days': self.days,
            'sort': self.sort,
            'reading_data': Paradata.reading_data_for_period(self.current_period, days=self.days, sort=self.sort),
        }
        return context


class DashboardActivityDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'shared/partial/modal_student_activity_detail.html'

    def get_context_data(self, **kwargs):
        user_id = kwargs['user_id']
        book_id = kwargs['book_id']
        data = super().get_context_data(**kwargs)

        try:
            clusive_user = ClusiveUser.objects.get(pk=user_id)
            data['clusive_user'] = clusive_user
            book = Book.objects.get(pk=book_id)
            data['book'] = book
            data['book_has_versions'] = book.versions.count() > 1

            paras = Paradata.objects.filter(user=clusive_user, book=book)
            # Annotate with the time total from the last week
            start_date = date.today()-timedelta(days=7)
            paras = paras.annotate(recent_time=Sum('paradatadaily__total_time',
                                                           filter=Q(paradatadaily__date__gt=start_date)))
            paradata = paras[0]
            data['paradata'] = paradata
            if paradata.first_version and paradata.first_version != paradata.last_version:
                data['version_switched'] = True

            # Affect and Comp check
            affect_checks = AffectiveCheckResponse.objects.filter(user=clusive_user, book=book)
            if affect_checks:
                data['affect_check'] = affect_checks[0]
            comp_checks = ComprehensionCheckResponse.objects.filter(user=clusive_user, book=book)
            if comp_checks:
                data['comp_check'] = comp_checks[0]

            # Highlights and notes
            data['highlight_count'] = Annotation.objects.filter(bookVersion__book=book, user=clusive_user, dateDeleted=None).count()
            data['note_count'] = Annotation.objects.filter(bookVersion__book=book, user=clusive_user, dateDeleted=None,
                                                           note__isnull=False).exclude(note='').count()

            return data
        except ClusiveUser.DoesNotExist:
            logger.error('No clusive user %d', user_id)
            raise Http404('No such user')
        except Book.DoesNotExist:
            logger.error('No such book %d', book_id)
            raise Http404('No such book')


class SetStarRatingView(LoginRequiredMixin, BaseCreateView):
    form_class = ClusiveRatingForm
    success_url = reverse_lazy('star_rating_results')

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        # Save rating
        self.object = form.save(commit=False)
        self.object.user = self.request.clusive_user
        self.object.save()
        # Update Call To Action
        CTAHistory.register_action(user=self.request.clusive_user,
                                   cta_name='star_rating', completion_type=CompletionType.TAKEN)
        # Log event
        question = 'How would you rate your experience with Clusive so far?'
        star_rating_completed.send(SetStarRatingView.__class__, request=self.request,
                                   question=question, answer=self.object.star_rating)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        logger.debug('Form invalid: %s', form)
        return super().form_invalid(form)


class StarRatingResultsView(LoginRequiredMixin,TemplateView):
    """Display just the star rating panel. Used for AJAX request"""
    template_name = 'pages/partial/dashboard_panel_star_rating_results.html'

    def dispatch(self, request, *args, **kwargs):
        self.rating = ClusiveRatingResponse.objects.filter(user=request.clusive_user).order_by('-created').first()
        self.results = ClusiveRatingResponse.get_graphable_results()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial = {'star_rating': self.rating.star_rating} if self.rating else None
        context['data'] = {
            'form': ClusiveRatingForm(initial=initial),
            'results': self.results,
        }
        return context


class ReaderIndexView(LoginRequiredMixin,RedirectView):
    """This is the 'home page', currently just redirects to the user's default library view."""
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_staff:
            logger.debug("Staff login")
            return 'admin'
        else:
            clusive_user : ClusiveUser
            clusive_user = get_object_or_404(ClusiveUser, user=self.request.user)
            view = clusive_user.library_view
            style = clusive_user.library_style
            sort = clusive_user.library_sort
            if view == 'period' and clusive_user.current_period:
                return reverse('library', kwargs = {
                    'style': style,
                    'sort': sort,
                    'view': 'period',
                    'period_id': clusive_user.current_period.id
                })
            else:
                return reverse('library', kwargs = {
                    'style': style,
                    'sort': sort,
                    'view': view
                })


class ReaderChooseVersionView(RedirectView):
    """Determine appropriate version of book to show, and redirect to it. """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        book_id = kwargs.get('book_id')
        versions = BookVersion.objects.filter(book__pk=book_id)
        v = None
        if len(versions) == 1:
            # Shortcut: only one version exists, go there.
            v = 0
        else:
            clusive_user = get_object_or_404(ClusiveUser, user=self.request.user)
            try:
                paradata = Paradata.objects.get(book__pk=book_id, user=clusive_user)
                # Return to the last version this user viewed.
                v = paradata.last_version.sortOrder
                logger.debug('Returning to last version viewed (%d)', v)
            except:
                # No previous view - determine where to send the user based on vocabulary.
                logger.debug('New book for this user, choosing from versions...')
                # Compute an estimate of the fraction of words in each version that the user does not know
                # This is attached to the versions as "novel_frac".
                for bv in versions:
                    logger.debug('Considering version: %s', bv)
                    if bv.sortOrder==0:
                        words = bv.all_word_list
                        wordcount = len(words)
                        logger.debug('  Word count: %d', wordcount)
                        user_words = WordModel.objects.filter(user=clusive_user, word__in=words)
                        logger.debug('  Have ratings for %d', len(user_words))
                        not_known = len([u for u in user_words if (u.knowledge_est() or 3)<2])
                        bv.novel_frac = not_known/wordcount
                        logger.debug('  %d words have not-known ratings, so novel_frac = %f', not_known, bv.novel_frac)
                    else:
                        words = bv.all_word_list
                        prev_version = versions[bv.sortOrder - 1]
                        new_words = bv.new_word_list
                        logger.debug("  New words in this version (%d): %s", len(new_words), new_words)
                        user_words = WordModel.objects.filter(user=clusive_user, word__in=new_words)
                        user_words = [u for u in user_words if u.knowledge_est()!=None]
                        if (user_words):
                            not_known_count = len([u for u in user_words if u.knowledge_est()<2])
                            new_novel_frac = not_known_count/len(user_words)
                            logger.debug('  Have ratings for %d; of those %d are not known (%f)',
                                         len(user_words), not_known_count, new_novel_frac)
                            common_word_count = len(words)-len(new_words)
                            bv.novel_frac = (common_word_count*prev_version.novel_frac + len(new_words)*new_novel_frac)/len(words)
                            logger.debug('  Assuming %f of new words are NK, and %f of old words are NK, novel_frac = %f',
                                         new_novel_frac, prev_version.novel_frac, bv.novel_frac)
                        else:
                            # For now assume it's the same as the previous version, I guess.
                            bv.novel_frac = prev_version.novel_frac
                            logger.debug('  No ratings for these words. Defaulting to same novel_frac as last version: %f.',
                                         bv.novel_frac)
                # Choose highest version with novel_frac below a threshhold.
                threshhold = .01
                v=len(versions)-1
                while v>0 and versions[v].novel_frac > threshhold:
                    v -= 1
                logger.debug("Chose version %d: last one under threshhold of %f", v, threshhold)
        kwargs['version'] = v
        return super().get_redirect_url(*args, **kwargs)


class ReaderView(LoginRequiredMixin, EventMixin, ThemedPageMixin, SettingsPageMixin, TemplateView):
    """Reader page showing a page of a book"""
    template_name = 'pages/reader.html'
    page_name = 'Reading'

    def get(self, request, *args, **kwargs):
        book_id = kwargs.get('book_id')
        version = kwargs.get('version')
        book = Book.objects.get(pk=book_id)
        if not book.is_visible_to(request.clusive_user):
            raise PermissionDenied()
        versions = book.versions.all()
        clusive_user = request.clusive_user
        self.book_version = versions[version]
        self.book = book
        annotationList = Annotation.get_list(user=clusive_user, book_version=self.book_version)
        cuelist_map = choose_words_to_cue(book_version=self.book_version, user=clusive_user)
        # Make into format that R2D2BC wants for "definitions"
        cuelist = [{ 'order': i, 'result': 1, 'terms': terms } for i, terms in enumerate(cuelist_map.values())]
        logger.debug('Cuelist: %s', repr(cuelist))
        pdata = Paradata.record_view(book, version, clusive_user)
        # See if user wants the cues to be initially shown or not
        hide_cues = not Preference.get_glossary_pref_for_user(clusive_user)

        # See if there's a Tip that should be shown
        self.tip_shown = TipHistory.get_tip_to_show(clusive_user, page=self.page_name, version_count=len(versions))

        # See if there's a custom question
        customizations = Customization.objects.filter(book=book, periods=clusive_user.current_period) \
            if clusive_user.current_period else None
        logger.debug('Customization: %s', customizations)

        if exists(self.book_version.storage_dir + '/positions.json'):
            positions_path = self.book_version.positions_path
            weight_path = self.book_version.weight_path
            logger.debug('Positions: %s, Weight: %s', positions_path, weight_path)
        else:
            positions_path = weight_path = False
            logger.debug('No pre-calculated positions or weight')

        self.extra_context = {
            'pub': book,
            'version_id': self.book_version.id,
            'version_count': len(versions),
            'manifest_path': self.book_version.manifest_path,
            'positions_path': positions_path,
            'weight_path': weight_path,
            'last_position': pdata.last_location or "null",
            'annotations': annotationList,
            'cuelist': json.dumps(cuelist),
            'hide_cues': hide_cues,
            'tip_name': self.tip_shown.name if self.tip_shown else None,
            'customization': customizations[0] if customizations else None,
            'starred': pdata.starred,
            'book_id': book.id,
            'simplification_tool': clusive_user.transform_tool,
            'simplification_show_translate': translation.util.translation_is_configured(),
            'simplification_show_pictures': flaticon.util.flaticon_is_configured() or nounproject.util.nounproject_is_configured(),
        }
        return super().get(request, *args, **kwargs)

    def configure_event(self, event: Event):
        event.page = self.page_name
        event.book_version_id = self.book_version.id
        event.book_id = self.book.id
        event.tip_type = self.tip_shown


class WordBankView(LoginRequiredMixin, EventMixin, ThemedPageMixin, SettingsPageMixin, TemplateView):
    template_name = 'pages/wordbank.html'

    def get(self, request, *args, **kwargs):
        self.extra_context = {
            'words': WordModel.objects.filter(user=request.clusive_user, interest__gt=0).order_by('word')
        }
        return super().get(request, *args, **kwargs)

    def configure_event(self, event: Event):
        event.page = 'Wordbank'


class AboutView(TemplateView):
    template_name = 'pages/about.html'


class PrivacyView(TemplateView):
    template_name = 'pages/privacy.html'


class DebugView(TemplateView):
    template_name = 'pages/debug.html'
