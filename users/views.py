from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import SignUpForm, CustomAuthenticationForm, CustomPasswordChangeForm, BankDetailsForm, PersonalDataForm
from .models import UserProfile
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth import update_session_auth_hash
import json

# Create your views here.

def custom_404(request, exception):
    return render(request, '404.html', {}, status=404)

def index_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile', id=request.user.id)
    return redirect('users:login')

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('users:profile', id=user.id)
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('users:profile', id=user.id)
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('users:login')

@login_required
def profile_view(request, id):
    # Récupère l'utilisateur du profil demandé ou renvoie une 404 s'il n'existe pas.
    profile_user = get_object_or_404(User, id=id)
    profile = get_object_or_404(UserProfile, user=profile_user)

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = json.loads(request.body)
        form_type = data.pop('form_type', None)

        if form_type == 'personal_data':
            form = PersonalDataForm(data, instance=profile_user)
            if form.is_valid():
                user = form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Informations personnelles mises à jour avec succès.',
                    'user_data': {
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'username': user.username,
                    }
                })
            else:
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        
        elif form_type == 'bank_details':
            form = BankDetailsForm(data, instance=profile)
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Informations bancaires mises à jour avec succès.',
                })
            else:
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        
        elif form_type == 'password_change':
            form = CustomPasswordChangeForm(profile_user, data)
            if form.is_valid():
                form.save()
                # La mise à jour du hash de session est volontairement retirée ici.
                # Cela évite de corrompre la session de l'utilisateur qui effectue le changement.
                return JsonResponse({
                    'success': True,
                    'message': 'Le mot de passe a été mis à jour avec succès.',
                })
            else:
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        
        return JsonResponse({'success': False, 'errors': {'__all__': ['Type de formulaire invalide.']}}, status=400)

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'personal_form': PersonalDataForm(instance=profile_user),
        'bank_form': BankDetailsForm(instance=profile),
        'password_form': CustomPasswordChangeForm(profile_user),
    }
    
    return render(request, 'profile.html', context)
