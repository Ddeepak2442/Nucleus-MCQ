from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404

from nucleus import settings
from django.contrib import messages, auth
from django.core.files import File
from django.contrib.auth.decorators import login_required

from .models import Account, UserProfile, Referral, Profession

from .forms import RegistrationForm, UserForm, UserProfileForm

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.core.mail import send_mail
import re


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        print("Received POST request with form data")  # Debug print
        if form.is_valid():
            print("Form is valid")  # Debug print
            # Extract data from the form
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            date_of_birth = form.cleaned_data["date_of_birth"]
            gender = form.cleaned_data["gender"]
            
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            referral = form.cleaned_data["referral"]
            profession = form.cleaned_data["profession"]
            username = email.split("@")[0]

            print(f"Creating user: {username}")  # Debug print
            
            phone_number = form.cleaned_data["phone_number"]
                   # Check if the phone number already exists
            if UserProfile.objects.filter(phone_number=phone_number).exists():
                messages.error(request, "This phone number is already in use.")

            # Create a new user instance but don't save it yet
            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                gender=gender,
                email=email,
                username=username,
                password=password,
                referral=referral,
                profession=profession,
            )
            user.phone_number = phone_number
            user.save()
            print("User saved")  # Debug print

             # Create a user profile
            profile = UserProfile()
            profile.user_id = user.id
    
              # Assign a default image file
            default_image_path = Path(settings.MEDIA_ROOT) / 'default' / 'default-user.png'
            with open(default_image_path, 'rb') as default_image_file:
             profile.profile_picture.save('default-user.png', File(default_image_file), save=True)

            # Generate activation link and send email
            current_site = get_current_site(request)
            mail_subject = "Please activate your account"
            message = render_to_string(
                "accounts/account_verification_email.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            print("Verification email sent")  # Debug print

            # Display success message and redirect to login page
            messages.success(
                request,
                "Thank you for registering with us. We have sent you a verification email to your email address. Please verify it.",
            )
            return redirect("/accounts/login/?command=verification&email=" + email)
        else:
            print("Form is not valid")  # Debug print
            print(form.errors)  # Print form errors to debug
        return redirect(register)
    else:
        form = RegistrationForm()
    referrals = Referral.objects.all()
    professions = Profession.objects.all()

    context = {"form": form, "referrals": referrals, "professions": professions}

    return render(request, "accounts/register.html", context)



def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = auth.authenticate(email=email, password=password)

        if user is not None:

            auth.login(request, user)
            messages.success(request, "You are now logged in.")
            return redirect('subject-list')
        else:
            messages.error(request, "Invalid login credentials")
            return redirect("login")
    return render(request, "accounts/login.html")


@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    messages.success(request, "You are logged out.")
    return redirect("login")


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Congratulations! Your account is activated.")
        return redirect("login")
    else:
        messages.error(request, "Invalid activation link")
        return redirect("register")


@login_required(login_url="login")
def dashboard(request):
    userprofile, _ = UserProfile.objects.get_or_create(user=request.user)
    context = {
        "userprofile": userprofile,
    }
    return render(request, "accounts/dashboard.html", context)


def forgotPassword(request):
    if request.method == "POST":
        email = request.POST["email"]
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Reset password email
            current_site = get_current_site(request)
            mail_subject = "Reset Your Password"
            message = render_to_string(
                "accounts/reset_password_email.html",
                {
                    "user": user,
                    "domain": current_site,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(
                request, "Password reset email has been sent to your email address."
            )
            return redirect("login")
        else:
            messages.error(request, "Account does not exist!")
            return redirect("forgotPassword")
    return render(request, "accounts/forgotPassword.html")


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session["uid"] = uid
        messages.success(request, "Please reset your password")
        return redirect("resetPassword")
    else:
        messages.error(request, "This link has been expired!")
        return redirect("login")


def resetPassword(request):
    if request.method == "POST":
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password == confirm_password:
            uid = request.session.get("uid")
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successful")
            return redirect("login")
        else:
            messages.error(request, "Password do not match!")
            return redirect("resetPassword")
    else:
        return render(request, "accounts/resetPassword.html")


@login_required(login_url="login")
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(
            request.POST, request.FILES, instance=userprofile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("edit_profile")
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "userprofile": userprofile,
    }
    return render(request, "accounts/edit_profile.html", context)


@login_required(login_url="login")
def change_password(request):
    if request.method == "POST":
        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, "Password updated successfully.")
                return redirect("change_password")
            else:
                messages.error(request, "Please enter valid current password")
                return redirect("change_password")
        else:
            messages.error(request, "Password does not match!")
            return redirect("change_password")
    return render(request, "accounts/change_password.html")