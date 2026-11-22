
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from store.models import Category, Product, BusinessProfile


class Command(BaseCommand):
    help = "Import kategori, produk, dan profil usaha tanpa menghapus akun hosting"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="konten_local_utf8.json",
            help="Lokasi file JSON hasil export database lokal",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = Path(options["file"])

        if not file_path.exists():
            raise CommandError(f"File tidak ditemukan: {file_path}")

        try:
            data = json.loads(
                file_path.read_text(encoding="utf-8-sig")
            )
        except Exception as exc:
            raise CommandError(f"JSON tidak valid: {exc}")

        if not isinstance(data, list):
            raise CommandError("Format JSON harus berupa list.")

        # Validasi semua model sebelum perubahan database
        allowed_models = {
            "store.category",
            "store.product",
            "store.businessprofile",
        }

        for item in data:
            if item.get("model") not in allowed_models:
                raise CommandError(
                    f"Model tidak diizinkan: {item.get('model')}"
                )

        categories = {}
        category_count = 0
        product_count = 0
        profile_count = 0

        with transaction.atomic():
            # Import kategori dengan ID baru jika terjadi konflik
            for item in data:
                if item["model"] != "store.category":
                    continue

                fields = item["fields"]
                obj, created = Category.objects.get_or_create(
                    slug=fields["slug"],
                    defaults={
                        "name": fields["name"],
                        "description": fields.get("description", ""),
                    },
                )

                categories[item["pk"]] = obj
                category_count += int(created)

            # Import produk dengan relasi kategori yang benar
            for item in data:
                if item["model"] != "store.product":
                    continue

                fields = item["fields"]
                category = categories.get(fields.get("category"))

                if category is None:
                    raise CommandError(
                        f"Kategori produk tidak ditemukan: {fields['name']}"
                    )

                obj, created = Product.objects.get_or_create(
                    slug=fields["slug"],
                    defaults={
                        "name": fields["name"],
                        "category": category,
                        "price": fields.get("price"),
                        "description": fields.get("description", ""),
                        "composition": fields.get("composition", ""),
                        "history": fields.get("history", ""),
                        "image_path": fields.get("image_path", ""),
                        "stock": fields.get("stock", 0),
                        "is_active": fields.get("is_active", True),
                    },
                )

                product_count += int(created)

            # Import profil usaha jika belum tersedia
            for item in data:
                if item["model"] != "store.businessprofile":
                    continue

                fields = item["fields"]

                if not BusinessProfile.objects.exists():
                    BusinessProfile.objects.create(**fields)
                    profile_count += 1

        self.stdout.write(self.style.SUCCESS(
            "IMPORT BERHASIL\n"
            f"Kategori baru: {category_count}\n"
            f"Produk baru: {product_count}\n"
            f"Profil baru: {profile_count}\n"
            "Akun pengguna tidak diubah."
        ))
