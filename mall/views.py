import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.query import QuerySet
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from django.forms import modelformset_factory
from django.http import HttpResponse, HttpResponseForbidden

from PaymentPractice import settings
from mall.forms import CartProductForm, CommentForm, ProductOptionForm
from mall.models import Product, CartProduct, Order, OrderPayment, ProductOption

ALLOWED_WEBHOOK_IPS = ["52.78.5.241"]


@login_required
def add_comment(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.product = product
            comment.user = request.user
            comment.save()
            return redirect("product_detail", pk=product_pk)
    else:
        form = CommentForm()
    return redirect("product_detail", pk=product_pk)


# Create your views here.
class ProductListview(ListView):
    model = Product
    queryset = (
        Product.objects.filter(status=Product.Status.ACTIVE)
        .select_related("category")
        .prefetch_related("images")
    )
    paginate_by = 4

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get("query")
        if query:
            qs = qs.filter(name__icontains=query)
        return qs


product_list = ProductListview.as_view()


class ProductDetailView(DetailView):
    model = Product
    template_name = "mall/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images"] = self.object.images.all()
        context["form"] = CommentForm()  # CommentForm을 컨텍스트에 추가
        context["option_form"] = ProductOptionForm(product=self.object)
        return context


product_detail = ProductDetailView.as_view()


@login_required
@require_POST
def add_to_cart(request, product_pk):
    try:
        data = json.loads(request.body.decode("utf-8"))
        quantity = int(data.get("product_quantity", 1))
        selected_option_id = data.get("product_option")
        product_qs = Product.objects.filter(status=Product.Status.ACTIVE)
        product = get_object_or_404(product_qs, pk=product_pk)

        if not selected_option_id:
            return HttpResponse("옵션을 선택해 주세요.", status=400)

        selected_option = get_object_or_404(ProductOption, pk=selected_option_id)

        cart_product, is_created = CartProduct.objects.get_or_create(
            user=request.user,
            product=product,
            option=selected_option,
            defaults={"quantity": quantity},
        )

        if not is_created:
            cart_product.quantity += quantity
            cart_product.save()

        return HttpResponse("ok")

    except json.JSONDecodeError:
        return HttpResponse("잘못된 요청입니다.", status=400)


@login_required
def order_list(request):
    order_qs = Order.objects.all().filter(user=request.user)
    return render(
        request,
        "mall/order_list.html",
        {
            "order_list": order_qs,
        },
    )


@login_required
def cart_detail(request):
    cart_products_qs = (
        CartProduct.objects.filter(user=request.user)
        .select_related("product")
        .order_by("product__name")
    )

    CartProductFormSet = modelformset_factory(
        model=CartProduct,
        form=CartProductForm,
        can_delete=True,
        extra=0,
    )
    if request.method == "POST":
        formset = CartProductFormSet(
            data=request.POST,
            queryset=cart_products_qs,
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, "장바구니를 수정했습니다.")
            return redirect("cart_detail")
    else:
        formset = CartProductFormSet(
            queryset=cart_products_qs,
        )

    total_price = sum(cart_product.amount for cart_product in cart_products_qs)

    return render(
        request,
        "mall/cart_detail.html",
        {
            "cart_products_list": cart_products_qs,
            "formset": formset,
            "total_price": total_price,
        },
    )


@login_required
def order_new(request):
    cart_product_qs = CartProduct.objects.filter(user=request.user)

    order = Order.create_from_cart(request.user, cart_product_qs)
    # 장바구니 상품을 세션에 저장
    request.session["cart_product_ids"] = list(
        cart_product_qs.values_list("id", flat=True)
    )

    return redirect("order_pay", order.pk)


@login_required()
def order_pay(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if not order.can_pay():
        return redirect(order)

    payment = OrderPayment.create_by_order(order)
    payment_props = {
        "merchant_uid": payment.merchant_uid,
        "name": payment.name,
        "amount": payment.desired_amount,
        "buyer_email": payment.buyer_email,
        "buyer_name": payment.buyer_name,
    }

    return render(
        request,
        "mall/order_pay.html",
        {
            "portone_shop_id": settings.PORTONE_SHOP_ID,
            "payment_props": payment_props,
            "next_url": reverse("order_check", args=[order.pk, payment.pk]),
            "pre_url": reverse("cart_detail"),
        },
    )


@login_required()
def order_check(request, order_pk, payment_pk):
    payment = get_object_or_404(OrderPayment, pk=payment_pk, order__user=request.user)
    payment.portone_check()
    if payment.is_paid_ok:
        # 결제가 성공했을 때만 장바구니 상품 삭제
        cart_product_ids = request.session.pop("cart_product_ids", [])
        CartProduct.objects.filter(id__in=cart_product_ids).delete()

    return redirect("order_detail", order_pk)


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(
        request,
        "mall/order_detail.html",
        {
            "order": order,
        },
    )
