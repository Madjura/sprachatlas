from django import forms
from django.forms import fields


class SimilarityForm(forms.Form):
    # the texts to be processed, multiple can be selected
    texts = fields.MultipleChoiceField(required=True, help_text="Select all texts to process.",
                                       widget=forms.CheckboxSelectMultiple())

    def __init__(self, text_choices=None, *args, **kwargs):
        """
        Constructor.
        :param text_choices: The choices for the texts.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        if text_choices:
            self.fields["texts"].choices = [(text, text) for text in text_choices]


class BigramGraphForm(forms.Form):
    # the texts to be processed, multiple can be selected
    texts = fields.MultipleChoiceField(required=True, help_text="Select all texts to process.",
                                       widget=forms.CheckboxSelectMultiple())
    readable = fields.BooleanField(required=False, initial=True)

    def __init__(self, text_choices=None, *args, **kwargs):
        """
        Constructor.
        :param text_choices: The choices for the texts.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        if text_choices:
            self.fields["texts"].choices = [(text, text) for text in text_choices]