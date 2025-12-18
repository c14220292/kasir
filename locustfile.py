"""
Locust Performance Testing untuk Sistem Kasir
Load testing dan stress testing
"""
from locust import HttpUser, task, between, SequentialTaskSet
import random


# ============================================================
# Configuration
# ============================================================

RESPONSE_TIME_LIMIT_MS = 3000.0  # SLO: 3 seconds max


# ============================================================
# Test Data
# ============================================================

USERNAMES = ['kasir1', 'kasir2', 'kasir3', 'kasir4', 'kasir5']
PASSWORDS = ['testpass123'] * 5

PRODUCTS = [
    {'name': 'Indomie Goreng', 'stock': 100},
    {'name': 'Mie Gacoan', 'stock': 50},
    {'name': 'Aqua 600ml', 'stock': 200},
    {'name': 'Teh Botol', 'stock': 150},
]


# ============================================================
# Sequential Workflow - Realistic User Journey
# ============================================================

class CashierWorkflow(SequentialTaskSet):
    """
    Sequential workflow yang mensimulasikan user journey kasir
    1. Login
    2. View dashboard
    3. Check stock
    4. Process transaction
    5. View receipt
    """
    
    def on_start(self):
        """Setup - Login"""
        self.username = random.choice(USERNAMES)
        self.password = random.choice(PASSWORDS)
        self.login()
    
    def login(self):
        """Login to system"""
        response = self.client.post("/login/", {
            "username": self.username,
            "password": self.password,
        }, catch_response=True)
        
        if response.status_code == 200 or response.status_code == 302:
            response.success()
        else:
            response.failure(f"Login failed with status {response.status_code}")
    
    @task
    def view_dashboard(self):
        """Task 1: View dashboard"""
        with self.client.get("/", catch_response=True) as response:
            self._check_response_time(response, "Dashboard")
    
    @task
    def view_stock(self):
        """Task 2: View total stock"""
        with self.client.get("/stock/", catch_response=True) as response:
            self._check_response_time(response, "Stock page")
    
    @task
    def view_transaction_page(self):
        """Task 3: View transaction page"""
        with self.client.get("/cart/", catch_response=True) as response:
            self._check_response_time(response, "Transaction page")
    
    @task
    def process_transaction(self):
        """Task 4: Process a transaction (most important)"""
        # This is a simplified version
        # Real implementation would need CSRF token and proper form data
        transaction_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            # Add product data
        }
        
        with self.client.post("/cart/", transaction_data, catch_response=True) as response:
            self._check_response_time(response, "Process transaction")
    
    @task
    def view_purchase_list(self):
        """Task 5: View purchase list"""
        with self.client.get("/purchase/", catch_response=True) as response:
            self._check_response_time(response, "Purchase list")
    
    def _check_response_time(self, response, page_name):
        """Check if response time meets SLO"""
        response_time_ms = response.elapsed.total_seconds() * 1000
        
        if response_time_ms > RESPONSE_TIME_LIMIT_MS:
            response.failure(f"{page_name} exceeded {RESPONSE_TIME_LIMIT_MS}ms: ({response_time_ms:.0f}ms)")
        elif response.status_code != 200:
            response.failure(f"{page_name} returned {response.status_code}")
        else:
            response.success()


# ============================================================
# Random Task User - For Load Testing
# ============================================================

class CashierUser(HttpUser):
    """
    User yang melakukan random tasks
    Untuk load testing dengan realistic wait time
    """
    host = "http://localhost:8000"
    wait_time = between(1, 3)  # Think time: 1-3 seconds
    
    def on_start(self):
        """Login sebelum melakukan tasks"""
        self.username = random.choice(USERNAMES)
        self.password = random.choice(PASSWORDS)
        self.login()
    
    def login(self):
        """Login to system"""
        self.client.post("/login/", {
            "username": self.username,
            "password": self.password,
        })
    
    @task(5)  # Weight: 5 - Most frequent
    def view_dashboard(self):
        """View dashboard - Most common action"""
        self.client.get("/")
    
    @task(4)  # Weight: 4
    def view_stock(self):
        """View stock"""
        self.client.get("/stock/")
    
    @task(3)  # Weight: 3
    def view_transaction_page(self):
        """View transaction page"""
        self.client.get("/cart/")
    
    @task(2)  # Weight: 2
    def view_purchase_list(self):
        """View purchase list"""
        self.client.get("/purchase/")
    
    @task(1)  # Weight: 1 - Least frequent
    def view_report(self):
        """View report"""
        self.client.get("/report/")


# ============================================================
# Stress Testing User - No Wait Time
# ============================================================

class StressTestUser(HttpUser):
    """
    User untuk stress testing
    No wait time - maksimum load
    """
    host = "http://localhost:8000"
    wait_time = between(0, 0)  # No wait time!
    
    def on_start(self):
        """Login"""
        self.username = random.choice(USERNAMES)
        self.password = random.choice(PASSWORDS)
        self.client.post("/login/", {
            "username": self.username,
            "password": self.password,
        })
    
    @task
    def hammer_homepage(self):
        """Hammer the homepage"""
        with self.client.get("/", catch_response=True) as response:
            response_time_ms = response.elapsed.total_seconds() * 1000
            
            if response_time_ms > RESPONSE_TIME_LIMIT_MS:
                response.failure(f"Response exceeded {RESPONSE_TIME_LIMIT_MS}ms: ({response_time_ms:.0f}ms)")
            elif response.status_code == 500:
                response.failure("Server error 500")
            elif response.status_code == 503:
                response.failure("Service unavailable 503")
            else:
                response.success()


# ============================================================
# Sequential Task User - For Workflow Testing
# ============================================================

class SequentialCashierUser(HttpUser):
    """
    User yang mengikuti sequential workflow
    Simulasi realistic user journey
    """
    host = "http://localhost:8000"
    wait_time = between(2, 5)
    tasks = [CashierWorkflow]


# ============================================================
# API Load Testing User
# ============================================================

class APIUser(HttpUser):
    """
    User untuk testing REST API endpoints
    """
    host = "http://localhost:8000"
    wait_time = between(0.5, 1.5)
    
    def on_start(self):
        """Setup"""
        pass
    
    @task(3)
    def get_profile_list(self):
        """GET /auth/api/"""
        self.client.get("/auth/api/")
    
    @task(1)
    def get_profile_detail(self):
        """GET /auth/api/{id}/"""
        profile_id = random.randint(1, 10)
        self.client.get(f"/auth/api/{profile_id}/")


# ============================================================
# Heavy Transaction User - Simulate Peak Hours
# ============================================================

class PeakHourUser(HttpUser):
    """
    User simulasi peak hours dengan banyak transaksi
    """
    host = "http://localhost:8000"
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Login"""
        self.username = random.choice(USERNAMES)
        self.password = random.choice(PASSWORDS)
        self.client.post("/login/", {
            "username": self.username,
            "password": self.password,
        })
    
    @task(10)  # Very high weight - simulate many transactions
    def process_transaction(self):
        """Process many transactions"""
        self.client.get("/cart/")
        # Would POST transaction here
    
    @task(2)
    def view_stock(self):
        """Check stock"""
        self.client.get("/stock/")


# ============================================================
# Configuration untuk Different Test Scenarios
# ============================================================

"""
SCENARIO 1: Load Testing (Normal Load)
Command: locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 5m
Uses: CashierUser (with wait_time)

SCENARIO 2: Stress Testing (Find Breaking Point)
Command: locust -f locustfile.py --users 200 --spawn-rate 50 --run-time 10m
Uses: StressTestUser (no wait_time)

SCENARIO 3: Workflow Testing (User Journey)
Command: locust -f locustfile.py --users 20 --spawn-rate 2 --run-time 10m
Uses: SequentialCashierUser

SCENARIO 4: API Testing
Command: locust -f locustfile.py --users 100 --spawn-rate 10 --run-time 5m
Uses: APIUser

SCENARIO 5: Peak Hours Simulation
Command: locust -f locustfile.py --users 150 --spawn-rate 25 --run-time 15m
Uses: PeakHourUser

SCENARIO 6: Distributed Testing (Master/Worker)
Master: locust -f locustfile.py --master
Worker: locust -f locustfile.py --worker (run multiple times)
"""