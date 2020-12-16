import ast

from django import forms
from django.forms.widgets import RadioSelect, Textarea, CheckboxSelectMultiple


class MCQuestionForm(forms.Form):
    def __init__(self, question, selected_answers=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choice_list = [x for x in question.get_answers_list()]
        if selected_answers:
            selected_answers = ast.literal_eval(selected_answers)

        if (
            hasattr(question, "allow_multiple_answers")
            and question.allow_multiple_answers
        ):
            # show checkboxes
            self.fields["answers"] = forms.MultipleChoiceField(
                choices=choice_list,
                widget=CheckboxSelectMultiple,
                initial=selected_answers,
            )
        else:
            # only a single answer is possible, show radio buttons
            self.fields["answers"] = forms.ChoiceField(
                choices=choice_list,
                widget=RadioSelect,
                initial=selected_answers,
            )


class EssayForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(EssayForm, self).__init__(*args, **kwargs)
        self.fields["answers"] = forms.CharField(
            widget=Textarea(attrs={"style": "width:100%"})
        )
