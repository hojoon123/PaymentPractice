from dataclasses import dataclass
import requests
from django.core.management import BaseCommand
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

from mall.models import Category, Product, ProductImage

BASE_URL = "https://raw.githubusercontent.com/pyhub-kr/dump-data/main/django-shopping-with-iamport/"


@dataclass
class Item:
    category_name: str
    name: str
    price: int
    priceUnit: str
    desc: str
    photo_path: str


class Command(BaseCommand):
    help = "Load products from JSON file"

    def handle(self, *args, **options):
        json_url = BASE_URL + "product-list.json"
        item_dict_list = requests.get(json_url).json()

        item_list = [Item(**item) for item in item_dict_list]

        category_name_set = {item.category_name for item in item_list}

        category_dict = {}
        for category_name in category_name_set:
            category, __ = Category.objects.get_or_create(
                name=category_name or "미분류"
            )
            category_dict[category.name] = category

        from tqdm import tqdm

        for item in tqdm(item_list):
            category: Category = category_dict[item.category_name or "미분류"]
            product, is_created = Product.objects.get_or_create(
                category=category,
                name=item.name,
                defaults={
                    "description": item.desc,
                    "price": item.price,
                },
            )
            print(f"Product created: {item.photo_path}")
            photo_url = BASE_URL + item.photo_path
            filename = photo_url.rsplit("/", 1)[-1]
            photo_data = requests.get(photo_url).content

            # 이미지 데이터를 PIL Image로 변환
            image = Image.open(BytesIO(photo_data))

            # 이미지가 P 또는 RGBA 모드인 경우, RGB로 변환
            if image.mode in ("P", "RGBA"):
                image = image.convert("RGB")

            # 이미지를 BytesIO에 저장하여 ContentFile로 변환
            image_io = BytesIO()
            image.save(image_io, format="JPEG")
            image_io.seek(0)

            # ProductImage에 이미지 저장
            product_image = ProductImage(
                product=product,
            )
            product_image.image.save(
                name=filename, content=ContentFile(image_io.read()), save=True
            )
