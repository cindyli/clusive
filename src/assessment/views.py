import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView

from eventlog.signals import affect_check_completed, comprehension_check_completed
from library.models import Book, Customization
from roster.models import Roles
from .models import ComprehensionCheck, ComprehensionCheckResponse, AffectiveCheckResponse, \
    AffectiveUserTotal, AffectiveBookTotal

logger = logging.getLogger(__name__)

class AffectCheckView(LoginRequiredMixin, View):
    @staticmethod
    def create_from_request(request, affect_check_data, book_id):
        clusive_user = request.clusive_user
        book = Book.objects.get(id=book_id)
        words_changed = free_response_changed = False

        with transaction.atomic():
            (acr, created) = AffectiveCheckResponse.objects.get_or_create(user=clusive_user, book=book)
            orig_values = acr.to_list()
            acr.annoyed_option_response = affect_check_data.get('affect-option-annoyed')
            acr.bored_option_response = affect_check_data.get('affect-option-bored')
            acr.calm_option_response = affect_check_data.get('affect-option-calm')
            acr.confused_option_response = affect_check_data.get('affect-option-confused')
            acr.curious_option_response = affect_check_data.get('affect-option-curious')
            acr.disappointed_option_response = affect_check_data.get('affect-option-disappointed')
            acr.frustrated_option_response = affect_check_data.get('affect-option-frustrated')
            acr.happy_option_response = affect_check_data.get('affect-option-happy')
            acr.interested_option_response = affect_check_data.get('affect-option-interested')
            acr.okay_option_response = affect_check_data.get('affect-option-okay')
            acr.sad_option_response = affect_check_data.get('affect-option-sad')
            acr.surprised_option_response = affect_check_data.get('affect-option-surprised')

            free_question = affect_check_data.get('freeQuestion')
            if acr.affect_free_response != affect_check_data.get('freeResponse'):
                free_response_changed = True
                acr.affect_free_response = affect_check_data.get('freeResponse')
            acr.save()

        new_values = acr.to_list()
        page_event_id=affect_check_data.get("eventId")

        if new_values != orig_values:
            (aut, created) = AffectiveUserTotal.objects.get_or_create(user=clusive_user)
            aut.update(orig_values, new_values)
            aut.save()

            (abt, created) = AffectiveBookTotal.objects.get_or_create(book=book)
            abt.update(orig_values, new_values)
            abt.save()

            affect_check_completed.send(sender=AffectCheckView,
                                        request=request,
                                        event_id=page_event_id,
                                        control='affect_check_words',
                                        affect_check_response_id=acr.id,
                                        answer=acr.to_answer_string())

        if free_response_changed:
            affect_check_completed.send(sender=AffectCheckView,
                                        request=request,
                                        event_id=page_event_id,
                                        control='affect_check_free_response',
                                        affect_check_response_id=acr.id,
                                        question=free_question,
                                        answer=acr.affect_free_response)

    def post(self, request, book_id):
        try:
            affect_check_data = json.loads(request.body)
            logger.info('Received a valid affect check response: %s' % affect_check_data)
        except json.JSONDecodeError:
            logger.warning('Received malformed affect check data: %s' % request.body)
            return JsonResponse(status=501, data={'message': 'Invalid JSON in request body'})

        AffectCheckView.create_from_request(request, affect_check_data, book_id)

        return JsonResponse({"success": "1"})

    def get(self, request, book_id):
        user = request.clusive_user
        book = Book.objects.get(id=book_id)
        acr = get_object_or_404(AffectiveCheckResponse, user=user, book=book)
        response_value = {
            "affect-option-annoyed": acr.annoyed_option_response,
            "affect-option-bored": acr.bored_option_response,
            "affect-option-calm": acr.calm_option_response,
            "affect-option-confused": acr.confused_option_response,
            "affect-option-curious": acr.curious_option_response,
            "affect-option-disappointed": acr.disappointed_option_response,
            "affect-option-frustrated": acr.frustrated_option_response,
            "affect-option-happy": acr.happy_option_response,
            "affect-option-interested": acr.interested_option_response,
            "affect-option-okay": acr.okay_option_response,
            "affect-option-sad": acr.sad_option_response,
            "affect-option-surprised": acr.surprised_option_response,
            "freeResponse": acr.affect_free_response,
        }
        return JsonResponse(response_value)


class ComprehensionDetailView(LoginRequiredMixin, TemplateView):
    """
    Show a list of comprehension prompt responses for a teacher's current period.
    """
    template_name = 'shared/partial/modal_class_comp_detail.html'

    def get(self, request, *args, **kwargs):
        book = get_object_or_404(Book, id=kwargs['book_id'])
        clusive_user = request.clusive_user
        if clusive_user.can_manage_periods and clusive_user.current_period:
            period = clusive_user.current_period
            self.extra_context = {
                'details': ComprehensionCheckResponse.get_class_details_by_scale(book=book, period=period),
            }
            return super().get(request, *args, **kwargs)
        else:
            raise PermissionDenied()


class CustomQuestionDetailView(LoginRequiredMixin, TemplateView):
    """
    Show a list of responses to the customized comprehension question for a teacher's current period.
    """
    template_name = 'shared/partial/modal_class_custom_detail.html'

    def get(self, request, *args, **kwargs):
        book = get_object_or_404(Book, id=kwargs['book_id'])
        clusive_user = request.clusive_user
        if clusive_user.can_manage_periods and clusive_user.current_period:
            period = clusive_user.current_period
            customizations = Customization.objects.filter(book=book, periods=period)
            self.extra_context = {
                'question': customizations[0].question if customizations else None,
                'details': ComprehensionCheckResponse.get_class_details_custom_responses(book=book, period=period),
            }
            return super().get(request, *args, **kwargs)
        else:
            raise PermissionDenied()


class AffectDetailView(LoginRequiredMixin, TemplateView):
    """
    Show a list of what readings inspired particular affective responses.
    Slightly different for teachers and students:
    Students see: my own responses / global responses
    Parents/teachers see: my class responses / global responses
    """
    student_template_name = 'shared/partial/modal_affect_detail.html'
    teacher_template_name = 'shared/partial/modal_class_affect_detail.html'

    def get(self, request, *args, **kwargs):
        self.word = kwargs['word']
        clusive_user = request.clusive_user
        self.teacher_view = False
        self.class_popular = None
        self.any_unauthorized_book = False
        self.my_recent = None
        if clusive_user.can_manage_periods and clusive_user.current_period:
            self.teacher_view = True
            # Find and count student responses in this period with the given affect word
            period = clusive_user.current_period
            field = self.word + '_option_response'
            filters = {
                field: True,
                'user__periods': period,
                'user__role': Roles.STUDENT
            }
            map_book_to_votes = {}
            for resp in AffectiveCheckResponse.objects.filter(**filters):
                if resp.book in map_book_to_votes:
                    map_book_to_votes[resp.book].append(resp)
                else:
                    map_book_to_votes[resp.book] = [resp]
            top_books = list(map_book_to_votes.values()) # list of lists
            top_books.sort(reverse=True, key=lambda l: len(l))
            top_books = top_books[0:10]
            self.class_popular = [{
                'count': len(b),
                'book': b[0].book,
                'unauthorized': not b[0].book.is_visible_to(clusive_user),
                'names': ', '.join([v.user.user.first_name for v in b]),
            } for b in top_books]
            # Determine if any of the books is not visible to the user
            for p in self.class_popular:
                if p['unauthorized']:
                    self.any_unauthorized_book = True
        else:
            self.my_recent = AffectiveCheckResponse.recent_with_word(clusive_user, self.word)[0:5]
        # Globally-ranked books with particular ratings (public library only):
        self.popular = AffectiveBookTotal.most_with_word(self.word).filter(book__owner=None)[0:5]
        # Make it easier to access the correct count from template.
        for abt in self.popular:
            abt.count = getattr(abt, self.word)
        return super().get(request, *args, **kwargs)

    def get_template_names(self):
        if self.teacher_view:
            return [self.teacher_template_name]
        else:
            return [self.student_template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['word'] = self.word
        context['my_recent'] = self.my_recent
        context['class_popular'] = self.class_popular
        context['popular'] = self.popular
        context['any_unauthorized_book'] = self.any_unauthorized_book
        return context


class ComprehensionCheckView(LoginRequiredMixin, View):
    @staticmethod
    def create_from_request(request, comprehension_check_data, book_id):
        clusive_user = request.clusive_user
        book = Book.objects.get(id=book_id)

        scale_response_changed = free_response_changed = custom_response_changed = False
        (ccr, created) = ComprehensionCheckResponse.objects.get_or_create(user=clusive_user, book=book)
        try:
            scale_response = int(comprehension_check_data.get('scaleResponse'))
        except:
            scale_response = None
        if ccr.comprehension_scale_response != scale_response:
            scale_response_changed = True
            ccr.comprehension_scale_response = scale_response
        if ccr.comprehension_free_response != comprehension_check_data.get('freeResponse'):
            free_response_changed = True
            ccr.comprehension_free_response = comprehension_check_data.get('freeResponse')
        if ccr.custom_response != comprehension_check_data.get('customResponse'):
            custom_response_changed = True
            ccr.custom_response = comprehension_check_data.get('customResponse')

        if scale_response_changed or free_response_changed or custom_response_changed:
            ccr.save()

            # Fire event creation signals
            # Note, these events are recorded at the time they are received. May be a few seconds off
            # (or more, if there are network problems) from the time that the response was actually made.
            page_event_id = comprehension_check_data.get("eventId")
            if scale_response_changed:
                comprehension_check_completed.send(sender=ComprehensionCheckView,
                                                   request=request, event_id=page_event_id,
                                                   comprehension_check_response_id=ccr.id,
                                                   key=ComprehensionCheck.scale_response_key,
                                                   question=comprehension_check_data.get('scaleQuestion'),
                                                   answer=comprehension_check_data.get('scaleResponse'))

            if free_response_changed:
                comprehension_check_completed.send(sender=ComprehensionCheckView,
                                                   request=request, event_id=page_event_id,
                                                   comprehension_check_response_id=ccr.id,
                                                   key=ComprehensionCheck.free_response_key,
                                                   question=comprehension_check_data.get('freeQuestion'),
                                                   answer=ccr.comprehension_free_response)
            if custom_response_changed:
                comprehension_check_completed.send(sender=ComprehensionCheckView,
                                                   request=request, event_id=page_event_id,
                                                   comprehension_check_response_id=ccr.id,
                                                   key=ComprehensionCheck.custom_response_key,
                                                   question=comprehension_check_data.get('customQuestion'),
                                                   answer=ccr.custom_response)

    def post(self, request, book_id):
        try:
            comprehension_check_data = json.loads(request.body)
            logger.debug('Received a valid comprehension check response: %s' % comprehension_check_data)
        except json.JSONDecodeError:
            logger.warning('Received malformed comprehension check data: %s' % request.body)
            return JsonResponse(status=501, data={'message': 'Invalid JSON in request body'})

        ComprehensionCheckView.create_from_request(request, comprehension_check_data, book_id)

        return JsonResponse({"success": "1"})

    def get(self, request, book_id):
        user = request.clusive_user
        book = Book.objects.get(id=book_id)
        ccr = get_object_or_404(ComprehensionCheckResponse, user=user, book=book)
        response_value = {
            ComprehensionCheck.scale_response_key: ccr.comprehension_scale_response,
            ComprehensionCheck.free_response_key: ccr.comprehension_free_response,
            ComprehensionCheck.custom_response_key: ccr.custom_response,
        }
        return JsonResponse(response_value)
