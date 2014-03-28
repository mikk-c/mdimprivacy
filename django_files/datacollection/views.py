from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from models import *
import forms, json, urllib, urllib2, social_keys, hashlib, codecs, string, time, random, hmac, binascii

def home(request):
   facebook_id = None
   linkedin_id = None
   lastfm_id = None
   twitter_id = None
   gplus_id = None
   flickr_id = None
   if request.user.is_authenticated():
      authenticated = True
      form = None
      facebook_id = request.user.player.facebook_id
      linkedin_id = request.user.player.linkedin_id
      lastfm_id = request.user.player.lastfm_id
      twitter_id = request.user.player.twitter_id
      gplus_id = request.user.player.gplus_id
      flickr_id = request.user.player.flickr_id
   else:
      authenticated = False
      form = forms.LoginForm()
   return render_to_response("home.htm", {
      'username': request.user.username,
      'authenticated': authenticated,
      'form': form,
      'facebook_id': facebook_id,
      'linkedin_id': linkedin_id,
      'lastfm_id': lastfm_id,
      'twitter_id': twitter_id,
      'gplus_id': gplus_id,
      'flickr_id': flickr_id,
      'linkedin_app_id': social_keys.linkedin_api_key,
      'lastfm_app_id': social_keys.lastfm_api_key,
   }, context_instance = RequestContext(request))

def register(request):
   if request.method == 'POST':
      form = forms.RegisterForm(request.POST)
      if form.is_valid():
         user = User.objects.create_user(form.cleaned_data['username'], form.cleaned_data['email'], form.cleaned_data['password'])
         player = Player(user = user)
         player.save()
         return render_to_response("register.htm", {
           'username': form.cleaned_data['username'],
         }, context_instance = RequestContext(request))
   else:
      form = forms.RegisterForm()
   return render_to_response("register.htm", {
        'form': form,
   }, context_instance = RequestContext(request))

def system_login(request):
   authenticated = False
   if request.method == 'POST':
      form = forms.LoginForm(request.POST)
      if form.is_valid():
         user = authenticate(username = form.cleaned_data['username'], password = form.cleaned_data['password'])
         if user is not None:
            if user.is_active:
               authenticated = True
               login(request, user)
               return redirect(home)
            else:
               return render_to_response("home.htm", {
                  'error': "inactive",
                  'authenticated': authenticated,
                  'form': form,
               }, context_instance = RequestContext(request))
         else:
            return render_to_response("home.htm", {
               'error': "wrong_password",
               'authenticated': authenticated,
               'form': form,
            }, context_instance = RequestContext(request))

def system_logout(request):
   logout(request)
   return redirect(home)

@csrf_exempt
def facebook_player(request):
   if request.is_ajax():
      if request.method == 'POST':
         data = json.loads(request.raw_post_data)
         request.user.player.facebook_id = data["id"]
         qs = urllib.urlopen("https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s" % (social_keys.facebook_app_id, social_keys.facebook_app_secret, data["access_token"])).read()
         d = dict([x.split("=") for x in qs.split("&")])
         request.user.player.facebook_oauth_token = d["access_token"]
         request.user.player.save()
   return redirect(home)

@csrf_exempt
def linkedin_player(request):
   auth_code = request.GET.get('code', '')
   if auth_code != "":
      qs = urllib.urlopen("https://www.linkedin.com/uas/oauth2/accessToken?grant_type=authorization_code&client_id=%s&client_secret=%s&code=%s&redirect_uri=http://www.atlas.cid.harvard.edu/mdimprivacy/linkedin_player/" % (social_keys.linkedin_api_key, social_keys.linkedin_secret_key, auth_code)).read()
      d = json.loads(qs)
      request.user.player.linkedin_oauth_token = d["access_token"]
      qs = urllib.urlopen("https://api.linkedin.com/v1/people/~:(id)?oauth2_access_token=%s&format=json" % (d["access_token"])).read()
      d = json.loads(qs)
      request.user.player.linkedin_id = d["id"]
      request.user.player.save()
   return redirect(home)

@csrf_exempt
def lastfm_player(request):
   token = request.GET.get('token', '')
   if token != "":
      m = hashlib.md5("api_key%smethodauth.getSessiontoken%s%s" % (social_keys.lastfm_api_key, token, social_keys.lastfm_secret)).hexdigest()
      url = "http://ws.audioscrobbler.com/2.0/?method=auth.getSession&api_key=%s&token=%s&format=json&api_sig=%s" % (social_keys.lastfm_api_key, token, m)
      qs = urllib.urlopen(url).read()
      d = json.loads(qs)
      request.user.player.lastfm_oauth_token = d["session"]["key"]
      request.user.player.lastfm_id = d["session"]["name"]
      request.user.player.save()
   return redirect(home)

@csrf_exempt
def twitter_player(request):
   http_method = "POST"
   base_url = "https://api.twitter.com/oauth/access_token"
   oauth_consumer_key = social_keys.twitter_key
   oauth_nonce = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(32))
   oauth_signature_method = "HMAC-SHA1"
   oauth_timestamp = int(time.time())
   oauth_token = request.GET.get('oauth_token', '')
   oauth_verifier = request.GET.get('oauth_verifier', '')
   oauth_version = "1.0"
   parameter_string = "oauth_consumer_key=%s&oauth_nonce=%s&oauth_signature_method=%s&oauth_timestamp=%s&oauth_token=%s&oauth_verifier=%s&oauth_version=%s" % (urllib.quote_plus(oauth_consumer_key), urllib.quote_plus(oauth_nonce), urllib.quote_plus(oauth_signature_method), oauth_timestamp, urllib.quote_plus(oauth_token), urllib.quote_plus(oauth_verifier), urllib.quote_plus(oauth_version))
   signature_base_string = "%s&%s&%s" % (http_method, urllib.quote_plus(base_url), urllib.quote_plus(parameter_string))
   signing_key = "%s&%s" % (urllib.quote_plus(social_keys.twitter_secret), request.user.player.twitter_oauth_token)
   oauth_signature = binascii.b2a_base64(hmac.new(signing_key, signature_base_string, hashlib.sha1).digest())[:-1]
   post_data = []
   post_data.append("oauth_consumer_key=\"%s\"" % urllib.quote_plus(social_keys.twitter_key))
   post_data.append("oauth_nonce=\"%s\"" % urllib.quote_plus(oauth_nonce))
   post_data.append("oauth_signature_method=\"%s\"" % urllib.quote_plus("HMAC-SHA1"))
   post_data.append("oauth_timestamp=\"%s\"" % oauth_timestamp)
   post_data.append("oauth_token=\"%s\"" % urllib.quote_plus(oauth_token))
   post_data.append("oauth_version=\"%s\"" % urllib.quote_plus("1.0"))
   post_data.append("oauth_signature=\"%s\"" % urllib.quote_plus(oauth_signature))
   req = urllib2.Request(base_url, "oauth_verifier=%s" % oauth_verifier)
   req.add_header("Authorization", "OAuth %s" % ', '.join(post_data))
   try:
      page = urllib2.urlopen(req).read()
      tokens = dict([x.split("=") for x in page.split("&")])
      request.user.player.twitter_id = tokens["user_id"]
      request.user.player.twitter_oauth_token = tokens["oauth_token"]
      request.user.player.twitter_oauth_token_secret = tokens["oauth_token_secret"]
      request.user.player.save()
   except urllib2.HTTPError as e:
      print e.headers
   return redirect(home)

@csrf_exempt
def gplus_player(request):
   base_url = "https://accounts.google.com/o/oauth2/token"
   code = request.GET.get('code', '')
   client_id = social_keys.gplus_client_id
   client_secret = social_keys.gplus_client_secret
   redirect_uri = "http://www.atlas.cid.harvard.edu/mdimprivacy/gplus_player/"
   grant_type = "authorization_code"
   req = urllib2.Request(base_url, "code=%s&client_id=%s&client_secret=%s&redirect_uri=%s&grant_type=%s" % (code, client_id, client_secret, redirect_uri, grant_type))
   page = urllib2.urlopen(req).read()
   d = json.loads(page)
   request.user.player.gplus_oauth_token = d["access_token"]
   #request.user.player.gplus_oauth_refresh_token = d["refresh_token"]
   req = urllib2.Request("https://www.googleapis.com/plus/v1/people/me/?key=%s" % social_keys.gplus_api_key)
   req.add_header("Authorization", "Bearer %s" % d["access_token"])
   page = urllib2.urlopen(req).read()
   d = json.loads(page)
   request.user.player.gplus_id = d["id"]
   request.user.player.save()
   return redirect(home)

@csrf_exempt
def flickr_player(request):
   http_method = "GET"
   base_url = "http://www.flickr.com/services/oauth/access_token"
   oauth_consumer_key = social_keys.flickr_api_key
   oauth_nonce = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(32))
   oauth_signature_method = "HMAC-SHA1"
   oauth_timestamp = int(time.time())
   oauth_token = request.GET.get('oauth_token', '')
   oauth_verifier = request.GET.get('oauth_verifier', '')
   oauth_version = "1.0"
   parameter_string = "oauth_consumer_key=%s&oauth_nonce=%s&oauth_signature_method=%s&oauth_timestamp=%s&oauth_token=%s&oauth_verifier=%s&oauth_version=%s" % (urllib.quote_plus(oauth_consumer_key), urllib.quote_plus(oauth_nonce), urllib.quote_plus(oauth_signature_method), oauth_timestamp, urllib.quote_plus(oauth_token), urllib.quote_plus(oauth_verifier), urllib.quote_plus(oauth_version))
   signature_base_string = "%s&%s&%s" % (http_method, urllib.quote_plus(base_url), urllib.quote_plus(parameter_string))
   signing_key = "%s&%s" % (urllib.quote_plus(social_keys.flickr_secret), request.user.player.flickr_oauth_token)
   oauth_signature = binascii.b2a_base64(hmac.new(str(signing_key), str(signature_base_string), hashlib.sha1).digest())[:-1]
   try:
      print "%s?%s&oauth_signature=%s" % (base_url, parameter_string, oauth_signature)
      page = urllib2.urlopen("%s?%s&oauth_signature=%s" % (base_url, parameter_string, oauth_signature)).read()
      tokens = dict([x.split("=") for x in page.split("&")])
      request.user.player.flickr_id = tokens["user_nsid"]
      request.user.player.flickr_oauth_token = tokens["oauth_token"]
      request.user.player.flickr_oauth_token_secret = tokens["oauth_token_secret"]
      request.user.player.save()
   except urllib2.HTTPError as e:
      print e.headers
   return redirect(home)

def twitter_connect(request):
   http_method = "POST"
   base_url = "https://api.twitter.com/oauth/request_token"
   oauth_callback = "http://www.atlas.cid.harvard.edu/mdimprivacy/twitter_player/"
   oauth_consumer_key = social_keys.twitter_key
   oauth_nonce = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(32))
   oauth_signature_method = "HMAC-SHA1"
   oauth_timestamp = int(time.time())
   oauth_version = "1.0"
   parameter_string = "oauth_callback=%s&oauth_consumer_key=%s&oauth_nonce=%s&oauth_signature_method=%s&oauth_timestamp=%s&oauth_version=%s" % (urllib.quote_plus(oauth_callback), urllib.quote_plus(oauth_consumer_key), urllib.quote_plus(oauth_nonce), urllib.quote_plus(oauth_signature_method), oauth_timestamp, urllib.quote_plus(oauth_version))
   signature_base_string = "%s&%s&%s" % (http_method, urllib.quote_plus(base_url), urllib.quote_plus(parameter_string))
   signing_key = "%s&" % urllib.quote_plus(social_keys.twitter_secret)
   oauth_signature = binascii.b2a_base64(hmac.new(signing_key, signature_base_string, hashlib.sha1).digest())[:-1]
   post_data = []
   post_data.append("oauth_callback=\"%s\"" % urllib.quote_plus(oauth_callback))
   post_data.append("oauth_consumer_key=\"%s\"" % urllib.quote_plus(social_keys.twitter_key))
   post_data.append("oauth_nonce=\"%s\"" % urllib.quote_plus(oauth_nonce))
   post_data.append("oauth_signature_method=\"%s\"" % urllib.quote_plus("HMAC-SHA1"))
   post_data.append("oauth_timestamp=\"%s\"" % oauth_timestamp)
   post_data.append("oauth_version=\"%s\"" % urllib.quote_plus("1.0"))
   post_data.append("oauth_signature=\"%s\"" % urllib.quote_plus(oauth_signature))
   req = urllib2.Request(base_url, "")
   req.add_header("Authorization", "OAuth %s" % ', '.join(post_data))
   try:
      page = urllib2.urlopen(req).read()
      tokens = dict([x.split("=") for x in page.split("&")])
      request.user.player.twitter_oauth_token = tokens["oauth_token_secret"]
      request.user.player.save()
   except urllib2.HTTPError as e:
      print e.headers
   return redirect("https://api.twitter.com/oauth/authenticate?oauth_token=%s" % tokens["oauth_token"])

def gplus_connect(request):
   base_url = "https://accounts.google.com/o/oauth2/auth"
   response_type = "code"
   client_id = social_keys.gplus_client_id
   redirect_uri = "http://www.atlas.cid.harvard.edu/mdimprivacy/gplus_player/"
   scope = "https://www.googleapis.com/auth/plus.login"
   state = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(32))
   access_type = "offline"
   return redirect("%s?response_type=%s&client_id=%s&redirect_uri=%s&scope=%s&state=%s&access_type=%s" % (base_url, urllib.quote_plus(response_type), urllib.quote_plus(client_id), urllib.quote_plus(redirect_uri), urllib.quote_plus(scope), urllib.quote_plus(state), urllib.quote_plus(access_type)))

def flickr_connect(request):
   http_method = "GET"
   base_url = "http://www.flickr.com/services/oauth/request_token"
   oauth_callback = "http://www.atlas.cid.harvard.edu/mdimprivacy/flickr_player/"
   oauth_consumer_key = social_keys.flickr_api_key
   oauth_nonce = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(32))
   oauth_signature_method = "HMAC-SHA1"
   oauth_timestamp = int(time.time())
   oauth_version = "1.0"
   parameter_string = "oauth_callback=%s&oauth_consumer_key=%s&oauth_nonce=%s&oauth_signature_method=%s&oauth_timestamp=%s&oauth_version=%s" % (urllib.quote_plus(oauth_callback), urllib.quote_plus(oauth_consumer_key), urllib.quote_plus(oauth_nonce), urllib.quote_plus(oauth_signature_method), oauth_timestamp, urllib.quote_plus(oauth_version))
   signature_base_string = "%s&%s&%s" % (http_method, urllib.quote_plus(base_url), urllib.quote_plus(parameter_string))
   signing_key = "%s&" % urllib.quote_plus(social_keys.flickr_secret)
   oauth_signature = binascii.b2a_base64(hmac.new(str(signing_key), str(signature_base_string), hashlib.sha1).digest())[:-1]
   try:
      page = urllib2.urlopen("%s?%s&oauth_signature=%s" % (base_url, parameter_string, oauth_signature)).read()
      tokens = dict([x.split("=") for x in page.split("&")])
      request.user.player.flickr_oauth_token = tokens["oauth_token_secret"]
      request.user.player.save()
      return redirect("http://www.flickr.com/services/oauth/authorize?oauth_token=%s" % tokens["oauth_token"])
   except urllib2.HTTPError as e:
      print e.headers
      return redirect(home)

def refresh(request):
   ################### Facebook ########################
   """
   # To get mutual friends
   qs = urllib.urlopen("https://graph.facebook.com/me/friends/?access_token=%s" % (request.user.player.facebook_oauth_token)).read()
   fb_friends = json.loads(qs)
   for i in range(len(fb_friends["data"])):
      qs = urllib.urlopen("https://graph.facebook.com/me/mutualfriends/%s/?access_token=%s" % (fb_friends["data"][i]["id"], request.user.player.facebook_oauth_token)).read()
      fb_mutual_friends = json.loads(qs)
      for j in range(len(fb_mutual_friends["data"])):
         if fb_friends["data"][i]["id"] < fb_mutual_friends["data"][j]["id"]:
            fb_edge = FacebookEdge(source = fb_friends["data"][i]["id"], target = fb_mutual_friends["data"][j]["id"])
            fb_edge.save()
   """
   """
   # To get friends' photos
   qs = urllib.urlopen("https://graph.facebook.com/me/friends/?access_token=%s" % (request.user.player.facebook_oauth_token)).read()
   fb_friends = json.loads(qs)
   f = open("/home/mikk/Documents/temp/user_photo", 'w')
   for i in range(len(fb_friends["data"])):
      qs = urllib.urlopen("https://graph.facebook.com/%s/photos?fields=id&limit=10000&access_token=%s" % (fb_friends["data"][i]["id"], request.user.player.facebook_oauth_token)).read()
      fb_photos = json.loads(qs)
      for j in range(len(fb_photos["data"])):
         f.write("%s\t%s\n" % (fb_friends["data"][i]["id"], fb_photos["data"][j]["id"]))
      qs = urllib.urlopen("https://graph.facebook.com/%s/photos/uploaded?fields=id&limit=10000&access_token=%s" % (fb_friends["data"][i]["id"], request.user.player.facebook_oauth_token)).read()
      fb_photos = json.loads(qs)
      for j in range(len(fb_photos["data"])):
         f.write("%s\t%s\n" % (fb_friends["data"][i]["id"], fb_photos["data"][j]["id"]))
   f.close()
   """
   """
   # To get friends' likes
   qs = urllib.urlopen("https://graph.facebook.com/me/friends/?access_token=%s" % (request.user.player.facebook_oauth_token)).read()
   fb_friends = json.loads(qs)
   f = open("/home/mikk/Documents/temp/user_like", 'w')
   for i in range(len(fb_friends["data"])):
      qs = urllib.urlopen("https://graph.facebook.com/%s/likes?fields=id&limit=5000&access_token=%s" % (fb_friends["data"][i]["id"], request.user.player.facebook_oauth_token)).read()
      fb_likes = json.loads(qs)
      for j in range(len(fb_likes["data"])):
         f.write("%s\t%s\n" % (fb_friends["data"][i]["id"], fb_likes["data"][j]["id"]))
   f.close()
   """
   """
   # To get friends' groups
   qs = urllib.urlopen("https://graph.facebook.com/me/friends/?access_token=%s" % (request.user.player.facebook_oauth_token)).read()
   fb_friends = json.loads(qs)
   f = open("/home/mikk/Documents/temp/user_group", 'w')
   for i in range(len(fb_friends["data"])):
      qs = urllib.urlopen("https://graph.facebook.com/%s/groups?fields=id&limit=5000&access_token=%s" % (fb_friends["data"][i]["id"], request.user.player.facebook_oauth_token)).read()
      fb_groups = json.loads(qs)
      for j in range(len(fb_groups["data"])):
         f.write("%s\t%s\n" % (fb_friends["data"][i]["id"], fb_groups["data"][j]["id"]))
   f.close()
   """
   ################### Linkedin ########################
   """
   # To get mutual friends
   qs = urllib.urlopen("https://api.linkedin.com/v1/people/~/connections?oauth2_access_token=%s&format=json" % (request.user.player.linkedin_oauth_token)).read()
   lin_friends = json.loads(qs)
   f = codecs.open("/home/mikk/Documents/temp/mynetworks/linkedin/linkedin_legend", 'wb', encoding = 'utf-8')
   for i in range(len(lin_friends["values"])):
      if lin_friends["values"][i]["id"] != "private":
         print lin_friends["values"][i]["firstName"], lin_friends["values"][i]["lastName"]
         try:
            f.write("%s\t%s %s\n" % (lin_friends["values"][i]["id"], lin_friends["values"][i]["firstName"], lin_friends["values"][i]["lastName"]))
         except:
            first = lin_friends["values"][i]["firstName"].decode("utf-32").encode("utf-8")
            last =  lin_friends["values"][i]["lastName"].decode("utf-32").encode("utf-8")
            f.write("%s\t%s %s\n" % (lin_friends["values"][i]["id"], first, last))
         qs = urllib.urlopen("https://api.linkedin.com/v1/people/%s/relation-to-viewer:(related-connections)?oauth2_access_token=%s&format=json" % (lin_friends["values"][i]["id"], request.user.player.linkedin_oauth_token)).read()
         lin_mutual_friends = json.loads(qs)
         if "relatedConnections" in lin_mutual_friends:
            if lin_mutual_friends["relatedConnections"]["_total"] > 0:
               for j in range(len(lin_mutual_friends["relatedConnections"]["values"])):
                  if lin_friends["values"][i]["id"] < lin_mutual_friends["relatedConnections"]["values"][j]["id"] and lin_mutual_friends["relatedConnections"]["values"][j]["id"] != "private":
                     lin_edge = LinkedinEdge(source = lin_friends["values"][i]["id"], target = lin_mutual_friends["relatedConnections"]["values"][j]["id"])
                     lin_edge.save()
   f.close()
   """
   ################### Lastfm ########################
   """
   # To get mutual friends
   qs = urllib.urlopen("http://ws.audioscrobbler.com/2.0/?method=user.getFriends&user=%s&api_key=%s&limit=4000&format=json" % (request.user.player.lastfm_id, social_keys.lastfm_api_key)).read()
   lfm_friends = json.loads(qs)
   friends = set()
   for i in range(len(lfm_friends["friends"]["user"])):
      friends.add(lfm_friends["friends"]["user"][i]["name"])
   for i in range(len(lfm_friends["friends"]["user"])):
      print lfm_friends["friends"]["user"][i]["name"]
      print "http://ws.audioscrobbler.com/2.0/?method=user.getFriends&user=%s&api_key=%s&limit=1000&format=json" % (lfm_friends["friends"]["user"][i]["name"], social_keys.lastfm_api_key)
      qs = urllib.urlopen("http://ws.audioscrobbler.com/2.0/?method=user.getFriends&user=%s&api_key=%s&limit=1000&format=json" % (lfm_friends["friends"]["user"][i]["name"], social_keys.lastfm_api_key)).read()
      lfm_friends_of_friend = json.loads(qs)
      number_of_pages = int(lfm_friends_of_friend["friends"]["@attr"]["totalPages"])
      for j in range(len(lfm_friends_of_friend["friends"]["user"])):
         if lfm_friends_of_friend["friends"]["user"][j]["name"] in friends and lfm_friends["friends"]["user"][i]["name"] < lfm_friends_of_friend["friends"]["user"][j]["name"]:
            lfm_edge = LastfmEdge(source = lfm_friends["friends"]["user"][i]["name"], target = lfm_friends_of_friend["friends"]["user"][j]["name"])
            lfm_edge.save()
      if number_of_pages > 1:
         for y in range(2, number_of_pages + 1):
            print y
            qs = urllib.urlopen("http://ws.audioscrobbler.com/2.0/?method=user.getFriends&user=%s&api_key=%s&limit=1000&page=%d&format=json" % (lfm_friends["friends"]["user"][i]["name"], social_keys.lastfm_api_key, y)).read()
            lfm_friends_of_friend = json.loads(qs)
            number_of_pages = int(lfm_friends_of_friend["friends"]["@attr"]["totalPages"])
            for j in range(len(lfm_friends_of_friend["friends"]["user"])):
               if lfm_friends_of_friend["friends"]["user"][j]["name"] in friends and lfm_friends["friends"]["user"][i]["name"] < lfm_friends_of_friend["friends"]["user"][j]["name"]:
                  lfm_edge = LastfmEdge(source = lfm_friends["friends"]["user"][i]["name"], target = lfm_friends_of_friend["friends"]["user"][j]["name"])
                  lfm_edge.save()
   """
   ################### Twitter ########################
   """
   # To get mutual friends
   f = codecs.open("/home/mikk/Documents/temp/mynetworks/twitter/twitter_legend", 'wb', encoding = 'utf-8')
   friends = set()
   http_method = "GET"
   base_url = "https://api.twitter.com/1.1/friends/list.json"
   cursor = -1
   include_user_entities = "false"
   oauth_consumer_key = social_keys.twitter_key
   oauth_nonce = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(32))
   oauth_signature_method = "HMAC-SHA1"
   oauth_token = request.user.player.twitter_oauth_token
   oauth_version = "1.0"
   skip_status = "true"
   user_id = request.user.player.twitter_id
   signing_key = "%s&%s" % (urllib.quote_plus(social_keys.twitter_secret), urllib.quote_plus(request.user.player.twitter_oauth_token_secret))
   while cursor != 0:
      oauth_timestamp = int(time.time())
      parameter_string = "cursor=%d&include_user_entities=%s&oauth_consumer_key=%s&oauth_nonce=%s&oauth_signature_method=%s&oauth_timestamp=%s&oauth_token=%s&oauth_version=%s&skip_status=%s&user_id=%s" % (cursor, urllib.quote_plus(include_user_entities), urllib.quote_plus(oauth_consumer_key), urllib.quote_plus(oauth_nonce), urllib.quote_plus(oauth_signature_method), oauth_timestamp, urllib.quote_plus(oauth_token), urllib.quote_plus(oauth_version), urllib.quote_plus(skip_status), urllib.quote_plus(user_id))
      signature_base_string = "%s&%s&%s" % (http_method, urllib.quote_plus(base_url), urllib.quote_plus(parameter_string))
      oauth_signature = binascii.b2a_base64(hmac.new(signing_key, signature_base_string, hashlib.sha1).digest())[:-1]
      post_data = []
      post_data.append("oauth_consumer_key=\"%s\"" % urllib.quote_plus(social_keys.twitter_key))
      post_data.append("oauth_nonce=\"%s\"" % urllib.quote_plus(oauth_nonce))
      post_data.append("oauth_signature=\"%s\"" % urllib.quote_plus(oauth_signature))
      post_data.append("oauth_signature_method=\"%s\"" % urllib.quote_plus("HMAC-SHA1"))
      post_data.append("oauth_timestamp=\"%s\"" % oauth_timestamp)
      post_data.append("oauth_token=\"%s\"" % urllib.quote_plus(oauth_token))
      post_data.append("oauth_version=\"%s\"" % urllib.quote_plus("1.0"))
      req = urllib2.Request("%s?cursor=%d&include_user_entities=%s&skip_status=%s&user_id=%s" % (base_url, cursor, include_user_entities, skip_status, user_id))
      req.add_header("Authorization", "OAuth %s" % ', '.join(post_data))
      #print signing_key
      #print "curl --request '%s' '%s' --header 'Authorization: %s' --verbose" % (http_method, req.get_full_url(), req.headers["Authorization"])
      #return redirect(home)
      try:
         tw_friends = json.loads(urllib2.urlopen(req).read())
      except urllib2.HTTPError as e:
         print e.args
         print e.code
         print e.errno
         print e.headers
         print e.info
         print e.msg
         print e.reason
         print e.url
         return redirect(home)
      cursor = tw_friends["next_cursor"]
      for i in range(len(tw_friends["users"])):
         try:
            f.write("%s\t%s\n" % (tw_friends["users"][i]["id"], tw_friends["users"][i]["name"]))
         except:
            name = tw_friends["users"][i]["name"].decode("utf-32").encode("utf-8")
            f.write("%s\t%s\n" % (tw_friends["values"][i]["id"], name))
         friends.add(tw_friends["users"][i]["id"])
   f.close()
   http_method = "GET"
   base_url = "https://api.twitter.com/1.1/friends/ids.json"
   count = 5000
   cursor = -1
   for friend in friends:
      print friend
      user_id = friend
      oauth_timestamp = int(time.time())
      parameter_string = "count=%d&cursor=%d&oauth_consumer_key=%s&oauth_nonce=%s&oauth_signature_method=%s&oauth_timestamp=%s&oauth_token=%s&oauth_version=%s&user_id=%s" % (count, cursor, urllib.quote_plus(oauth_consumer_key), urllib.quote_plus(oauth_nonce), urllib.quote_plus(oauth_signature_method), oauth_timestamp, urllib.quote_plus(oauth_token), urllib.quote_plus(oauth_version), user_id)
      signature_base_string = "%s&%s&%s" % (http_method, urllib.quote_plus(base_url), urllib.quote_plus(parameter_string))
      oauth_signature = binascii.b2a_base64(hmac.new(signing_key, signature_base_string, hashlib.sha1).digest())[:-1]
      post_data = []
      post_data.append("oauth_consumer_key=\"%s\"" % urllib.quote_plus(social_keys.twitter_key))
      post_data.append("oauth_nonce=\"%s\"" % urllib.quote_plus(oauth_nonce))
      post_data.append("oauth_signature=\"%s\"" % urllib.quote_plus(oauth_signature))
      post_data.append("oauth_signature_method=\"%s\"" % urllib.quote_plus("HMAC-SHA1"))
      post_data.append("oauth_timestamp=\"%s\"" % oauth_timestamp)
      post_data.append("oauth_token=\"%s\"" % urllib.quote_plus(oauth_token))
      post_data.append("oauth_version=\"%s\"" % urllib.quote_plus("1.0"))
      req = urllib2.Request("%s?count=%d&cursor=%d&user_id=%s" % (base_url, count, cursor, user_id))
      req.add_header("Authorization", "OAuth %s" % ', '.join(post_data))
      tw_friends_of_friend = json.loads(urllib2.urlopen(req).read())
      for i in range(len(tw_friends_of_friend["ids"])):
         if tw_friends_of_friend["ids"][i] in friends and friend < tw_friends_of_friend["ids"][i]:
            tw_edge = TwitterEdge(source = friend, target = tw_friends_of_friend["ids"][i])
            tw_edge.save()
      time.sleep(60)
   """
   ################### Google + ########################
   """
   # To get friends
   f = codecs.open("/home/mikk/Documents/temp/mynetworks/gplus/gplus_legend", 'wb', encoding = 'utf-8')
   req = urllib2.Request("https://www.googleapis.com/plus/v1/people/me/people/visible?maxResults=100&key=%s" % social_keys.gplus_api_key)
   req.add_header("Authorization", "Bearer %s" % request.user.player.gplus_oauth_token)
   gp_friends = json.loads(urllib2.urlopen(req).read())
   for i in range(len(gp_friends["items"])):
      if gp_friends["items"][i]["url"] != "":
         try:
            f.write("%s\t%s\n" % (gp_friends["items"][i]["id"], gp_friends["items"][i]["displayName"]))
         except:
            name = gp_friends["items"][i]["displayName"].decode("utf-32").encode("utf-8")
            f.write("%s\t%s\n" % (gp_friends["items"][i]["id"], name))
   while "nextPageToken" in gp_friends:
      req = urllib2.Request("https://www.googleapis.com/plus/v1/people/me/people/visible?maxResults=100&pageToken=%s&key=%s" % (gp_friends["nextPageToken"], social_keys.gplus_api_key))
      req.add_header("Authorization", "Bearer %s" % request.user.player.gplus_oauth_token)
      gp_friends = json.loads(urllib2.urlopen(req).read())
      for i in range(len(gp_friends["items"])):
         if gp_friends["items"][i]["url"] != "":
            try:
               f.write("%s\t%s\n" % (gp_friends["items"][i]["id"], gp_friends["items"][i]["displayName"]))
            except:
               name = gp_friends["items"][i]["displayName"].decode("utf-32").encode("utf-8")
               f.write("%s\t%s\n" % (gp_friends["items"][i]["id"], name))
   f.close()
   """
   ################### Flickr ########################
   #"""
   # To get mutual friends
   f = codecs.open("/home/mikk/Documents/temp/mynetworks/flickr/flickr_legend", 'wb', encoding = 'utf-8')
   friends = set()
   http_method = "GET"
   base_url = "http://api.flickr.com/services/rest/"
   api_key = social_keys.flickr_api_key
   auth_token = request.user.player.flickr_oauth_token
   method = "flickr.contacts.getList"
   oauth_nonce = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(32))
   oauth_signature_method = "HMAC-SHA1"
   oauth_timestamp = int(time.time())
   oauth_version = "1.0"
   signing_key = "%s&%s" % (urllib.quote_plus(social_keys.flickr_secret), urllib.quote_plus(request.user.player.flickr_oauth_token_secret))
   #parameter_string = "api_key=%s&auth_token=%s&format=json&method=%s" % (urllib.quote_plus(api_key), urllib.quote_plus(auth_token), urllib.quote_plus(method))
   parameter_string = "format=json&method=%s&nojsoncallback=1&oauth_consumer_key=%s&oauth_nonce=%s&oauth_signature_method=%s&oauth_timestamp=%s&oauth_token=%s&oauth_version=%s" % (urllib.quote_plus(method), urllib.quote_plus(api_key), urllib.quote_plus(oauth_nonce), urllib.quote_plus(oauth_signature_method), oauth_timestamp, urllib.quote_plus(auth_token), urllib.quote_plus(oauth_version))
   signature_base_string = "%s&%s&%s" % (http_method, urllib.quote_plus(base_url), urllib.quote_plus(parameter_string))
   oauth_signature = binascii.b2a_base64(hmac.new(str(signing_key), str(signature_base_string), hashlib.sha1).digest())[:-1]
   fl_friends = json.loads(urllib2.urlopen("%s?%s&oauth_signature=%s" % (base_url, parameter_string, oauth_signature)).read())
   for i in range(len(fl_friends["contacts"]["contact"])):
      friends.add(fl_friends["contacts"]["contact"][i]["nsid"])
   for i in range(len(fl_friends["contacts"]["contact"])):
      try:
         f.write("%s\t%s\n" % (fl_friends["contacts"]["contact"][i]["nsid"], fl_friends["contacts"]["contact"][i]["username"]))
      except:
         name = fl_friends["contacts"]["contact"][i]["username"].decode("utf-32").encode("utf-8")
         f.write("%s\t%s\n" % (fl_friends["contacts"]["contact"][i]["nsid"], name))
      print "%s?method=flickr.contacts.getPublicList&api_key=%s&user_id=%s&format=json" % (base_url, api_key, fl_friends["contacts"]["contact"][i]["nsid"])
      fl_friends_of_friend = json.loads(urllib2.urlopen("%s?method=flickr.contacts.getPublicList&api_key=%s&user_id=%s&format=json&nojsoncallback=1" % (base_url, api_key, fl_friends["contacts"]["contact"][i]["nsid"])).read())
      number_of_pages = int(fl_friends_of_friend["contacts"]["pages"])
      for j in range(len(fl_friends_of_friend["contacts"]["contact"])):
         if fl_friends_of_friend["contacts"]["contact"][j]["nsid"] in friends and fl_friends["contacts"]["contact"][i]["nsid"] < fl_friends_of_friend["contacts"]["contact"][j]["nsid"]:
            fl_edge = FlickrEdge(source = fl_friends["contacts"]["contact"][i]["nsid"], target = fl_friends_of_friend["contacts"]["contact"][j]["nsid"])
            fl_edge.save()
      if number_of_pages > 1:
         for y in range(2, number_of_pages + 1):
            print y
            fl_friends_of_friend = json.loads(urllib2.urlopen("%s?method=flickr.contacts.getPublicList&api_key=%s&user_id=%s&format=json&page=%d&nojsoncallback=1" % (base_url, api_key, fl_friends["contacts"]["contact"][i]["nsid"], y)).read())
            for j in range(len(fl_friends_of_friend["contacts"]["contact"])):
               if fl_friends_of_friend["contacts"]["contact"][j]["nsid"] in friends and fl_friends["contacts"]["contact"][i]["nsid"] < fl_friends_of_friend["contacts"]["contact"][j]["nsid"]:
                  fl_edge = FlickrEdge(source = fl_friends["contacts"]["contact"][i]["nsid"], target = fl_friends_of_friend["contacts"]["contact"][j]["nsid"])
                  fl_edge.save()

   #"""
   ################### Gmail ########################
   return redirect(home)


















