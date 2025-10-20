from typing import Any, ClassVar

from django import forms
from django.contrib.auth.models import User

from apps.builder.models.pc_build import OrderProgress, PCBuild, PCBuildOrder


class PCBuildOrderForm(forms.ModelForm):
    class Meta:
        model = PCBuildOrder
        fields: ClassVar[list[str]] = ["build", "customer", "address"]

    def __init__(self, *args, **kwargs) -> None:
        user: User | None = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["build"].label = "PC Build"
        self.fields["build"].queryset = PCBuild.objects.all()
        self.fields["build"].empty_label = "Select PC Build"
        self.fields["build"].required = True
        self.fields["markup"].label = "Markup"
        self.fields["markup"].required = True
        self.fields["customer"].label = "Customer"
        self.fields["customer"].queryset = User.objects.filter(is_staff=False)
        self.fields["address"].label = "Delivery Address"
        self.fields["address"].required = True

        if user and not user.is_staff:
            self.fields["customer"].initial = user
            self.fields["customer"].widget = forms.HiddenInput()

    def clean(self) -> dict[str, Any]:
        return super().clean()

    def save(self, *, commit: bool = True) -> PCBuildOrder:
        instance: PCBuildOrder = super().save(commit=False)

        if commit:
            instance.save()
            OrderProgress.objects.create(order=instance)

        return instance


class ComponentListForm(forms.Form):
    """Form for sending a component list with a service fee without creating an order."""

    build = forms.ModelChoiceField(
        queryset=PCBuild.objects.all(),
        empty_label="-- Select a build --",
        required=True,
        label="Select PC Build",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    service_fee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=True,
        label="Service Fee",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter service fee amount (€)",
                "step": "0.01",
                "min": "0",
            },
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        build = cleaned_data.get("build")
        service_fee = cleaned_data.get("service_fee")

        if not build:
            msg = "Please select a PC build."
            raise forms.ValidationError(msg)

        if service_fee is None or service_fee < 0:
            msg = "Service fee must be a positive number."
            raise forms.ValidationError(msg)

        return cleaned_data
