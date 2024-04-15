from datetime import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.
class MyAccountManager(BaseUserManager):
    def create_user(self, first_name, last_name, date_of_birth, gender, email, username, password=None, referral=None, profession=None):
        if not email:
            raise ValueError("User must have an email address")

        if not username:
            raise ValueError("User must have a username")

        if referral is None or profession is None:
            raise ValueError("Referral and profession are required for regular users.")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            referral=referral,
            profession=profession,
        )

        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, date_of_birth, gender, email, username, password=None):
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            gender=gender,
            referral=None,  # No referral for superuser
            profession=None,  # No profession for superuser
        )
        user.set_password(password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class Account(AbstractBaseUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(default=timezone.now)

    GENDER_CHOICES = (
        ("M","Male"),
        ("F","Female"),
        ("O","Other")
        )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='O')

    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15)
    referral = models.ForeignKey('Referral', on_delete=models.SET_NULL, null=True, blank=True)
    profession = models.ForeignKey('Profession', on_delete=models.SET_NULL, null=True, blank=True)


    # required
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name","date_of_birth","gender"]

    objects = MyAccountManager()

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, add_label):
        return True


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address_line_1 = models.CharField(blank=True, max_length=100)
    address_line_2 = models.CharField(blank=True, max_length=100)
    phone_number = PhoneNumberField()
    profile_picture = models.ImageField(upload_to="userprofile", blank=True, default='userprofile/default-user.png')


    city = models.CharField(blank=True, max_length=20)
    state = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20)
   

    def __str__(self):
        return self.user.first_name

    def full_address(self):
        return f"{self.address_line_1} {self.address_line_2}"
class Referral(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Profession(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


