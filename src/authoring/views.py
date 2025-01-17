import logging

import wordfreq as wf
from django.views.generic import FormView, TemplateView
from nltk.corpus import wordnet
from nltk.corpus.reader import Synset
from textstat import textstat

from authoring.forms import TextInputForm, TextSimplificationForm
from flaticon.util import FlaticonManager, flaticon_is_configured
from library.models import Book
from simplification.util import WordnetSimplifier

logger = logging.getLogger(__name__)


class SimplifyView(FormView):
    template_name = 'authoring/simplify.html'
    form_class = TextSimplificationForm
    lang = 'en'

    def post(self, request, *args, **kwargs):
        self.clusive_user = request.clusive_user
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        text = form.cleaned_data['text']
        percent = form.cleaned_data['percent']
        simplifier = WordnetSimplifier(self.lang)
        # Returns {
        #             'word_count': total_word_count,
        #             'to_replace': to_replace,
        #             'word_info': word_info,
        #             'result': out,
        #         }
        data = simplifier.simplify_text(text, clusive_user=self.clusive_user, percent=percent, include_full=True)
        self.extra_context = data
        # Don't do normal process of redirecting to success_url.  Just stay on this form page forever.
        r = 0

        # get the image replacements
        num_replace = data['to_replace']
        if flaticon_is_configured():
            icon_mgr = FlaticonManager()
            icon_session = icon_mgr.get_session()
            for index in range(len(data['word_info'])):
                temp_word = data['word_info'][index]['hw']
                (icon_url, icon_desc) = icon_mgr.get_icon(icon_session, temp_word)
                data['word_info'][index].update({ 'icon_url': icon_url,
                                                  'icon_alt': icon_desc,
                                                  })
                if icon_url is not None:
                    # logger.debug("UPDATED WORD INFO = %s", data['word_info'][index])
                    r = r + 1
                    if r == num_replace:
                        break
        return self.render_to_response(self.get_context_data(form=form))


class LevelingView(FormView):
    template_name = 'authoring/level.html'
    form_class = TextInputForm
    lang = 'en'
    words = []
    stats = []

    def form_valid(self, form):
        text = form.cleaned_data['text']
        word_list = wf.tokenize(text, self.lang)
        self.stats = [
            { 'name': 'Flesch-Kincaid grade level',
              'value':  textstat.flesch_kincaid_grade(text),
              'desc': 'Based on avg sentence length and syllables per word.'},
            { 'name': 'Dale-Chall grade level',
              'value': textstat.dale_chall_readability_score_v2(text),
              'desc': 'Based on avg sentence length and percent difficult words.'},
            { 'name': 'Number of words',
              'value': textstat.lexicon_count(text) },
            { 'name': 'Number of sentences',
              'value': textstat.sentence_count(text) },
            { 'name': 'Average sentence length',
              'value': textstat.avg_sentence_length(text) },
            { 'name': 'Average syllables per word',
              'value': textstat.avg_syllables_per_word(text) },
            { 'name': 'Difficult words',
              'value': "%d (%d%%): %s" % (textstat.difficult_words(text),
                                          100*textstat.difficult_words(text)/textstat.lexicon_count(text),
                                          ', '.join(textstat.difficult_words_list(text))) },
        ]
        simplifier = WordnetSimplifier(self.lang)
        self.words = simplifier.analyze_words(word_list)
        # Don't do normal process of redirecting to success_url.  Just stay on this form page forever.
        return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        logger.debug('invalid')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['words'] = self.words
        data['stats'] = self.stats
        return data


class SynonymsView(TemplateView):
    template_name = 'authoring/partial/synonyms.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        synsets = wordnet.synsets(kwargs['word'])
        context['synonyms'] = [ self.describe_synset(synset) for synset in synsets ]
        return context

    def describe_synset(self, synset : Synset):
        return "(%s) %s (%s)" % (synset.pos(), ', '.join([str(lemma.name()) for lemma in synset.lemmas()]), synset.definition())


class BookInfoView(TemplateView):
    template_name = 'authoring/book_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['books'] = Book.objects.filter(owner=None)
        return context
