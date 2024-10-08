# Generated by Django 5.1 on 2024-08-21 09:03

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mall", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="product",
            options={
                "ordering": ["-pk"],
                "verbose_name": "상품",
                "verbose_name_plural": "상품",
            },
        ),
        migrations.AddField(
            model_name="product",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="product",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("uid", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("total_amount", models.PositiveIntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("requested", "주문 요청"),
                            ("failed_payment", "결제 실패"),
                            ("paid", "결제 완료"),
                            ("perpared_product", "상품 준비 중"),
                            ("shipped", "배송 중"),
                            ("delivered", "배송 완료"),
                            ("cancelled", "주문 취소"),
                        ],
                        default="requested",
                        max_length=16,
                        verbose_name="진행상태",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "주문",
                "verbose_name_plural": "주문",
                "ordering": ["-pk"],
            },
        ),
        migrations.CreateModel(
            name="OrderedProduct",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="주문 시점의 상품명을 저장합니다.",
                        max_length=100,
                        verbose_name="상품명",
                    ),
                ),
                (
                    "price",
                    models.PositiveIntegerField(
                        help_text="주문 시점의 상품가격을 저장합니다.",
                        verbose_name="상품가격",
                    ),
                ),
                ("quantity", models.PositiveIntegerField(verbose_name="수량")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "order",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mall.order",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mall.product",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="order",
            name="product_set",
            field=models.ManyToManyField(
                through="mall.OrderedProduct", to="mall.product"
            ),
        ),
        migrations.CreateModel(
            name="OrderPayment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "meta",
                    models.JSONField(
                        default=dict, editable=False, verbose_name="포트원 결제내역"
                    ),
                ),
                (
                    "uid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        verbose_name="쇼핑몰 결제식별자",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        editable=False, max_length=200, verbose_name="결제명"
                    ),
                ),
                (
                    "desired_amount",
                    models.PositiveIntegerField(
                        editable=False, verbose_name="결제요청금액"
                    ),
                ),
                (
                    "buyer_name",
                    models.CharField(
                        editable=False, max_length=100, verbose_name="구매자명"
                    ),
                ),
                (
                    "buyer_email",
                    models.EmailField(
                        editable=False, max_length=254, verbose_name="구매자 이메일"
                    ),
                ),
                (
                    "pay_method",
                    models.CharField(
                        choices=[
                            ("card", "카드 결제"),
                            ("virutal_account", "가상계좌 결제"),
                        ],
                        default="card",
                        max_length=20,
                        verbose_name="결제수단",
                    ),
                ),
                (
                    "pay_status",
                    models.CharField(
                        choices=[
                            ("ready", "미결제"),
                            ("paid", "결제완료"),
                            ("cencelled", "결제취소"),
                            ("failed", "결제실패"),
                            ("virtualAccountIssued", "가상계좌"),
                        ],
                        default="ready",
                        max_length=20,
                        verbose_name="결제상태",
                    ),
                ),
                (
                    "is_paid_ok",
                    models.BooleanField(
                        db_index=True, default=False, verbose_name="결제성공여부"
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mall.order",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CartProduct",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "quantity",
                    models.PositiveIntegerField(
                        default=1,
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="mall.product",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cart_products_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "장바구니 상품",
                "verbose_name_plural": "장바구니 상품",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("user", "product"), name="unique_user_product"
                    )
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="orderedproduct",
            constraint=models.UniqueConstraint(
                fields=("order", "product"), name="unique_order_product"
            ),
        ),
    ]
