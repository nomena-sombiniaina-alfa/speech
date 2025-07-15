from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'john.doe@example.com'
        })
    )
    error_messages = {
        'invalid_login': (
            "Vos identifiants sont incorrects. Veuillez vérifier votre adresse e-mail et votre mot de passe."
        ),
        'inactive': ("Ce compte est inactif."),
    }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On retire la modification du champ username car on le définit entièrement ci-dessus
        self.fields['password'].widget.attrs.update({
            'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': '••••••••'
        })

class SignUpForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tailwind_classes = 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': tailwind_classes})
            field.help_text = '' # Clear default help texts

        self.fields['username'].widget.attrs['placeholder'] = 'johndoe'
        self.fields['email'].widget.attrs['placeholder'] = 'john.doe@example.com'
        self.fields['first_name'].widget.attrs['placeholder'] = 'John'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Doe'
        self.fields['password'].widget.attrs['placeholder'] = '••••••••'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class PersonalDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tailwind_classes = 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        
        self.fields['username'].widget.attrs.update({'class': tailwind_classes, 'placeholder': 'johndoe'})
        self.fields['email'].widget.attrs.update({'class': tailwind_classes, 'placeholder': 'john.doe@example.com'})
        self.fields['first_name'].widget.attrs.update({'class': tailwind_classes, 'placeholder': 'John'})
        self.fields['last_name'].widget.attrs.update({'class': tailwind_classes, 'placeholder': 'Doe'})


class BankDetailsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['card_number', 'card_expiry', 'card_cvv']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tailwind_classes = 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        
        self.fields['card_number'].widget.attrs.update({
            'class': tailwind_classes,
            'placeholder': 'XXXX XXXX XXXX XXXX'
        })
        self.fields['card_expiry'].widget.attrs.update({
            'class': tailwind_classes,
            'placeholder': 'MM/YY'
        })
        self.fields['card_cvv'].widget.attrs.update({
            'class': tailwind_classes,
            'placeholder': 'XXX'
        })

class CustomPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label="Ancien mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})
    )
    new_password2 = forms.CharField(
        label="Confirmer le nouveau mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = ''

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                "Votre ancien mot de passe est incorrect. Veuillez le vérifier."
            )
        return old_password

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        return new_password2

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data["new_password1"])
        if commit:
            self.user.save()
        return self.user 