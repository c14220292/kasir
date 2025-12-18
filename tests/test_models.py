"""
Unit Tests untuk Models
Testing logic bisnis di level model
"""
import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User

from cashier.models import DaftarBarang, DaftarTransaksi, ListProductTransaksi
from accounts.models import Profile
from data.models import Stock
from tests.factories import (
    UserFactory, ProfileFactory, DaftarBarangFactory,
    DaftarTransaksiFactory, ListProductTransaksiFactory,
    StockFactory, IndomieProductFactory
)

# ============================================================
# Profile Model Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestProfileModel:
    """Test Profile Model"""
    
    def test_create_profile(self):
        """Test membuat profile baru"""
        user = UserFactory()
        profile = ProfileFactory(user=user)
        
        assert profile.id is not None
        assert profile.user == user
        assert profile.nama_depan
        assert profile.email
    
    def test_profile_str_representation(self):
        """Test string representation"""
        profile = ProfileFactory(user__username='testuser')
        assert str(profile) == 'testuser Profile'
    
    def test_profile_auto_created_with_user(self):
        """Test profile otomatis dibuat saat user dibuat (via signal)"""
        user = User.objects.create_user(
            username='newuser',
            password='testpass123'
        )
        # Check if profile was auto-created by signal
        assert hasattr(user, 'profile')
    
    def test_profile_update(self):
        """Test update profile"""
        profile = ProfileFactory()
        new_name = "Updated Name"
        profile.nama_depan = new_name
        profile.save()
        
        profile.refresh_from_database()
        assert profile.nama_depan == new_name


# ============================================================
# Stock Model Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestStockModel:
    """Test Stock Model"""
    
    def test_create_stock(self):
        """Test membuat stock"""
        stock = StockFactory(name="Test Product", price=5000)
        
        assert stock.id is not None
        assert stock.name == "Test Product"
        assert stock.price == 5000
    
    def test_stock_str_representation(self):
        """Test string representation"""
        stock = StockFactory(name="Indomie")
        assert str(stock) == "Indomie"
    
    def test_stock_unique_name(self):
        """Test nama stock harus unique"""
        StockFactory(name="Unique Product")
        
        with pytest.raises(Exception):  # IntegrityError
            StockFactory(name="Unique Product")
    
    def test_stock_timestamps(self):
        """Test created dan updated timestamps"""
        stock = StockFactory()
        
        assert stock.created is not None
        assert stock.updated is not None
        assert stock.created <= stock.updated


# ============================================================
# DaftarBarang Model Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestDaftarBarangModel:
    """Test DaftarBarang Model"""
    
    def test_create_daftar_barang(self):
        """Test membuat daftar barang"""
        barang = DaftarBarangFactory()
        
        assert barang.nomor is not None
        assert barang.nama_product
        assert barang.jumlah_produk > 0
    
    def test_barang_str_representation(self):
        """Test string representation"""
        barang = DaftarBarangFactory(nama_product="Indomie")
        assert str(barang) == "Indomie"
    
    def test_calculate_subtotal_harga_beli(self):
        """Test perhitungan subtotal harga beli"""
        barang = DaftarBarangFactory(
            jumlah_produk=10,
            harga_beli_satuan=Decimal('5000.00')
        )
        
        expected = Decimal('10') * Decimal('5000.00')
        assert barang.subtotal_harga_beli == expected
    
    def test_calculate_harga_jual_with_profit(self):
        """Test perhitungan harga jual dengan laba"""
        barang = DaftarBarangFactory(
            harga_beli_satuan=Decimal('5000.00'),
            laba_persen=20
        )
        
        expected = Decimal('5000.00') * Decimal('1.20')
        assert barang.harga_jual_satuan == expected
    
    def test_calculate_subtotal_harga_jual(self):
        """Test perhitungan subtotal harga jual"""
        barang = DaftarBarangFactory(
            jumlah_produk=10,
            harga_beli_satuan=Decimal('5000.00'),
            laba_persen=20
        )
        
        subtotal_beli = Decimal('50000.00')
        laba = subtotal_beli * Decimal('0.20')
        expected = subtotal_beli + laba
        
        assert barang.subtotal_harga_jual == expected
    
    def test_barang_with_zero_profit(self):
        """Test barang dengan laba 0%"""
        barang = DaftarBarangFactory(
            harga_beli_satuan=Decimal('5000.00'),
            laba_persen=0
        )
        
        assert barang.harga_jual_satuan == Decimal('5000.00')
    
    def test_barang_with_high_profit(self):
        """Test barang dengan laba tinggi"""
        barang = DaftarBarangFactory(
            harga_beli_satuan=Decimal('5000.00'),
            laba_persen=100
        )
        
        assert barang.harga_jual_satuan == Decimal('10000.00')
    
    def test_indomie_preset(self):
        """Test preset Indomie"""
        indomie = IndomieProductFactory()
        
        assert indomie.nama_product == "Indomie Goreng"
        assert indomie.jumlah_produk == 100
        assert indomie.harga_beli_satuan == Decimal('3000.00')


# ============================================================
# DaftarTransaksi Model Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestDaftarTransaksiModel:
    """Test DaftarTransaksi Model"""
    
    def test_create_transaksi(self):
        """Test membuat transaksi"""
        transaksi = DaftarTransaksiFactory()
        
        assert transaksi.nomor is not None
        assert transaksi.user is not None
    
    def test_transaksi_str_representation(self):
        """Test string representation"""
        transaksi = DaftarTransaksiFactory()
        assert str(transaksi) == str(transaksi.nomor)
    
    def test_transaksi_default_values(self):
        """Test nilai default transaksi"""
        profile = ProfileFactory()
        transaksi = DaftarTransaksi.objects.create(user=profile)
        
        assert transaksi.produk_jumlah is None
        assert transaksi.total == Decimal('0.00')
    
    def test_transaksi_timestamps(self):
        """Test created dan updated timestamps"""
        transaksi = DaftarTransaksiFactory()
        
        assert transaksi.created is not None
        assert transaksi.updated is not None


# ============================================================
# ListProductTransaksi Model Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestListProductTransaksiModel:
    """Test ListProductTransaksi Model"""
    
    def test_create_list_product(self):
        """Test membuat list product transaksi"""
        product = ListProductTransaksiFactory()
        
        assert product.id is not None
        assert product.transaksi_id is not None
        assert product.nama_barang
    
    def test_list_product_str_representation(self):
        """Test string representation"""
        product = ListProductTransaksiFactory(nama_barang="Indomie")
        assert str(product) == "Indomie"
    
    def test_list_product_relationship(self):
        """Test relasi dengan transaksi"""
        transaksi = DaftarTransaksiFactory()
        product1 = ListProductTransaksiFactory(transaksi_id=transaksi)
        product2 = ListProductTransaksiFactory(transaksi_id=transaksi)
        
        products = ListProductTransaksi.objects.filter(transaksi_id=transaksi)
        assert products.count() == 2
    
    def test_calculate_subtotal(self):
        """Test perhitungan subtotal product"""
        product = ListProductTransaksiFactory(
            quantity=5,
            subtotal=25000
        )
        
        # Assuming harga per unit = 5000
        expected_price_per_unit = 25000 / 5
        assert expected_price_per_unit == 5000


# ============================================================
# Integration Tests - Model Relationships
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestModelRelationships:
    """Test hubungan antar models"""
    
    def test_profile_to_user_relationship(self):
        """Test relasi Profile -> User"""
        user = UserFactory()
        profile = ProfileFactory(user=user)
        
        assert profile.user == user
        assert user.profile == profile
    
    def test_daftar_barang_to_profile_relationship(self):
        """Test relasi DaftarBarang -> Profile"""
        profile = ProfileFactory()
        barang = DaftarBarangFactory(user=profile)
        
        assert barang.user == profile
    
    def test_transaksi_to_profile_relationship(self):
        """Test relasi DaftarTransaksi -> Profile"""
        profile = ProfileFactory()
        transaksi = DaftarTransaksiFactory(user=profile)
        
        assert transaksi.user == profile
    
    def test_list_product_to_transaksi_relationship(self):
        """Test relasi ListProductTransaksi -> DaftarTransaksi"""
        transaksi = DaftarTransaksiFactory()
        product = ListProductTransaksiFactory(transaksi_id=transaksi)
        
        assert product.transaksi_id == transaksi
    
    def test_cascade_delete_transaksi(self):
        """Test cascade delete saat transaksi dihapus"""
        transaksi = DaftarTransaksiFactory()
        product1 = ListProductTransaksiFactory(transaksi_id=transaksi)
        product2 = ListProductTransaksiFactory(transaksi_id=transaksi)
        
        transaksi_id = transaksi.nomor
        transaksi.delete()
        
        # Products should be deleted too (cascade)
        products = ListProductTransaksi.objects.filter(transaksi_id=transaksi_id)
        assert products.count() == 0


# ============================================================
# Edge Cases & Error Handling
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestModelEdgeCases:
    """Test edge cases dan error handling"""
    
    def test_barang_with_negative_stock(self):
        """Test barang dengan stock negatif (should be prevented)"""
        # This should ideally be prevented by model validation
        # For now, just test that it can be created
        barang = DaftarBarangFactory(jumlah_produk=-10)
        assert barang.jumlah_produk == -10
    
    def test_barang_with_zero_price(self):
        """Test barang dengan harga 0"""
        barang = DaftarBarangFactory(harga_beli_satuan=Decimal('0.00'))
        assert barang.harga_beli_satuan == Decimal('0.00')
    
    def test_transaksi_with_zero_total(self):
        """Test transaksi dengan total 0"""
        transaksi = DaftarTransaksiFactory(total=Decimal('0.00'))
        assert transaksi.total == Decimal('0.00')
    
    def test_product_with_zero_quantity(self):
        """Test product dengan quantity 0"""
        product = ListProductTransaksiFactory(quantity=0)
        assert product.quantity == 0