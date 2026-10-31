"""Hosted Payment Gateway Web Interface.

Provides a dedicated, hosted payment checkout page served at `/payments/checkout`
that simulates a live Razorpay payment gateway experience.
"""
from __future__ import annotations

PAYMENT_GATEWAY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>E-Commerce Secure Payment Gateway — Razorpay</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b1329;
      --card-bg: #111c44;
      --card-border: #1e295d;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --accent: #8b5cf6;
      --success: #10b981;
      --danger: #ef4444;
      --font-main: 'Plus Jakarta Sans', system-ui, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 1.5rem;
    }
    .gateway-container {
      max-width: 520px;
      width: 100%;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.45);
      overflow: hidden;
    }
    .gateway-header {
      background: linear-gradient(135deg, #1e295d 0%, #172554 100%);
      padding: 1.5rem;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand-title {
      font-weight: 800;
      font-size: 1.15rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .brand-subtitle {
      font-size: 0.75rem;
      color: var(--text-muted);
      font-family: var(--font-mono);
      margin-top: 0.2rem;
    }
    .amount-box {
      text-align: right;
    }
    .amount-label {
      font-size: 0.7rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .amount-val {
      font-size: 1.4rem;
      font-weight: 800;
      color: var(--success);
      font-family: var(--font-mono);
    }
    .gateway-body {
      padding: 1.75rem;
    }
    .order-meta-box {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 0.85rem 1rem;
      margin-bottom: 1.5rem;
      font-size: 0.8rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .meta-val {
      font-family: var(--font-mono);
      font-weight: 600;
      color: var(--primary);
    }
    .method-selector {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 0.5rem;
      margin-bottom: 1.5rem;
    }
    .method-btn {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 0.85rem 0.5rem;
      color: var(--text);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.8rem;
      font-weight: 600;
      transition: all 0.2s;
    }
    .method-btn:hover {
      border-color: var(--primary);
      background: rgba(59, 130, 246, 0.1);
    }
    .method-btn.active {
      border-color: var(--primary);
      background: rgba(59, 130, 246, 0.15);
      color: var(--primary);
      box-shadow: 0 0 15px rgba(59, 130, 246, 0.25);
    }
    .tab-content {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
      margin-bottom: 1.5rem;
    }
    .input-field {
      width: 100%;
      background: #0b1329;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 0.75rem 1rem;
      color: var(--text);
      font-family: var(--font-mono);
      font-size: 0.85rem;
      margin-top: 0.4rem;
    }
    .input-field:focus {
      outline: none;
      border-color: var(--primary);
    }
    .action-btn {
      width: 100%;
      background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
      color: white;
      border: none;
      border-radius: 12px;
      padding: 1rem;
      font-size: 1rem;
      font-weight: 800;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      box-shadow: 0 4px 15px rgba(37, 99, 235, 0.35);
    }
    .action-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 8px 25px rgba(37, 99, 235, 0.45);
    }
    .action-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none;
    }
    .back-btn {
      display: block;
      text-align: center;
      margin-top: 1rem;
      color: var(--text-muted);
      font-size: 0.85rem;
      text-decoration: none;
      transition: color 0.2s;
    }
    .back-btn:hover { color: var(--text); }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.25rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.7rem;
      font-weight: 700;
      background: rgba(16, 185, 129, 0.15);
      color: var(--success);
    }
    .qr-box {
      text-align: center;
      padding: 1rem;
    }
    .qr-frame {
      display: inline-block;
      background: white;
      padding: 0.75rem;
      border-radius: 12px;
      margin-bottom: 0.75rem;
    }
    .log-box {
      font-family: var(--font-mono);
      font-size: 0.75rem;
      background: #060914;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 0.75rem;
      margin-top: 1rem;
      display: none;
    }
  </style>
</head>
<body>
  <div class="gateway-container">
    <div class="gateway-header">
      <div>
        <div class="brand-title">
          <span>🛡️</span> E-Commerce Payment Gateway
        </div>
        <div class="brand-subtitle">256-Bit SSL Encrypted • Powered by Razorpay</div>
      </div>
      <div class="amount-box">
        <div class="amount-label">Total to Pay</div>
        <div class="amount-val" id="dispAmount">₹0.00</div>
      </div>
    </div>

    <div class="gateway-body">
      <!-- Order Info Bar -->
      <div class="order-meta-box">
        <div>
          <span style="color: var(--text-muted);">Payment Reference:</span>
          <span class="meta-val" id="dispOrderId">Loading...</span>
        </div>
        <span class="status-badge">● Encrypted Session</span>
      </div>

      <!-- Payment Method Selection -->
      <div class="method-selector">
        <button class="method-btn active" id="btnTabUpi" onclick="selectTab('upi')">
          <span style="font-size: 1.4rem;">📱</span>
          <span>UPI / QR</span>
        </button>
        <button class="method-btn" id="btnTabCard" onclick="selectTab('card')">
          <span style="font-size: 1.4rem;">💳</span>
          <span>Card</span>
        </button>
        <button class="method-btn" id="btnTabNet" onclick="selectTab('net')">
          <span style="font-size: 1.4rem;">🏦</span>
          <span>Net Banking</span>
        </button>
      </div>

      <!-- Tab Content: UPI -->
      <div class="tab-content" id="tabContentUpi">
        <div class="qr-box">
          <div class="qr-frame">
            <!-- Simulated QR representation -->
            <svg width="120" height="120" viewBox="0 0 100 100" fill="#0b1329">
              <rect x="0" y="0" width="30" height="30" />
              <rect x="70" y="0" width="30" height="30" />
              <rect x="0" y="70" width="30" height="30" />
              <rect x="35" y="10" width="10" height="10" />
              <rect x="10" y="35" width="10" height="10" />
              <rect x="40" y="40" width="20" height="20" />
              <rect x="70" y="70" width="10" height="20" />
              <rect x="85" y="85" width="15" height="15" />
            </svg>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;">
            Scan with Google Pay, PhonePe, Paytm, or BHIM
          </div>
          <div>
            <label style="font-size: 0.75rem; color: var(--text-muted); text-align: left; display: block;">Or enter UPI VPA Address:</label>
            <input type="text" id="upiInput" class="input-field" value="customer@okhdfcbank">
          </div>
        </div>
      </div>

      <!-- Tab Content: Card -->
      <div class="tab-content" id="tabContentCard" style="display: none;">
        <label style="font-size: 0.75rem; color: var(--text-muted);">Card Number (Sandbox Test)</label>
        <input type="text" class="input-field" value="4111 •••• •••• 1111 (Visa)" disabled>
        <div style="display: flex; gap: 0.75rem; margin-top: 0.5rem;">
          <div style="flex: 1;">
            <label style="font-size: 0.75rem; color: var(--text-muted);">Expiry</label>
            <input type="text" class="input-field" value="12/28" disabled>
          </div>
          <div style="flex: 1;">
            <label style="font-size: 0.75rem; color: var(--text-muted);">CVV</label>
            <input type="text" class="input-field" value="123" disabled>
          </div>
        </div>
      </div>

      <!-- Tab Content: Net Banking -->
      <div class="tab-content" id="tabContentNet" style="display: none;">
        <label style="font-size: 0.75rem; color: var(--text-muted);">Choose Bank</label>
        <select class="input-field" style="margin-top: 0.4rem;">
          <option>HDFC Bank (Instant Sandbox)</option>
          <option>ICICI Bank (Instant Sandbox)</option>
          <option>State Bank of India (Instant Sandbox)</option>
          <option>Axis Bank (Instant Sandbox)</option>
        </select>
      </div>

      <!-- Action Button -->
      <button class="action-btn" id="payActionBtn" onclick="submitPayment()">
        🔒 Authorize & Complete Payment
      </button>

      <!-- Terminal Output -->
      <div class="log-box" id="logBox"></div>

      <a href="/" class="back-btn">← Cancel and Return to Store</a>
    </div>
  </div>

  <script>
    const urlParams = new URLSearchParams(window.location.search);
    const orderId = urlParams.get('order_id') || 'Unknown';
    const amount = urlParams.get('amount') || '0.00';
    let token = urlParams.get('token') || localStorage.getItem('novatech_token') || '';

    document.getElementById('dispOrderId').textContent = orderId;
    document.getElementById('dispAmount').textContent = `₹${Number(amount).toLocaleString()} INR`;

    function selectTab(tab) {
      document.querySelectorAll('.method-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tabContentUpi').style.display = 'none';
      document.getElementById('tabContentCard').style.display = 'none';
      document.getElementById('tabContentNet').style.display = 'none';

      if (tab === 'upi') {
        document.getElementById('btnTabUpi').classList.add('active');
        document.getElementById('tabContentUpi').style.display = 'block';
      } else if (tab === 'card') {
        document.getElementById('btnTabCard').classList.add('active');
        document.getElementById('tabContentCard').style.display = 'block';
      } else {
        document.getElementById('btnTabNet').classList.add('active');
        document.getElementById('tabContentNet').style.display = 'block';
      }
    }

    function log(msg) {
      const box = document.getElementById('logBox');
      box.style.display = 'block';
      box.innerHTML += `<div>${msg}</div>`;
      box.scrollTop = box.scrollHeight;
    }

    async function submitPayment() {
      const btn = document.getElementById('payActionBtn');
      btn.disabled = true;
      btn.innerHTML = '⏳ Processing Secure Payment...';

      log('→ Encrypting payment authorization payload...');
      log(`→ Reference: ${orderId}`);

      try {
        if (!token) {
          log('→ Initializing secure customer session...');
          const loginRes = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: 'customer@example.com', password: 'CustomerPassword123!' })
          });
          const lData = await loginRes.json();
          token = lData.token;
        }

        log('→ Verifying payment with Razorpay Gateway...');
        const simPaymentId = 'pay_sim_' + Math.random().toString(36).substring(7);

        const verifyRes = await fetch(`/orders/${orderId}/payment/verify`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            razorpay_order_id: 'order_sim_' + orderId.substring(0, 8),
            razorpay_payment_id: simPaymentId,
            razorpay_signature: 'mock_signature_test'
          })
        });

        if (!verifyRes.ok) {
          const err = await verifyRes.json();
          throw new Error(err.detail || 'Payment verification failed');
        }

        const data = await verifyRes.json();
        log('✔ Payment signature verified successfully!');
        log(`✔ Status: Confirmed (${data.status})`);
        log(`✔ Payment ID: ${simPaymentId}`);
        log('🎉 Payment Confirmed! Returning to store...');

        btn.style.background = '#10b981';
        btn.innerHTML = '✅ Payment Verified & Confirmed!';

        setTimeout(() => {
          window.location.href = `/?order_success=${orderId}&amount=${amount}`;
        }, 2200);

      } catch (err) {
        log(`✗ Error: ${err.message}`);
        btn.disabled = false;
        btn.innerHTML = '🔒 Authorize & Complete Payment';
        alert('Payment Error: ' + err.message);
      }
    }
  </script>
</body>
</html>
"""
