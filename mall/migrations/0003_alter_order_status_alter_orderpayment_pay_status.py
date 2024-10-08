# Generated by Django 5.1 on 2024-08-21 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mall", "0002_alter_product_options_product_created_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("REQUSETED", "주문 요청"),
                    ("FAILED_PAYMENT", "결제 실패"),
                    ("PAID", "결제 완료"),
                    ("PREPARED_PRODUCT", "상품 준비 중"),
                    ("SHIPPED", "배송 중"),
                    ("DELIVERED", "배송 완료"),
                    ("CANCELLED", "주문 취소"),
                ],
                default="REQUSETED",
                max_length=16,
                verbose_name="진행상태",
            ),
        ),
        migrations.AlterField(
            model_name="orderpayment",
            name="pay_status",
            field=models.CharField(
                choices=[
                    ("READY", "미결제"),
                    ("PAID", "결제완료"),
                    ("CANCELLED", "결제취소"),
                    ("FAILED", "결제실패"),
                    ("VIRTUAL_ACCOUNT_ISSUED", "가상계좌"),
                ],
                default="READY",
                max_length=22,
                verbose_name="결제상태",
            ),
        ),
    ]
