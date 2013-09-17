# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from django.shortcuts import render, get_object_or_404
from democracy.models import Org, Body, Member, GenericToDo, Candidate, Election, Document, UserProfile, Choice, Review, AdmissionProcess 
from django.db.models import Count
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from datetime import datetime
from django import forms
from forms import OrgModelForm, UserModelForm, BodyModelForm, GenericToDoModelForm, DocumentForm, VoteModelForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm




def index(request):
	most_popular_orgs_list = Org.objects.annotate(num_member=Count('member')).order_by('-num_member')[:10]
	orgs_by_countries = Org.objects.values('country').annotate(Count('country')).order_by()
	users_by_countries = UserProfile.objects.values('country').annotate(Count('country')).order_by()
	users_by_sex = UserProfile.objects.values('sex').annotate(Count('sex')).order_by()
	context = { 
		'most_popular_orgs_list' : most_popular_orgs_list,
		'orgs_by_countries' : orgs_by_countries,
		'users_by_sex' : users_by_sex,
		'users_by_countries' : users_by_countries,
		}
	return render(request, 'democracy/index.html', context)

def login_view(request):
	if request.method == 'POST':
		if request.POST['what_to_do'] == 'login':
			username = request.POST['username']
			password = request.POST['password']
			user = authenticate(username=username, password=password)
			if user is not None:
				if user.is_active:
					login(request, user)

					return HttpResponseRedirect(request.POST['next'])
				else:
					return True
			else:
				return True
		if request.POST['what_to_do'] =='register':
			form = UserCreationForm(request.POST)
			if form.is_valid():
				f = form.save()
				#new_user = User.objects.get(username=request.POST['username'])
				#username = new_user.username
				#password = new_user.password
				#user = authenticate(username=username, password=password)
				#login(request, user)
				messages.success(request, 'All went OK. You may now login!')
				return HttpResponseRedirect(reverse('index'))
			else:
				messages.error(request, form.errors)
				return HttpResponseRedirect(reverse('index'))
	elif request.method =='GET':
		logout(request)
		return HttpResponseRedirect(reverse('index'))

@login_required
def profile(request):
	u = request.user
	context = {'user':u,}
	return render(request, 'democracy/profile.html', context)

@login_required
def org_detail(request, org_id):
	org = get_object_or_404(Org, pk=org_id)
	member = org.get_member(request.user)
	return render(request, 'democracy/org_detail.html',{'org':org,'member':member})

@login_required
def body_detail(request, org_id, body_id):
	body = get_object_or_404(Body, pk=body_id)
	org = get_object_or_404(Org, pk=org_id)
	member = org.get_member(request.user)
	candidate = member.get_candidate(body)
	is_working_here = member.works_in(body)
	election = body.election_set.all()
	context = {'body' : body, 'org' : org, 'member':member, 'candidate':candidate, 'is_working_here':is_working_here, 'election':election}
	return render(request, 'democracy/body_detail.html', context)

@login_required
def election_detail(request, org_id, body_id, election_id):
	user = request.user
	body = get_object_or_404(Body, pk=body_id)
	org = get_object_or_404(Org, pk=org_id)
	member = org.get_member(user)
	election = get_object_or_404(Election, pk=election_id)
	member_can_vote = election.member_can_vote(member)
	member_has_voted = election.member_has_voted(member)
	if request.method == 'POST':
		#validation is handled at the model
		choice = get_object_or_404(Choice, pk=request.POST['choice'])
		election.cast_recast_vote(member, choice)
		return HttpResponseRedirect(reverse('body_detail', args=[org.id, body.id]))
	else:
		context = {'election':election, 'member':member, 'member_can_vote': member_can_vote, 'member_has_voted': member_has_voted, }
		return render(request, 'democracy/election_detail.html', context)

@login_required
def form_org(request):
	if request.method == 'POST': # If the form has been submitted...
		form = OrgModelForm(request.POST, request.FILES) # A form bound to the POST data
		if form.is_valid(): # All validation rules pass
			o = form.save()
			u = request.user
			b = o.body_set.create(
				name = 'General Assembly',
				member_count = 0,
				duration = 0,
				voting_enabled = False,
				is_perpetual = True,
				is_general_assembly = True,
				)
			m = o.add_member(u, '2')
			b.members.add(m)
			#create admissions
			if o.has_admissions:
				adm = o.body_set.create(name='Admissions', member_count=0, duration='4 weeks', is_admissions=True, voting_body=b, reviewer=b)
				adm.members.add(m)
			#create badging body
			if o.has_badging_body:
				bedg = o.body_set.create(name='Badging and Awards', member_count=0, duration='4 weeks', is_badging=True, voting_body=b, reviewer=b)				
				bedg.members.add(m)
			#make creator president for a month
			p = o.body_set.create(name='President', member_count=1, duration='12 weeks', is_solitary=True, voting_body=b, reviewer=b, voting_enabled=True)
			p.members.add(m)
			messages.success(request, 'You have successfuly created your org! Good luck!')
			return HttpResponseRedirect(reverse('org_detail', args=[o.id]))
		else:
			return form.errors
	layout = request.GET.get('layout')
	if not layout:
		layout = 'horizontal'
 
	form = OrgModelForm()
	return render_to_response('democracy/form_org.html', RequestContext(request, {
		'form': form,
		'layout': layout,

	}))

@login_required
def form_user(request):
	layout = request.GET.get('layout')
	if not layout:
		layout = 'horizontal'
 
	form = UserModelForm()
	return render_to_response('democracy/form_register_user.html', RequestContext(request, {
		'form': form,
		'layout': layout,
		}))

@login_required
def form_body(request, org_id):
	org = get_object_or_404(Org, pk=org_id)
	#for POST
	if request.method == 'POST':
		data = request.POST.copy()
		data['org'] = org.id
		form = BodyModelForm(data, request.FILES)
		if form.is_valid():
			#validate members
			m = form.cleaned_data['members']
			if m.count() > form.cleaned_data['member_count'] and form.cleaned_data['member_count'] != 0:
				raise ValidationError(u'Too many members selected')
			b = form.save()
			#resolving hidden input for this field
			if b.member_count == 1:
				b.is_solitary = True
			else:
				b.is_solitary = False
			b.save()
			#saving m2m relationship:
			for x in m:
				b.members.add(x)

			
			return HttpResponseRedirect(reverse('body_detail', args=[org.id, b.id]))
		else:
			return form.errors
	#for GET
	layout = request.GET.get('layout')
	if not layout:
		layout = 'horizontal'
	
	form = BodyModelForm()

	form.fields['members'].queryset = org.member_set.all()
	form.fields['reviewer'].queryset = org.body_set.all()
	form.fields['voting_body'].queryset = org.body_set.all()
	form.fields['org'].widget = forms.HiddenInput()
	template_vars = RequestContext(request,{
		'form': form,
		'layout' : layout,
		'org' : org
		})
	#always return something
	return render_to_response('democracy/form_body.html', template_vars)

@login_required
def form_todo(request, body_id, org_id):
	body = get_object_or_404(Body, pk=body_id)
	org = get_object_or_404(Org, pk=org_id)
	user = request.user
	member = org.get_member(user)
	#for POST
	if request.method == 'POST':
		form = GenericToDoModelForm(request.POST)
		if form.is_valid():
			t = GenericToDo()
			t.title = form.cleaned_data['title']
			t.content = form.cleaned_data['content']
			t.priority = form.cleaned_data['priority']
			t.date_due = form.cleaned_data['date_due']
			t.recursivity = form.cleaned_data['recursivity']
			t.reviewer = form.cleaned_data['reviewer']
			t.owner = body
			#TODO 
			t.creator = member
			t.save()
			return HttpResponseRedirect(reverse('body_detail', args=[org.id, body.id]))

	layout = request.GET.get('layout')
	if not layout:
		layout = 'horizontal'
	form = GenericToDoModelForm()
	form.fields['reviewer'].queryset = body.org.body_set.all()

	template_vars = RequestContext(request,{
		'form': form,
		'layout' : layout,
		'body' : body
		})
	#always return something
	return render_to_response('democracy/form_todo.html', template_vars)	

@login_required
def todo_detail(request, org_id, body_id, todo_id):
	org = get_object_or_404(Org, pk=org_id)
	body = get_object_or_404(Body, pk=body_id)
	todo = get_object_or_404(GenericToDo, pk=todo_id)
	user = request.user
	member = org.get_member(user)
	# Handle file upload
	if request.method == 'POST':
		form = DocumentForm(request.POST, request.FILES)
		if form.is_valid():
			newdoc = Document(docfile = request.FILES['docfile'], uploaded_by = member, generictodo = todo, name = form.cleaned_data['name'])
			newdoc.save()

			# Redirect to the document list after POST
			return HttpResponseRedirect(reverse('todo_detail', args=[org.id, body.id, todo.id]))
	else:
		form = DocumentForm() # A empty, unbound form

	# Load documents for the list page
	documents = todo.document_set.all()

	#get layout for bootstrap
	layout = request.GET.get('layout')
	if not layout:
		layout = 'horizontal'

	# Render list page with the documents and the form
	return render_to_response(
		'democracy/todo_detail.html',
		{'documents': documents, 
		'form': form,
		'org': org,
		'body': body,
		'todo': todo,
		'layout': layout},
		context_instance=RequestContext(request)
	)

@login_required
def associate(request, org_id):
	user = request.user
	org = get_object_or_404(Org, pk=org_id)
	if org.has_admissions:
		m = org.add_member(user, '0')
		b = org.body_set.filter(is_admissions=True).get()
		p = AdmissionProcess(
			voting_target=m,
			poll_type=3, 
			voting_body=b, 
			in_progress=True, 
			date_start = datetime.now(),
			date_finish = datetime.now() + org.global_voting_period,
			)
		p.save()
		c1 = Choice(poll=p, choice='Accept', value=True)
		c2 = Choice(poll=p, choice='Decline acceptance', value=False)
		c3 = Choice(poll=p, choice='Abstain', value=None)
		c1.save()
		c2.save()
		c3.save()
	else:
		org.add_member(user, '1')
	return HttpResponseRedirect(reverse('org_detail', args=[org.id]))

@login_required
def add_candidate(request, org_id, body_id):
	user = request.user
	org = get_object_or_404(Org, pk=org_id)
	body = get_object_or_404(Body, pk=body_id)
	member = org.get_member(user)
	if not member.is_candidating(body):
		c = Candidate()
		c.member = member
		c.body = body
		c.save()
		return HttpResponseRedirect(reverse('body_detail', args=[org.id, body.id]))



@login_required
def create_election(request, org_id, body_id):
	org = get_object_or_404(Org, pk=org_id)
	body = get_object_or_404(Body, pk=body_id)
	body.create_election()
	return HttpResponseRedirect(reverse('body_detail', args=[org.id, body.id]))

@login_required
def start_election(request, org_id, body_id, election_id):
	e = get_object_or_404(Election, pk=election_id)
	try:
		e.start_election()
	except:
		return False

@login_required
def review_detail(request, org_id, body_id, todo_id):
	user = request.user
	org = get_object_or_404(Org, pk=org_id)
	member = org.get_member(user)
	todo = get_object_or_404(GenericToDo, pk=todo_id)

	#return func values for template
	for r in todo.review_set.all():
		r.member_has_voted = r.member_has_voted(member)
		r.member_can_vote = r.member_can_vote(member)


	#for reviewing		
	if request.method == 'POST':
		review = get_object_or_404(Review, pk=request.POST['review_id'])
		choice = get_object_or_404(Choice, pk=request.POST['choice'])
		try:
			review.cast_recast_vote(member, choice)
			messages.success(request, "Your review vote has been successfuly casted")
			return HttpResponseRedirect(reverse('todo_detail', args=[org_id, body_id, todo_id]))
		except Exception, e:
			
			messages.error(request, "%s"%e)
		

	context = {'todo' : todo, 'member':member,}
	return render(request, 'democracy/review_detail.html', context)

@login_required
def admission_detail(request, org_id, body_id):
	user = request.user
	org = get_object_or_404(Org, pk=org_id)
	body = get_object_or_404(Body, pk=body_id)
	member = org.get_member(user)
	#if body.is_admissions and member in body.members.all():
	if request.method == 'POST':
		admissionprocess = get_object_or_404(AdmissionProcess, pk=request.POST['adm_id'])
		choice = get_object_or_404(Choice, pk=request.POST['choice'])
		try:
			admissionprocess.cast_recast_vote(member, choice)
			messages.success(request, "Your admission vote has been successfuly casted")
		except Exception, e:
			
			messages.error(request, "%s"%e)
			
	adm = body.poll_set.filter(admissionprocess__in_progress = True)
	vote_states = []
	for a in adm:
		if a.vote_set.filter(member=member).exists():
			vote_states.append('%s'%a.vote_set.get(member=member).value)
		else:
			vote_states.append('Not voted yet')
	list = zip(adm,vote_states)
	context = {'list':list,'member':member }
	return render(request, 'democracy/admission_detail.html', context)








	







