# urls.py
from django.urls import path
from .views import (
    signup_view, UserLoginView, UserLogoutView,
    profile_view, UserPasswordChangeView
)

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('', profile_view, name='profile'),
    path('password-change/', UserPasswordChangeView.as_view(), name='password_change'),
]
