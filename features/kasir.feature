Feature: Sistem Kasir dan Inventory Management
  As a toko owner / kasir
  I want to manage products and process transactions
  So that I can track inventory and sales

  Background:
    Given I am logged in as "kasir1" with password "testpass123"
    And the following products exist:
      | nama_product    | jumlah_produk | harga_beli_satuan | laba_persen |
      | Indomie Goreng  | 100           | 3000              | 20          |
      | Mie Gacoan      | 50            | 15000             | 30          |
      | Aqua 600ml      | 200           | 2500              | 25          |
      | Teh Botol       | 150           | 4000              | 15          |
      | Kopi Kapal Api  | 80            | 12000             | 25          |

  # =========================================================================
  # INVENTORY MANAGEMENT SCENARIOS
  # =========================================================================

  Scenario: View all available products in stock
    When I visit the "Total Stock" page
    Then I should see 5 products listed
    And I should see "Indomie Goreng" with stock 100
    And I should see "Mie Gacoan" with stock 50
    And I should see "Aqua 600ml" with stock 200

  Scenario: Add new product to inventory
    When I visit the "Input Stock" page
    And I add a new product:
      | nama_product     | jumlah_produk | harga_beli_satuan | laba_persen |
      | Chitato BBQ      | 60            | 8000              | 30          |
    And I click "Simpan"
    Then I should see a success message
    And the product "Chitato BBQ" should be in the stock list
    And "Chitato BBQ" should have calculated prices:
      | subtotal_harga_beli | 480000  |
      | harga_jual_satuan   | 10400   |
      | subtotal_harga_jual | 624000  |

  Scenario: Add multiple products at once
    When I visit the "Input Stock" page
    And I add multiple products:
      | nama_product      | jumlah_produk | harga_beli_satuan | laba_persen |
      | Oreo Original     | 40            | 9000              | 25          |
      | Coca Cola 1.5L    | 30            | 8500              | 20          |
    And I click "Simpan"
    Then I should see a success message
    And I should see 7 products in total stock

  Scenario: Validate product price calculations
    When I visit the "Input Stock" page
    And I enter product details:
      | nama_product | jumlah_produk | harga_beli_satuan | laba_persen |
      | Test Product | 10            | 5000              | 40          |
    Then the system should automatically calculate:
      | subtotal_harga_beli | 50000 |
      | harga_jual_satuan   | 7000  |
      | subtotal_harga_jual | 70000 |

  # =========================================================================
  # TRANSACTION PROCESSING SCENARIOS (Critical Path)
  # =========================================================================

  @critical
  Scenario: Process successful transaction with single product
    When I visit the "Transaksi" page
    And I select product "Indomie Goreng"
    And I enter quantity "10"
    And I click "Bayar"
    Then I should see a success message
    And I should be redirected to the receipt page
    And the receipt should show:
      | product name    | Indomie Goreng |
      | quantity        | 10             |
      | subtotal        | 36000          |
      | total           | 36000          |
    And the stock of "Indomie Goreng" should be reduced to 90

  @critical
  Scenario: Process transaction with multiple products
    When I visit the "Transaksi" page
    And I add the following products to cart:
      | nama_product   | quantity |
      | Indomie Goreng | 5        |
      | Aqua 600ml     | 10       |
      | Teh Botol      | 3        |
    And I click "Bayar"
    Then I should see a success message
    And the total should be 62300
    And the stocks should be updated:
      | nama_product   | new_stock |
      | Indomie Goreng | 95        |
      | Aqua 600ml     | 190       |
      | Teh Botol      | 147       |

  @critical
  Scenario: Transaction fails when stock is insufficient
    Given "Mie Gacoan" has only 5 units in stock
    When I visit the "Transaksi" page
    And I select product "Mie Gacoan"
    And I enter quantity "10"
    And I click "Bayar"
    Then I should see an error message "Barang melebihi batas stock!"
    And the transaction should not be created
    And the stock of "Mie Gacoan" should remain 5

  Scenario: Product is removed from inventory when stock reaches zero
    Given "Kopi Kapal Api" has only 5 units in stock
    When I visit the "Transaksi" page
    And I select product "Kopi Kapal Api"
    And I enter quantity "5"
    And I click "Bayar"
    Then I should see a success message
    And "Kopi Kapal Api" should no longer appear in stock list

  Scenario: Cannot process transaction with zero quantity
    When I visit the "Transaksi" page
    And I select product "Indomie Goreng"
    And I enter quantity "0"
    And I click "Bayar"
    Then I should see an error message "Jumlah barang yang dibeli tidak boleh kosong!"

  # =========================================================================
  # RECEIPT/STRUCK SCENARIOS
  # =========================================================================

  Scenario: View receipt after successful transaction
    Given I have completed a transaction with ID "1"
    When I visit the receipt page for transaction "1"
    Then I should see the receipt details:
      | field           | value                  |
      | nomor_nota      | 1                      |
      | nama_kasir      | kasir1                 |
      | tanggal         | today's date           |
    And I should see the purchased products list
    And I should see the total amount

  Scenario: View list of all transactions
    Given I have completed 3 transactions today
    When I visit the "Daftar Pembelian" page
    Then I should see 3 transactions listed
    And each transaction should show:
      | nomor nota      |
      | jumlah pembelian|
      | total harga     |
      | tanggal         |

  # =========================================================================
  # REPORTING SCENARIOS
  # =========================================================================

  Scenario: View daily sales report
    Given I have completed transactions today totaling 500000
    When I visit the "Dashboard" page
    Then I should see "Pendapatan Hari Ini" showing "Rp. 500,000"

  Scenario: Filter report by date range
    Given I have transactions from "2024-01-01" to "2024-12-31"
    When I visit the "Report" page
    And I filter by date range "2024-06-01" to "2024-06-30"
    Then I should see only transactions from June 2024

  # =========================================================================
  # USER MANAGEMENT SCENARIOS
  # =========================================================================

  Scenario: Register new cashier account
    Given I am not logged in
    When I visit the "Register" page
    And I fill in the registration form:
      | username         | newkasir       |
      | email            | new@kasir.com  |
      | password         | NewPass123!    |
      | confirm_password | NewPass123!    |
    And I click "Submit"
    Then I should see a success message
    And a new profile should be created for "newkasir"

  Scenario: Login with valid credentials
    Given I am not logged in
    When I visit the "Login" page
    And I enter username "kasir1" and password "testpass123"
    And I click "Sign in"
    Then I should be logged in successfully
    And I should be redirected to the dashboard

  Scenario: Login fails with invalid credentials
    Given I am not logged in
    When I visit the "Login" page
    And I enter username "kasir1" and password "wrongpassword"
    And I click "Sign in"
    Then I should see an error message
    And I should remain on the login page

  Scenario: View and update profile
    When I visit the "Account" page
    Then I should see my profile information
    When I update my profile:
      | nama_depan  | Updated     |
      | email       | new@email.com |
    And I click "Submit Change"
    Then I should see a success message
    And my profile should be updated

  # =========================================================================
  # EDGE CASES & ERROR HANDLING
  # =========================================================================

  Scenario: Cannot add product with incomplete information
    When I visit the "Input Stock" page
    And I enter incomplete product details:
      | nama_product | Test Product |
      | jumlah_produk| 0            |
      | harga_beli_satuan | 0       |
    And I click "Simpan"
    Then I should see an error message "Anda belum memasukkan data dengan lengkap!"

  Scenario: Cannot access protected pages without login
    Given I am not logged in
    When I try to visit the "Total Stock" page
    Then I should be redirected to the login page

  Scenario: User can only see their own data
    Given I am logged in as "kasir1"
    And another user "kasir2" has products in their inventory
    When I visit the "Total Stock" page
    Then I should not see "kasir2"'s products
    And I should only see my own products

  # =========================================================================
  # CONCURRENT TRANSACTIONS (Advanced)
  # =========================================================================

  @slow
  Scenario: Handle concurrent transactions on same product
    Given "Popular Product" has 10 units in stock
    When two cashiers simultaneously try to sell 8 units each
    Then only the first transaction should succeed
    And the second transaction should fail with "stock insufficient" error
    And the final stock should be 2 units