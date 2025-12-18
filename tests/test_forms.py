"""
Unit Tests untuk Forms
Testing form validation dan business logic
"""
import pytest
from decimal import Decimal
from django.test import TestCase

from cashier.forms import (
    DaftarBarangForm, DaftarTransaksiForm,
    ListProductTransaksiForm, TransaksiProductListForm
)
from cashier.models import DaftarBarang, DaftarTransaksi, ListProductTransaksi
from tests.factories import (
    ProfileFactory, DaftarBarangFactory, DaftarTransaksiFactory
)


# ============================================================
# DaftarBarangForm Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestDaftarBarangForm:
    """Test DaftarBarangForm"""
    
    def test_form_valid_data(self):
        """Test form dengan data valid"""
        profile = ProfileFactory()
        form_data = {
            'user': profile.id,
            'nama_product': 'Indomie Goreng',
            'jumlah_produk': 100,
            'unit_produk': 1,
            'harga_beli_satuan': 3000,
            'laba_persen': 20,
        }
        
        form = DaftarBarangForm(data=form_data)
        assert form.is_valid()
    
    def test_form_automatic_calculation(self):
        """Test form otomatis menghitung harga"""
        profile = ProfileFactory()
        form_data = {
            'user': profile.id,
            'nama_product': 'Test Product',
            'jumlah_produk': 10,
            'unit_produk': 1,
            'harga_beli_satuan': 5000,
            'laba_persen': 20,
        }
        
        form = DaftarBarangForm(data=form_data)
        assert form.is_valid()
        
        instance = form.save(commit=False)
        
        # Check calculations
        assert instance.subtotal_harga_beli == Decimal('50000.00')
        assert instance.harga_jual_satuan == Decimal('6000.00')
        assert instance.subtotal_harga_jual == Decimal('60000.00')
    
    def test_form_missing_required_fields(self):
        """Test form tanpa field required"""
        form_data = {
            'nama_product': 'Test Product',
            # Missing: jumlah_produk, harga_beli_satuan, laba_persen
        }
        
        form = DaftarBarangForm(data=form_data)
        assert not form.is_valid()
        assert 'jumlah_produk' in form.errors
        assert 'harga_beli_satuan' in form.errors
        assert 'laba_persen' in form.errors
    
    def test_form_with_zero_profit(self):
        """Test form dengan laba 0%"""
        profile = ProfileFactory()
        form_data = {
            'user': profile.id,
            'nama_product': 'No Profit Product',
            'jumlah_produk': 10,
            'harga_beli_satuan': 5000,
            'laba_persen': 0,
        }
        
        form = DaftarBarangForm(data=form_data)
        assert form.is_valid()
        
        instance = form.save(commit=False)
        assert instance.harga_jual_satuan == Decimal('5000.00')
    
    def test_form_with_high_profit(self):
        """Test form dengan laba tinggi (100%)"""
        profile = ProfileFactory()
        form_data = {
            'user': profile.id,
            'nama_product': 'High Profit Product',
            'jumlah_produk': 10,
            'harga_beli_satuan': 5000,
            'laba_persen': 100,
        }
        
        form = DaftarBarangForm(data=form_data)
        assert form.is_valid()
        
        instance = form.save(commit=False)
        assert instance.harga_jual_satuan == Decimal('10000.00')
    
    def test_form_save_to_database(self):
        """Test form save ke database"""
        profile = ProfileFactory()
        form_data = {
            'user': profile.id,
            'nama_product': 'DB Test Product',
            'jumlah_produk': 50,
            'harga_beli_satuan': 2000,
            'laba_persen': 25,
        }
        
        form = DaftarBarangForm(data=form_data)
        assert form.is_valid()
        
        instance = form.save()
        assert instance.nomor is not None
        
        # Verify in database
        saved = DaftarBarang.objects.get(nomor=instance.nomor)
        assert saved.nama_product == 'DB Test Product'


# ============================================================
# TransaksiProductListForm Tests (Complex Business Logic)
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestTransaksiProductListForm:
    """Test TransaksiProductListForm - Critical business logic"""
    
    def test_form_valid_data(self):
        """Test form dengan data valid"""
        product = DaftarBarangFactory(jumlah_produk=100)
        
        form_data = {
            'nama_barang': product.nomor,
            'quantity': 10,
            'user': product.user.id,
        }
        
        form = TransaksiProductListForm(data=form_data)
        assert form.is_valid()
    
    def test_transaction_reduces_stock(self):
        """Test transaksi mengurangi stock"""
        product = DaftarBarangFactory(
            nama_product="Test Product",
            jumlah_produk=100,
            harga_jual_satuan=Decimal('5000.00')
        )
        
        transaksi = DaftarTransaksiFactory(user=product.user)
        
        form_data = {
            'nama_barang': product.nomor,
            'quantity': 10,
            'user': product.user.id,
        }
        
        form = TransaksiProductListForm(data=form_data)
        assert form.is_valid()
        
        result = form.save(transaksi)
        
        # Check stock reduced
        product.refresh_from_database()
        assert product.jumlah_produk == 90
        
        # Check product added to transaction
        assert result is not False
        assert result.quantity == 10
    
    def test_transaction_fails_insufficient_stock(self):
        """Test transaksi gagal jika stock tidak cukup"""
        product = DaftarBarangFactory(
            nama_product="Limited Product",
            jumlah_produk=5,  # Only 5 in stock
            harga_jual_satuan=Decimal('5000.00')
        )
        
        transaksi = DaftarTransaksiFactory(user=product.user)
        
        form_data = {
            'nama_barang': product.nomor,
            'quantity': 10,  # Trying to buy 10
            'user': product.user.id,
        }
        
        form = TransaksiProductListForm(data=form_data)
        assert form.is_valid()
        
        result = form.save(transaksi)
        
        # Transaction should fail
        assert result is False
        
        # Stock should not change
        product.refresh_from_database()
        assert product.jumlah_produk == 5
    
    def test_transaction_deletes_product_when_stock_zero(self):
        """Test produk dihapus saat stock habis"""
        product = DaftarBarangFactory(
            nama_product="Last Stock",
            jumlah_produk=10,
            harga_jual_satuan=Decimal('5000.00')
        )
        product_id = product.nomor
        
        transaksi = DaftarTransaksiFactory(user=product.user)
        
        form_data = {
            'nama_barang': product.nomor,
            'quantity': 10,  # Buy all
            'user': product.user.id,
        }
        
        form = TransaksiProductListForm(data=form_data)
        assert form.is_valid()
        
        result = form.save(transaksi)
        
        # Product should be deleted
        assert not DaftarBarang.objects.filter(nomor=product_id).exists()
        
        # Transaction should still succeed
        assert result is not False
    
    def test_transaction_calculates_subtotal(self):
        """Test perhitungan subtotal transaksi"""
        product = DaftarBarangFactory(
            jumlah_produk=100,
            harga_jual_satuan=Decimal('5000.00')
        )
        
        transaksi = DaftarTransaksiFactory(user=product.user)
        
        form_data = {
            'nama_barang': product.nomor,
            'quantity': 5,
            'user': product.user.id,
        }
        
        form = TransaksiProductListForm(data=form_data)
        result = form.save(transaksi)
        
        # Check subtotal calculation
        expected_subtotal = Decimal('5000.00') * 5
        assert result.subtotal == expected_subtotal
    
    def test_transaction_updates_product_prices(self):
        """Test harga produk diupdate setelah transaksi"""
        product = DaftarBarangFactory(
            jumlah_produk=100,
            harga_beli_satuan=Decimal('3000.00'),
            laba_persen=20
        )
        
        original_subtotal_beli = product.subtotal_harga_beli
        original_subtotal_jual = product.subtotal_harga_jual
        
        transaksi = DaftarTransaksiFactory(user=product.user)
        
        form_data = {
            'nama_barang': product.nomor,
            'quantity': 10,
            'user': product.user.id,
        }
        
        form = TransaksiProductListForm(data=form_data)
        form.save(transaksi)
        
        product.refresh_from_database()
        
        # Subtotals should be recalculated based on new stock
        assert product.subtotal_harga_beli < original_subtotal_beli
        assert product.subtotal_harga_jual < original_subtotal_jual


# ============================================================
# DaftarTransaksiForm Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestDaftarTransaksiForm:
    """Test DaftarTransaksiForm"""
    
    def test_form_valid_data(self):
        """Test form dengan data valid"""
        profile = ProfileFactory()
        form_data = {
            'user': profile.id,
            'produk_jumlah': 5,
            'total': 50000,
        }
        
        form = DaftarTransaksiForm(data=form_data)
        assert form.is_valid()
    
    def test_form_save(self):
        """Test save transaksi"""
        profile = ProfileFactory()
        form_data = {
            'user': profile.id,
            'produk_jumlah': 3,
            'total': 30000,
        }
        
        form = DaftarTransaksiForm(data=form_data)
        assert form.is_valid()
        
        instance = form.save()
        assert instance.nomor is not None


# ============================================================
# ListProductTransaksiForm Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestListProductTransaksiForm:
    """Test ListProductTransaksiForm"""
    
    def test_form_valid_data(self):
        """Test form dengan data valid"""
        transaksi = DaftarTransaksiFactory()
        form_data = {
            'transaksi_id': transaksi.nomor,
            'nama_barang': 'Indomie',
            'quantity': 5,
            'subtotal': 15000,
        }
        
        form = ListProductTransaksiForm(data=form_data)
        assert form.is_valid()


# ============================================================
# Edge Cases & Error Handling
# ============================================================

@pytest.mark.django_db
@pytest.mark.unit
class TestFormEdgeCases:
    """Test edge cases untuk forms"""
    
    def test_form_with_negative_quantity(self):
        """Test form dengan quantity negatif"""
        product = DaftarBarangFactory()
        transaksi = DaftarTransaksiFactory(user=product.user)
        
        form_data = {
            'nama_barang': product.nomor,
            'quantity': -5,  # Negative!
            'user': product.user.id,
        }
        
        form = TransaksiProductListForm(data=form_data)
        # Form might still be valid, but save() should handle it
        if form.is_valid():
            result = form.save(transaksi)
            # Depends on implementation
    
    def test_form_with_zero_quantity(self):
        """Test form dengan quantity 0"""
        product = DaftarBarangFactory()
        transaksi = DaftarTransaksiFactory(user=product.user)
        
        form_data = {
            'nama_barang': product.nomor,
            'quantity': 0,
            'user': product.user.id,
        }
        
        form = TransaksiProductListForm(data=form_data)
        # Should ideally fail or be handled gracefully
    
    def test_concurrent_transactions_same_product(self):
        """Test 2 transaksi simultan pada produk yang sama"""
        product = DaftarBarangFactory(jumlah_produk=15)
        transaksi1 = DaftarTransaksiFactory(user=product.user)
        transaksi2 = DaftarTransaksiFactory(user=product.user)
        
        # First transaction
        form1_data = {
            'nama_barang': product.nomor,
            'quantity': 10,
            'user': product.user.id,
        }
        form1 = TransaksiProductListForm(data=form1_data)
        result1 = form1.save(transaksi1)
        assert result1 is not False
        
        # Second transaction (only 5 left)
        form2_data = {
            'nama_barang': product.nomor,
            'quantity': 10,  # Trying to buy 10, but only 5 left
            'user': product.user.id,
        }
        form2 = TransaksiProductListForm(data=form2_data)
        result2 = form2.save(transaksi2)
        assert result2 is False  # Should fail