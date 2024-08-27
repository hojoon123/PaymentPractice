from django.urls import path, include

from . import views, decorators

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("cart/<int:product_pk>/add/", views.add_to_cart, name="add_to_cart"),
    path("order/", views.order_list, name="order_list"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("order/new/", views.order_new, name="order_new"),
    path("order/<int:pk>/pay/", views.order_pay, name="order_pay"),
    path(
        "order/<int:order_pk>/check/<int:payment_pk>/",
        views.order_check,
        name="order_check",
    ),
    path("order/<int:pk>/", views.order_detail, name="order_detail"),
    path("webhook/", decorators.portone_webhook, name="webhook"),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("product/<int:product_pk>/comment/", views.add_comment, name="add_comment"),
]
