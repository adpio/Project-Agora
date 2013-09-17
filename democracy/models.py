from django.db import models
from django.contrib.auth.models import User
import timedelta
from django.core.exceptions import ValidationError
from datetime import datetime
from django_countries import CountryField

def validate_0_to_100(value):
	if value > 100 or value <=0:
		raise ValidationError(u'You enetered %s. It has to be 0 - 100 range.' % value)

class UserProfile(models.Model):
	avatar = models.ImageField(upload_to='user_avatars/')
	user = models.OneToOneField(User)
	country = CountryField()
	sex = models.IntegerField(choices=((1,'Male'),(2,'Female')))
	birthday = models.DateField()

class Org(models.Model):
	name = models.CharField(max_length=60)
	description = models.TextField()
	country = CountryField()
	date_created = models.DateField(auto_now_add=True)
	logo = models.ImageField(upload_to='logos/%Y/%m/%d/', default='mocks/non-profit.jpg')
	#org's global constitution defs:
	#qourum for voting and reviewing
	users = models.ManyToManyField(User, through='Member', blank=True, null=True,)
	quorum = models.IntegerField(
		validators=[validate_0_to_100],
		help_text='Enter a number from 0 to 100. 100 means that all members have to vote in order to pass a motion',
		)
	#amount of time for voting
	global_voting_period = timedelta.fields.TimedeltaField(
		help_text="How much time do you allow members to vote. If a user does not vote within this limit he or she will be punished. Enter 3 days or 5 weeks or 12 months etc. <strong>Years are not allowed. For 1 year just enetr 12 months</strong>"
		)
	has_admissions = models.BooleanField(
		help_text='If marked, this org will have a body which admits and expels members.'
		)
	has_badging_body = models.BooleanField(
		help_text='If marked this body will have a special coucil which awards and creates badges to reward members for special acomplisments and punishes with negative badges',
		)
	associated_members_can_view = models.BooleanField(
		help_text='If marked, associated members can see everything'
		)
	rolling_voting = models.BooleanField(
		help_text='If marked, users will be able to vote for candidates even if there is no vote in progress')

	def is_member(self, user):
		if user in self.users:
			return True
		else:
			return False

	def get_member(self, user):
		try:
			return self.member_set.get(user=user)
		except:
			return False


	def add_member(self, user, type):
		m = Member()
		m.org = self
		m.user = user
		m.membership_type = type
		m.save()
		if type >= 1:
			self.body_set.get(is_general_assembly=True).add_member(m)
		return m

	#for sanity
	def __unicode__(self):
		return u'org %s' %(self.name)

class Member(models.Model):

	MEMBERSHIP_TYPES = (
		(0,'associated'),
		(1,'member'),
		(2,'creator'),
		(3,'almighty'),
		(-1,'declined'),
		(-2,'expelled'),
		(-3,'banned')
		)
	user = models.ForeignKey(User)
	org = models.ForeignKey(Org)
	date_created = models.DateField(auto_now_add=True)
	date_last_update = models.DateField(auto_now=True)
	membership_type = models.IntegerField(max_length=1, choices=MEMBERSHIP_TYPES, default=0)
	#for sanity
	def __unicode__(self):
		return u'member %s %s' %(self.user.first_name , self.user.last_name)
	def _get_membership_type_name(self):
		m = self.membership_type
		return u'%s' %(MEMBERSHIP_TYPES[m])

	class Meta:
		unique_together = (('user','org'))

	def works_in(self, body):
		if self in body.members.all():
			return True
		else:
			return False

	def is_candidating(self, body):
		
		try:
			if self.candidate_set.get(body=body):
				return True
		except:
			return False

	def get_candidate(self, body):
		try:
			return self.candidate_set.get(body=body)
		except:
			return []

class Body(models.Model):
	name = models.CharField(max_length=30, help_text='Name of the body')
	date_created = models.DateField(auto_now_add=True)
	org = models.ForeignKey(Org)
	#for single member bodies ie. president
	is_solitary = models.BooleanField(help_text='If checked this body will have only one member')
	member_count = models.PositiveIntegerField(help_text='Enter a positive integer. <strong>For solitary body just enter 1</strong>')
	members = models.ManyToManyField('Member', blank=True, null=True, help_text='Choose members who will constitute this body.<br/>')
	logo = models.ImageField(upload_to='body_logos/', blank=True, null=True, default='mocks/m.jpg')
	reviewer = models.ForeignKey(
		'Body', 
		blank=True, 
		null=True, 
		help_text='Choose <strong>another</strong> body which will be reviewing this body\'s performance. Think of it as a direct supervisor.',
		related_name='bodies_to_review',
		)
	#cadency duration
	date_start = models.DateField(help_text="First day of body's term", default=datetime.now())
	is_perpetual = models.BooleanField(
		help_text = 'If marked, this body will never expire'
		)
	duration = timedelta.fields.TimedeltaField(
		help_text="Input term duartion ex: 3 days, 5 weeks. <strong>Months and years are not allowed. Ie: for 1 year just enetr 52 weeks</strong>",
		blank=True, 
		null=True, 
		)
	voting_enabled = models.BooleanField(
		help_text='If marked, candidating and voting on will be enabled for this body'
		)
	voting_body = models.ForeignKey(
		'Body',
		 blank=True,
		 null=True, 
		 help_text='Choose a another which will be electing members of this body',
		 related_name='bodies_to_vote_on')
	is_admissions = models.BooleanField(default=False, help_text="if marked this body will have rights to admit and expel members")
	is_badging = models.BooleanField(default=False, help_text="If marked this body will have rights to design and award badges")
	is_general_assembly = models.BooleanField(default=False)

	@property
	def date_finish(self):
		return self.date_start + self.duration
	#adding members
	def add_member(self, member):
		if self.member_count == 0:
			self.members.add(member)
		else:
			if self.is_solitary:
				if self.members.count() >= 1:
					raise Exception("This is a solitary body")
				else:
					self.members.add(member)

			elif self.members.count() >= self.member_count:
				raise Exception("Too many members in this body")
			else:
				self.members.add(member)

		

	#election mechanism
	def create_election(self):
		e = Election(
			poll_type = 2,
			description = ('election time for %s'%self.name),
			voting_body = self.voting_body,
			voting_target = self,
			date_start = datetime.now(),
			date_finish = datetime.now() + self.org.global_voting_period,
			)
		e.save()
		for c in self.candidate_set.all():
			e.choice_set.create(
				choice=('candidate name %s'%c.member.user.id),
				candidate = c
				)		

	#for sanity
	def __unicode__(self):
		return u'body %s' %(self.name)

class Candidate(models.Model):
	member = models.ForeignKey(Member)
	body = models.ForeignKey(Body)
	votes = models.IntegerField(default=0)

class GenericToDo(models.Model):
	#general props
	PRIORITY_TYPES = (
		(1,'low'),
		(2,'medium'),
		(3,'critical')
		)
	title = models.CharField(max_length=30)
	content = models.TextField()
	priority = models.IntegerField(max_length=1, choices=PRIORITY_TYPES)
	#review props
	RECURSIVE_TYPES=(
		('d','daily'),
		('w','weekly'),
		('m','monthly'),
		('q','quarterly'),
		('a','annualy')
		)
	ready_for_review = models.BooleanField(default=False)
	review_result = models.NullBooleanField()
	creator = models.ForeignKey(Member)
	owner = models.ForeignKey(Body, related_name = 'my_todos')
	reviewer = models.ForeignKey(Body, related_name = 'todos_to_review')
	date_created = models.DateField(auto_now_add=True)
	date_due = models.DateField()
	is_recursive = models.BooleanField()
	recursivity = models.CharField(max_length=1,default=None,choices=RECURSIVE_TYPES)
	assigned_members = models.ManyToManyField(Member, blank=True, null=True, related_name='my_todos')
	

	#for sanity
	def __unicode__(self):
		return self.title

	def member_is_assigned(self,member):
		if member in self.assigned_members.all():
			return True
		else:
			return False

	def add_or_remove_assigned_member(self, member):
		#chek if member belongs to the org. Just to be sure.
		if member in self.owner.org.member_set.all():
			if member in self.assigned_members.all():
				self.assigned_members.remove(member)
				self.save()
			else:
				self.assigned_members.add(member)
				self.save()
				
		else:
			pass


	def review(self):
		if self.ready_for_review:
			p = Review(
				poll_type=1, 
				description='just answer, yo', 
				voting_body=self.reviewer, 
				voting_target=self, 
				in_progress=True, 
				date_start = datetime.now(),
				date_finish = datetime.now() + self.owner.org.global_voting_period,
				)
			p.save()
			c1 = Choice(poll=p, choice='Accept', value=True)
			c2 = Choice(poll=p, choice='Decline acceptance', value=False)
			c3 = Choice(poll=p, choice='Abstain', value=None)
			c1.save()
			c2.save()
			c3.save()

class Document(models.Model):
	generictodo = models.ForeignKey(GenericToDo)
	docfile = models.FileField(upload_to='evidence/%Y/%m/%d/')
	date_created = models.DateTimeField(auto_now_add=True)
	uploaded_by = models.ForeignKey(Member)
	name = models.CharField(max_length=255, help_text='provide some description')

	@property
	def file_ext(self):
		return self.docfile.name.split('.').pop(-1)

class Poll(models.Model):
	POLL_TYPES = (
	(1,'review'),
	(2,'election'),
	(3,'admit_member')
	)
	date_start = models.DateTimeField(default=datetime.now())
	date_finish = models.DateTimeField()
	date_created = models.DateTimeField(auto_now_add=True)
	in_progress = models.BooleanField(default=False)
	poll_type = models.IntegerField(max_length=1, choices=POLL_TYPES)
	description = models.TextField(blank=True)
	voting_body = models.ForeignKey(Body)

	def member_can_vote(self,member):
		if member in self.voting_body.members.all():
			return True
		else:
			return False

	def member_has_voted(self,member):
		if self.vote_set.filter(member=member).exists():
			return True
		else:
			return False

	def cast_recast_vote(self,member,choice):
		can_vote = member in self.voting_body.members.all()
		has_voted = self.vote_set.filter(member=member).exists()
		if can_vote and not has_voted:
			v = Vote(member=member,choice=choice)
			self.vote_set.add(v)
		elif can_vote and has_voted:
			v = self.vote_set.filter(member=member).get()
			v.choice = choice
			v.save()
		else:
			raise ValidationError("You can not vote!")
		
	
class Choice(models.Model):
	poll = models.ForeignKey(Poll)
	choice = models.CharField(max_length=255)
	value = models.NullBooleanField(blank=True, null=True)
	candidate = models.ForeignKey(Candidate, blank=True, null=True)

	def count_votes(self):
		return self.vote_set.count()

	#deprecated
	def cast_vote(self, member):
		has_voted = self.poll.vote_set.filter(member=member).exists()
		can_vote = member in self.poll.voting_body.members.all()
		if can_vote and not has_voted:
			#casting a new vote
			v = Vote()
			v.member = member
			v.poll = self.poll
			v.choice = self
			try:
				v.save()
			except Exception, e:
				raise e
		elif can_vote and has_voted:
			pass
		else:
			raise ValidationError(u'You are not allowed to vote on this')

	def __unicode__(self):
		return self.choice

	class Meta:
		ordering = ['choice']

class Vote(models.Model):
	#used for boolean reviews
	def _get_value(self):
		return self.choice.value
	#used for multiple model choice ie. elections
	def _get_candidate(self):
		return self.choice.candidate

	member = models.ForeignKey(Member)
	poll = models.ForeignKey(Poll)
	choice = models.ForeignKey(Choice)
	value = property(_get_value)



	def __unicode__(self):
		return u'vote for %s' %(self.choice)




class Review(Poll):
	voting_target = models.ForeignKey(GenericToDo)
	result = models.NullBooleanField(blank=True, null=True, default=None)
	def _get_result(self):
		#count votes
		yes = 0
		no = 0
		total_votes = self.vote_set.count()
		eligible_voters = self.voting_body.members.count()
		quorum = self.voting_body.org.quorum
		for v in self.vote_set.all():
			if v.choice.value:
				yes += 1
			else:
				no += 1

		#check if quorum is satisfied
		if ((total_votes.__float__()/eligible_voters.__float__())*100 > quorum):
			if yes >= no:
				self.result = True
			else:
				self.result = False
			self.result.save()
		else:
			return False

class Election(Poll):
	voting_target = models.ForeignKey(Body)



	def start_election(self):
		if not self.voting_target.election_set.filter(in_progress = True):
			self.in_progress = True
			self.save()
		else:
			raise ValidationError(u'An election is already in progress')

	def _get_results(self):
		total_votes = self.vote_set.count()
		eligible_voters = self.voting_body.members.count()
		quorum = self.voting_body.org.quorum
		member_count = self.voting_target.member_count
		#reseting number of vites to 0
		for c in self.choice_set.all():
			c.candidate.votes = 0
			c.candidate.save()
		#recounting votes
		for v in self.vote_set.all():
			v.choice.candidate.votes += 1
			v.choice.candidate.save()
		#changing body members
		if (total_votes*100/eligible_voters > quorum):
			 new_set = self.voting_target.candidate_set.order_by('votes')[:member_count]
			 self.voting_target.members.clear()
			 for c in new_set.all():
			 	self.voting_target.members.add(c.member)

class AdmissionProcess(Poll):
	voting_target = models.ForeignKey(Member)

	def admit_member(self, member):
		if member in self.voting_body.org.members.all() and member.membership_type == 0 and self.voting_body.is_admissions:
			member.membership_type = 1
			member.save()
			try:
				member.body_set.filter(is_general_assembly=True).get().members.add(member)
			except Exception, e:
				raise e
		else:
			raise ValidationError('admission err: member not valid')

	def expel_member(self,member):
		if member in self.voting_body.org.members.all() and member.membership_type >= 1 and self.voting_body.is_admissions:
			member.membership_type = 0
			member.save()
		else:
			raise ValidationError('expel err: member not valid')





	







