from django import forms
from .models import Checklist

class UploadForm(forms.Form):
    file = forms.FileField(label='Select Excel (.xlsx/.xls/.csv)', widget=forms.ClearableFileInput(attrs={'class':'form-control'}))
    source = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Source'}))

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['excel','status','note','scheduled_at']
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={'type':'datetime-local','class':'form-control'}),
            'note': forms.Textarea(attrs={'rows':3,'class':'form-control'}),
            'status': forms.Select(attrs={'class':'form-control'}),
            'excel': forms.Select(attrs={'class':'form-control'}),
        }
