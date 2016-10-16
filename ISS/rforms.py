from django import forms            
from django.contrib.auth.models import User   
from django.contrib.auth.forms import UserCreationForm      

class RegistrationForm(UserCreationForm):
    username = # Unsure how to proceed
    
    class Meta:
        model = poster
        fields = ('username', 'email', 'password')        

    def save(self,commit = True):   
        poster = super(RegistrationForm, self).save(commit = False)
        poster.username = self.cleaned_data['password']



        if commit:
            user.save()

        return user
