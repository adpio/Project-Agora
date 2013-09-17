"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from mockups import Mockup
from democracy.models import *
from django.contrib.auth.models import User

Mockup(User).create(1000)
Mockup(Org).create(60)

Mockup(Body).create(300)
Mockup(Member).create(2000)
Mockup(Candidate).create(1000)

Mockup(GenericToDo).create(900)
Mockup(UserProfile).create(1000)





