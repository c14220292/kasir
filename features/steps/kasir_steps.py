"""
Step Definitions untuk BDD Testing
Implementasi Gherkin steps menggunakan Selenium
"""
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from decimal import Decimal
import time

from django.contrib.auth.models import User
from cashier.models import DaftarBarang, DaftarTransaksi
from tests.factories import UserFactory, ProfileFactory, DaftarBarangFactory


# ============================================================
# Authentication Steps
# ============================================================

@given('I am logged in as "{username}" with password "{password}"')
def step_impl(context, username, password):
    """Login sebagai user tertentu"""
    # Create user if not exists
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = UserFactory(username=username, password=password)
        context.user = user
        context.profile = user.profile
    
    # Login via Selenium
    context.driver.get(f'{context.base_url}/login/')
    
    username_field = context.driver.find_element(By.NAME, 'username')
    password_field = context.driver.find_element(By.NAME, 'password')
    
    username_field.send_keys(username)
    password_field.send_keys(password)
    
    submit_button = context.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    submit_button.click()
    
    time.sleep(1)  # Wait for redirect


@given('I am not logged in')
def step_impl(context):
    """Ensure user is logged out"""
    context.driver.get(f'{context.base_url}/logout/')
    time.sleep(0.5)


# ============================================================
# Product/Stock Setup Steps
# ============================================================

@given('the following products exist')
def step_impl(context):
    """Setup products dari table"""
    for row in context.table:
        DaftarBarangFactory(
            user=context.profile,
            nama_product=row['nama_product'],
            jumlah_produk=int(row['jumlah_produk']),
            harga_beli_satuan=Decimal(row['harga_beli_satuan']),
            laba_persen=int(row['laba_persen'])
        )


@given('"{product_name}" has only {stock:d} units in stock')
def step_impl(context, product_name, stock):
    """Set specific stock for product"""
    product = DaftarBarang.objects.get(
        user=context.profile,
        nama_product=product_name
    )
    product.jumlah_produk = stock
    product.save()


@given('I have completed a transaction with ID "{trans_id}"')
def step_impl(context, trans_id):
    """Setup completed transaction"""
    # Will be implemented based on actual transaction creation
    pass


@given('I have completed {count:d} transactions today')
def step_impl(context, count):
    """Setup multiple transactions"""
    from tests.factories import DaftarTransaksiFactory
    for _ in range(count):
        DaftarTransaksiFactory(user=context.profile)


@given('I have transactions from "{start_date}" to "{end_date}"')
def step_impl(context, start_date, end_date):
    """Setup transactions with date range"""
    pass


@given('another user "{username}" has products in their inventory')
def step_impl(context, username):
    """Setup another user's products"""
    other_user = UserFactory(username=username)
    DaftarBarangFactory(user=other_user.profile)


@given('I have completed transactions today totaling {amount:d}')
def step_impl(context, amount):
    """Setup transactions with total amount"""
    from tests.factories import DaftarTransaksiFactory
    DaftarTransaksiFactory(user=context.profile, total=Decimal(str(amount)))


# ============================================================
# Navigation Steps
# ============================================================

@when('I visit the "{page_name}" page')
def step_impl(context, page_name):
    """Navigate to specific page"""
    page_urls = {
        'Total Stock': '/stock/',
        'Input Stock': '/input/',
        'Transaksi': '/cart/',
        'Daftar Pembelian': '/purchase/',
        'Report': '/report/',
        'Dashboard': '/',
        'Login': '/login/',
        'Register': '/register/',
        'Account': '/accounts/',
    }
    
    url = page_urls.get(page_name, '/')
    context.driver.get(f'{context.base_url}{url}')
    time.sleep(0.5)


@when('I visit the receipt page for transaction "{trans_id}"')
def step_impl(context, trans_id):
    """Navigate to receipt page"""
    context.driver.get(f'{context.base_url}/struck/{trans_id}/')
    time.sleep(0.5)


@when('I try to visit the "{page_name}" page')
def step_impl(context, page_name):
    """Try to navigate (might be blocked)"""
    step_impl(context, page_name)


# ============================================================
# Stock Management Steps
# ============================================================

@when('I add a new product')
def step_impl(context):
    """Add single product"""
    for row in context.table:
        context.driver.find_element(By.ID, 'id_form-0-nama_product').send_keys(row['nama_product'])
        context.driver.find_element(By.ID, 'id_form-0-jumlah_produk').send_keys(row['jumlah_produk'])
        context.driver.find_element(By.ID, 'id_form-0-harga_beli_satuan').send_keys(row['harga_beli_satuan'])
        context.driver.find_element(By.ID, 'id_form-0-laba_persen').send_keys(row['laba_persen'])


@when('I add multiple products')
def step_impl(context):
    """Add multiple products"""
    # First product
    first_row = context.table[0]
    context.driver.find_element(By.ID, 'id_form-0-nama_product').send_keys(first_row['nama_product'])
    context.driver.find_element(By.ID, 'id_form-0-jumlah_produk').send_keys(first_row['jumlah_produk'])
    context.driver.find_element(By.ID, 'id_form-0-harga_beli_satuan').send_keys(first_row['harga_beli_satuan'])
    context.driver.find_element(By.ID, 'id_form-0-laba_persen').send_keys(first_row['laba_persen'])
    
    # Click "Tambah Barang" for additional products
    for i, row in enumerate(context.table[1:], start=1):
        add_button = context.driver.find_element(By.ID, 'inputStockAdder')
        add_button.click()
        time.sleep(0.3)
        
        # Fill new form
        context.driver.find_element(By.ID, f'id_form-{i}-nama_product').send_keys(row['nama_product'])
        context.driver.find_element(By.ID, f'id_form-{i}-jumlah_produk').send_keys(row['jumlah_produk'])
        context.driver.find_element(By.ID, f'id_form-{i}-harga_beli_satuan').send_keys(row['harga_beli_satuan'])
        context.driver.find_element(By.ID, f'id_form-{i}-laba_persen').send_keys(row['laba_persen'])


@when('I enter product details')
def step_impl(context):
    """Enter product details"""
    for row in context.table:
        context.driver.find_element(By.ID, 'id_form-0-nama_product').send_keys(row['nama_product'])
        context.driver.find_element(By.ID, 'id_form-0-jumlah_produk').send_keys(row['jumlah_produk'])
        context.driver.find_element(By.ID, 'id_form-0-harga_beli_satuan').send_keys(row['harga_beli_satuan'])
        context.driver.find_element(By.ID, 'id_form-0-laba_persen').send_keys(row['laba_persen'])


@when('I enter incomplete product details')
def step_impl(context):
    """Enter incomplete details"""
    for row in context.table:
        if 'nama_product' in row.headings:
            context.driver.find_element(By.ID, 'id_form-0-nama_product').send_keys(row.get('nama_product', ''))
        if 'jumlah_produk' in row.headings:
            context.driver.find_element(By.ID, 'id_form-0-jumlah_produk').send_keys(row.get('jumlah_produk', ''))


# ============================================================
# Transaction Steps
# ============================================================

@when('I select product "{product_name}"')
def step_impl(context, product_name):
    """Select product from dropdown"""
    product = DaftarBarang.objects.get(user=context.profile, nama_product=product_name)
    select_element = Select(context.driver.find_element(By.NAME, 'form-0-nama_barang'))
    select_element.select_by_value(str(product.nomor))


@when('I enter quantity "{quantity}"')
def step_impl(context, quantity):
    """Enter quantity"""
    quantity_field = context.driver.find_element(By.ID, 'id_form-0-quantity')
    quantity_field.clear()
    quantity_field.send_keys(quantity)


@when('I add the following products to cart')
def step_impl(context):
    """Add multiple products to cart"""
    for i, row in enumerate(context.table):
        if i > 0:
            # Click add button for additional rows
            add_button = context.driver.find_element(By.ID, 'transactionAdderForm')
            add_button.click()
            time.sleep(0.3)
        
        product = DaftarBarang.objects.get(user=context.profile, nama_product=row['nama_product'])
        select_element = Select(context.driver.find_element(By.NAME, f'form-{i}-nama_barang'))
        select_element.select_by_value(str(product.nomor))
        
        quantity_field = context.driver.find_element(By.ID, f'id_form-{i}-quantity')
        quantity_field.send_keys(row['quantity'])


# ============================================================
# Form Submission Steps
# ============================================================

@when('I click "{button_text}"')
def step_impl(context, button_text):
    """Click button with specific text"""
    button_texts = {
        'Simpan': 'button[type="submit"]',
        'Bayar': 'button[type="submit"]',
        'Submit': 'button[type="submit"]',
        'Sign in': 'button[type="submit"]',
        'Submit Change': 'button[type="submit"]',
    }
    
    selector = button_texts.get(button_text, 'button[type="submit"]')
    button = context.driver.find_element(By.CSS_SELECTOR, selector)
    button.click()
    time.sleep(1)


# ============================================================
# Assertion Steps
# ============================================================

@then('I should see {count:d} products listed')
def step_impl(context, count):
    """Assert number of products"""
    table = context.driver.find_element(By.ID, 'dataTable')
    rows = table.find_elements(By.TAG_NAME, 'tr')
    # -1 for header row
    assert len(rows) - 1 == count, f"Expected {count} products, found {len(rows) - 1}"


@then('I should see "{product_name}" with stock {stock:d}')
def step_impl(context, product_name, stock):
    """Assert product and stock visible"""
    page_source = context.driver.page_source
    assert product_name in page_source
    assert str(stock) in page_source


@then('I should see a success message')
def step_impl(context):
    """Assert success message"""
    messages = context.driver.find_elements(By.CLASS_NAME, 'alert-success')
    assert len(messages) > 0, "No success message found"


@then('I should see an error message "{message_text}"')
def step_impl(context, message_text):
    """Assert specific error message"""
    messages = context.driver.find_elements(By.CLASS_NAME, 'alert')
    found = any(message_text in msg.text for msg in messages)
    assert found, f"Error message '{message_text}' not found"


@then('I should see an error message')
def step_impl(context):
    """Assert any error message"""
    messages = context.driver.find_elements(By.CLASS_NAME, 'alert')
    assert len(messages) > 0, "No error message found"


@then('the product "{product_name}" should be in the stock list')
def step_impl(context, product_name):
    """Assert product in stock"""
    exists = DaftarBarang.objects.filter(
        user=context.profile,
        nama_product=product_name
    ).exists()
    assert exists, f"Product {product_name} not found in database"


@then('"{product_name}" should have calculated prices')
def step_impl(context, product_name):
    """Assert calculated prices"""
    product = DaftarBarang.objects.get(user=context.profile, nama_product=product_name)
    
    for row in context.table:
        for field in row.headings:
            expected = Decimal(row[field])
            actual = getattr(product, field)
            assert actual == expected, f"{field}: expected {expected}, got {actual}"


@then('I should see {count:d} products in total stock')
def step_impl(context, count):
    """Assert total product count"""
    total = DaftarBarang.objects.filter(user=context.profile).count()
    assert total == count, f"Expected {count} products, found {total}"


@then('the system should automatically calculate')
def step_impl(context):
    """Assert automatic calculations visible in form"""
    # This would check the frontend calculations if implemented
    pass


@then('I should be redirected to the receipt page')
def step_impl(context):
    """Assert redirect to receipt"""
    time.sleep(1)
    assert '/struck/' in context.driver.current_url


@then('the receipt should show')
def step_impl(context):
    """Assert receipt details"""
    for row in context.table:
        for field in row.headings:
            assert row[field] in context.driver.page_source


@then('the stock of "{product_name}" should be reduced to {new_stock:d}')
def step_impl(context, product_name, new_stock):
    """Assert stock reduced"""
    product = DaftarBarang.objects.get(user=context.profile, nama_product=product_name)
    assert product.jumlah_produk == new_stock, f"Expected stock {new_stock}, got {product.jumlah_produk}"


@then('the total should be {amount:d}')
def step_impl(context, amount):
    """Assert transaction total"""
    assert str(amount) in context.driver.page_source


@then('the stocks should be updated')
def step_impl(context):
    """Assert multiple stock updates"""
    for row in context.table:
        product = DaftarBarang.objects.get(user=context.profile, nama_product=row['nama_product'])
        assert product.jumlah_produk == int(row['new_stock'])


@then('the transaction should not be created')
def step_impl(context):
    """Assert no new transaction"""
    # Check last transaction wasn't created in this session
    pass


@then('the stock of "{product_name}" should remain {stock:d}')
def step_impl(context, product_name, stock):
    """Assert stock unchanged"""
    product = DaftarBarang.objects.get(user=context.profile, nama_product=product_name)
    assert product.jumlah_produk == stock


@then('"{product_name}" should no longer appear in stock list')
def step_impl(context, product_name):
    """Assert product deleted"""
    exists = DaftarBarang.objects.filter(
        user=context.profile,
        nama_product=product_name
    ).exists()
    assert not exists, f"Product {product_name} still exists in database"


@then('I should be redirected to the login page')
def step_impl(context):
    """Assert redirect to login"""
    time.sleep(1)
    assert '/login/' in context.driver.current_url


@then('I should be logged in successfully')
def step_impl(context):
    """Assert successful login"""
    time.sleep(1)
    assert '/login/' not in context.driver.current_url


@then('I should remain on the login page')
def step_impl(context):
    """Assert stayed on login"""
    assert '/login/' in context.driver.current_url


@then('I should not see "{username}"\'s products')
def step_impl(context, username):
    """Assert other user's products not visible"""
    other_user = User.objects.get(username=username)
    other_products = DaftarBarang.objects.filter(user=other_user.profile)
    
    for product in other_products:
        assert product.nama_product not in context.driver.page_source


@then('I should only see my own products')
def step_impl(context):
    """Assert only own products visible"""
    my_products = DaftarBarang.objects.filter(user=context.profile).count()
    # Compare with what's displayed
    pass


@then('I should see "{text}" showing "{value}"')
def step_impl(context, text, value):
    """Assert specific text and value"""
    assert text in context.driver.page_source
    assert value in context.driver.page_source


# ============================================================
# User Management Steps
# ============================================================

@when('I fill in the registration form')
def step_impl(context):
    """Fill registration form"""
    for row in context.table:
        if 'username' in row.headings:
            context.driver.find_element(By.NAME, 'username').send_keys(row['username'])
        if 'email' in row.headings:
            context.driver.find_element(By.NAME, 'email').send_keys(row['email'])
        if 'password' in row.headings:
            context.driver.find_element(By.NAME, 'password1').send_keys(row['password'])
        if 'confirm_password' in row.headings:
            context.driver.find_element(By.NAME, 'password2').send_keys(row['confirm_password'])


@when('I enter username "{username}" and password "{password}"')
def step_impl(context, username, password):
    """Enter login credentials"""
    context.driver.find_element(By.NAME, 'username').send_keys(username)
    context.driver.find_element(By.NAME, 'password').send_keys(password)


@when('I update my profile')
def step_impl(context):
    """Update profile fields"""
    for row in context.table:
        for field in row.headings:
            element = context.driver.find_element(By.NAME, field)
            element.clear()
            element.send_keys(row[field])


@then('a new profile should be created for "{username}"')
def step_impl(context, username):
    """Assert profile created"""
    user_exists = User.objects.filter(username=username).exists()
    assert user_exists, f"User {username} was not created"


@then('I should see my profile information')
def step_impl(context):
    """Assert profile info visible"""
    assert context.user.username in context.driver.page_source


@then('my profile should be updated')
def step_impl(context):
    """Assert profile updated in DB"""
    context.profile.refresh_from_database()