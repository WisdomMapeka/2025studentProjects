# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegistrationForm

def index_view(request):
    if request.user.is_authenticated:
        return redirect("my_bookings")
    return render(request, 'core/index.html')
 
def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('/login/')  # or 'booking_create'
    else:
        form = UserRegistrationForm()
    return render(request, 'users/signup.html', {'form': form})


# views.py
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from .forms import EmailLoginForm

class UserLoginView(LoginView):
    template_name = 'users/login.html'   # ✅ tell Django to use this template
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True
    
class UserLogoutView(LogoutView):
    next_page = reverse_lazy('login')



# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ProfileForm

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile')
    else:
        form = ProfileForm(instance=user)

    return render(request, 'users/profile.html', {'form': form, 'user': user})



# views.py
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages

class UserPasswordChangeView(PasswordChangeView):
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('profile')  # redirect back to profile after success

    def form_valid(self, form):
        messages.success(self.request, "Your password was changed successfully!")
        return super().form_valid(form)
