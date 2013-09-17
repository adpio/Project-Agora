from django import forms
from democracy.models import Org, Body, GenericToDo, Document, Vote
from django.contrib.auth.models import User
from bootstrap_toolkit.widgets import BootstrapDateInput, BootstrapTextInput, BootstrapUneditableInput
from timedelta.widgets import TimedeltaWidget
from democracy.widgets import AdvancedFileInput


class OrgModelForm(forms.ModelForm):
	logo = forms.ImageField(widget=AdvancedFileInput)
	class Meta:
		model = Org
		exclude = ('members', 'users')


class UserModelForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ('first_name', 'last_name', 'email', 'password')

class BodyModelForm(forms.ModelForm):

	class Meta:
		model = Body
		widgets = {
			'date_start' : BootstrapDateInput(),
			'duration' : TimedeltaWidget(),
		}
		exclude = ('is_solitary')

class GenericToDoModelForm(forms.ModelForm):
	class Meta:
		model = GenericToDo
		widgets = {
			'review_result' : BootstrapUneditableInput(),
			'date_due' : BootstrapDateInput(),
		}
		exclude = ('date_created', 'owner', 'creator', 'owner', 'assigned_members','ready_for_review','review_result')

class DocumentForm(forms.ModelForm):
	class Meta:
		model = Document
		exclude = ('uploaded_by', 'date_created', 'generictodo', 'assigned_members')

class VoteModelForm(forms.ModelForm):
	class Meta:
		model = Vote




