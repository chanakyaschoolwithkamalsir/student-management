from django import forms
from .models import StudentTestResults

class StudentTestResultsForm(forms.ModelForm):
    class Meta:
        model = StudentTestResults
        fields = ['student_id', 'test_id', 'obtained']