import logging
from uuid import uuid4
from typing import List

import requests
from PIL import Image
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint, QuerySet
from django.http import Http404
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from iamport import Iamport

from PaymentPractice import settings
from accounts.models import User

logger = logging.getLogger(__name__)


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = verbose_name_plural = "상품 분류"


class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = (
            "a",
            "판매 중",
        )
        INACTIVE = (
            "i",
            "판매 중지",
        )
        SOLD_OUT = (
            "s",
            "품절",
        )
        OBSOLETE = (
            "o",
            "단종",
        )

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, db_constraint=False
    )

    name = models.CharField(max_length=100, db_index=True)
    description = CKEditor5Field("설명", config_name="extends")  # CKEditor 5 필드 적용
    price = models.PositiveIntegerField()  # 0 포함
    status = models.CharField(
        choices=Status.choices, default=Status.ACTIVE, max_length=1
    )  # 제품 상태
    specifications = models.JSONField("제품 사양", default=dict)  # 제품 사양
    presentation_image = models.ImageField(
        upload_to="mall/product/presentation/%Y/%m/%d",
        blank=True,
        null=True,
        verbose_name="Presentation 이미지",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.pk}> {self.name}"

    class Meta:
        verbose_name = verbose_name_plural = "상품"
        ordering = ["-pk"]


class ProductOption(models.Model):
    product = models.ForeignKey(
        Product, related_name="options", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)  # 옵션 이름 (예: 색상, 크기 등)
    additional_price = models.PositiveIntegerField(default=0)  # 추가 금액

    def __str__(self):
        return f"{self.product.name} - {self.name} (+{self.additional_price}원)"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="mall/product/images/%Y/%m/%d")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

    def __str__(self):
        return f"Image for {self.product.name}"

    class Meta:
        verbose_name = "상품 이미지"
        verbose_name_plural = "상품 이미지"


class Comment(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="comments"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField("댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name}의 댓글: {self.content}"


class CartProduct(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="cart_products_set",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_constraint=False)
    option = models.ForeignKey(
        ProductOption, on_delete=models.CASCADE, null=True, blank=True
    )  # 새로운 필드 추가
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    @property
    def total_price(self):
        return (self.product.price + self.option.additional_price) * self.quantity

    @property
    def amount(self):
        return self.total_price

    def __str__(self):
        return f"<{self.pk}> {self.product.name} - {self.option.name if self.option else '기본 옵션'} ({self.quantity}개)"

    class Meta:
        verbose_name = verbose_name_plural = "장바구니 상품"
        constraints = [
            UniqueConstraint(
                fields=["user", "product", "option"], name="unique_user_product_option"
            )
        ]


class Order(models.Model):
    class Status(models.TextChoices):
        REQUSETED = (
            "REQUSETED",
            "주문 요청",
        )
        FAILED_PAYMENT = (
            "FAILED_PAYMENT",
            "결제 실패",
        )
        PAID = (
            "PAID",
            "결제 완료",
        )
        PREPARED_PRODUCT = (
            "PREPARED_PRODUCT",
            "상품 준비 중",
        )
        SHIPPED = (
            "SHIPPED",
            "배송 중",
        )
        DELIVERED = (
            "DELIVERED",
            "배송 완료",
        )
        CANCELLED = (
            "CANCELLED",
            "주문 취소",
        )

    uid = models.UUIDField(default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_constraint=False)
    total_amount = models.PositiveIntegerField()
    status = models.CharField(
        "진행상태", choices=Status.choices, default=Status.REQUSETED, max_length=16
    )
    product_set = models.ManyToManyField(Product, through="OrderedProduct", blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self) -> str:
        return reverse("order_detail", args=[self.pk])

    def can_pay(self):
        return self.status in (self.Status.REQUSETED, self.Status.FAILED_PAYMENT)

    def cancel(self, reason=""):
        for payment in self.orderpayment_set.all():
            payment.cancel(reason=reason)

    def mark_as_prepared(self):
        """주문을 상품 준비 중 상태로 변경합니다."""
        if self.status != self.Status.PAID:
            raise ValueError(
                "결제 완료 상태인 주문만 상품 준비 중 상태로 변경할 수 있습니다."
            )
        self.status = self.Status.PREPARED_PRODUCT
        self.save()

    def mark_as_shipped(self):
        """주문을 배송 중 상태로 변경합니다."""
        if self.status != self.Status.PREPARED_PRODUCT:
            raise ValueError(
                "상품 준비 중 상태인 주문만 배송 중 상태로 변경할 수 있습니다."
            )
        self.status = self.Status.SHIPPED
        self.save()

    def mark_as_delivered(self):
        """주문을 배송 완료 상태로 변경합니다."""
        if self.status != self.Status.SHIPPED:
            raise ValueError(
                "배송 중 상태인 주문만 배송 완료 상태로 변경할 수 있습니다."
            )
        self.status = self.Status.DELIVERED
        self.save()

    @property
    def name(self):
        first_product = self.product_set.first()
        if first_product is None:
            return "주문 상품 없음"
        size = self.product_set.all().count()
        if size < 2:
            return first_product.name
        return f"{first_product.name} 외 {size - 1}건"

    @classmethod
    def create_from_cart(
        cls, user: User, cart_product_qs: QuerySet[CartProduct]
    ) -> "Order":
        cart_product_list: List[CartProduct] = list(cart_product_qs)
        total_amount = sum(cart_product.amount for cart_product in cart_product_list)
        order = cls.objects.create(user=user, total_amount=total_amount)

        ordered_product_list = []
        for cart_product in cart_product_list:
            product = cart_product.product
            ordered_product = OrderedProduct(
                order=order,
                product=product,
                name=product.name,
                price=product.price,
                quantity=cart_product.quantity,
            )
            ordered_product_list.append(ordered_product)

        OrderedProduct.objects.bulk_create(ordered_product_list)

        return order

    class Meta:
        ordering = ["-pk"]
        verbose_name = verbose_name_plural = "주문"


class OrderedProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_constraint=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, db_constraint=False)
    name = models.CharField(
        "상품명", max_length=100, help_text="주문 시점의 상품명을 저장합니다."
    )
    price = models.PositiveIntegerField(
        "상품가격", help_text="주문 시점의 상품가격을 저장합니다."
    )
    quantity = models.PositiveIntegerField("수량")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["order", "product"], name="unique_order_product")
        ]


class AbstarctPortOnePayment(models.Model):
    class PayMethod(models.TextChoices):
        CARD = (
            "card",
            "카드 결제",
        )
        VIRUTAL_ACCOUNT = (
            "virutal_account",
            "가상계좌 결제",
        )

    class PayStatus(models.TextChoices):
        READY = "READY", "미결제"
        PAID = "PAID", "결제완료"
        CANCELLED = "CANCELLED", "결제취소"
        FAILED = "FAILED", "결제실패"
        VIRTUAL_ACCOUNT_ISSUED = "VIRTUAL_ACCOUNT_ISSUED", "가상계좌"

    meta = models.JSONField("포트원 결제내역", default=dict, editable=False)
    uid = models.UUIDField("쇼핑몰 결제식별자", default=uuid4, editable=False)
    name = models.CharField("결제명", max_length=200, editable=False)
    desired_amount = models.PositiveIntegerField("결제요청금액", editable=False)
    buyer_name = models.CharField("구매자명", max_length=100, editable=False)
    buyer_email = models.EmailField("구매자 이메일", editable=False)
    pay_method = models.CharField(
        "결제수단", choices=PayMethod.choices, max_length=20, default=PayMethod.CARD
    )
    pay_status = models.CharField(
        "결제상태", choices=PayStatus.choices, max_length=22, default=PayStatus.READY
    )
    is_paid_ok = models.BooleanField("결제성공여부", default=False, db_index=True)

    @property
    def merchant_uid(self):
        return str(self.uid)

    def portone_check(self):
        try:
            response = requests.get(
                f"https://api.portone.io/payments/{self.merchant_uid}",
                headers={"Authorization": f"PortOne {settings.PORTONE_API_SECRET}"},
            )
            self.meta = response.json()
            print(response.json())

        except (Iamport.ResponseError, Iamport.HttpError) as e:
            logger.error(str(e), exc_info=e)
            raise Http404("포트원에서 결제 내역을 찾을 수 없습니다.")

        self.pay_status = self.meta["status"]
        self.is_paid_ok = (
            self.meta["status"] == "PAID"
            and self.meta["amount"]["total"] == self.desired_amount
        )

        # TODO : 결제는 되었는데, 결제 금액이 맞지 않는 경우 -> 의심된다는 플래그 지정
        self.save()

    # TODO : 결제 취소 기능 구현
    def cancel(self, reason):
        """결제를 취소합니다."""
        print(self.pay_status)
        if self.pay_status != self.PayStatus.PAID:
            raise ValueError("결제 완료 상태만 취소할 수 있습니다.")

        url = f"https://api.portone.io/payments/{self.merchant_uid}/cancel"
        payload = {"reason": reason}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"PortOne {settings.PORTONE_API_SECRET}",
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            print(response_data)

            if response.status_code == 200:
                # 취소가 성공적으로 처리된 경우 상태를 업데이트합니다.
                self.pay_status = self.PayStatus.CANCELLED
                self.save()

                # 상태를 취소로 변경하는 메서드 호출 (구체적인 클래스에서 구현됨)
                self.update_related_statuses_to_cancelled()

            else:
                raise ValueError(
                    f"결제 취소 실패: {response_data.get('message', '알 수 없는 오류')}"
                )

        except requests.exceptions.RequestException as e:
            logger.error(str(e), exc_info=e)
            raise Http404("포트원 결제 취소 요청 중 오류가 발생했습니다.")

    def update_related_statuses_to_cancelled(self):
        """연관된 상태를 취소로 변경하기 위한 메서드. 상속받는 클래스에서 구현해야 합니다."""
        raise NotImplementedError("이 메서드는 상속받는 클래스에서 구현해야 합니다.")

    def handle_cancel_error(self, status_code, response_data):
        """취소 실패 시 발생할 수 있는 오류를 처리합니다."""
        error_message = response_data.get("message", "알 수 없는 오류가 발생했습니다.")

        if status_code == 400:
            raise ValueError(f"잘못된 요청: {error_message}")
        elif status_code == 401:
            raise PermissionError(f"인증 오류: {error_message}")
        elif status_code == 403:
            raise PermissionError(f"요청 거절: {error_message}")
        elif status_code == 404:
            raise ValueError(f"결제 건을 찾을 수 없습니다: {error_message}")
        elif status_code == 409:
            if "PaymentNotPaidError" in error_message:
                raise ValueError("결제가 완료되지 않았습니다.")
            elif "PaymentAlreadyCancelledError" in error_message:
                raise ValueError("결제가 이미 취소되었습니다.")
            elif "CancellableAmountConsistencyBrokenError" in error_message:
                raise ValueError("취소 가능 잔액 검증에 실패했습니다.")
            elif "CancelAmountExceedsCancellableAmountError" in error_message:
                raise ValueError("결제 취소 금액이 취소 가능 금액을 초과했습니다.")
            elif "SumOfPartsExceedsCancelAmountError" in error_message:
                raise ValueError(
                    "면세 금액 등 하위 항목들의 합이 전체 취소 금액을 초과했습니다."
                )
            elif (
                "CancelTaxFreeAmountExceedsCancellableTaxFreeAmountError"
                in error_message
            ):
                raise ValueError(
                    "취소 면세 금액이 취소 가능한 면세 금액을 초과했습니다."
                )
            elif "CancelTaxAmountExceedsCancellableTaxAmountError" in error_message:
                raise ValueError(
                    "취소 과세 금액이 취소 가능한 과세 금액을 초과했습니다."
                )
            elif (
                "RemainedAmountLessThanPromotionMinPaymentAmountError" in error_message
            ):
                raise ValueError(
                    "남은 금액이 프로모션 최소 결제 금액보다 작아질 수 없습니다."
                )
            else:
                raise ValueError(f"취소 실패: {error_message}")
        else:
            raise ValueError(f"취소 실패: {error_message}")

    class Meta:
        abstract = True


class OrderPayment(AbstarctPortOnePayment):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_constraint=False)

    def portone_check(self):
        super().portone_check()

        if self.is_paid_ok:
            self.order.status = Order.Status.PAID
            self.order.save()
            self.order.orderpayment_set.exclude(pk=self.pk).delete()

        elif self.pay_status == self.PayStatus.FAILED:
            self.order.status = Order.Status.FAILED_PAYMENT
            self.order.save()

        elif self.pay_status == self.PayStatus.CANCELLED:
            self.order.status = Order.Status.CANCELLED
            self.order.save()

    def update_related_statuses_to_cancelled(self):
        """연관된 상태를 취소로 변경합니다."""
        self.order.status = Order.Status.CANCELLED
        self.order.save()

    @classmethod
    def create_by_order(cls, order: Order) -> "OrderPayment":
        order_payment = cls.objects.create(
            order=order,
            name=order.name,
            desired_amount=order.total_amount,
            buyer_name=order.user.get_full_name() or order.user.username,
            buyer_email=order.user.email,
        )

        return order_payment
