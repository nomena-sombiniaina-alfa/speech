from django.urls import path
from .views import signup_view, login_view, logout_view, profile_view, index_view

app_name = 'users'

urlpatterns = [
    path('', index_view, name='index'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/<int:id>/', profile_view, name='profile'),
] 