"""
Behave Environment Configuration
Setup dan teardown untuk BDD testing
"""
import os
import django
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')
WAIT_SECONDS = int(os.getenv('WAIT_SECONDS', '10'))


def before_all(context):
    """
    Executed once before all tests
    Setup browser and database
    """
    context.base_url = BASE_URL
    context.wait_seconds = WAIT_SECONDS
    
    # Setup Chrome WebDriver
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    context.driver = webdriver.Chrome(options=chrome_options)
    context.driver.implicitly_wait(WAIT_SECONDS)
    
    print(f"\n🚀 Starting BDD tests against {BASE_URL}")


def before_feature(context, feature):
    """
    Executed before each feature
    """
    print(f"\n📝 Testing Feature: {feature.name}")


def before_scenario(context, scenario):
    """
    Executed before each scenario
    Clean database and setup fresh state
    """
    # Clean up database before each scenario
    from django.contrib.auth.models import User
    from cashier.models import DaftarBarang, DaftarTransaksi, ListProductTransaksi
    
    # Don't delete superuser, but clean other data
    DaftarBarang.objects.all().delete()
    ListProductTransaksi.objects.all().delete()
    DaftarTransaksi.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()
    
    # Handle continue_after_failed_step tag
    if "continue_after_failed_step" in scenario.effective_tags:
        scenario.continue_after_failed_step = True
    
    print(f"\n  ▶ Scenario: {scenario.name}")


def after_scenario(context, scenario):
    """
    Executed after each scenario
    """
    if scenario.status == 'failed':
        print(f"  ❌ FAILED: {scenario.name}")
        # Take screenshot on failure
        try:
            screenshot_name = f"screenshots/{scenario.name.replace(' ', '_')}.png"
            os.makedirs('screenshots', exist_ok=True)
            context.driver.save_screenshot(screenshot_name)
            print(f"  📸 Screenshot saved: {screenshot_name}")
        except Exception as e:
            print(f"  ⚠ Could not save screenshot: {e}")
    elif scenario.status == 'passed':
        print(f"  ✅ PASSED: {scenario.name}")


def after_feature(context, feature):
    """
    Executed after each feature
    """
    if feature.status == 'passed':
        print(f"\n✅ Feature '{feature.name}' completed successfully")
    else:
        print(f"\n❌ Feature '{feature.name}' had failures")


def after_all(context):
    """
    Executed once after all tests
    Cleanup browser
    """
    if hasattr(context, 'driver'):
        context.driver.quit()
    
    print("\n🎉 All BDD tests completed!")


# ============================================================
# Custom Hooks for Specific Tags
# ============================================================

def before_tag(context, tag):
    """
    Handle specific tags
    """
    if tag == "critical":
        print("  🔴 CRITICAL TEST - Extra logging enabled")
    elif tag == "slow":
        print("  🐌 SLOW TEST - May take longer")


def after_tag(context, tag):
    """
    Cleanup after specific tags
    """
    pass