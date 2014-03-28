from django.db import models
from django.contrib.auth.models import User

class Player(models.Model):
   user = models.OneToOneField(User)
   facebook_id = models.CharField(max_length = 256)
   facebook_oauth_token = models.CharField(max_length = 256)
   linkedin_id = models.CharField(max_length = 256)
   linkedin_oauth_token = models.CharField(max_length = 256)
   lastfm_id = models.CharField(max_length = 256)
   lastfm_oauth_token = models.CharField(max_length = 256)
   twitter_id = models.CharField(max_length = 256)
   twitter_oauth_token = models.CharField(max_length = 256)
   twitter_oauth_token_secret = models.CharField(max_length = 256)
   gplus_id = models.CharField(max_length = 256)
   gplus_oauth_token = models.CharField(max_length = 256)
   gplus_oauth_refresh_token = models.CharField(max_length = 256)
   flickr_id = models.CharField(max_length = 256)
   flickr_oauth_token = models.CharField(max_length = 256)
   flickr_oauth_token_secret = models.CharField(max_length = 256)

class FacebookEdge(models.Model):
   source = models.CharField(max_length = 256)
   target = models.CharField(max_length = 256)

class LinkedinEdge(models.Model):
   source = models.CharField(max_length = 256)
   target = models.CharField(max_length = 256)

class LastfmEdge(models.Model):
   source = models.CharField(max_length = 256)
   target = models.CharField(max_length = 256)

class TwitterEdge(models.Model):
   source = models.CharField(max_length = 256)
   target = models.CharField(max_length = 256)

class GplusEdge(models.Model):
   source = models.CharField(max_length = 256)
   target = models.CharField(max_length = 256)

class FlickrEdge(models.Model):
   source = models.CharField(max_length = 256)
   target = models.CharField(max_length = 256)
