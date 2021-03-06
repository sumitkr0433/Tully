#-*- coding:utf-8 -*-
from django.db import models

# Create your models here.
from django.db import models
# Create your models here.
from django.contrib.auth.models import User
from userena.models import UserenaBaseProfile
from userena.managers import UserenaBaseProfileManager
from userena.managers import UserenaManager
from friendship.models import Friend,Follow
#from bookmark.models import Tag,Bookmark
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.base import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from userena.models import UserenaBaseProfile
import datetime


class ProfileManager(UserenaBaseProfileManager):
    '''
    def get_fans_list(self,**kwargs):
        username = kwargs.get('username',None)
        ex_username = kwargs.get('ex_username',None)
        if ex_username:
            try:
                user = User.objects.get(username = ex_username)
            except ObjectDoesNotExist:
                user = None
        else :
            try:
                user = User.objects.get(username = username)
            except ObjectDoesNotExist:
                user = None
        if user:
            fans = user.friend_set.all()
            if fans.count() > 0:
                return ({'user':item.to_friend,'info':self.get_info(username = username,ex_username = item.to_friend.username)
                                               } for item in fans) 
    '''  
    '''
    def get_follows_list(self,**kwargs):
        username = kwargs.get('username')
        ex_username = kwargs.get('ex_username')
        if kwargs.has_key('ex_username'):
            try:
                user = User.objects.get(username = ex_username)
            except ObjectDoesNotExist:
                user = None
        else:
            try:
                user = User.objects.get(username = username)
            except ObjectDoesNotExist:
                user = None
        if user:
            follows = user.to_friend_set.all()
            if follows.count() > 0:
                return ({'user':item.from_friend,'info':self.get_info(username = username,ex_username = item.from_friend.username)} for item in follows)
    '''

    #共同关注
    def get_same_follows_list(self,**kwargs):
        if kwargs.has_key('username') and kwargs.has_key('ex_username'):
            username,ex_username = [item for item in kwargs.itervalues()]
            list1 = Friend.objects.get(to_user=username)
            list2 = Friend.objects.get(to_user=ex_username)
            same_follows = ({'user':item,'info':self.get_info(username = username,ex_username = item.username)} for item in list1 if item in list2 )
            if len(list(same_follows)) >0 :
                return same_follows
        else:
            pass

    #我关注的人也关注他
    def get_second_follows_list(self,**kwargs):
        if kwargs.has_key('username') and kwargs.has_key('ex_username'):
            username,ex_username = [item for item in kwargs.itervalues()]
            list1 = Follow.objects.get(follower=username)
            list2 = Follow.objects.get(follower=ex_username)
            second_follows = ({'user':item,'info':self.get_info(username = username,ex_username = item.username)} for item in list1 if item in list2)
            if len(list(second_follows)) > 0:
                return second_follows
        else:
            pass
    
    def get_profile_list(self,userlist):
        profile_list =[]
        for user in userlist:
            if user:
                profile=Profile.objects.get(user=user)
                profile_list.append(profile)
        return profile_list



class Profile(UserenaBaseProfile):
    """ Default profile """
    GENDER_CHOICES = (
        (1, _('Male')),
        (2, _('Female')),
    )

    user = models.OneToOneField(User,
                                unique=True,
                                verbose_name=_('user'),
                                related_name='profile')
    favourite_snack = models.CharField(_('favourite snack'),
                                       max_length=5)

    gender = models.PositiveSmallIntegerField(_('gender'),
                                              choices=GENDER_CHOICES,
                                              blank=True,
                                              null=True)
    objects = ProfileManager()

     #django 1.3
    '''
    website = models.URLField(_('website'), blank=True, verify_exists=True)
    '''
    #django 1.6
    website = models.URLField(_('website'), blank=True)
    location =  models.CharField(_('location'), max_length=255, blank=True)
    birth_date = models.DateField(_('birth date'), blank=True, null=True)
    about_me = models.TextField(_('about me'), blank=True)

    @property
    def age(self):
        if not self.birth_date: return False
        else:
            today = datetime.date.today()
            # Raised when birth date is February 29 and the current year is not a
            # leap year.
            try:
                birthday = self.birth_date.replace(year=today.year)
            except ValueError:
                day = today.day - 1 if today.day != 1 else today.day + 2
                birthday = self.birth_date.replace(year=today.year, day=day)
            if birthday > today: return today.year - self.birth_date.year - 1
            else: return today.year - self.birth_date.year
           
    def is_fans(self,ex_username):
        username = self.user.username

        try:
            user_id = User.objects.get(username = username)
        except:
            user_id = None
        try:
            ex_id = User.objects.get(username = ex_username)
        except:
            ex_id = None
        if ex_id and user_id:
            try:
                return Follow.objects.follows(follower = user_id,followee = ex_id)
            except ObjectDoesNotExist:
                return False
        else:
            return False

    def is_follows(self,ex_username):
        username = self.user.username

        try:
            ex_id = User.objects.get(username = ex_username)
        except:
            ex_id = None
        try:
            id = User.objects.get(username = username)
        except:
            id = None
        if id and ex_id:
            try:
                return Follow.objects.follows(follower = ex_id,followee = id)
                
            except ObjectDoesNotExist:
                return False
        else:
            return False        


    def fans_follows(self,ex_username):
        pass


    def get_fans_count(self,ex_username):
        username = self.user.username

        if username:
            try:
                user = User.objects.get(username = username )
            except:
                user = None
        elif ex_username:
            try:
                user = User.objects.get(username = ex_username )
            except:
                user = None
        else:
            return 0
        
        #fans_count = user.friend_set.all().count()
        fans_count = Follow.objects.following(user).count()
        return fans_count
            
 
    def get_follows_count(self,ex_username):
        username = self.user.username
        
        if username:
            try:
                user = User.objects.get(username = username )
            except:
                user = None
        elif ex_username:
            try:
                user = User.objects.get(username = ex_username )
            except:
                user = None
        else:
            return 0
        
        follow_count = Follow.objects.followers(user).count()
        #follow_count = user.to_friend_set.all().count()
        return follow_count
    

    def get_info(self,ex_username):
        username = self.user.username

        return {'fans_count':self.get_fans_count(username = ex_username),
                'follows_count':self.get_follows_count(username = ex_username),
                'is_follows':self.is_follows(username = username,ex_username = ex_username),
                'is_fans':self.is_fans(username = username,ex_username = ex_username),
                #'tag_count':Tag.objects.user_tag_counts(ex_username),
                #'bookmark_count':Bookmark.objects.get_user_bookmark_count(ex_username),
                }            
    
      
    def __unicode__(self):
        return self.user.username








   
