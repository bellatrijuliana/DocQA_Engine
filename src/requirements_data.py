# requirements data is the source of truth that translated from decomposition table.
# the engine will read this list to generate test cases

requirements = [
    # US-01: Order Item Selection
    # AC: "Checkout" button is disabled if no items are selected.
    {
        "id": "US-01",
        "name": "Order Item Selection - Checkout State",
        "type": "logic_check", 
        "params": {
            "dependency": "Selected_Items > 0",
            "action": "Click Checkout Button"
        },
        "risk": "MEDIUM"
    },

    # --- US-02: Cart Management ---
    # AC: Deleting the last item should show an "Empty Cart" state.
    {
        "id": "US-02",
        "name": "Cart Management - Empty State Logic",
        "type": "logic_check",
        "params": {
            "dependency": "Cart_Item_Count == 0",
            "action": "View Cart Page"
        },
        "risk": "LOW"
    },

    # --- US-03: Global Payment (CRITICAL) ---
    # Breakdown berdasarkan daftar spesifik dari User
    
    # 1. Kartu Kredit/Debit (Visa, Mastercard, Amex, JCB)
    # Karakteristik: Input Angka.
    # Strategi BVA: Amex 15 digit, Visa/MC 16 digit. Kita set range 15-16.
    {
        "id": "US-03-CC",
        "name": "Payment - Global Credit/Debit Card",
        "type": "input_validation",
        "params": {
            "field": "Card Number (Visa/MC/Amex)",
            "min_len": 15,
            "max_len": 16
        },
        "risk": "CRITICAL"
    },

    # 2. SWIFT (Wire Transfer)
    # Karakteristik: Input Kode BIC/SWIFT.
    # Strategi BVA: Validasi panjang kode 8 atau 11 karakter.
    {
        "id": "US-03-SWIFT",
        "name": "Payment - SWIFT/Wire Transfer",
        "type": "input_validation",
        "params": {
            "field": "SWIFT/BIC Code",
            "min_len": 8,
            "max_len": 11
        },
        "risk": "CRITICAL"
    },

    # 3. Cryptocurrency (Bitcoin/USDT)
    # Karakteristik: Input Wallet Address yang panjang dan rumit.
    # Strategi BVA: Tes ketahanan input panjang (misal 30-42 char).
    {
        "id": "US-03-CRYPTO",
        "name": "Payment - Cryptocurrency (BTC/USDT)",
        "type": "input_validation",
        "params": {
            "field": "Wallet Address",
            "min_len": 30,
            "max_len": 42
        },
        "risk": "HIGH"
    },

    # 4. PayPal
    # Karakteristik: Redirect ke External Page. Tidak ada input angka di app kita.
    # Strategi: Functional Flow (Cek Redirect).
    {
        "id": "US-03-PAYPAL",
        "name": "Payment - PayPal Redirection",
        "type": "functional_flow",
        "params": {
            "description": "User selects PayPal. System should redirect to PayPal login page properly."
        },
        "risk": "HIGH"
    },

    # 5. Wise (Transferwise)
    # Karakteristik: Integrasi Kurs/Redirect.
    # Strategi: Functional Flow (Cek Integrasi).
    {
        "id": "US-03-WISE",
        "name": "Payment - Wise Integration",
        "type": "functional_flow",
        "params": {
            "description": "User selects Wise. System displays FX Rate & generates transfer reference."
        },
        "risk": "MEDIUM"
    },

    # 6. Western Union
    # Karakteristik: Generate Instruksi Pembayaran Tunai.
    # Strategi: Functional Flow.
    {
        "id": "US-03-WU",
        "name": "Payment - Western Union",
        "type": "functional_flow",
        "params": {
            "description": "User selects WU. System generates Payment Slip/Code for physical agent."
        },
        "risk": "MEDIUM"
    },

    # 7. Remittance Bank (Pekerja Migran)
    # Karakteristik: Dropdown pilihan bank tujuan khusus.
    # Strategi: Functional Flow.
    {
        "id": "US-03-REMIT",
        "name": "Payment - Remittance Bank",
        "type": "functional_flow",
        "params": {
            "description": "User selects Remittance. Ensure specialized bank list is loaded."
        },
        "risk": "MEDIUM"
    },

    # AC 2: New credit cards must trigger a "Verification" flow.
    # Ini menggunakan fallback logic (Standard Functional Test).
    {
        "id": "US-03-C",
        "name": "Global Payment - New Card Verification",
        "type": "functional_flow", # Tipe umum untuk tes alur
        "params": {
            "description": "User adds a new Credit Card not previously saved."
        },
        "risk": "HIGH"
    },

    # --- US-04: Discount Logic (HIGH) ---
    # AC 1: Points can only be used if the balance > 0.
    {
        "id": "US-04-A",
        "name": "Discount Logic - Use Points Requirement",
        "type": "logic_check",
        "params": {
            "dependency": "Total_Order_Balance > 0",
            "action": "Enable 'Use Points' Checkbox"
        },
        "risk": "HIGH"
    },

    # AC 2: Coupon field must validate the code.
    # Kita asumsikan kode kupon valid minimal 6 char, maksimal 15 char untuk BVA.
    {
        "id": "US-04-B",
        "name": "Discount Logic - Coupon Code Input",
        "type": "input_validation",
        "params": {
            "field": "Coupon Code",
            "min_len": 6,
            "max_len": 15
        },
        "risk": "HIGH"
    },

    # AC: Points and Coupons can be combined (stacked) unless specified otherwise.
        # Engine akan men-generate:
    # 1. Positif: Coupon allows stacking -> User bisa apply Points.
    # 2. Negatif: Coupon DOES NOT allow stacking -> User gagal/dilarang apply Points.
    {
        "id": "US-04-STACK",
        "name": "Discount - Stacking Logic (Points + Coupon)",
        "type": "logic_check",
        "params": {
            # Kondisi ketergantungan utama
            "dependency": "Selected_Coupon_Is_Stackable == TRUE",
            # Aksi yang ingin dilakukan user
            "action": "Apply Points on top of Coupon"
        },
        "risk": "HIGH"
    },

    # --- US-05: Legal Compliance ---
    # AC 1: The "Confirm" button remains inactive until the checkbox is ticked.
    {
        "id": "US-05",
        "name": "Legal Compliance - Mandatory Checkbox",
        "type": "logic_check",
        "params": {
            "dependency": "Precautions_Checkbox == CHECKED",
            "action": "Click Final Confirm Button"
        },
        "risk": "MEDIUM"
    }
]