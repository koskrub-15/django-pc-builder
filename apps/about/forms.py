from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=60,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Your name"},
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "you@example.com"},
        ),
    )
    # CharField strips by default, so a whitespace-only message fails "required".
    message = forms.CharField(
        max_length=2000,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 5, "placeholder": "What would you like to build?"},
        ),
    )
