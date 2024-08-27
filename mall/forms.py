from django import forms

from mall.models import CartProduct, Comment, ProductOption


class CartProductForm(forms.ModelForm):
    class Meta:
        model = CartProduct
        fields = ["quantity"]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "댓글을 입력하세요...",
                }
            ),
        }


class SpecificationForm(forms.Form):
    key = forms.CharField(max_length=100, help_text="키를 입력하세요.")
    value = forms.CharField(max_length=100, help_text="값을 입력하세요.")


class ProductOptionForm(forms.Form):
    option = forms.ModelChoiceField(
        queryset=ProductOption.objects.none(), required=True
    )

    def __init__(self, *args, **kwargs):
        product = kwargs.pop("product", None)
        super().__init__(*args, **kwargs)
        if product:
            self.fields["option"].queryset = product.options.all()
