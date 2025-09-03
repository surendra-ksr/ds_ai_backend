from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from .models import Transaction, Security, MutualFundScheme

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class TransactionForm(forms.ModelForm):
    """Form for creating a new portfolio transaction.
    """
    asset = forms.ChoiceField(choices=[])

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'asset', 'quantity', 'price', 'transaction_date']
        widgets = {
            'transaction_date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate asset choices dynamically
        securities = [(f"security_{s.id}", s.name) for s in Security.objects.all()]
        mutual_funds = [(f"mutualfundscheme_{mf.id}", mf.name) for mf in MutualFundScheme.objects.all()]
        self.fields['asset'].choices = [('Securities', securities), ('Mutual Funds', mutual_funds)]

    def save(self, commit=True):
        # Custom save method to handle the generic foreign key
        asset_choice = self.cleaned_data['asset']
        model_name, object_id = asset_choice.split('_')
        
        self.instance.content_type = ContentType.objects.get(model=model_name)
        self.instance.object_id = object_id
        
        return super().save(commit)
