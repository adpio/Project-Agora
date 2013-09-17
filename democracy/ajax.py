from democracy.models import *
from dajaxice.decorators import dajaxice_register
from dajax.core import Dajax
from django.utils import simplejson


@dajaxice_register
def assign_member(request, m_id, todo_id):
	dajax = Dajax()
	todo = GenericToDo.objects.get(id=todo_id)
	member = Member.objects.get(id=m_id)
	member_id = str('#member_%s'%(m_id))

	if todo.member_is_assigned(member):
		todo.add_or_remove_assigned_member(member)
		dajax.remove_css_class(member_id, 'label-success')

		msg = {
			"atrib":"alert-info",
			"message":"<i class=\"icon-bullhorn\"></i> You have just unassigned a member to this todo. We will inform him."
		}
		dajax.script('showmsg(%s);'%msg)		
	else:
		todo.add_or_remove_assigned_member(member)
		dajax.add_css_class(member_id, 'label-success')
		msg = {
			"atrib":"alert-success",
			"message":"<i class=\"icon-bullhorn\"></i> You have just assigned a member to this todo. We will inform him."
		}
		dajax.script('showmsg(%s);'%msg)	
	return dajax.json()

@dajaxice_register
def flip_task_completion(request, todo_id):
	dajax = Dajax()
	t = GenericToDo.objects.get(id=todo_id)
	#chack task state
	if not t.ready_for_review:
		t.ready_for_review = True
		t.save()
		t.review()
		msg = {
			"atrib":"alert-success",
			"message":"<i class=\"icon-bullhorn\"></i> You marked this task as completed. Your reviewer body has been informed"
		}
		dajax.script('showmsg(%s);'%msg)
		dajax.script('$(\'#review_state\').fadeIn();')
	else:
		t.ready_for_review = False
		t.save()
		msg = {
			"atrib":"alert-warning",
			"message":"<i class=\"icon-bullhorn\"></i> Task has been marked as not completed"
		}
		dajax.script('showmsg(%s);'%msg)
		dajax.script('$(\'#review_state\').fadeOut();')
	return dajax.json()






