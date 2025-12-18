"""
Integration Tests untuk Views
Testing HTTP endpoints dan user workflows
"""
import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

from cashier.models import DaftarBarang, DaftarTransaksi, ListProductTransaksi
from tests.factories import (
    UserFactory, ProfileFactory, DaftarBarangFactory,
    DaftarTransaksiFactory, IndomieProductFactory,
    CashierUserFactory
)


# ============================================================
# Test Setup
# ============================================================

@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.fixture
def authenticated_client(client):
    """Client dengan user yang sudah login"""
    user = CashierUserFactory()
    client.force_login(user)
    client.user = user
    return client


# ============================================================
# Home/Dashboard View Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestHomeView:
    """Test HomeIndex view"""
    
    def test_home_requires_login(self, client):
        """Test home page memerlukan login"""
        response = client.get(reverse('HomeIndex'))
        assert response.status_code == 302  # Redirect to login
        assert '/login/' in response.url
    
    def test_home_page_accessible_when_logged_in(self, authenticated_client):
        """Test home page bisa diakses setelah login"""
        response = authenticated_client.get(reverse('HomeIndex'))
        assert response.status_code == 200
        assert 'data' in response.context
    
    def test_home_displays_user_products(self, authenticated_client):
        """Test home menampilkan produk user"""
        user_profile = authenticated_client.user.profile
        product1 = DaftarBarangFactory(user=user_profile)
        product2 = DaftarBarangFactory(user=user_profile)
        
        response = authenticated_client.get(reverse('HomeIndex'))
        
        products = response.context['data']
        assert products.count() == 2
    
    def test_home_shows_daily_revenue(self, authenticated_client):
        """Test home menampilkan pendapatan hari ini"""
        user_profile = authenticated_client.user.profile
        transaksi = DaftarTransaksiFactory(
            user=user_profile,
            total=Decimal('100000.00')
        )
        
        response = authenticated_client.get(reverse('HomeIndex'))
        
        assert 'data_pendapatan' in response.context
        # Should show today's revenue


# ============================================================
# Stock Management Views Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestStockViews:
    """Test stock management views"""
    
    def test_total_stock_view(self, authenticated_client):
        """Test view total stock"""
        user_profile = authenticated_client.user.profile
        DaftarBarangFactory.create_batch(5, user=user_profile)
        
        response = authenticated_client.get(reverse('TotalStock'))
        assert response.status_code == 200
        
        # Check data in context
        assert 'data' in response.context
        assert response.context['data'].count() == 5
    
    def test_input_stock_get(self, authenticated_client):
        """Test GET input stock page"""
        response = authenticated_client.get(reverse('InputStock'))
        assert response.status_code == 200
        assert 'forms' in response.context
        assert 'stocks' in response.context
    
    def test_input_stock_post_valid(self, authenticated_client):
        """Test POST input stock dengan data valid"""
        user_profile = authenticated_client.user.profile
        
        form_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-nama_product': 'Test Product',
            'form-0-jumlah_produk': '100',
            'form-0-harga_beli_satuan': '3000',
            'form-0-laba_persen': '20',
            'form-0-user': user_profile.id,
        }
        
        response = authenticated_client.post(reverse('InputStock'), data=form_data)
        
        # Should redirect after success
        assert response.status_code == 302
        
        # Check product created
        products = DaftarBarang.objects.filter(user=user_profile)
        assert products.count() == 1
    
    def test_input_stock_post_invalid(self, authenticated_client):
        """Test POST input stock dengan data invalid"""
        user_profile = authenticated_client.user.profile
        
        form_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-0-nama_product': 'Invalid Product',
            'form-0-jumlah_produk': '0',  # Invalid: 0
            'form-0-harga_beli_satuan': '0',  # Invalid: 0
            'form-0-laba_persen': '0',  # Invalid: 0
            'form-0-user': user_profile.id,
        }
        
        response = authenticated_client.post(reverse('InputStock'), data=form_data)
        
        # Should redirect with error message
        assert response.status_code == 302


# ============================================================
# Transaction Views Tests (Critical Path)
# ============================================================

@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.critical
class TestTransactionViews:
    """Test transaction views - Critical business path"""
    
    def test_cart_get(self, authenticated_client):
        """Test GET cart/transaction page"""
        response = authenticated_client.get(reverse('Cart'))
        assert response.status_code == 200
        assert 'forms' in response.context
        assert 'data_barang' in response.context
    
    def test_cart_post_successful_transaction(self, authenticated_client):
        """Test POST successful transaction"""
        user_profile = authenticated_client.user.profile
        product = DaftarBarangFactory(
            user=user_profile,
            nama_product="Indomie",
            jumlah_produk=100,
            harga_jual_satuan=Decimal('3600.00')
        )
        
        form_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-0-nama_barang': product.nomor,
            'form-0-quantity': '10',
            'form-0-user': user_profile.id,
        }
        
        response = authenticated_client.post(reverse('Cart'), data=form_data)
        
        # Should redirect to receipt
        assert response.status_code == 302
        assert '/struck/' in response.url
        
        # Check transaction created
        transaksi = DaftarTransaksi.objects.filter(user=user_profile).first()
        assert transaksi is not None
        assert transaksi.produk_jumlah == 10
        assert transaksi.total == Decimal('36000.00')
        
        # Check stock reduced
        product.refresh_from_database()
        assert product.jumlah_produk == 90
    
    def test_cart_post_insufficient_stock(self, authenticated_client):
        """Test POST transaction dengan stock tidak cukup"""
        user_profile = authenticated_client.user.profile
        product = DaftarBarangFactory(
            user=user_profile,
            jumlah_produk=5  # Only 5 in stock
        )
        
        form_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-0-nama_barang': product.nomor,
            'form-0-quantity': '10',  # Trying to buy 10
            'form-0-user': user_profile.id,
        }
        
        response = authenticated_client.post(reverse('Cart'), data=form_data)
        
        # Should redirect with error
        assert response.status_code == 302
        
        # Stock should not change
        product.refresh_from_database()
        assert product.jumlah_produk == 5
    
    def test_cart_post_zero_quantity(self, authenticated_client):
        """Test POST transaction dengan quantity 0"""
        user_profile = authenticated_client.user.profile
        product = DaftarBarangFactory(user=user_profile)
        
        form_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-0-nama_barang': product.nomor,
            'form-0-quantity': '0',  # Zero quantity
            'form-0-user': user_profile.id,
        }
        
        response = authenticated_client.post(reverse('Cart'), data=form_data)
        
        # Should redirect with error
        assert response.status_code == 302
    
    def test_multiple_products_transaction(self, authenticated_client):
        """Test transaksi dengan multiple products"""
        user_profile = authenticated_client.user.profile
        product1 = DaftarBarangFactory(
            user=user_profile,
            jumlah_produk=100,
            harga_jual_satuan=Decimal('5000.00')
        )
        product2 = DaftarBarangFactory(
            user=user_profile,
            jumlah_produk=50,
            harga_jual_satuan=Decimal('3000.00')
        )
        
        form_data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-0-nama_barang': product1.nomor,
            'form-0-quantity': '5',
            'form-0-user': user_profile.id,
            'form-1-nama_barang': product2.nomor,
            'form-1-quantity': '10',
            'form-1-user': user_profile.id,
        }
        
        response = authenticated_client.post(reverse('Cart'), data=form_data)
        assert response.status_code == 302
        
        # Check total
        transaksi = DaftarTransaksi.objects.filter(user=user_profile).first()
        expected_total = (5 * Decimal('5000.00')) + (10 * Decimal('3000.00'))
        assert transaksi.total == expected_total


# ============================================================
# Receipt/Struck Views Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestReceiptViews:
    """Test receipt/struck views"""
    
    def test_struck_pembelian_view(self, authenticated_client):
        """Test view struck pembelian"""
        user_profile = authenticated_client.user.profile
        transaksi = DaftarTransaksiFactory(user=user_profile)
        product = ListProductTransaksiFactory(transaksi_id=transaksi)
        
        url = reverse('StruckPembelian', kwargs={'pk': transaksi.nomor})
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'dataStruck' in response.context
        assert 'dataStruckListProduk' in response.context
        assert 'dataUser' in response.context
    
    def test_daftar_pembelian_view(self, authenticated_client):
        """Test daftar pembelian view"""
        user_profile = authenticated_client.user.profile
        DaftarTransaksiFactory.create_batch(3, user=user_profile)
        
        response = authenticated_client.get(reverse('DaftarPembelian'))
        
        assert response.status_code == 200
        assert 'data' in response.context
        assert response.context['data'].count() == 3


# ============================================================
# Report Views Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestReportViews:
    """Test report views"""
    
    def test_report_view_get(self, authenticated_client):
        """Test GET report page"""
        response = authenticated_client.get(reverse('ReportView'))
        assert response.status_code == 200
    
    def test_report_view_ajax_filter(self, authenticated_client):
        """Test AJAX filter on report"""
        user_profile = authenticated_client.user.profile
        transaksi = DaftarTransaksiFactory(user=user_profile)
        ListProductTransaksiFactory(transaksi_id=transaksi)
        
        response = authenticated_client.get(
            reverse('ReportView'),
            {'startDate': '2024-01-01', 'endDate': '2024-12-31'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        assert response.status_code == 200


# ============================================================
# Authentication Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestAuthenticationViews:
    """Test authentication views"""
    
    def test_register_view_get(self, client):
        """Test GET register page"""
        response = client.get(reverse('Register'))
        assert response.status_code == 200
    
    def test_register_view_post_valid(self, client):
        """Test POST register dengan data valid"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        
        response = client.post(reverse('Register'), data=form_data)
        
        # Should redirect after success
        assert response.status_code == 302
        
        # Check user created
        user = User.objects.filter(username='newuser').first()
        assert user is not None
    
    def test_login_view(self, client):
        """Test login view"""
        user = UserFactory(password='testpass123')
        
        response = client.post(reverse('Login'), {
            'username': user.username,
            'password': 'testpass123'
        })
        
        # Should redirect after successful login
        assert response.status_code == 302
    
    def test_account_view(self, authenticated_client):
        """Test account profile view"""
        response = authenticated_client.get(reverse('Account'))
        assert response.status_code == 200
        assert 'user_form' in response.context
        assert 'profile_form' in response.context


# ============================================================
# Error Handling Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestErrorHandling:
    """Test error handling"""
    
    def test_404_handler(self, client):
        """Test 404 error page"""
        response = client.get('/nonexistent-url/')
        assert response.status_code == 404
    
    def test_access_other_user_data(self, authenticated_client):
        """Test user tidak bisa akses data user lain"""
        other_user_profile = ProfileFactory()
        other_product = DaftarBarangFactory(user=other_user_profile)
        
        # Try to view all stock (should only see own)
        response = authenticated_client.get(reverse('TotalStock'))
        
        products = response.context['data']
        assert other_product not in products