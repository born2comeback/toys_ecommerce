from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField, PasswordChangeForm
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Customer


class UserRegisterForm(UserCreationForm):
    error_messages = {
        'password_mismatch': 'Два введенных пароля не совпадают'
    }
    email = forms.EmailField(error_messages={'invalid': 'Введите корректный email-адрес'})
    password1 = forms.CharField(label='Пароль',
                                widget=(forms.PasswordInput(attrs={'class': 'form-control'})),
                                )
    password2 = forms.CharField(label='Подтверждение пароля',
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}),
                                )
    username = forms.CharField(
        label="Имя пользователя",
        max_length=150,
        error_messages={'unique': "Пользователь с таким именем уже существует"},
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get('email')
        email_qs = User.objects.filter(email=email)
        if email_qs.exists():
            raise forms.ValidationError(
                "Пользователь с таким email-адресом уже существует")
        return super(UserRegisterForm, self).clean(*args, **kwargs)

    @receiver(post_save, sender=User)
    def create_profile(sender, instance, created, **kwargs):
        if created:
            Customer.objects.create(user=instance)


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    phone = forms.CharField()

    class Meta:
        model = Customer
        fields = ['username', 'email', 'phone']


class CustomAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        label='Имя',
        widget=forms.TextInput(attrs={'autofocus': True})
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )


class CustomPassChangeForm(PasswordChangeForm):
    new_password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'})
    )


class ContactForm(forms.Form):
    name = forms.CharField(max_length = 50)
    from_email = forms.EmailField(max_length = 150)
    message = forms.CharField(widget = forms.Textarea, max_length = 2000)
    subject = forms.CharField(max_length = 100)


class SubscriberForm(forms.Form):
    email = forms.EmailField(label='Your email',
                             max_length=100,
                             widget=forms.EmailInput(attrs={'class': 'form-control'}))
