from typing import ClassVar

from django import forms

from apps.builder.models.pc_build import PCBuild, PCComponent


class PCBuildForm(forms.ModelForm):
    component = forms.ModelChoiceField(
        queryset=PCComponent.objects.all(),
        required=False,
        label="Component",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model: ClassVar = PCBuild
        fields: ClassVar[list[str]] = ["name"]
        widgets: ClassVar[dict] = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }


class PCComponentForm(forms.ModelForm):
    class Meta:
        model: ClassVar = PCComponent
        fields: ClassVar[list[str]] = ["name", "price", "link"]
        widgets: ClassVar[dict] = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "link": forms.URLInput(attrs={"class": "form-control"}),
        }
