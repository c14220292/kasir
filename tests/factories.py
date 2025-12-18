"""
Test Factories untuk Generate Fake Data
Menggunakan Factory Boy + Faker
"""
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyDecimal
from faker import Faker
from datetime import date, timedelta
from django.contrib.auth.models import User

from accounts.models import Profile
from cashier.models import DaftarBarang, DaftarTransaksi, ListProductTransaksi
from data.models import Stock

fake = Faker('id_ID')  # Indonesian locale

# ============================================================
# User & Profile Factories
# ============================================================

class UserFactory(DjangoModelFactory):
    """Factory untuk Django User"""
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name', locale='id_ID')
    last_name = factory.Faker('last_name', locale='id_ID')
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password('testpass123')


class ProfileFactory(DjangoModelFactory):
    """Factory untuk Profile User"""
    class Meta:
        model = Profile
    
    user = factory.SubFactory(UserFactory)
    picture = 'profile_pictures/default.png'
    nama_depan = factory.Faker('first_name', locale='id_ID')
    nama_belakang = factory.Faker('last_name', locale='id_ID')
    email = factory.LazyAttribute(lambda obj: f'{obj.nama_depan.lower()}@example.com')
    nomor_telephone = factory.Faker('phone_number', locale='id_ID')
    provinsi = factory.Faker('state', locale='id_ID')
    kota = factory.Faker('city', locale='id_ID')
    kecamatan = factory.Faker('city', locale='id_ID')
    kelurahan = factory.Faker('city', locale='id_ID')
    alamat = factory.Faker('address', locale='id_ID')
    kode_pos = factory.Faker('postcode', locale='id_ID')


# ============================================================
# Stock Factory
# ============================================================

class StockFactory(DjangoModelFactory):
    """Factory untuk Stock"""
    class Meta:
        model = Stock
    
    name = factory.Sequence(lambda n: f'Product-{n}')
    price = FuzzyInteger(1000, 100000)


# ============================================================
# Cashier Factories
# ============================================================

class DaftarBarangFactory(DjangoModelFactory):
    """Factory untuk Daftar Barang"""
    class Meta:
        model = DaftarBarang
    
    user = factory.SubFactory(ProfileFactory)
    nama_product = factory.Faker('word', locale='id_ID')
    jumlah_produk = FuzzyInteger(10, 1000)
    unit_produk = FuzzyInteger(1, 10)
    harga_beli_satuan = FuzzyDecimal(1000.0, 100000.0, 2)
    laba_persen = FuzzyInteger(10, 50)
    
    # Calculated fields - will be set by form/model save()
    subtotal_harga_beli = None
    harga_jual_satuan = None
    subtotal_harga_jual = None
    
    @factory.post_generation
    def calculate_prices(obj, create, extracted, **kwargs):
        """Calculate prices after creation"""
        if create:
            obj.subtotal_harga_beli = obj.jumlah_produk * obj.harga_beli_satuan
            obj.harga_jual_satuan = obj.harga_beli_satuan * (1 + obj.laba_persen / 100)
            laba = obj.laba_persen * obj.subtotal_harga_beli / 100
            obj.subtotal_harga_jual = laba + obj.subtotal_harga_beli
            obj.save()


class DaftarTransaksiFactory(DjangoModelFactory):
    """Factory untuk Daftar Transaksi"""
    class Meta:
        model = DaftarTransaksi
    
    user = factory.SubFactory(ProfileFactory)
    produk_jumlah = FuzzyInteger(1, 10)
    total = FuzzyDecimal(10000.0, 1000000.0, 2)


class ListProductTransaksiFactory(DjangoModelFactory):
    """Factory untuk List Product dalam Transaksi"""
    class Meta:
        model = ListProductTransaksi
    
    transaksi_id = factory.SubFactory(DaftarTransaksiFactory)
    nama_barang = factory.Faker('word', locale='id_ID')
    quantity = FuzzyInteger(1, 20)
    subtotal = FuzzyInteger(10000, 500000)


# ============================================================
# Preset Factories untuk Scenarios Spesifik
# ============================================================

class IndomieProductFactory(DaftarBarangFactory):
    """Preset: Indomie Goreng"""
    nama_product = "Indomie Goreng"
    jumlah_produk = 100
    harga_beli_satuan = 3000
    laba_persen = 20


class MieGacoanProductFactory(DaftarBarangFactory):
    """Preset: Mie Gacoan Frozen"""
    nama_product = "Mie Gacoan Frozen"
    jumlah_produk = 50
    harga_beli_satuan = 15000
    laba_persen = 30


class AquaProductFactory(DaftarBarangFactory):
    """Preset: Aqua 600ml"""
    nama_product = "Aqua 600ml"
    jumlah_produk = 200
    harga_beli_satuan = 2500
    laba_persen = 25


class CashierUserFactory(UserFactory):
    """Preset: Cashier User"""
    username = factory.Sequence(lambda n: f'kasir{n}')
    first_name = "Kasir"
    is_staff = True


class AdminUserFactory(UserFactory):
    """Preset: Admin User"""
    username = "admin"
    first_name = "Administrator"
    is_staff = True
    is_superuser = True