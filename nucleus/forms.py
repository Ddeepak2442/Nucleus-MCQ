from django import forms

class HealthForm(forms.Form):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]
    DIET_CHOICES = [
        ('vegetarian', 'Vegetarian'),
        ('non_vegetarian', 'Non Vegetarian'),
        ('eggtarian', 'Eggtarian')
    ]
    LACTOSE_CHOICES = [
        ('tolerant', 'Tolerant'),
        ('intolerant', 'Intolerant')
    ]
    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sedentary'),
        ('lightly_active', 'Lightly Active'),
        ('moderately_active', 'Moderately Active'),
        ('very_active', 'Very Active'),
        ('extra_active', 'Extra Active')
    ]
    GOAL_CHOICES = [
        ('lose_weight', 'Lose Weight'),
        ('gain_muscle', 'Gain Muscle'),
        ('maintenance', 'Maintenance')
    ]

    name = forms.CharField(label='Name', max_length=100)
    age = forms.IntegerField(label='Age')
    gender = forms.ChoiceField(label='Gender', choices=GENDER_CHOICES)
    height = forms.DecimalField(label='Height', max_digits=5, decimal_places=2)
    weight = forms.DecimalField(label='Weight', max_digits=5, decimal_places=2)
    diet = forms.ChoiceField(label='Dietary Preference', choices=DIET_CHOICES)
    lactose = forms.ChoiceField(label='Lactose Tolerance', choices=LACTOSE_CHOICES)
    activity_level = forms.ChoiceField(label='Activity Level', choices=ACTIVITY_LEVEL_CHOICES)
    dietary_restrictions = forms.CharField(label='Dietary Restrictions', max_length=255, required=False)
    goal = forms.ChoiceField(label='Goal', choices=GOAL_CHOICES)