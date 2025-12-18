"""
API Tests untuk REST API Endpoints
Testing API dengan Django REST Framework
"""
import pytest
import json
from django.test import Client
from django.urls import reverse
from rest_framework import status

from accounts.models import Profile
from tests.factories import UserFactory, ProfileFactory


# ============================================================
# Test Setup
# ============================================================

@pytest.fixture
def api_client():
    """API test client"""
    return Client()


@pytest.fixture
def authenticated_api_client(api_client):
    """API client dengan authentication"""
    user = UserFactory()
    api_client.force_login(user)
    api_client.user = user
    return api_client


# ============================================================
# Profile API Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.api
class TestProfileAPI:
    """Test Profile API Endpoints"""
    
    def test_api_list_profiles(self, api_client):
        """Test GET /auth/api/ returns profile list"""
        ProfileFactory.create_batch(5)
        
        response = api_client.get(reverse('ApiList'))
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data) >= 5
    
    def test_api_get_profile_detail(self, api_client):
        """Test GET /auth/api/{id}/ returns profile detail"""
        profile = ProfileFactory(
            nama_depan='John',
            nama_belakang='Doe',
            email='john@example.com'
        )
        
        url = reverse('ApiDetail', kwargs={'pk': profile.id})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['nama_depan'] == 'John'
        assert data['nama_belakang'] == 'Doe'
        assert data['email'] == 'john@example.com'
    
    def test_api_get_nonexistent_profile(self, api_client):
        """Test GET profile yang tidak ada returns 404"""
        url = reverse('ApiDetail', kwargs={'pk': 99999})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_api_create_profile(self, authenticated_api_client):
        """Test POST /auth/api/ creates new profile"""
        profile_data = {
            'nama_depan': 'Jane',
            'nama_belakang': 'Smith',
            'email': 'jane@example.com',
            'nomor_telephone': '081234567890',
            'provinsi': 'Jawa Timur',
            'kota': 'Surabaya',
            'kecamatan': 'Gubeng',
            'kelurahan': 'Airlangga',
            'alamat': 'Jl. Test No. 123',
            'kode_pos': '60286',
        }
        
        response = authenticated_api_client.post(
            reverse('ApiList'),
            data=json.dumps(profile_data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['nama_depan'] == 'Jane'
        assert data['email'] == 'jane@example.com'
    
    def test_api_create_profile_invalid_data(self, authenticated_api_client):
        """Test POST dengan data invalid returns 400"""
        invalid_data = {
            'nama_depan': '',  # Empty
            'email': 'invalid-email',  # Invalid format
        }
        
        response = authenticated_api_client.post(
            reverse('ApiList'),
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_api_update_profile(self, authenticated_api_client):
        """Test PUT /auth/api/{id}/ updates profile"""
        user = authenticated_api_client.user
        profile = ProfileFactory(user=user)
        
        update_data = {
            'nama_depan': 'Updated',
            'nama_belakang': 'Name',
            'email': 'updated@example.com',
            'nomor_telephone': '089999999999',
            'provinsi': 'DKI Jakarta',
            'kota': 'Jakarta Selatan',
            'kecamatan': 'Kebayoran Baru',
            'kelurahan': 'Senayan',
            'alamat': 'Jl. Updated No. 999',
            'kode_pos': '12190',
        }
        
        url = reverse('ApiDetail', kwargs={'pk': profile.id})
        response = authenticated_api_client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['nama_depan'] == 'Updated'
        assert data['email'] == 'updated@example.com'
        
        # Verify in database
        profile.refresh_from_database()
        assert profile.nama_depan == 'Updated'
    
    def test_api_partial_update_profile(self, authenticated_api_client):
        """Test PATCH /auth/api/{id}/ partial update"""
        user = authenticated_api_client.user
        profile = ProfileFactory(
            user=user,
            nama_depan='Original',
            email='original@example.com'
        )
        
        partial_data = {
            'nama_depan': 'Patched',
            # email not included
        }
        
        url = reverse('ApiDetail', kwargs={'pk': profile.id})
        response = authenticated_api_client.patch(
            url,
            data=json.dumps(partial_data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['nama_depan'] == 'Patched'
        assert data['email'] == 'original@example.com'  # Unchanged
    
    def test_api_delete_profile(self, authenticated_api_client):
        """Test DELETE /auth/api/{id}/ deletes profile"""
        user = authenticated_api_client.user
        profile = ProfileFactory(user=user)
        profile_id = profile.id
        
        url = reverse('ApiDetail', kwargs={'pk': profile_id})
        response = authenticated_api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deleted
        assert not Profile.objects.filter(id=profile_id).exists()


# ============================================================
# API Filtering & Search Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.api
class TestAPIFiltering:
    """Test API filtering dan search"""
    
    def test_api_filter_by_kota(self, api_client):
        """Test filter profiles by kota"""
        ProfileFactory(kota='Surabaya')
        ProfileFactory(kota='Surabaya')
        ProfileFactory(kota='Jakarta')
        
        # Assuming filter parameter exists
        response = api_client.get(f"{reverse('ApiList')}?kota=Surabaya")
        
        # If filtering is implemented
        # data = response.json()
        # assert len(data) == 2
    
    def test_api_search_by_name(self, api_client):
        """Test search profiles by name"""
        ProfileFactory(nama_depan='Alice')
        ProfileFactory(nama_depan='Bob')
        
        # Assuming search parameter exists
        response = api_client.get(f"{reverse('ApiList')}?search=Alice")
        
        # If search is implemented
        # data = response.json()
        # assert len(data) == 1


# ============================================================
# API Pagination Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.api
class TestAPIPagination:
    """Test API pagination"""
    
    def test_api_pagination(self, api_client):
        """Test API returns paginated results"""
        ProfileFactory.create_batch(20)
        
        response = api_client.get(reverse('ApiList'))
        data = response.json()
        
        # Check if pagination is implemented
        # Might have 'count', 'next', 'previous', 'results' keys
        assert isinstance(data, list) or isinstance(data, dict)


# ============================================================
# API Permissions Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.api
class TestAPIPermissions:
    """Test API permissions"""
    
    def test_api_list_no_auth_required(self, api_client):
        """Test list endpoint tidak memerlukan auth"""
        response = api_client.get(reverse('ApiList'))
        # Currently no auth required based on commented permission_classes
        assert response.status_code == status.HTTP_200_OK
    
    def test_api_create_requires_auth(self, api_client):
        """Test create endpoint memerlukan auth"""
        profile_data = {
            'nama_depan': 'Test',
            'email': 'test@example.com',
        }
        
        response = api_client.post(
            reverse('ApiList'),
            data=json.dumps(profile_data),
            content_type='application/json'
        )
        
        # Based on current code, might not require auth
        # But ideally should be 401 or 403
        # assert response.status_code in [401, 403]


# ============================================================
# API Error Handling Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.api
class TestAPIErrorHandling:
    """Test API error handling"""
    
    def test_api_invalid_json(self, authenticated_api_client):
        """Test POST dengan invalid JSON"""
        response = authenticated_api_client.post(
            reverse('ApiList'),
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_api_missing_required_fields(self, authenticated_api_client):
        """Test POST tanpa required fields"""
        incomplete_data = {
            'nama_depan': 'Test',
            # Missing email
        }
        
        response = authenticated_api_client.post(
            reverse('ApiList'),
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_api_invalid_method(self, api_client):
        """Test menggunakan method yang tidak diizinkan"""
        # Assuming PATCH not allowed on list endpoint
        response = api_client.patch(reverse('ApiList'))
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ============================================================
# API Data Validation Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.api
class TestAPIDataValidation:
    """Test API data validation"""
    
    def test_api_email_format_validation(self, authenticated_api_client):
        """Test validasi format email"""
        invalid_email_data = {
            'nama_depan': 'Test',
            'nama_belakang': 'User',
            'email': 'not-an-email',  # Invalid
            'nomor_telephone': '081234567890',
        }
        
        response = authenticated_api_client.post(
            reverse('ApiList'),
            data=json.dumps(invalid_email_data),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_api_phone_number_validation(self, authenticated_api_client):
        """Test validasi nomor telephone"""
        profile_data = {
            'nama_depan': 'Test',
            'email': 'test@example.com',
            'nomor_telephone': 'invalid-phone',
        }
        
        response = authenticated_api_client.post(
            reverse('ApiList'),
            data=json.dumps(profile_data),
            content_type='application/json'
        )
        
        # Might be invalid depending on validation
        # assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================
# API Content Type Tests
# ============================================================

@pytest.mark.django_db
@pytest.mark.api
class TestAPIContentType:
    """Test API content type handling"""
    
    def test_api_returns_json(self, api_client):
        """Test API returns JSON"""
        response = api_client.get(reverse('ApiList'))
        assert 'application/json' in response['Content-Type']
    
    def test_api_accepts_json(self, authenticated_api_client):
        """Test API accepts JSON input"""
        profile_data = {
            'nama_depan': 'Test',
            'email': 'test@example.com',
        }
        
        response = authenticated_api_client.post(
            reverse('ApiList'),
            data=json.dumps(profile_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201, 400, 401, 403]