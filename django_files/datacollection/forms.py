from django import forms

class RegisterForm(forms.Form):
    username = forms.CharField(required = True)
    email = forms.EmailField(required = True)
    password = forms.CharField(max_length = 32, widget = forms.PasswordInput, required = True)

class LoginForm(forms.Form):
    username = forms.CharField(required = True)
    password = forms.CharField(max_length = 32, widget = forms.PasswordInput, required = True)
