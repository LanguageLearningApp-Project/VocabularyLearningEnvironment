from django import forms
from .models import Member, StudySession, VocabularyList

class MemberForm(forms.ModelForm):
  class Meta:
    model = Member
    fields = ["user_name", "password"]
    
class StudySessionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None) 
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["vocabulary_list"].queryset = VocabularyList.objects.filter(user=user)
            
        self.fields["name"].widget.attrs["placeholder"] = "Session name"
        self.fields["goal_value"].widget.attrs["placeholder"] = "Goal value"
        self.fields["start_date"].widget.attrs["placeholder"] = "Start date"
        self.fields["end_date"].widget.attrs["placeholder"] = "End date"

    class Meta:
        model = StudySession
        fields = ["name", "vocabulary_list", "goal_type", "goal_value", "start_date", "end_date", "is_active"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

