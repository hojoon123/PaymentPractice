import json

from django import forms
from django.contrib import admin
from django.forms import formset_factory
from django_ckeditor_5.widgets import CKEditor5Widget
from django_json_widget.widgets import JSONEditorWidget

from .forms import SpecificationForm
from .models import Category, Product, Order, ProductImage, ProductOption


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "total_amount", "status", "created_at"]
    actions = [
        "make_cancel",
        "mark_as_prepared",
        "mark_as_shipped",
        "mark_as_delivered",
    ]
    list_filter = ["status", "created_at", "updated_at", "user"]
    search_fields = ["name", "user__username", "user__email"]

    @admin.display(description=f"지정 주문 결제를 취소합니다.")
    def make_cancel(self, request, queryset):
        for order in queryset:
            order.cancel("관리자에 의해 취소됨")
        self.message_user(
            request, f"{queryset.count()}개의 주문 결제를 취소하였습니다."
        )

    @admin.display(description="선택된 주문을 상품 준비 중으로 변경합니다.")
    def mark_as_prepared(self, request, queryset):
        for order in queryset:
            try:
                order.mark_as_prepared()
                self.message_user(
                    request,
                    f"{queryset.count()}개의 주문이 상품 준비 중으로 변경되었습니다.",
                )
            except ValueError as e:
                self.message_user(request, f"주문 {order.pk}: {str(e)}", level="error")

    @admin.display(description="선택된 주문을 배송 중으로 변경합니다.")
    def mark_as_shipped(self, request, queryset):
        for order in queryset:
            try:
                order.mark_as_shipped()
                self.message_user(
                    request,
                    f"{queryset.count()}개의 주문이 배송 중으로 변경되었습니다.",
                )
            except ValueError as e:
                self.message_user(request, f"주문 {order.pk}: {str(e)}", level="error")

    @admin.display(description="선택된 주문을 배송 완료로 변경합니다.")
    def mark_as_delivered(self, request, queryset):
        for order in queryset:
            try:
                order.mark_as_delivered()
                self.message_user(
                    request,
                    f"{queryset.count()}개의 주문이 배송 완료로 변경되었습니다.",
                )
            except ValueError as e:
                self.message_user(request, f"주문 {order.pk}: {str(e)}", level="error")

    def get_readonly_fields(self, request, obj=None):
        """배송 완료된 주문은 수정 불가하도록 설정"""
        if obj and obj.status == Order.Status.DELIVERED:
            return self.readonly_fields + ("status",)
        return self.readonly_fields


# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["pk", "name"]
    list_display_links = ["name"]
    search_fields = ["name"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # 기본적으로 추가할 수 있는 이미지 필드 수
    fields = ["image"]


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1  # 기본적으로 추가할 수 있는 옵션 필드 수
    fields = ["name", "additional_price"]


class ProductAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditor5Widget())
    specifications = forms.JSONField(
        widget=JSONEditorWidget, required=False  # JSONEditorWidget 사용
    )

    class Meta:
        model = Product
        fields = "__all__"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm  # 폼 설정
    inlines = [ProductImageInline, ProductOptionInline]
    list_display = ["name", "category", "price", "status"]
    list_filter = ["category", "status", "created_at", "updated_at"]
    search_fields = ["name"]
    list_editable = ["price", "status"]
    list_per_page = 10
    list_max_show_all = 100
    list_select_related = ["category"]
    fieldsets = (
        (
            "상품 정보",
            {
                "fields": (
                    "category",
                    "name",
                    "description",
                    "price",
                    "status",
                    "specifications",
                    "presentation_image",
                )
            },
        ),
    )
    actions = ["make_sold_out", "make_obsolete"]

    def make_sold_out(self, request, queryset):
        queryset.update(status=Product.Status.SOLD_OUT)

    make_sold_out.short_description = "선택된 상품을 품절로 변경"

    def make_obsolete(self, request, queryset):
        queryset.update(status=Product.Status.OBSOLETE)

    make_obsolete.short_description = "선택된 상품을 단종으로 변경"
