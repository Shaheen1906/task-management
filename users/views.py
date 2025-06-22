from django.shortcuts import redirect, render
from django.views.generic import CreateView
from .forms import UserLoginForm, UserRegisterForm
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView

# Create your views here.


class RegisterView(CreateView):
    template_name = 'users/register.html'
    form_class = UserRegisterForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Account created successfully! You are now logged in.")
        return redirect('home')
    
    def form_invalid(self, form):
        messages.error(self.request, "Error creating account. Please correct the errors below.")
        return super().form_invalid(form)
    
class CustomLoginView(LoginView):
    authentication_form = UserLoginForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('task_list') 

    def form_valid(self, form):
         messages.success(self.request, f"Welcome back, {self.request.user.username}!")
         return super().form_valid(form)
     
    def form_invalid(self, form):
         messages.error(self.request, "Invalid username or password. Please try again.")
         return super().form_invalid(form)
    

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)