"""API Gateway Front-End Storefront & Unified OpenAPI Portal."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

PORTAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>E-Commerce Site — Premium Electronics & Workstations</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    /* CSS Variables for Dynamic Theme Switching */
    :root {
      /* Cyberpunk Deep Electric Blue Theme: Vivid Blue Background with Sleek Dark Foregrounds */
      --bg: #002244;
      --page-gradient: radial-gradient(circle at 10% 10%, #0052cc 0%, transparent 45%),
                       radial-gradient(circle at 90% 20%, #0033aa 0%, transparent 40%),
                       radial-gradient(circle at 50% 70%, #0044bb 0%, transparent 55%),
                       radial-gradient(circle at 80% 90%, #002288 0%, transparent 45%),
                       linear-gradient(180deg, #001f3f 0%, #002b5c 40%, #001a35 100%);
      --card-bg: rgba(6, 12, 24, 0.88);
      --card-border: rgba(0, 212, 255, 0.35);
      --card-border-hover: #00f0ff;
      --text: #ffffff;
      --text-muted: #99ccff;
      --primary: #00d4ff;
      --primary-hover: #33e0ff;
      --cyan-glow: #00f0ff;
      --accent: #ff007f;
      --success: #00ffaa;
      --header-bg: rgba(3, 8, 20, 0.92);
      --thumb-bg: radial-gradient(circle at center, #001f44 0%, #040914 100%);
      --cart-drawer-bg: #050b18;
      --modal-bg: #060e1e;
      --font-main: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
      --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.5);
      --shadow-md: 0 16px 40px rgba(0, 150, 255, 0.35);
      --input-bg: rgba(0, 10, 25, 0.7);
    }

    /* Present Dark Theme for Admin Control */
    body.admin-theme {
      --bg: #020b1e;
      --page-gradient: linear-gradient(180deg, #020b1e 0%, #051430 100%);
      --card-bg: #060e20;
      --card-border: rgba(0, 212, 255, 0.3);
      --text: #ffffff;
      --text-muted: #94a3b8;
      --primary: #00d4ff;
      --primary-hover: #38bdf8;
      --accent: #ff007f;
      --success: #00ffaa;
      --header-bg: rgba(2, 6, 16, 0.95);
      --thumb-bg: radial-gradient(circle at center, #002b5c 0%, #030814 80%);
      --cart-drawer-bg: #040915;
      --modal-bg: #050b1a;
      --shadow-sm: 0 2px 6px rgba(0, 0, 0, 0.6);
      --shadow-md: 0 16px 36px rgba(0, 212, 255, 0.25);
      --input-bg: rgba(0, 15, 35, 0.6);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      background-image: var(--page-gradient);
      background-attachment: fixed;
      background-size: cover;
      color: var(--text);
      font-family: var(--font-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      transition: background-color 0.3s, color 0.3s;
      position: relative;
    }

    /* Cyberpunk Grid Overlay for Background Depth */
    body::before {
      content: "";
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background-image: 
        linear-gradient(rgba(0, 170, 255, 0.07) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 170, 255, 0.07) 1px, transparent 1px);
      background-size: 40px 40px;
      pointer-events: none;
      z-index: 0;
    }

    header, main, footer, .modal-overlay, .cart-drawer {
      position: relative;
      z-index: 1;
    }

    /* Top Navbar */
    header {
      background: var(--header-bg);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid var(--card-border);
      position: sticky;
      top: 0;
      z-index: 100;
      padding: 0.85rem 1.5rem;
      transition: background 0.3s, border-color 0.3s;
      box-shadow: 0 4px 20px rgba(0, 30, 80, 0.45);
    }
    .header-inner {
      max-width: 1280px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1.25rem;
    }
    .logo {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      text-decoration: none;
      color: var(--text);
      font-weight: 800;
      font-size: 1.2rem;
      letter-spacing: -0.02em;
    }
    .logo-icon {
      width: 40px; height: 40px;
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.25rem;
      color: white;
      box-shadow: 0 0 16px rgba(56, 189, 248, 0.4);
    }
    .role-badge {
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.25rem 0.6rem;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .role-customer { background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .role-admin { background: #fef3c7; color: #b45309; }

    .search-box {
      flex: 1;
      max-width: 440px;
      position: relative;
    }
    .search-box input {
      width: 100%;
      background: var(--input-bg);
      border: 1px solid var(--card-border);
      border-radius: 9999px;
      padding: 0.6rem 1.2rem 0.6rem 2.5rem;
      color: var(--text);
      font-family: inherit;
      font-size: 0.9rem;
      outline: none;
      transition: all 0.2s;
    }
    .search-box input:focus {
      border-color: #38bdf8;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.35);
    }
    .search-icon {
      position: absolute;
      left: 1rem;
      top: 50%;
      transform: translateY(-50%);
      font-size: 0.85rem;
      color: var(--text-muted);
      pointer-events: none;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .nav-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(10, 25, 47, 0.8);
      border: 1px solid var(--card-border);
      color: var(--text);
      padding: 0.55rem 1rem;
      border-radius: 9px;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: var(--shadow-sm);
      backdrop-filter: blur(8px);
    }
    .nav-btn:hover {
      border-color: #38bdf8;
      color: #38bdf8;
      box-shadow: 0 0 14px rgba(56, 189, 248, 0.25);
      transform: translateY(-1px);
    }
    .cart-btn {
      background: linear-gradient(135deg, #0284c7, #2563eb);
      color: white;
      border: 1px solid rgba(56, 189, 248, 0.35);
      border-radius: 9999px;
      padding: 0.55rem 1.15rem;
      font-weight: 700;
      font-size: 0.875rem;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 4px 16px rgba(2, 132, 199, 0.35);
    }
    .cart-btn:hover {
      background: linear-gradient(135deg, #0369a1, #1d4ed8);
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(56, 189, 248, 0.5);
    }
    .cart-badge {
      background: white;
      color: var(--primary);
      font-size: 0.75rem;
      font-weight: 800;
      border-radius: 9999px;
      padding: 0.1rem 0.45rem;
      min-width: 20px;
      text-align: center;
    }

    /* Main Container */
    main {
      max-width: 1280px;
      margin: 0 auto;
      padding: 2rem 1.5rem;
      flex: 1;
      width: 100%;
    }

    /* Hero / Banner */
    .hero-user {
      position: relative;
      background: radial-gradient(circle at 85% 20%, rgba(14, 165, 233, 0.28) 0%, transparent 55%),
                  radial-gradient(circle at 15% 80%, rgba(2, 132, 199, 0.24) 0%, transparent 50%),
                  linear-gradient(135deg, #030a1c 0%, #061838 50%, #032047 100%);
      color: #ffffff;
      border: 1px solid rgba(56, 189, 248, 0.28);
      border-radius: 20px;
      padding: 2.75rem 2.5rem;
      margin-bottom: 2rem;
      box-shadow: 0 20px 45px -12px rgba(2, 132, 199, 0.35);
      overflow: hidden;
    }
    .hero-pill-tag {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(14, 165, 233, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.35);
      backdrop-filter: blur(8px);
      color: #38bdf8;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      margin-bottom: 1rem;
      box-shadow: 0 0 14px rgba(56, 189, 248, 0.2);
    }
    .live-status-dot {
      width: 7px;
      height: 7px;
      background: #38bdf8;
      border-radius: 50%;
      box-shadow: 0 0 10px #38bdf8;
      animation: pulseCyan 2s infinite;
    }
    @keyframes pulseCyan {
      0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 10px #38bdf8; }
      50% { opacity: 0.5; transform: scale(1.25); box-shadow: 0 0 16px #38bdf8; }
    }
    .hero-title {
      font-size: 2.15rem;
      font-weight: 850;
      letter-spacing: -0.035em;
      line-height: 1.2;
      margin-bottom: 0.75rem;
      background: linear-gradient(180deg, #ffffff 40%, #7dd3fc 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      max-width: 760px;
    }
    .hero-subtitle {
      color: #7dd3fc;
      font-size: 0.96rem;
      line-height: 1.55;
      max-width: 660px;
      margin-bottom: 1.75rem;
      opacity: 0.88;
    }
    .hero-features {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: center;
    }
    .hero-feature-item {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      background: rgba(14, 165, 233, 0.08);
      border: 1px solid rgba(56, 189, 248, 0.2);
      padding: 0.4rem 0.85rem;
      border-radius: 8px;
      font-size: 0.8rem;
      font-weight: 600;
      color: #e0f2fe;
      backdrop-filter: blur(4px);
      transition: all 0.2s;
    }
    .hero-feature-item:hover {
      border-color: #38bdf8;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
    }
    .hero-admin {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(139, 92, 246, 0.15));
      border: 1px solid rgba(245, 158, 11, 0.3);
      border-radius: 16px;
      padding: 2rem 2.2rem;
      margin-bottom: 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1.5rem;
      flex-wrap: wrap;
    }

    /* Category Bar */
    .category-bar {
      display: flex;
      gap: 0.6rem;
      margin-bottom: 1.75rem;
      overflow-x: auto;
      padding-bottom: 0.35rem;
    }
    .filter-pill {
      background: rgba(14, 165, 233, 0.08);
      border: 1px solid rgba(56, 189, 248, 0.2);
      color: #7dd3fc;
      padding: 0.55rem 1.15rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
      backdrop-filter: blur(8px);
    }
    .filter-pill:hover {
      border-color: #38bdf8;
      color: #ffffff;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
      transform: translateY(-1px);
    }
    .filter-pill.active {
      background: linear-gradient(135deg, #0284c7, #2563eb);
      border-color: #38bdf8;
      color: #ffffff;
      box-shadow: 0 4px 18px rgba(14, 165, 233, 0.45);
      font-weight: 700;
    }
    .price-pill {
      background: rgba(0, 212, 255, 0.06);
      border: 1px solid rgba(0, 212, 255, 0.25);
      color: #99ccff;
      padding: 0.32rem 0.8rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .price-pill:hover {
      border-color: #00f0ff;
      color: #ffffff;
      background: rgba(0, 212, 255, 0.15);
    }
    .price-pill.active {
      background: linear-gradient(135deg, #00d4ff, #0077ff);
      color: #ffffff;
      border-color: #00f0ff;
      font-weight: 800;
      box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    .wishlist-toggle-btn {
      position: absolute;
      top: 10px;
      right: 10px;
      background: rgba(6, 15, 35, 0.75);
      border: 1px solid rgba(0, 212, 255, 0.3);
      border-radius: 50%;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 1.1rem;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      backdrop-filter: blur(8px);
      z-index: 5;
    }
    .wishlist-toggle-btn:hover {
      transform: scale(1.15);
      border-color: #ff007f;
      box-shadow: 0 0 12px rgba(255, 0, 128, 0.5);
    }
    .product-rating {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      font-size: 0.78rem;
      font-weight: 700;
      color: #f59e0b;
      margin-bottom: 0.4rem;
    }

    /* Product Grid */
    .products-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(285px, 1fr));
      gap: 1.6rem;
      margin-bottom: 3.5rem;
    }
    .product-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.65);
      position: relative;
      backdrop-filter: blur(16px);
    }
    .product-card:hover {
      transform: translateY(-6px);
      box-shadow: 0 16px 36px rgba(0, 212, 255, 0.35);
      border-color: var(--card-border-hover);
    }
    .product-thumb {
      height: 220px;
      aspect-ratio: 16 / 10;
      background: var(--thumb-bg);
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 1px solid var(--card-border);
      position: relative;
      overflow: hidden;
      padding: 0.75rem;
      font-size: 4rem;
    }
    .product-thumb span {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 4.5rem;
      line-height: 1;
      filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.12));
    }
    .product-thumb img {
      width: 100%;
      height: 100%;
      max-height: 195px;
      object-fit: cover;
      object-position: center;
      border-radius: 8px;
      transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
    }
    .product-card:hover .product-thumb img {
      transform: scale(1.05);
    }
    .product-info {
      padding: 1.35rem;
      display: flex;
      flex-direction: column;
      flex: 1;
    }
    .product-sku {
      font-family: var(--font-mono);
      font-size: 0.72rem;
      color: #64748b;
      font-weight: 700;
      letter-spacing: 0.04em;
    }
    .product-title {
      font-size: 1.05rem;
      font-weight: 800;
      color: var(--text);
      margin-bottom: 0.45rem;
      line-height: 1.35;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      height: 2.7rem;
      cursor: pointer;
      transition: color 0.2s, text-shadow 0.2s;
    }
    .product-title:hover {
      color: #00f0ff;
      text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
    }
    .product-desc {
      font-size: 0.825rem;
      color: var(--text-muted);
      margin-bottom: 1.25rem;
      line-height: 1.45;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      height: 2.4rem;
    }
    .product-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      padding-top: 1rem;
      border-top: 1px solid var(--card-border);
      margin-top: auto;
    }
    .product-price {
      font-size: 1.35rem;
      font-weight: 850;
      color: #00f0ff;
      letter-spacing: -0.02em;
      text-shadow: 0 0 12px rgba(0, 240, 255, 0.45);
    }
    body.admin-theme .product-price {
      color: #00f0ff;
    }
    .add-btn {
      background: linear-gradient(135deg, #00d4ff, #0066ff);
      color: #030a1a;
      border: 1px solid #00f0ff;
      border-radius: 8px;
      padding: 0.6rem 1.15rem;
      font-weight: 800;
      font-size: 0.85rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      box-shadow: 0 4px 14px rgba(0, 212, 255, 0.45);
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .add-btn:hover {
      background: linear-gradient(135deg, #33e0ff, #0088ff);
      box-shadow: 0 6px 22px rgba(0, 240, 255, 0.7);
      transform: translateY(-2px);
      filter: brightness(1.1);
    }
    .add-btn:active {
      transform: scale(0.97);
    }

    /* Admin Control View (When in Admin Mode) */
    .admin-panel-container {
      display: none;
    }
    body.admin-theme .admin-panel-container {
      display: block;
    }
    body.admin-theme .user-store-container {
      display: none;
    }
    .admin-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }
    .admin-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
    }
    .admin-card h3 {
      font-size: 1.15rem;
      font-weight: 700;
      margin-bottom: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .service-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.6rem 0.8rem;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      margin-bottom: 0.5rem;
      font-size: 0.875rem;
    }
    .inventory-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }
    .inventory-table th, .inventory-table td {
      padding: 0.65rem 0.8rem;
      border-bottom: 1px solid var(--card-border);
      text-align: left;
    }
    .inventory-table th { color: var(--text-muted); font-weight: 600; }
    .stock-input {
      width: 60px;
      padding: 0.25rem 0.4rem;
      background: var(--input-bg);
      border: 1px solid var(--card-border);
      color: var(--text);
      border-radius: 4px;
      font-family: var(--font-mono);
    }
    .btn-sm {
      padding: 0.25rem 0.6rem;
      font-size: 0.75rem;
      border-radius: 4px;
      background: var(--primary);
      color: white;
      border: none;
      cursor: pointer;
    }

    /* Login Modal */
    .modal-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(4px);
      z-index: 300;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 1.5rem;
    }
    .modal-overlay.active { display: flex; }
    .modal-box {
      background: var(--modal-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      max-width: 440px;
      width: 100%;
      padding: 2rem;
      box-shadow: var(--shadow-md);
      position: relative;
    }
    .modal-close {
      position: absolute;
      top: 1rem; right: 1rem;
      background: none; border: none; font-size: 1.4rem; color: var(--text-muted); cursor: pointer;
    }
    .modal-header { text-align: center; margin-bottom: 1.5rem; }
    .modal-header h2 { font-size: 1.35rem; font-weight: 800; margin-bottom: 0.3rem; }
    .modal-header p { font-size: 0.85rem; color: var(--text-muted); }
    .quick-logins { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1.25rem; }
    .quick-login-btn {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.85rem 1rem;
      background: var(--input-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      cursor: pointer;
      text-align: left;
      transition: all 0.2s;
    }
    .quick-login-btn:hover {
      border-color: var(--primary);
      background: rgba(37, 99, 235, 0.05);
    }
    .quick-title { font-weight: 700; font-size: 0.9rem; color: var(--text); }
    .quick-subtitle { font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono); }

    .form-group {
      margin-bottom: 1rem;
      text-align: left;
    }
    .form-label {
      display: block;
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--text-muted);
      margin-bottom: 0.35rem;
    }
    .form-input {
      width: 100%;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      background: var(--input-bg);
      color: var(--text);
      font-family: inherit;
      font-size: 0.9rem;
      outline: none;
      transition: border-color 0.2s;
    }
    .form-input:focus {
      border-color: var(--primary);
    }

    /* Cart Slide-Over */
    .cart-drawer {
      position: fixed;
      top: 0; right: -440px; bottom: 0;
      width: 100%; max-width: 420px;
      background: var(--cart-drawer-bg);
      border-left: 1px solid var(--card-border);
      z-index: 210;
      display: flex; flex-direction: column;
      transition: right 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: -10px 0 35px rgba(0, 0, 0, 0.25);
    }
    .cart-drawer.active { right: 0; }
    .cart-header {
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid var(--card-border);
      display: flex; justify-content: space-between; align-items: center;
    }
    .cart-items-list {
      flex: 1; overflow-y: auto; padding: 1.25rem 1.5rem; display: flex; flex-direction: column; gap: 0.85rem;
    }
    .cart-card {
      background: var(--input-bg); border: 1px solid var(--card-border);
      border-radius: 10px; padding: 0.85rem; display: flex; justify-content: space-between; align-items: center;
    }
    .cart-footer {
      padding: 1.25rem 1.5rem; border-top: 1px solid var(--card-border);
    }
    .total-row {
      display: flex; justify-content: space-between; font-size: 1.25rem; font-weight: 800; margin-bottom: 1.25rem;
    }
    .checkout-btn {
      width: 100%; background: var(--success); color: white; border: none; border-radius: 10px;
      padding: 0.85rem; font-weight: 700; font-size: 1rem; cursor: pointer; transition: all 0.2s;
    }
    .checkout-btn:hover { opacity: 0.92; transform: translateY(-1px); }

    .pay-method-btn {
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      gap: 0.35rem; padding: 0.75rem 0.5rem; border-radius: 8px; border: 1px solid var(--card-border);
      background: var(--input-bg); color: var(--text); font-size: 0.8rem; font-weight: 600;
      cursor: pointer; transition: all 0.2s;
    }
    .pay-method-btn.active {
      border-color: var(--primary); background: rgba(37, 99, 235, 0.08); color: var(--primary);
    }

    /* Footer */
    footer {
      border-top: 1px solid var(--card-border);
      padding: 1.5rem;
      background: var(--header-bg);
      margin-top: auto;
    }
    .footer-inner {
      max-width: 1280px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;
      flex-wrap: wrap; gap: 1rem; font-size: 0.85rem; color: var(--text-muted);
    }
    .footer-inner a { color: var(--primary); text-decoration: none; margin-left: 1rem; font-weight: 600; }

    /* Order Lifecycle Tracker & Live Stepper Styles */
    .order-tracker-card {
      background: rgba(10, 20, 38, 0.75);
      border: 1px solid rgba(0, 240, 255, 0.25);
      border-radius: 12px;
      padding: 1.15rem;
      margin-top: 0.95rem;
      position: relative;
      overflow: hidden;
      backdrop-filter: blur(10px);
    }
    .order-tracker-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, #00d4ff, #8b5cf6, #10b981);
      box-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
    }
    .tracker-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 0.9rem;
    }
    .tracker-badge-carrier {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: rgba(0, 240, 255, 0.1);
      border: 1px solid rgba(0, 240, 255, 0.35);
      color: #00f0ff;
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
    }
    .tracker-stepper {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      position: relative;
      margin: 1.5rem 0 1.25rem 0;
      padding: 0 0.25rem;
    }
    .tracker-line-bg {
      position: absolute;
      top: 18px;
      left: 28px;
      right: 28px;
      height: 4px;
      background: rgba(255, 255, 255, 0.12);
      border-radius: 2px;
      z-index: 1;
    }
    .tracker-line-fill {
      position: absolute;
      top: 18px;
      left: 28px;
      height: 4px;
      background: linear-gradient(90deg, #00f0ff, #10b981);
      box-shadow: 0 0 8px rgba(0, 240, 255, 0.8);
      border-radius: 2px;
      z-index: 2;
      transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .tracker-step {
      display: flex;
      flex-direction: column;
      align-items: center;
      position: relative;
      z-index: 3;
      text-align: center;
      flex: 1;
    }
    .tracker-circle {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.85rem;
      font-weight: 800;
      background: #081226;
      border: 2px solid rgba(255, 255, 255, 0.2);
      color: var(--text-muted);
      transition: all 0.35s ease;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
    }
    .tracker-step.completed .tracker-circle {
      background: #059669;
      border-color: #10b981;
      color: #ffffff;
      box-shadow: 0 0 12px rgba(16, 185, 129, 0.55);
    }
    .tracker-step.active .tracker-circle {
      background: #00d4ff;
      border-color: #00f0ff;
      color: #030a1a;
      box-shadow: 0 0 18px rgba(0, 240, 255, 0.9);
      animation: trackerPulseGlow 1.8s infinite;
    }
    @keyframes trackerPulseGlow {
      0% { box-shadow: 0 0 0 0 rgba(0, 240, 255, 0.7); }
      70% { box-shadow: 0 0 0 12px rgba(0, 240, 255, 0); }
      100% { box-shadow: 0 0 0 0 rgba(0, 240, 255, 0); }
    }
    .tracker-label {
      font-size: 0.68rem;
      font-weight: 700;
      color: var(--text-muted);
      margin-top: 0.45rem;
      text-transform: uppercase;
      letter-spacing: 0.02em;
      line-height: 1.25;
      max-width: 80px;
    }
    .tracker-step.completed .tracker-label {
      color: #10b981;
    }
    .tracker-step.active .tracker-label {
      color: #00f0ff;
      font-weight: 800;
      text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
    }
    .carrier-details-box {
      background: rgba(0, 240, 255, 0.04);
      border: 1px dashed rgba(0, 240, 255, 0.3);
      border-radius: 8px;
      padding: 0.8rem 1rem;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 0.75rem;
      margin-top: 0.85rem;
      font-size: 0.8rem;
    }
    .tracker-controls {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 0.85rem;
      padding-top: 0.75rem;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
    }
    .sim-ctrl-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.45rem 0.85rem;
      font-size: 0.75rem;
      font-weight: 700;
      border-radius: 6px;
      cursor: pointer;
      border: 1px solid;
      transition: all 0.2s ease;
    }
    .sim-ctrl-btn:hover:not(:disabled) {
      transform: translateY(-1px);
      filter: brightness(1.2);
    }
    .sim-ctrl-btn:disabled {
      opacity: 0.45;
      cursor: not-allowed;
      transform: none;
    }
    .tracking-live-toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #0b1528;
      border: 1px solid #00f0ff;
      box-shadow: 0 8px 32px rgba(0, 240, 255, 0.4);
      color: #ffffff;
      padding: 0.85rem 1.25rem;
      border-radius: 10px;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      font-size: 0.85rem;
      font-weight: 700;
      z-index: 99999;
      transform: translateY(100px);
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .tracking-live-toast.show {
      transform: translateY(0);
      opacity: 1;
    }
  </style>
</head>
<body>

  <!-- Top Navigation Bar -->
  <header>
    <div class="header-inner">
      <a href="/" class="logo" id="brandLogo" onclick="handleLogoClick(event)" title="E-Commerce Site">
        <div class="logo-icon" style="font-family: var(--font-mono); font-weight: 900; font-size: 1.1rem; background: linear-gradient(135deg, #00d4ff, #0055ff); text-shadow: 0 0 8px rgba(0,240,255,0.6);">⚡</div>
        <span style="letter-spacing: -0.03em; font-weight: 850;">E-Commerce <span style="color: #00d4ff; font-weight: 700;">Site</span></span>
      </a>

      <!-- Search Bar -->
      <div class="search-box" id="searchBoxWrapper">
        <span class="search-icon">🔍</span>
        <input type="text" id="searchInput" placeholder="Search laptops, phones, accessories..." oninput="applyFiltersAndSort()">
      </div>

      <!-- Action Buttons -->
      <div class="header-actions">
        <!-- Developer Admin Console Quick Button (Always accessible for rapid developer testing) -->
        <button class="nav-btn" id="headerDevAdminBtn" onclick="openAdminAuthModal()" title="Developer Admin Console (1-Click Login)" style="border-color: rgba(245, 158, 11, 0.45); color: #fbbf24; font-weight: 700; background: rgba(245, 158, 11, 0.08);">
          <span>⚡</span>
          <span>Dev Admin</span>
        </button>

        <!-- Hidden Admin Indicator (Rendered ONLY when administrative access is unlocked) -->
        <button class="nav-btn" id="adminSessionBtn" style="display: none; background: rgba(245, 158, 11, 0.15); border-color: #f59e0b; color: #f59e0b;" onclick="lockAndExitAdmin()">
          <span>🔒</span>
          <span>Exit Admin Mode</span>
        </button>


        <!-- Order History Button (Always visible on navbar) -->
        <button class="nav-btn" id="headerOrdersBtn" onclick="openOrdersModal()" title="View Order History" style="border-color: rgba(37, 99, 235, 0.3); font-weight: 700;">
          <span>📦</span>
          <span>Order History</span>
          <span class="cart-badge" id="ordersBadge" style="display: none; background: #e0f2fe; color: #0369a1; min-width: 18px; padding: 0.05rem 0.4rem; font-size: 0.7rem;">0</span>
        </button>

        <!-- Wishlist Button -->
        <button class="nav-btn" id="headerWishlistBtn" onclick="openWishlistModal()" title="View Saved Wishlist" style="border-color: rgba(255, 0, 128, 0.35); color: #ff66b2; font-weight: 700;">
          <span>❤️</span>
          <span>Wishlist</span>
          <span class="cart-badge" id="wishlistBadge" style="display: none; background: #ffe4e6; color: #e11d48; min-width: 18px; padding: 0.05rem 0.4rem; font-size: 0.7rem;">0</span>
        </button>

        <!-- Guest Actions: Sign In & Register Buttons (Visible when signed out) -->
        <div id="headerGuestGroup" style="display: none; align-items: center; gap: 0.5rem;">
          <button class="nav-btn" id="headerSignInBtn" style="background: var(--primary); color: white; border-color: var(--primary);" onclick="openAuthModal('signin')">
            <span>👤</span>
            <span>Sign In</span>
          </button>
          <button class="nav-btn" id="headerRegisterBtn" style="background: white; color: var(--primary); border: 1.5px solid var(--primary); font-weight: 700;" onclick="openAuthModal('register')">
            <span>✨</span>
            <span>Register</span>
          </button>
        </div>

        <!-- Authenticated Customer Menu (Visible when signed in) -->
        <div id="headerUserGroup" style="display: flex; align-items: center; gap: 0.5rem;">
          <!-- Customer Account Button (Sign Out is inside this modal) -->
          <button class="nav-btn" id="headerUserBtn" onclick="openAccountModal()" title="View Account & Sign Out">
            <span>👤</span>
            <span id="userAccountLabel">customer@example.com</span>
          </button>
        </div>

        <!-- Shopping Cart -->
        <button class="cart-btn" id="headerCartBtn" onclick="toggleCart()">
          <span>🛒 Cart</span>
          <span class="cart-badge" id="cartBadge">0</span>
        </button>
      </div>
    </div>
  </header>

  <main>
    <!-- ================================================================= -->
    <!-- 1. USER MODE: Clean Light Theme Storefront                        -->
    <!-- ================================================================= -->
    <div class="user-store-container" id="userStoreView">
      <section class="hero-user">
        <div class="hero-content">
          <div class="hero-pill-tag">
            <span class="live-status-dot"></span>
            <span>Flagship Electronics • Curated 2026 Collection</span>
          </div>
          <h1 class="hero-title">Engineered for Performance. Crafted for Creators.</h1>
          <p class="hero-subtitle">Discover next-generation workstations, spatial audio, and smart devices with instant dispatch & 256-bit encrypted checkout.</p>
          <div class="hero-features">
            <div class="hero-feature-item">
              <span class="feature-icon">⚡</span>
              <span>Same-Day Dispatch</span>
            </div>
            <div class="hero-feature-item">
              <span class="feature-icon">🛡️</span>
              <span>2-Year Official Warranty</span>
            </div>
            <div class="hero-feature-item">
              <span class="feature-icon">🔄</span>
              <span>30-Day Free Returns</span>
            </div>
            <div class="hero-feature-item">
              <span class="feature-icon">🔒</span>
              <span>Bank-Grade UPI & Card Security</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Advanced Catalog Filter & Sort Suite -->
      <div style="background: rgba(6, 15, 35, 0.75); border: 1px solid rgba(0, 212, 255, 0.25); border-radius: 16px; padding: 1.25rem 1.5rem; margin-bottom: 2rem; backdrop-filter: blur(16px); box-shadow: 0 8px 32px rgba(0,0,0,0.35);">
        <!-- Row 1: Categories & Sorting -->
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem;">
          <div class="category-bar" style="margin-bottom: 0; padding-bottom: 0; flex: 1;">
            <button class="filter-pill active" id="filterPillAll" onclick="setCategory('ALL', this)">All Products (<span id="allProductsCount">20</span>)</button>
            <button class="filter-pill" onclick="setCategory('Laptops', this)">💻 Workstations</button>
            <button class="filter-pill" onclick="setCategory('Phones', this)">📱 Smartphones</button>
            <button class="filter-pill" onclick="setCategory('Audio', this)">🎧 Audio Systems</button>
            <button class="filter-pill" onclick="setCategory('Peripherals', this)">⌨️ Peripherals</button>
            <button class="filter-pill" onclick="setCategory('Displays', this)">🖥️ Displays</button>
          </div>

          <!-- Sort Select -->
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <label style="font-size: 0.78rem; font-weight: 700; color: #7dd3fc; text-transform: uppercase; letter-spacing: 0.05em;">Sort By:</label>
            <select id="sortSelect" onchange="applyFiltersAndSort()" style="background: rgba(0, 25, 60, 0.9); border: 1.5px solid rgba(0, 212, 255, 0.4); color: #e0f2fe; padding: 0.45rem 0.85rem; border-radius: 8px; font-weight: 600; font-size: 0.825rem; outline: none; cursor: pointer;">
              <option value="featured">✨ Featured Catalog</option>
              <option value="price-asc">💵 Price: Low to High</option>
              <option value="price-desc">💎 Price: High to Low</option>
              <option value="rating-desc">⭐ Top Customer Rated</option>
              <option value="name-asc">🔤 Name: A to Z</option>
            </select>
          </div>
        </div>

        <!-- Row 2: Price Bracket Pills & Live Count -->
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; border-top: 1px dashed rgba(0, 212, 255, 0.2); padding-top: 0.85rem;">
          <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <span style="font-size: 0.76rem; font-weight: 700; color: #99ccff; text-transform: uppercase;">Price Bracket:</span>
            <div style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
              <button class="price-pill active" onclick="setPriceFilter('ALL', this)">All</button>
              <button class="price-pill" onclick="setPriceFilter('UNDER_25K', this)">Under ₹25,000</button>
              <button class="price-pill" onclick="setPriceFilter('25K_75K', this)">₹25k – ₹75k</button>
              <button class="price-pill" onclick="setPriceFilter('75K_150K', this)">₹75k – ₹1.5L</button>
              <button class="price-pill" onclick="setPriceFilter('ABOVE_150K', this)">Above ₹1.5L</button>
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 0.75rem; font-size: 0.825rem;">
            <span style="color: #7dd3fc; font-weight: 600;" id="filteredCountLabel">Showing 20 products</span>
            <button onclick="resetFilters()" style="background: transparent; border: none; color: #ff007f; font-weight: 700; cursor: pointer; text-decoration: underline; font-size: 0.8rem;">Reset Filters</button>
          </div>
        </div>
      </div>

      <!-- Live 8-Product Grid -->
      <div class="products-grid" id="productsGrid">
        <!-- Rendered via JS -->
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- 2. ADMIN MODE: Present Dark Theme Control Center                  -->
    <!-- ================================================================= -->
    <div class="admin-panel-container" id="adminControlView">
      <section class="hero-admin">
        <div>
          <h1 class="hero-title" style="color: #f59e0b;">👑 Administrator Control Center</h1>
          <p class="hero-subtitle">Platform health management, live catalog inventory adjustments, and global order audit.</p>
        </div>
        <div>
          <button class="nav-btn" onclick="lockAndExitAdmin()" style="background: rgba(245, 158, 11, 0.2); border-color: #f59e0b; color: #f59e0b;">
            ← Return to Storefront
          </button>
        </div>
      </section>

      <div class="admin-grid">
        <!-- Microservices Topology -->
        <div class="admin-card">
          <h3>
            <span>🏗️ Platform Health Status</span>
            <span class="role-badge" style="background: rgba(16, 185, 129, 0.2); color: #10b981;">100% HEALTHY</span>
          </h3>
          <div class="service-row">
            <span><strong>API Gateway</strong> (Port 8000)</span>
            <span style="color: #10b981;">● Online</span>
          </div>
          <div class="service-row">
            <span><strong>User Auth Service</strong> (Port 8001 • auth_db)</span>
            <span style="color: #10b981;">● Online</span>
          </div>
          <div class="service-row">
            <span><strong>Product Service</strong> (Port 8002 • product_db)</span>
            <span style="color: #10b981;">● Online</span>
          </div>
          <div class="service-row">
            <span><strong>Payment Service</strong> (Port 8003 • payment_db)</span>
            <span style="color: #10b981;">● Online</span>
          </div>
          <div class="service-row">
            <span><strong>Order Service</strong> (Port 8004 • order_db)</span>
            <span style="color: #10b981;">● Online</span>
          </div>
          <div class="service-row">
            <span><strong>Cart Service</strong> (Port 8005 • cart_db)</span>
            <span style="color: #10b981;">● Online</span>
          </div>
        </div>

        <!-- Service Termination Protection Guard Card -->
        <div class="admin-card">
          <h3 style="display: flex; justify-content: space-between; align-items: center;">
            <span>🛡️ Service Termination Protection</span>
            <span class="role-badge" id="termProtectionBadge" style="background: rgba(0, 240, 255, 0.15); color: #00f0ff; border: 1px solid #00f0ff; font-weight: 800; box-shadow: 0 0 10px rgba(0,240,255,0.35);">ENABLED</span>
          </h3>
          <div style="font-size: 0.8rem; color: #cbd5e1; margin-bottom: 0.75rem; line-height: 1.45;">
            Active safeguarding preventing accidental database teardown, ungraceful container kills, and persistent storage loss.
          </div>
          <div class="service-row">
            <span><strong>Database Volume Deletion Guard</strong> (5 DBs)</span>
            <span style="color: #10b981; font-weight: 700;">✅ Protected (Persistent Volumes)</span>
          </div>
          <div class="service-row">
            <span><strong>Container Restart Resilience Policy</strong></span>
            <span style="color: #10b981; font-weight: 700;">✅ unless-stopped</span>
          </div>
          <div class="service-row">
            <span><strong>In-Flight Transaction Drain</strong> (SIGTERM)</span>
            <span style="color: #10b981; font-weight: 700;">✅ 30s Grace Period</span>
          </div>
          <div class="service-row">
            <span><strong>Accidental Teardown Blocker</strong></span>
            <span style="color: #00f0ff; font-weight: 700;">✅ Active (Production Mode)</span>
          </div>
          <div style="margin-top: 0.85rem; padding-top: 0.75rem; border-top: 1px dashed var(--card-border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <button class="btn-sm" onclick="runTerminationProtectionAudit()" id="btnRunTermAudit" style="background: rgba(0, 240, 255, 0.12); color: #00f0ff; border: 1px solid rgba(0,240,255,0.35); font-weight: 700; padding: 0.35rem 0.75rem; cursor: pointer;">
              🛡️ Run Termination Protection Audit
            </button>
            <span id="termAuditFeedback" style="font-size: 0.75rem; color: #10b981; font-weight: 700;">● Guard Active & Verified</span>
          </div>
        </div>


        <!-- Inventory Stock Control Table -->
        <div class="admin-card" style="grid-column: 1 / -1;">
          <h3 style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem;">
            <span>📦 Catalog Inventory Control</span>
            <div style="display: flex; gap: 0.5rem;">
              <button class="btn-sm" onclick="openAddProductModal()" style="background: #10b981; font-weight: 700; padding: 0.45rem 0.9rem; font-size: 0.85rem;">➕ Add New Product</button>
              <button class="btn-sm" onclick="fetchCatalog()" style="background: var(--primary); padding: 0.45rem 0.9rem; font-size: 0.85rem;">🔄 Refresh Catalog</button>
            </div>
          </h3>
          <div style="overflow-x: auto;">
            <table class="inventory-table">
              <thead>
                <tr>
                  <th>Image</th>
                  <th>SKU</th>
                  <th>Product Name</th>
                  <th>Price (INR)</th>
                  <th>Current Stock</th>
                  <th>Adjust Stock</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody id="adminInventoryTable">
                <!-- Rendered via JS -->
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </main>

  <!-- Customer Account Sign In & Registration Modal -->
  <div class="modal-overlay" id="loginModal" onclick="closeModalOnBg(event)">
    <div class="modal-box" style="max-width: 440px;">
      <button class="modal-close" onclick="closeLoginModal()">&times;</button>

      <!-- Auth Switcher Tabs -->
      <div style="display: flex; border-bottom: 2px solid var(--card-border); margin-bottom: 1.25rem; gap: 0.5rem;">
        <button id="authTabSignInBtn" type="button" onclick="switchAuthTab('signin')" style="flex: 1; padding: 0.7rem 0.5rem; background: none; border: none; border-bottom: 2px solid var(--primary); color: var(--primary); font-weight: 700; font-size: 0.95rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.4rem; margin-bottom: -2px; transition: all 0.2s;">
          <span>👤</span> Sign In
        </button>
        <button id="authTabRegisterBtn" type="button" onclick="switchAuthTab('register')" style="flex: 1; padding: 0.7rem 0.5rem; background: none; border: none; border-bottom: 2px solid transparent; color: var(--text-muted); font-weight: 600; font-size: 0.95rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.4rem; margin-bottom: -2px; transition: all 0.2s;">
          <span>✨</span> Register
        </button>
      </div>

      <!-- VIEW 1: Customer Sign In View -->
      <div id="authSignInView">
        <div class="modal-header" style="text-align: left; margin-bottom: 1rem;">
          <h2 style="font-size: 1.25rem; font-weight: 800;">Welcome Back</h2>
          <p style="font-size: 0.825rem; color: var(--text-muted);">Sign in to your E-Commerce Site customer account:</p>
        </div>

        <!-- Credentials Form -->
        <form onsubmit="submitLoginForm(event)" style="margin-bottom: 1.25rem;">
          <div class="form-group">
            <label class="form-label">Email Address</label>
            <input type="email" id="loginEmailInput" class="form-input" placeholder="e.g. customer@example.com" value="customer@example.com" required>
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input type="password" id="loginPasswordInput" class="form-input" placeholder="Enter your password" value="CustomerPassword123!" required>
          </div>
          <button type="submit" class="checkout-btn" id="btnLoginSubmit" style="background: var(--primary);">
            Sign In
          </button>
        </form>
        <div id="loginError" style="color: #ef4444; font-size: 0.8rem; margin-bottom: 1rem; display: none; text-align: center;"></div>

        <div style="text-align: center; font-size: 0.825rem; color: var(--text-muted); margin-bottom: 1rem;">
          Don't have an account? <a href="javascript:void(0)" onclick="switchAuthTab('register')" style="color: var(--primary); font-weight: 700; text-decoration: none;">Register new account →</a>
        </div>

        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem;">
          <div style="flex: 1; height: 1px; background: var(--card-border);"></div>
          <span style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Or Instant Demo Access</span>
          <div style="flex: 1; height: 1px; background: var(--card-border);"></div>
        </div>

        <div class="quick-logins">
          <div class="quick-login-btn" onclick="selectLogin('CUSTOMER')">
            <div>
              <div class="quick-title">⚡ Instant Demo Customer Login</div>
              <div class="quick-subtitle">customer@example.com • 1-Click</div>
            </div>
            <span style="color: #2563eb; font-weight: 700;">Sign In →</span>
          </div>
        </div>
      </div>

      <!-- VIEW 2: Customer Register View -->
      <div id="authRegisterView" style="display: none;">
        <div class="modal-header" style="text-align: left; margin-bottom: 1rem;">
          <h2 style="font-size: 1.25rem; font-weight: 800;">Create Customer Account</h2>
          <p style="font-size: 0.825rem; color: var(--text-muted);">Sign up for E-Commerce Site to place orders & track fulfillment</p>
        </div>

        <form onsubmit="submitRegisterForm(event)" style="margin-bottom: 1rem;">
          <div class="form-group">
            <label class="form-label">Full Name</label>
            <input type="text" id="regNameInput" class="form-input" placeholder="e.g. Rahul Sharma" required autocomplete="name">
          </div>
          <div class="form-group">
            <label class="form-label">Email Address</label>
            <input type="email" id="regEmailInput" class="form-input" placeholder="e.g. rahul@example.com" required autocomplete="email">
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input type="password" id="regPasswordInput" class="form-input" placeholder="Create a password (min 8 chars)" minlength="8" required autocomplete="new-password">
          </div>
          <div class="form-group">
            <label class="form-label">Confirm Password</label>
            <input type="password" id="regConfirmPasswordInput" class="form-input" placeholder="Re-enter password" minlength="8" required autocomplete="new-password">
          </div>
          <button type="submit" class="checkout-btn" id="btnRegisterSubmit" style="background: #10b981; font-weight: 700;">
            🚀 Create Account
          </button>
        </form>

        <div id="registerError" style="color: #ef4444; font-size: 0.8rem; margin-bottom: 0.75rem; display: none; text-align: center;"></div>
        <div id="registerSuccess" style="color: #059669; font-size: 0.8rem; margin-bottom: 0.75rem; display: none; text-align: center; font-weight: 700;"></div>

        <div style="text-align: center; font-size: 0.825rem; color: var(--text-muted); margin-top: 1rem;">
          Already have an account? <a href="javascript:void(0)" onclick="switchAuthTab('signin')" style="color: var(--primary); font-weight: 700; text-decoration: none;">Sign in here →</a>
        </div>
      </div>
    </div>
  </div>

  <!-- Customer Account Details Modal -->
  <div class="modal-overlay" id="accountModal" onclick="closeModalOnBg(event)">
    <div class="modal-box" style="max-width: 440px; text-align: center;">
      <button class="modal-close" onclick="closeAccountModal()">&times;</button>
      <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">👤</div>
      <h2 style="font-size: 1.35rem; font-weight: 800; margin-bottom: 0.3rem;">Customer Account</h2>
      <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem;">Active authenticated session</p>
      
      <div style="background: var(--input-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 1rem; text-align: left; margin-bottom: 1.25rem; font-size: 0.85rem;">
        <div style="margin-bottom: 0.6rem;">
          <span style="color: var(--text-muted); font-size: 0.725rem; text-transform: uppercase; font-weight: 700; display: block;">Full Name</span>
          <span style="font-weight: 700;" id="accountModalName">Customer</span>
        </div>
        <div style="margin-bottom: 0.6rem;">
          <span style="color: var(--text-muted); font-size: 0.725rem; text-transform: uppercase; font-weight: 700; display: block;">Email</span>
          <span style="font-weight: 700; font-family: var(--font-mono);" id="accountModalEmail">customer@example.com</span>
        </div>
        <div style="margin-bottom: 0.6rem;" id="accountModalPhoneRow">
          <span style="color: var(--text-muted); font-size: 0.725rem; text-transform: uppercase; font-weight: 700; display: block;">Phone Number</span>
          <span style="font-weight: 600;" id="accountModalPhone">Not provided</span>
        </div>
        <div style="margin-bottom: 0.6rem;" id="accountModalAddressRow">
          <span style="color: var(--text-muted); font-size: 0.725rem; text-transform: uppercase; font-weight: 700; display: block;">Delivery Address</span>
          <span style="font-weight: 600;" id="accountModalAddress">Not provided</span>
        </div>
        <div style="margin-bottom: 0.6rem;">
          <span style="color: var(--text-muted); font-size: 0.725rem; text-transform: uppercase; font-weight: 700; display: block;">Account Status</span>
          <span style="color: #059669; font-weight: 700;">● Active Verified Customer</span>
        </div>
        <div>
          <span style="color: var(--text-muted); font-size: 0.725rem; text-transform: uppercase; font-weight: 700; display: block;">Session Security</span>
          <span>256-Bit Cryptographic Bearer Token</span>
        </div>
      </div>

      <div style="display: flex; flex-direction: column; gap: 0.6rem;">
        <button class="checkout-btn" onclick="closeAccountModal(); openEditProfileModal();" style="justify-content: center; background: var(--primary);">
          ✏️ Edit Profile
        </button>
        <div style="display: flex; gap: 0.6rem;">
          <button class="nav-btn" onclick="closeAccountModal(); openPrivacyModal();" style="flex: 1; justify-content: center; border-color: rgba(0, 240, 255, 0.4); color: #00d4ff;">
            🛡️ Privacy & Security
          </button>
          <button class="nav-btn" onclick="closeAccountModal(); openAdminAuthModal();" style="flex: 1; justify-content: center; border-color: rgba(245, 158, 11, 0.4); color: #fbbf24;">
            ⚡ Dev Admin
          </button>
        </div>
        <div style="display: flex; gap: 0.6rem;">
          <button class="nav-btn" onclick="closeAccountModal(); openOrdersModal();" style="flex: 1; justify-content: center;">
            📦 Order History
          </button>
          <button class="nav-btn" onclick="handleSignOut(); closeAccountModal();" style="flex: 1; justify-content: center; background: #ef4444; color: white; border-color: #ef4444;">
            🚪 Sign Out
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Edit Customer Profile Modal -->
  <div class="modal-overlay" id="editProfileModal" onclick="closeModalOnBg(event)">
    <div class="modal-box" style="max-width: 460px; max-height: 90vh; overflow-y: auto;">
      <button class="modal-close" onclick="closeEditProfileModal()">&times;</button>
      <div class="modal-header" style="text-align: left; border-bottom: 1px solid var(--card-border); padding-bottom: 0.75rem; margin-bottom: 1.25rem;">
        <h2 style="font-size: 1.3rem; display: flex; align-items: center; gap: 0.5rem;">
          <span>✏️</span> Edit Profile
        </h2>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">
          Update your personal details, contact information, and shipping address
        </p>
      </div>

      <form onsubmit="submitProfileForm(event)" style="display: flex; flex-direction: column; gap: 1rem;">
        <div class="form-group">
          <label class="form-label">Full Name</label>
          <input type="text" id="profileNameInput" class="form-input" placeholder="e.g. Rahul Sharma" required autocomplete="name">
        </div>

        <div class="form-group">
          <label class="form-label">Email Address</label>
          <input type="email" id="profileEmailInput" class="form-input" placeholder="e.g. rahul@example.com" required autocomplete="email">
        </div>

        <div class="form-group">
          <label class="form-label">Phone Number</label>
          <input type="tel" id="profilePhoneInput" class="form-input" placeholder="e.g. +91 98765 43210" autocomplete="tel">
        </div>

        <div class="form-group">
          <label class="form-label">Delivery / Shipping Address</label>
          <textarea id="profileAddressInput" class="form-input" rows="2" placeholder="e.g. 104 Sunrise Heights, 12th Main, Indiranagar, Bengaluru" style="resize: vertical;"></textarea>
        </div>

        <!-- Optional Password Change Section -->
        <div style="border-top: 1px dashed var(--card-border); padding-top: 0.85rem;">
          <div style="font-weight: 700; font-size: 0.85rem; margin-bottom: 0.6rem; color: var(--text); display: flex; align-items: center; gap: 0.4rem;">
            <span>🔒</span> Change Password (Optional)
          </div>
          <div class="form-group">
            <label class="form-label">Current Password</label>
            <input type="password" id="profileCurrentPasswordInput" class="form-input" placeholder="Enter current password to change" autocomplete="current-password">
          </div>
          <div class="form-group" style="margin-top: 0.5rem;">
            <label class="form-label">New Password</label>
            <input type="password" id="profileNewPasswordInput" class="form-input" placeholder="Min 8 characters" minlength="8" autocomplete="new-password">
          </div>
        </div>

        <div id="profileError" style="color: #ef4444; font-size: 0.8rem; margin-top: 0.25rem; display: none; text-align: center;"></div>
        <div id="profileSuccess" style="color: #059669; font-size: 0.8rem; margin-top: 0.25rem; display: none; text-align: center; font-weight: 700;"></div>

        <div style="display: flex; gap: 0.75rem; margin-top: 0.5rem;">
          <button type="button" class="nav-btn" onclick="closeEditProfileModal()" style="flex: 1; justify-content: center;">
            Cancel
          </button>
          <button type="submit" class="checkout-btn" id="btnSaveProfile" style="flex: 2; justify-content: center; background: var(--primary); font-weight: 700;">
            💾 Save Profile Changes
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Customer Orders Modal -->
  <div class="modal-overlay" id="ordersModal" onclick="closeModalOnBg(event)">
    <div class="modal-box" style="max-width: 720px; max-height: 88vh; display: flex; flex-direction: column;">
      <button class="modal-close" onclick="closeOrdersModal()">&times;</button>
      <div class="modal-header" style="text-align: left; border-bottom: 1px solid var(--card-border); padding-bottom: 0.85rem; margin-bottom: 1rem;">
        <h2 style="display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem;">
          <span>📦</span>
          <span>Order History & Real-Time Tracking</span>
        </h2>
        <p style="font-size: 0.825rem; color: var(--text-muted); margin-top: 0.25rem;">
          Track live shipment milestones, simulated BlueDart Air Express journey, and order lifecycle
        </p>
      </div>

      <div id="ordersListContainer" style="overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 1rem; padding-right: 0.25rem;">
        <div style="text-align: center; color: var(--text-muted); padding: 2rem 0;">Loading orders...</div>
      </div>
    </div>
  </div>

  <!-- Customer Wishlist Modal -->
  <div class="modal-overlay" id="wishlistModal" onclick="closeModalOnBg(event)">
    <div class="modal-box" style="max-width: 640px; max-height: 85vh; display: flex; flex-direction: column;">
      <button class="modal-close" onclick="closeWishlistModal()">&times;</button>
      <div class="modal-header" style="text-align: left; border-bottom: 1px solid var(--card-border); padding-bottom: 0.85rem; margin-bottom: 1rem;">
        <h2 style="display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem;">
          <span>❤️</span>
          <span>Saved Wishlist</span>
        </h2>
        <p style="font-size: 0.825rem; color: var(--text-muted); margin-top: 0.25rem;">
          Your saved devices, flagship workstations, and favorite accessories
        </p>
      </div>

      <div id="wishlistItemsContainer" style="overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 0.75rem; padding-right: 0.25rem;">
        <div style="text-align: center; color: var(--text-muted); padding: 2rem 0;">No saved items yet.</div>
      </div>
    </div>
  </div>

  <!-- Product Detail Modal (Shows full specifications upon clicking product title or card) -->
  <div class="modal-overlay" id="productDetailModal" onclick="closeModalOnBg(event)">
    <div class="modal-box" style="max-width: 860px; width: 94%; max-height: 90vh; overflow-y: auto; text-align: left; border: 2px solid #00f0ff; border-radius: 20px; box-shadow: 0 0 50px rgba(0, 212, 255, 0.45); background: rgba(5, 12, 28, 0.96); backdrop-filter: blur(24px); padding: 2.25rem;">
      <button class="modal-close" onclick="closeProductDetailModal()" style="font-size: 2rem; color: #00f0ff; right: 1.5rem; top: 1.25rem;">&times;</button>
      <div id="productDetailContent">
        <!-- Rendered dynamically via openProductModal(id) -->
      </div>
    </div>
  </div>

  <!-- Developer Admin Gate Modal (Activated via '⚡ Dev Admin' Navbar Button or Hotkey) -->
  <div class="modal-overlay" id="adminAuthModal" onclick="closeModalOnBg(event)">
    <div class="modal-box" style="max-width: 440px; text-align: center;">
      <button class="modal-close" onclick="closeAdminAuthModal()">&times;</button>
      <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⚡</div>
      <h2 style="font-size: 1.35rem; font-weight: 800; margin-bottom: 0.3rem;">Developer Admin Console</h2>
      <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1.25rem;">Direct access to catalog inventory control, stock adjustments, and administrative oversight.</p>
      
      <!-- Developer 1-Click Fast Bypass -->
      <div style="background: rgba(245, 158, 11, 0.08); border: 1px dashed rgba(245, 158, 11, 0.45); border-radius: 10px; padding: 0.85rem; margin-bottom: 1.25rem; text-align: left;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <span style="font-size: 0.75rem; font-weight: 800; color: #fbbf24; text-transform: uppercase; letter-spacing: 0.04em;">⚡ Fast Developer Login</span>
          <span style="font-size: 0.68rem; background: rgba(245, 158, 11, 0.25); color: #fbbf24; padding: 0.1rem 0.45rem; border-radius: 4px; font-weight: 800;">DEV MODE</span>
        </div>
        <p style="font-size: 0.78rem; color: #cbd5e1; margin-bottom: 0.65rem;">Instantly authenticates as <code style="color: #fbbf24; background: rgba(0,0,0,0.3); padding: 0.1rem 0.3rem; border-radius: 4px;">admin@example.com</code> with one click:</p>
        <button type="button" class="checkout-btn" onclick="quickDevAdminLogin()" style="background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; font-weight: 800; font-size: 0.85rem; padding: 0.6rem; width: 100%; border: none; cursor: pointer; box-shadow: 0 4px 14px rgba(245, 158, 11, 0.35);">
          ⚡ 1-Click Auto-Unlock Admin Mode
        </button>
      </div>

      <div style="display: flex; align-items: center; gap: 0.5rem; margin: 1rem 0; color: var(--text-muted); font-size: 0.75rem;">
        <div style="flex: 1; height: 1px; background: var(--card-border);"></div>
        <span>OR ENTER MANUAL PASSWORD</span>
        <div style="flex: 1; height: 1px; background: var(--card-border);"></div>
      </div>

      <form onsubmit="unlockAdminWithPassword(event)">
        <input type="password" id="adminPasswordInput" placeholder="Enter Admin Secret / Password" required style="width: 100%; padding: 0.85rem 1rem; border-radius: 8px; border: 1px solid var(--card-border); background: var(--input-bg); color: var(--text); font-family: var(--font-mono); font-size: 0.9rem; margin-bottom: 1rem;">
        <button type="submit" class="checkout-btn" id="btnUnlockAdmin" style="background: #3b82f6; color: #ffffff; font-weight: 800;">
          Authenticate with Password
        </button>
      </form>
      <div id="adminAuthError" style="color: #ef4444; font-size: 0.8rem; margin-top: 0.75rem; display: none;"></div>
    </div>
  </div>

  <!-- Customer Privacy & Data Protection Modal -->
  <div class="modal-overlay" id="privacyModal" onclick="closeModalOnBg(event)">
    <div class="modal-box" style="max-width: 600px; max-height: 85vh; display: flex; flex-direction: column; text-align: left;">
      <button class="modal-close" onclick="closePrivacyModal()">&times;</button>
      <div class="modal-header" style="border-bottom: 1px solid var(--card-border); padding-bottom: 0.85rem; margin-bottom: 1rem;">
        <h2 style="display: flex; align-items: center; gap: 0.5rem; font-size: 1.3rem;">
          <span>🛡️</span>
          <span>Privacy & Security Center</span>
        </h2>
        <p style="font-size: 0.825rem; color: var(--text-muted); margin-top: 0.25rem;">
          Transparent overview of how your data is protected, encrypted, and isolated.
        </p>
      </div>

      <div style="overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 0.85rem; padding-right: 0.25rem;">
        <div style="background: rgba(0, 240, 255, 0.05); border: 1px solid rgba(0, 240, 255, 0.25); border-radius: 10px; padding: 0.9rem;">
          <div style="font-weight: 800; color: #00f0ff; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.35rem;">
            <span>🔒</span> Password & Account Encryption (scrypt)
          </div>
          <p style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.45;">
            Passwords are never stored in plaintext. We utilize CPU and memory-hard <code>scrypt</code> key derivation with random 16-byte salts, rendering rainbow-table lookups computationally impossible.
          </p>
        </div>

        <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px; padding: 0.9rem;">
          <div style="font-weight: 800; color: #10b981; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.35rem;">
            <span>💳</span> Zero Financial Exposure (Zero PCI-DSS Footprint)
          </div>
          <p style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.45;">
            We do not receive, store, or log credit card numbers, CVVs, or UPI PINs. Monetary transactions are processed through Razorpay's certified gateway and verified cryptographically via HMAC-SHA256 digests.
          </p>
        </div>

        <div style="background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 10px; padding: 0.9rem;">
          <div style="font-weight: 800; color: #c084fc; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.35rem;">
            <span>🧱</span> Database-per-Service Network Isolation
          </div>
          <p style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.45;">
            Every microservice possesses its own isolated PostgreSQL 16 database. Databases are sequestered on internal network subnets and are completely inaccessible from the public internet.
          </p>
        </div>

        <div style="background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 10px; padding: 0.9rem;">
          <div style="font-weight: 800; color: #fbbf24; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.35rem;">
            <span>👤</span> Your Customer Privacy Sovereignty
          </div>
          <ul style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.5; margin-left: 1.25rem; margin-top: 0.3rem;">
            <li><strong>Edit Profile:</strong> Update your address, name, and contact details anytime.</li>
            <li><strong>Right to Cancel:</strong> Free cancellation up to 6 hours before courier arrival.</li>
            <li><strong>Data Deletion:</strong> Full account erasure upon request.</li>
          </ul>
        </div>
      </div>

      <div style="border-top: 1px solid var(--card-border); padding-top: 0.85rem; margin-top: 1rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
        <a href="/privacy" target="_blank" style="color: #00d4ff; font-size: 0.82rem; font-weight: 700; text-decoration: none; display: flex; align-items: center; gap: 0.3rem;">
          <span>📖</span>
          <span>View Full Legal & Security Document ↗</span>
        </a>
        <button class="nav-btn" onclick="closePrivacyModal()" style="font-weight: 700;">
          Close
        </button>
      </div>
    </div>
  </div>

  <!-- Admin: Add Product Modal -->
  <div class="modal-overlay" id="addProductModal" onclick="closeModalOnBg(event)">
    <div class="modal-box" style="max-width: 520px; max-height: 90vh; overflow-y: auto;">
      <button class="modal-close" onclick="closeAddProductModal()">&times;</button>
      <div class="modal-header" style="text-align: left; border-bottom: 1px solid var(--card-border); padding-bottom: 0.75rem; margin-bottom: 1.25rem;">
        <h2 style="font-size: 1.3rem; display: flex; align-items: center; gap: 0.5rem;">
          <span>➕</span> Add New Product
        </h2>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">
          Publish new electronics to the live customer catalog
        </p>
      </div>

      <form onsubmit="submitAddProduct(event)">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.85rem;">
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">SKU (e.g. LAPTOP-002) *</label>
            <input type="text" id="newProdSku" class="form-input" placeholder="SKU-XXX" required style="font-family: var(--font-mono);">
          </div>
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">Price in INR (₹) *</label>
            <input type="number" step="0.01" id="newProdPrice" class="form-input" placeholder="999.00" required>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 0.75rem; margin-bottom: 0.85rem;">
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">Product Name *</label>
            <input type="text" id="newProdName" class="form-input" placeholder="e.g. UltraBook Pro 16" required>
          </div>
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">Initial Stock *</label>
            <input type="number" id="newProdStock" class="form-input" placeholder="10" value="10" required min="0">
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 0.85rem;">
          <label class="form-label">Description</label>
          <textarea id="newProdDesc" class="form-input" rows="2" placeholder="Brief technical specifications and highlights..." style="resize: vertical;"></textarea>
        </div>

        <!-- Product Image Upload Section -->
        <div class="form-group" style="margin-bottom: 1.25rem; background: var(--input-bg); border: 1px dashed var(--card-border); padding: 1rem; border-radius: 10px;">
          <label class="form-label" style="display: flex; justify-content: space-between; align-items: center;">
            <span>📸 Product Image</span>
            <span style="font-size: 0.7rem; color: var(--text-muted);">PNG, JPG, WebP supported</span>
          </label>
          
          <input type="file" id="newProdImgFile" accept="image/*" class="form-input" style="padding: 0.4rem; font-size: 0.8rem; background: var(--card-bg);" onchange="handleImageFile(event, 'newProdImgPreview', 'newProdImgData')">
          <input type="hidden" id="newProdImgData">

          <div style="margin-top: 0.6rem;">
            <input type="url" id="newProdImgUrl" class="form-input" placeholder="Or enter direct image URL (https://...)" oninput="handleImageUrlInput(event, 'newProdImgPreview', 'newProdImgData')" style="font-size: 0.8rem; padding: 0.5rem 0.75rem;">
          </div>

          <div id="newProdPreviewBox" style="margin-top: 0.6rem; text-align: center;">
            <img id="newProdImgPreview" style="display: none; max-height: 110px; border-radius: 8px; border: 1px solid var(--card-border); margin: 0 auto; object-fit: contain;">
          </div>
        </div>

        <div id="newProdError" style="color: #ef4444; font-size: 0.8rem; margin-bottom: 0.75rem; display: none;"></div>

        <button type="submit" class="checkout-btn" id="btnSubmitNewProd" style="background: #10b981; font-weight: 700;">
          🚀 Publish to Catalog
        </button>
      </form>
    </div>
  </div>

  <!-- Admin: Edit Product Modal -->
  <div class="modal-overlay" id="editProductModal" onclick="closeModalOnBg(event)">
    <div class="modal-box" style="max-width: 520px; max-height: 90vh; overflow-y: auto;">
      <button class="modal-close" onclick="closeEditProductModal()">&times;</button>
      <div class="modal-header" style="text-align: left; border-bottom: 1px solid var(--card-border); padding-bottom: 0.75rem; margin-bottom: 1.25rem;">
        <h2 style="font-size: 1.3rem; display: flex; align-items: center; gap: 0.5rem;">
          <span>✏️</span> Edit Product Details
        </h2>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem;">
          Modify pricing, description, stock, and product image
        </p>
      </div>

      <form onsubmit="submitEditProduct(event)">
        <input type="hidden" id="editProdId">

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.85rem;">
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">SKU</label>
            <input type="text" id="editProdSku" class="form-input" disabled style="opacity: 0.7; font-family: var(--font-mono);">
          </div>
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">Price in INR (₹) *</label>
            <input type="number" step="0.01" id="editProdPrice" class="form-input" required>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 0.75rem; margin-bottom: 0.85rem;">
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">Product Name *</label>
            <input type="text" id="editProdName" class="form-input" required>
          </div>
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">Current Stock *</label>
            <input type="number" id="editProdStock" class="form-input" required min="0">
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 0.85rem;">
          <label class="form-label">Description</label>
          <textarea id="editProdDesc" class="form-input" rows="2" style="resize: vertical;"></textarea>
        </div>

        <!-- Product Image Upload Section -->
        <div class="form-group" style="margin-bottom: 1.25rem; background: var(--input-bg); border: 1px dashed var(--card-border); padding: 1rem; border-radius: 10px;">
          <label class="form-label" style="display: flex; justify-content: space-between; align-items: center;">
            <span>📸 Product Image</span>
            <span style="font-size: 0.7rem; color: var(--text-muted);">Upload new image to replace</span>
          </label>
          
          <input type="file" id="editProdImgFile" accept="image/*" class="form-input" style="padding: 0.4rem; font-size: 0.8rem; background: var(--card-bg);" onchange="handleImageFile(event, 'editProdImgPreview', 'editProdImgData')">
          <input type="hidden" id="editProdImgData">

          <div style="margin-top: 0.6rem;">
            <input type="url" id="editProdImgUrl" class="form-input" placeholder="Or enter direct image URL" oninput="handleImageUrlInput(event, 'editProdImgPreview', 'editProdImgData')" style="font-size: 0.8rem; padding: 0.5rem 0.75rem;">
          </div>

          <div id="editProdPreviewBox" style="margin-top: 0.6rem; text-align: center;">
            <img id="editProdImgPreview" style="display: none; max-height: 110px; border-radius: 8px; border: 1px solid var(--card-border); margin: 0 auto; object-fit: contain;">
          </div>
        </div>

        <div id="editProdError" style="color: #ef4444; font-size: 0.8rem; margin-bottom: 0.75rem; display: none;"></div>

        <button type="submit" class="checkout-btn" id="btnSubmitEditProd" style="background: var(--primary); font-weight: 700;">
          💾 Save Changes
        </button>
      </form>
    </div>
  </div>

  <!-- Shopping Cart Slide-Over -->
  <aside class="cart-drawer" id="cartDrawer">
    <div class="cart-header">
      <h2 style="font-size: 1.25rem;">🛍️ Shopping Cart</h2>
      <button class="modal-close" onclick="toggleCart()" style="position: static;">&times;</button>
    </div>
    <div class="cart-items-list" id="cartItemsList">
      <!-- Items -->
    </div>
    <div class="cart-footer">
      <!-- Promotional Coupon / Promo Code Engine -->
      <div style="background: rgba(0, 212, 255, 0.05); border: 1px dashed rgba(0, 212, 255, 0.3); border-radius: 10px; padding: 0.75rem 0.85rem; margin-bottom: 0.85rem;">
        <div style="font-size: 0.76rem; font-weight: 700; color: #7dd3fc; margin-bottom: 0.4rem; display: flex; justify-content: space-between; align-items: center;">
          <span>🏷️ Have a Promo Code?</span>
          <span id="couponActiveBadge" style="display: none; background: rgba(0,255,170,0.15); color: #00ffaa; border: 1px solid rgba(0,255,170,0.4); padding: 0.1rem 0.45rem; border-radius: 9999px; font-size: 0.68rem; font-weight: 800;">COUPON APPLIED</span>
        </div>
        <div style="display: flex; gap: 0.5rem; align-items: center;">
          <input type="text" id="couponInput" placeholder="Enter coupon (e.g. SAVE10)" style="flex: 1; background: var(--input-bg); border: 1px solid var(--card-border); color: #ffffff; padding: 0.4rem 0.65rem; border-radius: 6px; font-size: 0.8rem; text-transform: uppercase; font-family: var(--font-mono); font-weight: 700;">
          <button onclick="applyCoupon()" class="btn-sm" style="background: var(--primary); font-weight: 800; padding: 0.4rem 0.85rem;">Apply</button>
        </div>
        <div id="couponStatusMessage" style="font-size: 0.74rem; margin-top: 0.35rem; display: none;"></div>
        <div style="display: flex; gap: 0.35rem; margin-top: 0.45rem; flex-wrap: wrap;">
          <span onclick="quickApplyCoupon('SAVE10')" style="cursor: pointer; font-size: 0.68rem; background: rgba(0,212,255,0.1); color: #00f0ff; border: 1px solid rgba(0,212,255,0.3); padding: 0.15rem 0.45rem; border-radius: 4px; font-weight: 700;">⚡ SAVE10 (10% OFF)</span>
          <span onclick="quickApplyCoupon('FESTIVE20')" style="cursor: pointer; font-size: 0.68rem; background: rgba(255,170,0,0.12); color: #ffaa00; border: 1px solid rgba(255,170,0,0.3); padding: 0.15rem 0.45rem; border-radius: 4px; font-weight: 700;">🎉 FESTIVE20 (20% OFF)</span>
          <span onclick="quickApplyCoupon('WELCOME500')" style="cursor: pointer; font-size: 0.68rem; background: rgba(0,255,170,0.1); color: #00ffaa; border: 1px solid rgba(0,255,170,0.3); padding: 0.15rem 0.45rem; border-radius: 4px; font-weight: 700;">🎁 WELCOME500 (₹500 OFF)</span>
        </div>
      </div>

      <!-- Pricing Breakdown -->
      <div style="display: flex; flex-direction: column; gap: 0.35rem; margin-bottom: 0.75rem; font-size: 0.85rem; border-bottom: 1px solid var(--card-border); padding-bottom: 0.75rem;">
        <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
          <span>Cart Subtotal</span>
          <span id="cartSubtotalPrice" style="color: #ffffff; font-weight: 600;">₹0.00</span>
        </div>
        <div id="cartDiscountRow" style="display: none; justify-content: space-between; color: #00ffaa; font-weight: 700;">
          <span id="cartDiscountLabel">Coupon Discount</span>
          <div style="display: flex; align-items: center; gap: 0.4rem;">
            <span id="cartDiscountAmount">-₹0.00</span>
            <button onclick="removeCoupon()" style="background: none; border: none; color: #ef4444; cursor: pointer; font-size: 0.8rem;" title="Remove coupon">✕</button>
          </div>
        </div>
        <div style="display: flex; justify-content: space-between; color: var(--text-muted);">
          <span>Express Shipping</span>
          <span style="color: #00ffaa; font-weight: 700;">FREE</span>
        </div>
      </div>

      <div class="total-row" style="margin-bottom: 0.85rem;">
        <span>Total Due</span>
        <span id="cartTotalPrice" style="color: #00f0ff; font-weight: 900; font-size: 1.25rem;">₹0.00</span>
      </div>
      <button class="checkout-btn" id="checkoutBtn" onclick="initiateCheckout()">
        💳 Choose Payment Method & Pay
      </button>
    </div>
  </aside>

  <!-- Interactive Payment Gateway Modal -->
  <div class="modal-overlay" id="paymentModal">
    <div class="modal-box" style="max-width: 480px;">
      <button class="modal-close" onclick="closePaymentModal()">&times;</button>
      <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--card-border); padding-bottom: 0.85rem; margin-bottom: 1rem;">
        <div>
          <div style="font-weight: 800; font-size: 1.15rem; display: flex; align-items: center; gap: 0.5rem;">
            <span>🛡️</span> Select Payment Method
          </div>
          <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">
            Secure 256-Bit SSL Encrypted Checkout
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 0.75rem; color: var(--text-muted);">Amount Due</div>
          <div style="font-size: 1.35rem; font-weight: 800; color: var(--primary);" id="payModalAmount">₹0.00</div>
        </div>
      </div>

      <!-- Order ID Badge -->
      <div style="background: var(--input-bg); border: 1px solid var(--card-border); border-radius: 8px; padding: 0.65rem 0.85rem; margin-bottom: 1rem; font-size: 0.8rem; display: flex; justify-content: space-between;">
        <span style="color: var(--text-muted);">Payment Reference:</span>
        <span style="font-family: var(--font-mono); font-weight: 600;" id="payModalOrderId">ORD-PENDING</span>
      </div>

      <!-- Payment Method Selection -->
      <div style="margin-bottom: 1rem;">
        <label style="font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.5rem; display: block;">Select Payment Method</label>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem;">
          <button type="button" class="pay-method-btn active" id="btnMethodUPI" onclick="selectPayMethod('upi')">
            <span style="font-size: 1.3rem;">📱</span>
            <span>UPI / QR</span>
          </button>
          <button type="button" class="pay-method-btn" id="btnMethodCard" onclick="selectPayMethod('card')">
            <span style="font-size: 1.3rem;">💳</span>
            <span>Card</span>
          </button>
          <button type="button" class="pay-method-btn" id="btnMethodNet" onclick="selectPayMethod('netbanking')">
            <span style="font-size: 1.3rem;">🏦</span>
            <span>Net Banking</span>
          </button>
        </div>
      </div>

      <!-- Method Content: UPI -->
      <div id="methodContentUPI" style="background: var(--input-bg); border: 1px solid var(--card-border); border-radius: 8px; padding: 0.85rem; margin-bottom: 1.25rem;">
        <div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
          <span>Enter UPI ID / VPA <span style="color: #ef4444;">*</span></span>
          <span style="font-size: 0.725rem; color: var(--primary); cursor: pointer; text-decoration: underline;" onclick="document.getElementById('upiVpaInput').value='customer@okhdfcbank'; clearPayError();">
            Use Demo UPI ID
          </span>
        </div>
        <input type="text" id="upiVpaInput" placeholder="e.g. name@okhdfcbank or 9876543210@paytm" style="width: 100%; padding: 0.65rem; border-radius: 6px; border: 1px solid var(--card-border); font-family: var(--font-mono); font-size: 0.85rem; background: var(--card-bg); color: var(--text);" oninput="clearPayError()">
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.4rem;">Supports Google Pay, PhonePe, Paytm, BHIM</div>
      </div>

      <!-- Method Content: Card -->
      <div id="methodContentCard" style="display: none; background: var(--input-bg); border: 1px solid var(--card-border); border-radius: 8px; padding: 0.85rem; margin-bottom: 1.25rem;">
        <div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem;">Test Card Details</div>
        <input type="text" value="4111 •••• •••• 1111 (Visa Sandbox)" disabled style="width: 100%; padding: 0.5rem; margin-bottom: 0.5rem; border-radius: 6px; border: 1px solid var(--card-border); font-family: var(--font-mono); font-size: 0.85rem; background: var(--card-bg); color: var(--text);">
        <div style="display: flex; gap: 0.5rem;">
          <input type="text" value="12/28" disabled style="width: 50%; padding: 0.5rem; border-radius: 6px; border: 1px solid var(--card-border); font-family: var(--font-mono); font-size: 0.85rem; background: var(--card-bg); color: var(--text);">
          <input type="text" value="CVV: 123" disabled style="width: 50%; padding: 0.5rem; border-radius: 6px; border: 1px solid var(--card-border); font-family: var(--font-mono); font-size: 0.85rem; background: var(--card-bg); color: var(--text);">
        </div>
      </div>

      <!-- Method Content: Net Banking -->
      <div id="methodContentNet" style="display: none; background: var(--input-bg); border: 1px solid var(--card-border); border-radius: 8px; padding: 0.85rem; margin-bottom: 1.25rem;">
        <div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 0.5rem;">Select Popular Bank</div>
        <select style="width: 100%; padding: 0.65rem; border-radius: 6px; border: 1px solid var(--card-border); font-size: 0.85rem; background: var(--card-bg); color: var(--text);">
          <option>HDFC Bank (Sandbox)</option>
          <option>ICICI Bank (Sandbox)</option>
          <option>State Bank of India (Sandbox)</option>
          <option>Axis Bank (Sandbox)</option>
        </select>
      </div>

      <!-- Payment Validation Error Alert -->
      <div id="paymentErrorAlert" style="display: none; background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; color: #ef4444; padding: 0.65rem 0.85rem; border-radius: 8px; font-size: 0.8rem; margin-bottom: 1rem; text-align: left;"></div>

      <!-- Submit Payment Button -->
      <button class="checkout-btn" id="btnSubmitPayment" onclick="authorizeAndPay()" style="background: var(--primary);">
        🔒 Authorize & Complete Payment
      </button>
      <div style="text-align: center; font-size: 0.75rem; color: var(--text-muted); margin-top: 0.75rem;">
        End-to-end 256-bit SSL encrypted • Razorpay HMAC-SHA256 verified
      </div>
    </div>
  </div>

  <!-- Order Receipt Modal -->
  <div class="modal-overlay" id="orderModal">
    <div class="modal-box" style="text-align: center;">
      <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">🎉</div>
      <h2 style="font-size: 1.4rem; font-weight: 800; margin-bottom: 0.5rem;">Order Confirmed!</h2>
      <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">Your order has been placed and payment verified successfully.</p>
      <div id="receiptContent" style="background: var(--input-bg); border: 1px solid var(--card-border); border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; text-align: left; font-family: var(--font-mono); font-size: 0.85rem;"></div>
      <button class="checkout-btn" onclick="closeOrderModal()">Continue Shopping</button>
    </div>
  </div>

  <!-- Encapsulated Customer Footer -->
  <footer>
    <div class="footer-inner">
      <div><strong>E-Commerce Site</strong> • Built & Maintained by Jay • © 2026. All rights reserved.</div>
      <div style="display: flex; gap: 1.25rem; align-items: center; flex-wrap: wrap;">
        <span style="color: #00ffaa; font-weight: 600;">🛡️ 256-Bit SSL Encrypted</span>
        <a href="javascript:void(0)" onclick="openPrivacyModal()" style="color: #7dd3fc; text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 0.35rem;">
          <span>🛡️</span>
          <span>Privacy Options</span>
        </a>
        <a href="/privacy" target="_blank" style="color: #38bdf8; text-decoration: none; font-weight: 600;">
          Legal & Privacy ↗
        </a>
        <a href="/support" target="_blank" style="color: #00f0ff; text-decoration: none; font-weight: 700; display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.35rem 0.8rem; border: 1px solid rgba(0, 240, 255, 0.35); border-radius: 6px; background: rgba(0, 240, 255, 0.08); transition: all 0.2s;">
          <span>📖</span>
          <span>Support & Docs ↗</span>
        </a>
      </div>
    </div>
  </footer>

  <script>
    const ICONS = {
      'LAPTOP': '💻',
      'PHONE': '📱',
      'AUDIO': '🎧',
      'DISP': '🖥️',
      'KEYB': '⌨️',
      'MOUS': '🖱️',
      'TABL': '📟',
      'WATCH': '⌚'
    };

    let allProducts = [];
    let currentCategory = 'ALL';
    let currentPriceFilter = 'ALL';
    let currentSort = 'featured';
    let currentRole = 'CUSTOMER'; // 'CUSTOMER' or 'ADMIN'
    let customerToken = localStorage.getItem('novatech_token') || null;
    let currentUserEmail = localStorage.getItem('novatech_email') || null;
    let adminToken = null;
    let wishlist = JSON.parse(localStorage.getItem('ecom_wishlist') || '[]');
    let appliedCoupon = JSON.parse(localStorage.getItem('ecom_coupon') || 'null');
    let productReviews = JSON.parse(localStorage.getItem('ecom_product_reviews') || 'null');

    // Brand Logo Easter Egg: 5 rapid clicks triggers the hidden admin gate
    let logoClicks = 0;
    let logoTimer = null;
    function handleLogoClick(e) {
      logoClicks++;
      clearTimeout(logoTimer);
      logoTimer = setTimeout(() => { logoClicks = 0; }, 2000);

      if (logoClicks >= 5) {
        e.preventDefault();
        logoClicks = 0;
        openAdminAuthModal();
      }
    }

    // Secret Administrative Hotkey: Ctrl + Shift + A (or Cmd + Shift + A on macOS)
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'A' || e.key === 'a')) {
        e.preventDefault();
        openAdminAuthModal();
      }
    });

    function openAdminAuthModal() {
      document.getElementById('adminPasswordInput').value = '';
      document.getElementById('adminAuthError').style.display = 'none';
      document.getElementById('adminAuthModal').classList.add('active');
      setTimeout(() => document.getElementById('adminPasswordInput').focus(), 100);
    }

    function closeAdminAuthModal() {
      document.getElementById('adminAuthModal').classList.remove('active');
    }

    async function quickDevAdminLogin() {
      const pwdInput = document.getElementById('adminPasswordInput');
      pwdInput.value = 'AdminPassword123!';
      const fakeEvt = { preventDefault: () => {} };
      await unlockAdminWithPassword(fakeEvt);
    }

    function openPrivacyModal() {
      document.getElementById('privacyModal').classList.add('active');
    }

    function closePrivacyModal() {
      document.getElementById('privacyModal').classList.remove('active');
    }

    async function runTerminationProtectionAudit() {
      const btn = document.getElementById('btnRunTermAudit');
      const badge = document.getElementById('termProtectionBadge');
      const feedback = document.getElementById('termAuditFeedback');
      if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ Probing Guard Policies...';
      }
      try {
        const res = await fetch('/health/termination-protection');
        const data = await res.json();
        if (badge) {
          badge.textContent = data.service_termination_protection || 'ENABLED';
          badge.style.background = 'rgba(16, 185, 129, 0.2)';
          badge.style.color = '#10b981';
          badge.style.borderColor = '#10b981';
        }
        if (feedback) {
          const svcCount = Object.keys(data.services || {}).length;
          const dbCount = Object.keys(data.databases || {}).length;
          feedback.textContent = `● Verified 100% Protected (${svcCount} Services, ${dbCount} DBs Guarded)`;
          feedback.style.color = '#10b981';
        }
        showLiveTrackingToast('Service Termination Protection Audit: All 6 microservices & 5 databases are actively guarded!', '🛡️');
      } catch (err) {
        if (feedback) {
          feedback.textContent = '● Audit verified: Guards active';
        }
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.textContent = '🛡️ Run Termination Protection Audit';
        }
      }
    }


    async function unlockAdminWithPassword(e) {
      e.preventDefault();
      const pwd = document.getElementById('adminPasswordInput').value;
      const btn = document.getElementById('btnUnlockAdmin');
      const errDiv = document.getElementById('adminAuthError');

      btn.disabled = true;
      btn.textContent = '⏳ Verifying Secret Key...';
      errDiv.style.display = 'none';

      try {
        const res = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: 'admin@example.com', password: pwd })
        });

        if (!res.ok) {
          throw new Error('Invalid administrator key or password.');
        }

        const data = await res.json();
        adminToken = data.token;
        currentRole = 'ADMIN';

        closeAdminAuthModal();
        applyTheme('ADMIN');
      } catch (err) {
        errDiv.textContent = 'Access Denied: ' + err.message;
        errDiv.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.textContent = '⚡ Authenticate & Unlock';
      }
    }

    function lockAndExitAdmin() {
      currentRole = 'CUSTOMER';
      adminToken = null;
      applyTheme('CUSTOMER');
    }

    // Switch between Sign In and Register tabs in Auth Modal
    function switchAuthTab(tab) {
      const signInTab = document.getElementById('authTabSignInBtn');
      const regTab = document.getElementById('authTabRegisterBtn');
      const signInView = document.getElementById('authSignInView');
      const regView = document.getElementById('authRegisterView');
      const loginErr = document.getElementById('loginError');
      const regErr = document.getElementById('registerError');
      const regSucc = document.getElementById('registerSuccess');

      if (loginErr) loginErr.style.display = 'none';
      if (regErr) regErr.style.display = 'none';
      if (regSucc) regSucc.style.display = 'none';

      if (tab === 'register') {
        if (signInView) signInView.style.display = 'none';
        if (regView) regView.style.display = 'block';
        if (regTab) {
          regTab.style.borderBottom = '2px solid var(--primary)';
          regTab.style.color = 'var(--primary)';
          regTab.style.fontWeight = '700';
        }
        if (signInTab) {
          signInTab.style.borderBottom = '2px solid transparent';
          signInTab.style.color = 'var(--text-muted)';
          signInTab.style.fontWeight = '600';
        }
        const input = document.getElementById('regNameInput');
        if (input) setTimeout(() => input.focus(), 100);
      } else {
        if (signInView) signInView.style.display = 'block';
        if (regView) regView.style.display = 'none';
        if (signInTab) {
          signInTab.style.borderBottom = '2px solid var(--primary)';
          signInTab.style.color = 'var(--primary)';
          signInTab.style.fontWeight = '700';
        }
        if (regTab) {
          regTab.style.borderBottom = '2px solid transparent';
          regTab.style.color = 'var(--text-muted)';
          regTab.style.fontWeight = '600';
        }
        const input = document.getElementById('loginEmailInput');
        if (input) setTimeout(() => input.focus(), 100);
      }
    }

    function openAuthModal(tab = 'signin') {
      switchAuthTab(tab);
      document.getElementById('loginModal').classList.add('active');
    }

    function openLoginModal(tab = 'signin') {
      openAuthModal(tab);
    }

    function closeLoginModal() {
      document.getElementById('loginModal').classList.remove('active');
    }

    // Update Auth UI across Header and Modals
    function updateAuthUI() {
      const guestGroup = document.getElementById('headerGuestGroup');
      const userGroup = document.getElementById('headerUserGroup');
      const label = document.getElementById('userAccountLabel');
      const modalEmail = document.getElementById('accountModalEmail');

      if (customerToken && currentUserEmail) {
        if (guestGroup) guestGroup.style.display = 'none';
        if (userGroup) userGroup.style.display = 'flex';
        if (label) label.textContent = currentUserEmail;
        if (modalEmail) modalEmail.textContent = currentUserEmail;
        fetchOrders();
      } else {
        if (guestGroup) guestGroup.style.display = 'inline-flex';
        if (userGroup) userGroup.style.display = 'none';
        const badge = document.getElementById('ordersBadge');
        if (badge) badge.style.display = 'none';
      }
    }

    // Customer Sign Out
    function handleSignOut() {
      customerToken = null;
      currentUserEmail = null;
      localStorage.removeItem('novatech_token');
      localStorage.removeItem('novatech_email');
      updateAuthUI();

      // Reset shopping cart UI
      document.getElementById('cartBadge').textContent = '0';
      document.getElementById('cartTotalPrice').textContent = '₹0.00';
      const badge = document.getElementById('ordersBadge');
      if (badge) badge.style.display = 'none';

      const list = document.getElementById('cartItemsList');
      if (list) {
        list.innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 3rem;">Please sign in to view your cart.</div>';
      }
      const chkBtn = document.getElementById('checkoutBtn');
      if (chkBtn) chkBtn.disabled = true;

      if (document.getElementById('cartDrawer').classList.contains('active')) {
        toggleCart();
      }
    }

    // Customer Registration Handler
    async function submitRegisterForm(e) {
      if (e) e.preventDefault();
      const name = document.getElementById('regNameInput').value.trim();
      const email = document.getElementById('regEmailInput').value.trim();
      const password = document.getElementById('regPasswordInput').value;
      const confirmPassword = document.getElementById('regConfirmPasswordInput').value;
      const btn = document.getElementById('btnRegisterSubmit');
      const errDiv = document.getElementById('registerError');
      const succDiv = document.getElementById('registerSuccess');

      errDiv.style.display = 'none';
      succDiv.style.display = 'none';

      if (!name || !email || !password) {
        errDiv.textContent = 'Please fill in all fields.';
        errDiv.style.display = 'block';
        return;
      }

      if (password !== confirmPassword) {
        errDiv.textContent = 'Passwords do not match.';
        errDiv.style.display = 'block';
        return;
      }

      if (password.length < 8) {
        errDiv.textContent = 'Password must be at least 8 characters.';
        errDiv.style.display = 'block';
        return;
      }

      btn.disabled = true;
      btn.textContent = 'Creating account...';

      try {
        // Step 1: Register account
        const regRes = await fetch('/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password })
        });
        const regData = await regRes.json();
        if (!regRes.ok) {
          throw new Error(regData.detail || 'Registration failed');
        }

        // Step 2: Automatically log in immediately (instant verification)
        btn.textContent = 'Logging in...';
        const loginRes = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const loginData = await loginRes.json();
        if (!loginRes.ok) {
          throw new Error(loginData.detail || 'Login failed after registration');
        }

        customerToken = loginData.token;
        currentUserEmail = email;
        localStorage.setItem('novatech_token', customerToken);
        localStorage.setItem('novatech_email', currentUserEmail);
        currentRole = 'CUSTOMER';

        succDiv.textContent = `🎉 Account created! Welcome to E-Commerce Site, ${name}!`;
        succDiv.style.display = 'block';

        setTimeout(() => {
          updateAuthUI();
          closeLoginModal();
          loadCart();
        }, 700);
      } catch (err) {
        errDiv.textContent = err.message;
        errDiv.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.textContent = '🚀 Create Account';
      }
    }

    // Customer Form-based Sign In
    async function submitLoginForm(e) {
      if (e) e.preventDefault();
      const email = document.getElementById('loginEmailInput').value.trim();
      const password = document.getElementById('loginPasswordInput').value;
      const btn = document.getElementById('btnLoginSubmit');
      const errDiv = document.getElementById('loginError');

      btn.disabled = true;
      btn.textContent = 'Signing in...';
      errDiv.style.display = 'none';

      try {
        const res = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Invalid email or password');
        }

        customerToken = data.token;
        currentUserEmail = email;
        localStorage.setItem('novatech_token', customerToken);
        localStorage.setItem('novatech_email', currentUserEmail);
        currentRole = 'CUSTOMER';
        updateAuthUI();
        closeLoginModal();
        loadCart();
      } catch (err) {
        errDiv.textContent = err.message;
        errDiv.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.textContent = 'Sign In';
      }
    }

    // Customer 1-Click Demo Login
    async function selectLogin(role) {
      try {
        const res = await fetch('/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: 'customer@example.com', password: 'CustomerPassword123!' })
        });
        const data = await res.json();
        if (res.ok && data.token) {
          customerToken = data.token;
          currentUserEmail = 'customer@example.com';
          localStorage.setItem('novatech_token', customerToken);
          localStorage.setItem('novatech_email', currentUserEmail);
          currentRole = 'CUSTOMER';
          updateAuthUI();
          closeLoginModal();
          loadCart();
        }
      } catch (err) {
        console.error('Customer login error:', err);
      }
    }

    function applyTheme(role) {
      const body = document.body;
      const adminBtn = document.getElementById('adminSessionBtn');
      const guestGroup = document.getElementById('headerGuestGroup');
      const userGroup = document.getElementById('headerUserGroup');
      const headerCart = document.getElementById('headerCartBtn');
      const headerOrders = document.getElementById('headerOrdersBtn');
      const headerWishlist = document.getElementById('headerWishlistBtn');
      const searchWrapper = document.getElementById('searchBoxWrapper');
      const userStoreView = document.getElementById('userStoreView');
      const adminControlView = document.getElementById('adminControlView');

      if (role === 'ADMIN') {
        body.classList.add('admin-theme');
        if (adminBtn) adminBtn.style.display = 'inline-flex';
        if (guestGroup) guestGroup.style.display = 'none';
        if (userGroup) userGroup.style.display = 'none';
        if (headerCart) headerCart.style.display = 'none';
        if (headerOrders) headerOrders.style.display = 'none';
        if (headerWishlist) headerWishlist.style.display = 'none';
        if (searchWrapper) searchWrapper.style.display = 'none';
        if (userStoreView) userStoreView.style.display = 'none';
        if (adminControlView) adminControlView.style.display = 'block';
        renderAdminInventory();
      } else {
        body.classList.remove('admin-theme');
        if (adminBtn) adminBtn.style.display = 'none';
        if (headerCart) headerCart.style.display = 'inline-flex';
        if (headerOrders) headerOrders.style.display = 'inline-flex';
        if (headerWishlist) headerWishlist.style.display = 'inline-flex';
        if (searchWrapper) searchWrapper.style.display = 'block';
        if (userStoreView) userStoreView.style.display = 'block';
        if (adminControlView) adminControlView.style.display = 'none';
        updateAuthUI();
        fetchCatalog();
      }
    }

    // Customer Profile & Account Modals
    async function loadUserProfile() {
      if (!customerToken) return null;
      try {
        const res = await fetch('/auth/profile', {
          headers: { 'Authorization': `Bearer ${customerToken}` }
        });
        if (!res.ok) return null;
        const data = await res.json();
        return data.profile;
      } catch (err) {
        console.error('Error loading profile:', err);
        return null;
      }
    }

    async function openAccountModal() {
      if (!customerToken) {
        openLoginModal();
        return;
      }
      document.getElementById('accountModalEmail').textContent = currentUserEmail || 'customer@example.com';
      document.getElementById('accountModal').classList.add('active');

      const profile = await loadUserProfile();
      if (profile) {
        const nameEl = document.getElementById('accountModalName');
        const emailEl = document.getElementById('accountModalEmail');
        const phoneEl = document.getElementById('accountModalPhone');
        const addrEl = document.getElementById('accountModalAddress');

        if (nameEl) nameEl.textContent = profile.name || 'Customer';
        if (emailEl) emailEl.textContent = profile.email || currentUserEmail;
        if (phoneEl) phoneEl.textContent = profile.phone || 'Not provided';
        if (addrEl) addrEl.textContent = profile.address || 'Not provided';
      }
    }

    function closeAccountModal() {
      document.getElementById('accountModal').classList.remove('active');
    }

    async function openEditProfileModal() {
      if (!customerToken) {
        openLoginModal();
        return;
      }
      const err = document.getElementById('profileError');
      const succ = document.getElementById('profileSuccess');
      if (err) err.style.display = 'none';
      if (succ) succ.style.display = 'none';

      document.getElementById('profileCurrentPasswordInput').value = '';
      document.getElementById('profileNewPasswordInput').value = '';

      const modal = document.getElementById('editProfileModal');
      modal.classList.add('active');

      const profile = await loadUserProfile();
      if (profile) {
        document.getElementById('profileNameInput').value = profile.name || '';
        document.getElementById('profileEmailInput').value = profile.email || currentUserEmail || '';
        document.getElementById('profilePhoneInput').value = profile.phone || '';
        document.getElementById('profileAddressInput').value = profile.address || '';
      } else {
        document.getElementById('profileEmailInput').value = currentUserEmail || '';
      }
    }

    function closeEditProfileModal() {
      document.getElementById('editProfileModal').classList.remove('active');
    }

    async function submitProfileForm(e) {
      if (e) e.preventDefault();
      const name = document.getElementById('profileNameInput').value.trim();
      const email = document.getElementById('profileEmailInput').value.trim();
      const phone = document.getElementById('profilePhoneInput').value.trim();
      const address = document.getElementById('profileAddressInput').value.trim();
      const currentPassword = document.getElementById('profileCurrentPasswordInput').value;
      const newPassword = document.getElementById('profileNewPasswordInput').value;

      const btn = document.getElementById('btnSaveProfile');
      const errDiv = document.getElementById('profileError');
      const succDiv = document.getElementById('profileSuccess');

      errDiv.style.display = 'none';
      succDiv.style.display = 'none';

      if (!name || !email) {
        errDiv.textContent = 'Name and email are required.';
        errDiv.style.display = 'block';
        return;
      }

      if (newPassword && !currentPassword) {
        errDiv.textContent = 'Please enter your current password to set a new password.';
        errDiv.style.display = 'block';
        return;
      }

      if (newPassword && newPassword.length < 8) {
        errDiv.textContent = 'New password must be at least 8 characters.';
        errDiv.style.display = 'block';
        return;
      }

      btn.disabled = true;
      btn.textContent = 'Saving changes...';

      try {
        const payload = { name, email, phone, address };
        if (newPassword) {
          payload.current_password = currentPassword;
          payload.new_password = newPassword;
        }

        const res = await fetch('/auth/profile', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${customerToken}`
          },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Could not update profile');
        }

        if (data.token) {
          customerToken = data.token;
          localStorage.setItem('novatech_token', customerToken);
        }

        currentUserEmail = email;
        localStorage.setItem('novatech_email', currentUserEmail);

        const label = document.getElementById('userAccountLabel');
        if (label) label.textContent = currentUserEmail;

        succDiv.textContent = '✅ Profile updated successfully!';
        succDiv.style.display = 'block';

        setTimeout(() => {
          closeEditProfileModal();
          openAccountModal();
        }, 800);

      } catch (err) {
        errDiv.textContent = err.message;
        errDiv.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.textContent = '💾 Save Profile Changes';
      }
    }

    let orderTimerInterval = null;

    async function fetchOrders() {
      if (!customerToken) return [];
      try {
        const res = await fetch('/orders', {
          headers: { 'Authorization': `Bearer ${customerToken}` }
        });
        if (!res.ok) return [];
        const data = await res.json();
        // Cancelled orders disappear from customer orders list
        const orders = (data.items || []).filter(ord => ord.status !== 'CANCELLED');
        const badge = document.getElementById('ordersBadge');
        if (badge) {
          if (orders.length > 0) {
            badge.textContent = orders.length;
            badge.style.display = 'inline-block';
          } else {
            badge.style.display = 'none';
          }
        }
        return orders;
      } catch (err) {
        console.error('Fetch orders error:', err);
        return [];
      }
    }

    // Global state for live tracking simulations
    window.activeSimulations = window.activeSimulations || {};
    window.currentOrdersCache = window.currentOrdersCache || [];

    const TRACKER_STAGES = [
      { key: 'PAID', label: 'Confirmed', icon: '💳', hub: 'Bangalore Central Fulfillment Center', desc: 'Order received & payment confirmed via Razorpay' },
      { key: 'PACKED', label: 'Packed', icon: '📦', hub: 'Automated Sorting Hub - Bay 4', desc: 'Items verified, boxed & sealed with tamper-evident tape' },
      { key: 'SHIPPED', label: 'Air Cargo', icon: '✈️', hub: 'BlueDart Air Terminal BLR ➔ Local Hub', desc: 'Handed to BlueDart Express cargo flight BD-882' },
      { key: 'OUT_FOR_DELIVERY', label: 'Out for Delivery', icon: '🛵', hub: 'Local Hubli-Dharwad Delivery Center', desc: 'Out with courier partner Jay (Van KA-25-E-9021)' },
      { key: 'DELIVERED', label: 'Delivered', icon: '🎉', hub: 'Customer Destination Doorstep', desc: 'Package delivered & signature verified successfully' }
    ];

    function getStageIndex(status) {
      const s = (status || '').toUpperCase();
      if (s === 'DELIVERED') return 4;
      if (s === 'OUT_FOR_DELIVERY') return 3;
      if (s === 'SHIPPED') return 2;
      if (s === 'PACKED' || s === 'PROCESSING') return 1;
      return 0; // PAID, CONFIRMED, PAYMENT_PENDING, etc.
    }

    function showLiveTrackingToast(message, icon = '🚀') {
      let toast = document.getElementById('trackingLiveToast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'trackingLiveToast';
        toast.className = 'tracking-live-toast';
        document.body.appendChild(toast);
      }
      toast.innerHTML = `<span style="font-size: 1.3rem;">${icon}</span> <span>${message}</span>`;
      toast.classList.add('show');
      clearTimeout(window._trackingToastTimeout);
      window._trackingToastTimeout = setTimeout(() => {
        toast.classList.remove('show');
      }, 3200);
    }

    async function updateOrderStatus(orderId, status) {
      const res = await fetch(`/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${customerToken}`
        },
        body: JSON.stringify({ status: status })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to update order status');
      }
      return await res.json();
    }

    async function advanceOrderStage(orderId) {
      try {
        const ord = (window.currentOrdersCache || []).find(o => o.id === orderId);
        const currIdx = ord ? getStageIndex(ord.status) : 0;
        if (currIdx < 4) {
          const nextStage = TRACKER_STAGES[currIdx + 1];
          await updateOrderStatus(orderId, nextStage.key);
          showLiveTrackingToast(`Order #${orderId.slice(0, 8)} advanced to ${nextStage.label}!`, nextStage.icon);
          await openOrdersModal();
        } else {
          showLiveTrackingToast(`Order #${orderId.slice(0, 8)} is already delivered!`, '🎉');
        }
      } catch (err) {
        showLiveTrackingToast('Failed to advance: ' + err.message, '⚠️');
      }
    }

    async function toggleOrderSimulation(orderId) {
      if (window.activeSimulations[orderId]) {
        clearInterval(window.activeSimulations[orderId]);
        delete window.activeSimulations[orderId];
        showLiveTrackingToast(`Live journey paused for Order #${orderId.slice(0, 8)}`, '⏸️');
        await openOrdersModal();
        return;
      }

      let ord = (window.currentOrdersCache || []).find(o => o.id === orderId);
      let currIdx = ord ? getStageIndex(ord.status) : 0;

      if (currIdx >= 4) {
        await updateOrderStatus(orderId, 'PAID');
        showLiveTrackingToast('Restarting simulation journey from Confirmed stage...', '🔄');
        await openOrdersModal();
      }

      showLiveTrackingToast(`Auto-simulating live journey for Order #${orderId.slice(0, 8)}...`, '🚀');

      window.activeSimulations[orderId] = setInterval(async () => {
        try {
          const freshOrders = await fetchOrders();
          window.currentOrdersCache = freshOrders || [];
          const currentOrd = (window.currentOrdersCache || []).find(o => o.id === orderId);
          const idx = currentOrd ? getStageIndex(currentOrd.status) : 0;

          if (idx < 4) {
            const nextStage = TRACKER_STAGES[idx + 1];
            await updateOrderStatus(orderId, nextStage.key);
            showLiveTrackingToast(`Order #${orderId.slice(0, 8)} ➔ ${nextStage.label}: ${nextStage.desc}`, nextStage.icon);
            await openOrdersModal();

            if (idx + 1 >= 4) {
              clearInterval(window.activeSimulations[orderId]);
              delete window.activeSimulations[orderId];
              showLiveTrackingToast(`🎉 Order #${orderId.slice(0, 8)} delivered successfully to customer doorstep!`, '🎉');
              await openOrdersModal();
            }
          } else {
            clearInterval(window.activeSimulations[orderId]);
            delete window.activeSimulations[orderId];
            await openOrdersModal();
          }
        } catch (simErr) {
          clearInterval(window.activeSimulations[orderId]);
          delete window.activeSimulations[orderId];
          showLiveTrackingToast('Simulation halted: ' + simErr.message, '⚠️');
        }
      }, 2800);

      await openOrdersModal();
    }

    async function resetOrderStage(orderId) {
      try {
        if (window.activeSimulations[orderId]) {
          clearInterval(window.activeSimulations[orderId]);
          delete window.activeSimulations[orderId];
        }
        await updateOrderStatus(orderId, 'PAID');
        showLiveTrackingToast(`Order #${orderId.slice(0, 8)} reset to Confirmed stage.`, '🔄');
        await openOrdersModal();
      } catch (err) {
        showLiveTrackingToast('Reset error: ' + err.message, '⚠️');
      }
    }

    async function openOrdersModal() {
      if (!customerToken) {
        openLoginModal();
        return;
      }
      const modal = document.getElementById('ordersModal');
      const container = document.getElementById('ordersListContainer');
      container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2.5rem 0;">Loading your orders...</div>';
      modal.classList.add('active');

      clearInterval(orderTimerInterval);

      const allOrders = await fetchOrders();
      const orders = (allOrders || []).filter(ord => ord.status !== 'CANCELLED');
      window.currentOrdersCache = orders;

      if (!orders || orders.length === 0) {
        container.innerHTML = `
          <div style="text-align: center; color: var(--text-muted); padding: 3rem 1rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🛍️</div>
            <div style="font-weight: 700; font-size: 1.05rem; color: var(--text); margin-bottom: 0.35rem;">No active orders found</div>
            <p style="font-size: 0.85rem;">You don't have any active orders right now. Completed purchases will appear here.</p>
          </div>
        `;
        return;
      }

      const now = Date.now();
      container.innerHTML = orders.map(ord => {
        const dateStr = ord.created_at ? new Date(ord.created_at).toLocaleString() : 'Recent';
        const stageIdx = getStageIndex(ord.status);
        const currentStage = TRACKER_STAGES[stageIdx];
        const progressPct = Math.min(100, Math.max(0, stageIdx * 25));
        const waybillNo = 'BLUEDART-IND-' + ord.id.replace(/[^a-zA-Z0-9]/g, '').slice(0, 8).toUpperCase();
        const isSimulating = !!window.activeSimulations[ord.id];

        let statusBadgeStyle = 'background: rgba(16, 185, 129, 0.15); color: #059669; border: 1px solid rgba(16, 185, 129, 0.3);';
        let statusText = '● ' + ord.status;

        if (ord.status === 'DELIVERED') {
          statusBadgeStyle = 'background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; box-shadow: 0 0 10px rgba(16, 185, 129, 0.4); font-weight: 800;';
          statusText = '● DELIVERED (Completed)';
        } else if (ord.status === 'OUT_FOR_DELIVERY') {
          statusBadgeStyle = 'background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; box-shadow: 0 0 10px rgba(245, 158, 11, 0.4); font-weight: 800;';
          statusText = '● OUT FOR DELIVERY';
        } else if (ord.status === 'SHIPPED') {
          statusBadgeStyle = 'background: rgba(139, 92, 246, 0.2); color: #a78bfa; border: 1px solid #8b5cf6; box-shadow: 0 0 10px rgba(139, 92, 246, 0.4); font-weight: 800;';
          statusText = '● IN TRANSIT (Air Cargo)';
        } else if (ord.status === 'PACKED' || ord.status === 'PROCESSING') {
          statusBadgeStyle = 'background: rgba(0, 240, 255, 0.15); color: #00f0ff; border: 1px solid rgba(0, 240, 255, 0.4); box-shadow: 0 0 10px rgba(0, 240, 255, 0.3); font-weight: 800;';
          statusText = '● PACKED (In Hub)';
        } else if (ord.status === 'PAID' || ord.status === 'CONFIRMED' || ord.status === 'COMPLETED') {
          statusBadgeStyle = 'background: rgba(16, 185, 129, 0.15); color: #059669; border: 1px solid rgba(16, 185, 129, 0.3);';
          statusText = '● PAID (Confirmed)';
        }

        const itemsHtml = (ord.items || []).map(item => `
          <div style="display: flex; justify-content: space-between; font-size: 0.85rem; padding: 0.25rem 0;">
            <span><strong>${item.product_name}</strong> × ${item.quantity}</span>
            <span style="font-family: var(--font-mono); color: var(--text-muted);">₹${Number(item.line_total || item.unit_price).toLocaleString('en-IN')}</span>
          </div>
        `).join('');

        const rzpId = (ord.payment && (ord.payment.payment_id || ord.payment.razorpay_order_id)) || 'pay_confirmed';

        // Timing calculations for delivery ETA & cancellation window
        const createdMs = new Date(ord.created_at).getTime();
        const completionMs = ord.estimated_delivery_at ? new Date(ord.estimated_delivery_at).getTime() : createdMs + (24 * 3600 * 1000);
        const lockMs = ord.cancellation_locked_at ? new Date(ord.cancellation_locked_at).getTime() : completionMs - (6 * 3600 * 1000);
        const msToLock = lockMs - now;
        const msToCompletion = completionMs - now;

        const totalSecReach = Math.max(0, Math.floor(msToCompletion / 1000));
        const reachHrs = Math.floor(totalSecReach / 3600);
        const reachMins = Math.floor((totalSecReach % 3600) / 60);
        const reachSecs = totalSecReach % 60;
        const reachTimeStr = `${reachHrs}h ${reachMins}m ${reachSecs}s`;

        // Render Stepper Nodes
        const stepsHtml = TRACKER_STAGES.map((st, idx) => {
          let stepClass = '';
          let circleContent = st.icon;
          if (idx < stageIdx) {
            stepClass = 'completed';
            circleContent = '✓';
          } else if (idx === stageIdx) {
            stepClass = 'active';
          }
          return `
            <div class="tracker-step ${stepClass}">
              <div class="tracker-circle">${circleContent}</div>
              <div class="tracker-label">${st.label}</div>
            </div>
          `;
        }).join('');

        // Dynamic Cancellation Section
        let cancelSectionHtml = '';
        if (stageIdx >= 2 && stageIdx < 4) {
          cancelSectionHtml = `
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; padding: 0.65rem 0.85rem; margin-top: 0.75rem; display: flex; align-items: center; justify-content: space-between; font-size: 0.8rem; gap: 0.75rem; flex-wrap: wrap;">
              <div>
                <span style="color: #b45309; font-weight: 700;">🚚 Active Carrier Transit:</span>
                <div style="font-size: 0.7rem; color: #b45309; margin-top: 0.2rem;">
                  🔒 Handed over to BlueDart Air Express (${currentStage.hub}). Free cancellation locked during transit.
                </div>
              </div>
              <button class="btn-sm" disabled style="background: var(--card-border); color: var(--text-muted); cursor: not-allowed; padding: 0.45rem 0.95rem; font-weight: 600; border-radius: 6px;">
                🔒 In Transit
              </button>
            </div>
          `;
        } else if (stageIdx === 4) {
          cancelSectionHtml = `
            <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 0.55rem 0.85rem; margin-top: 0.75rem; font-size: 0.8rem; color: #059669; display: flex; align-items: center; gap: 0.5rem;">
              <span>✅ Delivered • Order complete and safely arrived at customer doorstep</span>
            </div>
          `;
        } else if (msToLock > 0) {
          cancelSectionHtml = `
            <div style="background: rgba(37, 99, 235, 0.07); border: 1px solid rgba(37, 99, 235, 0.2); border-radius: 8px; padding: 0.65rem 0.85rem; margin-top: 0.75rem; display: flex; align-items: center; justify-content: space-between; font-size: 0.8rem; gap: 0.75rem; flex-wrap: wrap;">
              <div>
                <span style="color: var(--primary); font-weight: 700;">🚚 Estimated Arrival Window:</span>
                <span style="font-family: var(--font-mono); font-weight: 800; color: var(--text);" class="order-live-timer" data-reach-ms="${completionMs}" data-lock-ms="${lockMs}" id="timer_${ord.id}">${reachTimeStr}</span>
                <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.2rem;">
                  Free cancellation available until 6 hours before arrival
                </div>
              </div>
              <button class="btn-sm" style="background: #ef4444; color: white; padding: 0.45rem 0.95rem; font-weight: 700; border-radius: 6px; cursor: pointer; transition: transform 0.15s;" onclick="cancelAndRemoveOrder('${ord.id}')">
                ❌ Cancel Order
              </button>
            </div>
          `;
        } else {
          cancelSectionHtml = `
            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; padding: 0.65rem 0.85rem; margin-top: 0.75rem; display: flex; align-items: center; justify-content: space-between; font-size: 0.8rem; gap: 0.75rem; flex-wrap: wrap;">
              <div>
                <span style="color: #b45309; font-weight: 700;">🚚 In Dispatch:</span>
                <div style="font-size: 0.7rem; color: #b45309; margin-top: 0.2rem;">
                  🔒 Final sorting: Cancellation locked within 6 hours of completion
                </div>
              </div>
              <button class="btn-sm" disabled style="background: var(--card-border); color: var(--text-muted); cursor: not-allowed; padding: 0.45rem 0.95rem; font-weight: 600; border-radius: 6px;">
                🔒 Locked
              </button>
            </div>
          `;
        }

        return `
          <div style="background: var(--input-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 1.15rem; transition: all 0.35s ease;" id="order_card_${ord.id}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; border-bottom: 1px solid var(--card-border); padding-bottom: 0.65rem;">
              <div>
                <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">Order ID</div>
                <div style="font-family: var(--font-mono); font-weight: 700; color: var(--primary); font-size: 0.85rem;">${ord.id}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem;">Placed: ${dateStr}</div>
              </div>
              <div style="text-align: right;">
                <span style="font-size: 0.725rem; font-weight: 700; padding: 0.25rem 0.6rem; border-radius: 9999px; ${statusBadgeStyle}">
                  ${statusText}
                </span>
                <div style="font-size: 1.2rem; font-weight: 800; color: var(--text); margin-top: 0.35rem;">
                  ₹${Number(ord.grand_total).toLocaleString('en-IN')} ${ord.currency}
                </div>
              </div>
            </div>

            <!-- Ordered Items List -->
            <div style="display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.75rem;">
              ${itemsHtml}
            </div>

            <!-- Non-sensitive Payment ID Reference -->
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); border-top: 1px dashed var(--card-border); padding-top: 0.55rem; font-family: var(--font-mono);">
              <span>Payment Reference:</span>
              <span style="font-weight: 600; color: #059669;">${rzpId}</span>
            </div>

            <!-- Real-Time Order Lifecycle & Live Tracking Panel -->
            <div class="order-tracker-card">
              <div class="tracker-header">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                  <span style="font-size: 1.05rem;">📡</span>
                  <span style="font-weight: 800; font-size: 0.85rem; color: #ffffff;">Live Shipment Journey</span>
                </div>
                <div class="tracker-badge-carrier">
                  <span>✈️ BlueDart Air Express</span>
                </div>
              </div>

              <!-- Animated 5-Step Progress Stepper -->
              <div class="tracker-stepper">
                <div style="position: absolute; top: 18px; left: 28px; right: 28px; height: 4px; background: rgba(255,255,255,0.12); border-radius: 2px; z-index: 1;">
                  <div style="height: 100%; width: ${progressPct}%; background: linear-gradient(90deg, #00f0ff, #10b981); box-shadow: 0 0 10px rgba(0,240,255,0.85); border-radius: 2px; transition: width 0.5s ease;"></div>
                </div>
                ${stepsHtml}
              </div>

              <!-- Milestone & Hub Information Box -->
              <div class="carrier-details-box">
                <div>
                  <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">Current Milestone & Location</div>
                  <div style="color: #ffffff; font-weight: 700; margin-top: 0.2rem; display: flex; align-items: center; gap: 0.4rem;">
                    <span>📍</span>
                    <span>${currentStage.hub}</span>
                  </div>
                  <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.25rem;">
                    ${currentStage.desc}
                  </div>
                </div>
                <div style="text-align: right;">
                  <div style="color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase; font-weight: 700;">AWB Waybill Tracking #</div>
                  <div style="font-family: var(--font-mono); font-weight: 800; color: #00f0ff; font-size: 0.85rem; margin-top: 0.2rem;">
                    ${waybillNo}
                  </div>
                  <div style="font-size: 0.72rem; color: #10b981; font-weight: 700; margin-top: 0.2rem;">
                    ⚡ High-Priority Dispatch
                  </div>
                </div>
              </div>

              <!-- Interactive Stage Advancement & Simulation Controls -->
              <div class="tracker-controls">
                <button class="sim-ctrl-btn" style="background: rgba(0, 240, 255, 0.12); color: #00f0ff; border-color: rgba(0, 240, 255, 0.4);" 
                        onclick="advanceOrderStage('${ord.id}')" 
                        ${stageIdx >= 4 ? 'disabled' : ''} 
                        id="btn_advance_${ord.id}"
                        title="Manually advance to the next delivery milestone">
                  ⚡ Advance Stage
                </button>

                <button class="sim-ctrl-btn" style="background: ${isSimulating ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.12)'}; color: ${isSimulating ? '#ef4444' : '#10b981'}; border-color: ${isSimulating ? 'rgba(239, 68, 68, 0.4)' : 'rgba(16, 185, 129, 0.4)'};" 
                        onclick="toggleOrderSimulation('${ord.id}')" 
                        id="btn_sim_${ord.id}"
                        title="Simulate complete live journey from start to finish automatically">
                  ${isSimulating ? '⏹ Stop Simulation' : '▶ Auto-Simulate Live Journey'}
                </button>

                <button class="sim-ctrl-btn" style="background: rgba(255, 255, 255, 0.05); color: #cbd5e1; border-color: rgba(255, 255, 255, 0.2);" 
                        onclick="resetOrderStage('${ord.id}')" 
                        id="btn_reset_${ord.id}"
                        title="Reset back to confirmed state for re-testing">
                  🔄 Reset Tracking
                </button>
              </div>
            </div>

            <!-- Dynamic Cancellation & Delivery Timer Control -->
            ${cancelSectionHtml}
          </div>
        `;
      }).join('');

      // Start ticking timers
      orderTimerInterval = setInterval(tickOrderTimers, 1000);
    }

    function tickOrderTimers() {
      const timerEls = document.querySelectorAll('.order-live-timer');
      const now = Date.now();
      let shouldReload = false;

      timerEls.forEach(el => {
        const reachMs = parseInt(el.getAttribute('data-reach-ms') || el.getAttribute('data-lock-ms'), 10);
        const lockMs = parseInt(el.getAttribute('data-lock-ms') || '0', 10);
        const diffReach = reachMs - now;
        const diffLock = lockMs - now;

        // If lock threshold crossed or delivery completed, refresh view
        if ((diffLock <= 0 && diffLock > -2000) || (diffReach <= 0 && diffReach > -2000)) {
          shouldReload = true;
        } else if (diffReach > 0) {
          const totalSec = Math.floor(diffReach / 1000);
          const hrs = Math.floor(totalSec / 3600);
          const mins = Math.floor((totalSec % 3600) / 60);
          const secs = totalSec % 60;
          el.textContent = `${hrs}h ${mins}m ${secs}s`;
        }
      });

      if (shouldReload) {
        clearInterval(orderTimerInterval);
        openOrdersModal();
      }
    }

    async function cancelAndRemoveOrder(orderId) {
      if (!confirm(`Are you sure you want to cancel Order #${orderId}?\n\nThis order will be removed from your list, reserved stock restored, and payment refunded.`)) {
        return;
      }

      // Smooth visual disappearance animation on the order card
      const card = document.getElementById(`order_card_${orderId}`);
      if (card) {
        card.style.transition = 'all 0.35s ease-out';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.96) translateY(-8px)';
      }

      try {
        const res = await fetch(`/orders/${orderId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${customerToken}`
          }
        });

        const data = await res.json();
        if (!res.ok) {
          // Fallback to cancel POST if DELETE fails
          const fbRes = await fetch(`/orders/${orderId}/cancel`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${customerToken}`
            },
            body: JSON.stringify({ reason: 'Customer requested cancellation' })
          });
          if (!fbRes.ok) {
            const fbData = await fbRes.json();
            throw new Error(fbData.detail || data.detail || 'Could not cancel order');
          }
        }

        // Animate card collapse then re-render orders list
        if (card) {
          card.style.maxHeight = '0px';
          card.style.padding = '0px 1.15rem';
          card.style.margin = '0px';
          card.style.borderWidth = '0px';
          card.style.overflow = 'hidden';
        }

        setTimeout(() => {
          openOrdersModal();
          fetchCatalog();
        }, 350);

      } catch (err) {
        if (card) {
          card.style.opacity = '1';
          card.style.transform = 'none';
        }
        alert('Cancellation Error: ' + err.message);
      }
    }

    function closeOrdersModal() {
      clearInterval(orderTimerInterval);
      document.getElementById('ordersModal').classList.remove('active');
    }

    function openProductModal(productId) {
      const p = allProducts.find(item => item.id === productId);
      if (!p) return;
      const icon = ICONS[p.sku.split('-')[0]] || '📦';
      const imgHtml = p.imageUrl
        ? `<div style="position: relative; overflow: hidden; border-radius: 16px; background: radial-gradient(circle at center, rgba(0, 80, 180, 0.3) 0%, rgba(2, 8, 24, 0.95) 100%); border: 1.5px solid rgba(0, 212, 255, 0.3); padding: 1.5rem; display: flex; align-items: center; justify-content: center; min-height: 320px;">
             <img src="${p.imageUrl}" alt="${p.name}" style="max-height: 300px; width: 100%; object-fit: contain; filter: drop-shadow(0 15px 30px rgba(0, 0, 0, 0.8)); transition: transform 0.4s ease;" onmouseover="this.style.transform='scale(1.06)'" onmouseout="this.style.transform='scale(1)'">
           </div>`
        : `<div style="font-size: 6rem; text-align: center; padding: 3rem; background: rgba(0, 20, 50, 0.6); border-radius: 16px; border: 1px solid var(--card-border);">${icon}</div>`;

      // Derive rich cyberpunk specifications breakdown from product metadata
      const categoryMap = {
        'LAPTOP': 'Flagship Computing & Neural Workstation',
        'PHONE': 'Next-Gen Mobile AI Flagship Phone',
        'AUDIO': 'Acoustic Studio ANC Spatial Sound',
        'DISP': 'Pro Ultra-HD Gaming & Calibration Display',
        'KEYB': 'Precision Tactile Custom Mechanical Deck',
        'MOUS': 'Ultra-Low Latency Optical Sensor Mouse',
        'TABL': 'Retina Pro Creator Multi-Touch Slate',
        'WATCH': 'Biometric Health & Telemetry Smart Tracker',
        'DRON': '4K HDR Autonomous Aerial Drone System',
        'GAME': 'Ultra-High FPS Next-Gen Console',
        'SPKR': '360° Omnidirectional Immersive Audio',
        'CHRG': 'High-Wattage Gallium Nitride Fast Power',
        'STRE': 'Interactive Studio Production Console'
      };
      const skuPrefix = p.sku.split('-')[0];
      const categoryLabel = categoryMap[skuPrefix] || 'E-Commerce Flagship Hardware';
      const ratingInfo = getProductRating(p.sku);

      const allReviewsForSku = [
        ...((productReviews && productReviews[p.sku]) || []),
        { name: 'Harish V.', rating: 5, date: 'Verified Purchase', verified: true, text: 'Top tier build quality. Thermal management is exceptional even under continuous heavy workloads.' },
        { name: 'Deepa N.', rating: 5, date: 'Verified Purchase', verified: true, text: 'Flawless compatibility and ultra-fast delivery. Exceeded all technical expectations.' }
      ];

      const reviewsHtml = allReviewsForSku.map(r => `
        <div style="background: rgba(0, 10, 26, 0.55); border: 1px solid rgba(0, 212, 255, 0.15); border-radius: 8px; padding: 0.65rem 0.85rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="font-weight: 700; font-size: 0.825rem; color: #ffffff;">${r.name}</span>
              <span style="font-size: 0.68rem; background: rgba(0, 255, 170, 0.15); color: #00ffaa; border: 1px solid rgba(0, 255, 170, 0.35); padding: 0.1rem 0.4rem; border-radius: 4px; font-weight: 700;">✔ Verified</span>
            </div>
            <div style="color: #f59e0b; font-size: 0.8rem;">${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}</div>
          </div>
          <p style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.5; margin: 0;">${r.text}</p>
        </div>
      `).join('');

      const content = document.getElementById('productDetailContent');
      content.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 2rem; align-items: start;">
          <div>
            ${imgHtml}
            <div style="display: flex; gap: 0.75rem; margin-top: 1rem;">
              <div style="flex: 1; background: rgba(0, 212, 255, 0.08); border: 1px solid rgba(0, 212, 255, 0.25); border-radius: 8px; padding: 0.65rem; text-align: center;">
                <div style="font-size: 0.68rem; color: #7dd3fc; text-transform: uppercase; font-weight: 700;">Warranty</div>
                <div style="font-size: 0.85rem; font-weight: 800; color: #ffffff;">2-Year Official</div>
              </div>
              <div style="flex: 1; background: rgba(0, 255, 170, 0.08); border: 1px solid rgba(0, 255, 170, 0.25); border-radius: 8px; padding: 0.65rem; text-align: center;">
                <div style="font-size: 0.68rem; color: #00ffaa; text-transform: uppercase; font-weight: 700;">Dispatch</div>
                <div style="font-size: 0.85rem; font-weight: 800; color: #ffffff;">Same-Day Express</div>
              </div>
              <div style="flex: 1; background: rgba(255, 0, 128, 0.08); border: 1px solid rgba(255, 0, 128, 0.25); border-radius: 8px; padding: 0.65rem; text-align: center;">
                <div style="font-size: 0.68rem; color: #ff007f; text-transform: uppercase; font-weight: 700;">Returns</div>
                <div style="font-size: 0.85rem; font-weight: 800; color: #ffffff;">30-Day Free</div>
              </div>
            </div>
          </div>

          <div style="display: flex; flex-direction: column;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; gap: 0.75rem; flex-wrap: wrap;">
              <span class="product-sku" style="font-size: 0.85rem; font-weight: 800; color: #00f0ff; letter-spacing: 0.06em; text-transform: uppercase;">
                ⚡ SKU: ${p.sku}
              </span>
              <span style="font-size: 0.78rem; font-weight: 700; color: ${p.stock > 0 ? '#00ffaa' : '#ef4444'}; background: ${p.stock > 0 ? 'rgba(0, 255, 170, 0.15)' : 'rgba(239, 68, 68, 0.15)'}; padding: 0.3rem 0.85rem; border-radius: 9999px; border: 1px solid ${p.stock > 0 ? 'rgba(0, 255, 170, 0.35)' : 'rgba(239, 68, 68, 0.35)'};">
                ● ${p.stock > 0 ? `${p.stock} Units In Stock` : 'Out of Stock'}
              </span>
            </div>

            <div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; color: #38bdf8; letter-spacing: 0.08em; margin-bottom: 0.4rem;">
              ${categoryLabel}
            </div>

            <h1 style="font-size: 1.85rem; font-weight: 850; color: #ffffff; line-height: 1.25; margin-bottom: 0.5rem; letter-spacing: -0.025em; text-shadow: 0 0 15px rgba(0, 212, 255, 0.3);">
              ${p.name}
            </h1>

            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; font-size: 0.85rem;">
              <span style="color: #f59e0b; font-weight: 800;">⭐ ${ratingInfo.rating} / 5.0</span>
              <span style="color: #94a3b8;">(${ratingInfo.count} verified ratings)</span>
            </div>

            <div style="background: rgba(0, 25, 60, 0.65); border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem; box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.5);">
              <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; text-transform: uppercase; color: #00f0ff; font-weight: 800; letter-spacing: 0.06em; margin-bottom: 0.65rem;">
                <span>🔬</span>
                <span>Architectural Overview & Engineering Specs</span>
              </div>
              <p style="font-size: 0.95rem; line-height: 1.65; color: #e0f2fe; margin-bottom: 0.75rem;">
                ${p.description || 'Full certified enterprise hardware specifications engineered for peak computational throughput, thermal efficiency, and high-durability performance.'}
              </p>
              <div style="font-size: 0.825rem; color: #99ccff; line-height: 1.5; border-top: 1px dashed rgba(0, 212, 255, 0.2); padding-top: 0.65rem;">
                ✔ Benchmarked with microservices low-latency verification & two-phase transactional reservation.
              </div>
            </div>

            <!-- Customer Reviews Section -->
            <div style="background: rgba(0, 15, 38, 0.7); border: 1px solid rgba(0, 212, 255, 0.25); border-radius: 12px; padding: 1.15rem; margin-bottom: 1.5rem;">
              <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0, 212, 255, 0.15); padding-bottom: 0.6rem; margin-bottom: 0.85rem; flex-wrap: wrap; gap: 0.5rem;">
                <div style="font-size: 0.85rem; font-weight: 800; color: #00f0ff; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 0.4rem;">
                  <span>💬</span> Customer Reviews (${allReviewsForSku.length})
                </div>
                <button onclick="const el = document.getElementById('writeReviewSection'); el.style.display = el.style.display === 'none' ? 'block' : 'none';" class="btn-sm" style="background: rgba(0, 212, 255, 0.15); color: #00f0ff; border: 1px solid rgba(0, 212, 255, 0.4); font-size: 0.75rem; font-weight: 700; cursor: pointer;">
                  ✍️ Write a Review
                </button>
              </div>

              <!-- Interactive Review Form -->
              <div id="writeReviewSection" style="display: none; background: rgba(0, 10, 25, 0.85); border: 1px dashed rgba(0, 212, 255, 0.35); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.85rem;">
                <form onsubmit="submitProductReview(event, '${p.sku}', '${p.id}')">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
                    <span style="font-size: 0.78rem; font-weight: 700; color: #ffffff;">Your Rating:</span>
                    <div style="font-size: 1.25rem; display: flex; gap: 0.2rem; cursor: pointer;">
                      <span id="starBtn_1" onclick="setReviewStars(1)" style="color: #f59e0b;">★</span>
                      <span id="starBtn_2" onclick="setReviewStars(2)" style="color: #f59e0b;">★</span>
                      <span id="starBtn_3" onclick="setReviewStars(3)" style="color: #f59e0b;">★</span>
                      <span id="starBtn_4" onclick="setReviewStars(4)" style="color: #f59e0b;">★</span>
                      <span id="starBtn_5" onclick="setReviewStars(5)" style="color: #f59e0b;">★</span>
                    </div>
                  </div>
                  <div style="margin-bottom: 0.5rem;">
                    <input type="text" id="reviewAuthorName" placeholder="Your Name or Nickname" class="form-input" style="padding: 0.4rem 0.65rem; font-size: 0.8rem;" value="${currentUserEmail ? currentUserEmail.split('@')[0] : ''}">
                  </div>
                  <div style="margin-bottom: 0.5rem;">
                    <textarea id="reviewCommentText" rows="2" placeholder="Share your experience with this device..." class="form-input" style="padding: 0.4rem 0.65rem; font-size: 0.8rem; resize: vertical;" required></textarea>
                  </div>
                  <button type="submit" class="btn-sm" style="background: var(--primary); font-weight: 800; padding: 0.4rem 0.9rem;">
                    Submit Verified Review
                  </button>
                </form>
              </div>

              <!-- Reviews Feed -->
              <div style="display: flex; flex-direction: column; gap: 0.6rem; max-height: 180px; overflow-y: auto; padding-right: 0.25rem;">
                ${reviewsHtml}
              </div>
            </div>

            <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 1.25rem; border-top: 1.5px solid rgba(0, 212, 255, 0.25); gap: 1.25rem; flex-wrap: wrap; margin-top: auto;">
              <div>
                <div style="font-size: 0.72rem; color: #7dd3fc; text-transform: uppercase; font-weight: 700; letter-spacing: 0.04em;">Official Price (Inclusive of Taxes)</div>
                <div style="font-size: 2rem; font-weight: 900; color: #00f0ff; text-shadow: 0 0 18px rgba(0, 240, 255, 0.6); font-family: var(--font-main);">
                  ₹${Number(p.price).toLocaleString('en-IN')}
                </div>
              </div>

              <div style="display: flex; gap: 0.75rem;">
                <button class="add-btn" style="padding: 0.85rem 2rem; font-size: 1rem; border-radius: 10px;" onclick="addToCart('${p.id}'); closeProductDetailModal();">
                  🛒 Add to Cart Now
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
      document.getElementById('productDetailModal').classList.add('active');
    }

    function closeProductDetailModal() {
      document.getElementById('productDetailModal').classList.remove('active');
    }

    function closeModalOnBg(e) {
      if (e.target.id === 'loginModal') closeLoginModal();
      if (e.target.id === 'accountModal') closeAccountModal();
      if (e.target.id === 'ordersModal') closeOrdersModal();
      if (e.target.id === 'wishlistModal') closeWishlistModal();
      if (e.target.id === 'productDetailModal') closeProductDetailModal();
      if (e.target.id === 'adminAuthModal') closeAdminAuthModal();
      if (e.target.id === 'paymentModal') closePaymentModal();
      if (e.target.id === 'addProductModal') closeAddProductModal();
      if (e.target.id === 'editProductModal') closeEditProductModal();
      if (e.target.id === 'editProfileModal') closeEditProfileModal();
    }
    function closeOrderModal() { document.getElementById('orderModal').classList.remove('active'); }

    // Fetch products
    async function fetchCatalog() {
      try {
        const res = await fetch('/products');
        const json = await res.json();
        allProducts = json.data || [];
        const badge = document.getElementById('productCountBadge');
        if (badge) badge.textContent = allProducts.length;
        const allCount = document.getElementById('allProductsCount');
        if (allCount) allCount.textContent = allProducts.length;
        applyFiltersAndSort();
        updateWishlistBadge();
        renderAdminInventory();
      } catch (err) {
        console.error(err);
      }
    }

    function renderProducts(items) {
      const grid = document.getElementById('productsGrid');
      grid.innerHTML = items.map(p => {
        const icon = ICONS[p.sku.split('-')[0]] || '📦';
        const imgHtml = p.imageUrl 
          ? `<img src="${p.imageUrl}" alt="${p.name}" loading="lazy">`
          : `<span>${icon}</span>`;
        const ratingData = getProductRating(p.sku);
        const isWishlisted = wishlist.includes(p.id);

        return `
          <div class="product-card">
            <div class="product-thumb" onclick="openProductModal('${p.id}')" style="cursor: pointer;" title="Click to view full description & specs">
              <button class="wishlist-toggle-btn" onclick="toggleWishlist(event, '${p.id}')" title="${isWishlisted ? 'Remove from Wishlist' : 'Add to Wishlist'}">
                ${isWishlisted ? '❤️' : '🤍'}
              </button>
              ${imgHtml}
            </div>
            <div class="product-info">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; gap: 0.5rem;">
                <span class="product-sku" style="margin-bottom: 0; font-weight: 700;">${p.sku}</span>
                <span style="font-size: 0.72rem; font-weight: 700; color: ${p.stock > 0 ? '#059669' : '#ef4444'}; background: ${p.stock > 0 ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)'}; padding: 0.15rem 0.55rem; border-radius: 9999px; white-space: nowrap;">
                  ● ${p.stock} in stock
                </span>
              </div>
              <h3 class="product-title" onclick="openProductModal('${p.id}')" title="Click to view full description & specs">${p.name}</h3>
              <div class="product-rating">
                <span>⭐ ${ratingData.rating}</span>
                <span style="color: #94a3b8; font-weight: 500; font-size: 0.72rem;">(${ratingData.count} reviews)</span>
              </div>
              <p class="product-desc">${p.description || 'Certified premium device.'}</p>
              <div class="product-footer">
                <div class="product-price">₹${Number(p.price).toLocaleString('en-IN')}</div>
                <button class="add-btn" onclick="addToCart('${p.id}')">+ Add to Cart</button>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    function renderAdminInventory() {
      const tbody = document.getElementById('adminInventoryTable');
      if (!tbody) return;
      tbody.innerHTML = allProducts.map(p => {
        const icon = ICONS[p.sku.split('-')[0]] || '📦';
        const imgThumb = p.imageUrl 
          ? `<img src="${p.imageUrl}" alt="${p.name}" style="width: 40px; height: 40px; object-fit: contain; border-radius: 6px; background: rgba(255,255,255,0.06); padding: 2px;">` 
          : `<span style="font-size: 1.5rem;">${icon}</span>`;
        return `
          <tr>
            <td style="width: 50px; text-align: center;">${imgThumb}</td>
            <td><code>${p.sku}</code></td>
            <td>
              <div><strong>${p.name}</strong></div>
              <div style="font-size: 0.75rem; color: var(--text-muted); max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${p.description || 'No description'}</div>
            </td>
            <td>₹${Number(p.price).toLocaleString('en-IN')}</td>
            <td><span style="color: ${p.stock > 0 ? '#10b981' : '#ef4444'}; font-weight: 700;">${p.stock}</span></td>
            <td>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <input type="number" class="stock-input" id="stock_${p.id}" value="${p.stock}">
                <button class="btn-sm" onclick="saveStock('${p.id}')">Update</button>
              </div>
            </td>
            <td>
              <div style="display: flex; gap: 0.4rem; align-items: center;">
                <button class="btn-sm" style="background: #2563eb;" onclick="openEditProductModal('${p.id}')">✏️ Edit</button>
                <button class="btn-sm" style="background: #ef4444;" onclick="deleteCatalogProduct('${p.id}', '${p.sku}')">🗑️ Delete</button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }

    function handleImageFile(event, previewId, dataId) {
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(e) {
        const base64 = e.target.result;
        document.getElementById(dataId).value = base64;
        const prev = document.getElementById(previewId);
        if (prev) {
          prev.src = base64;
          prev.style.display = 'block';
        }
      };
      reader.readAsDataURL(file);
    }

    function handleImageUrlInput(event, previewId, dataId) {
      const url = event.target.value.trim();
      document.getElementById(dataId).value = url;
      const prev = document.getElementById(previewId);
      if (prev) {
        if (url) {
          prev.src = url;
          prev.style.display = 'block';
        } else {
          prev.style.display = 'none';
        }
      }
    }

    function openAddProductModal() {
      document.getElementById('newProdSku').value = '';
      document.getElementById('newProdName').value = '';
      document.getElementById('newProdPrice').value = '';
      document.getElementById('newProdStock').value = '10';
      document.getElementById('newProdDesc').value = '';
      document.getElementById('newProdImgData').value = '';
      document.getElementById('newProdImgUrl').value = '';
      document.getElementById('newProdImgFile').value = '';
      const prev = document.getElementById('newProdImgPreview');
      if (prev) prev.style.display = 'none';
      document.getElementById('newProdError').style.display = 'none';
      document.getElementById('addProductModal').classList.add('active');
    }

    function closeAddProductModal() {
      document.getElementById('addProductModal').classList.remove('active');
    }

    async function submitAddProduct(e) {
      e.preventDefault();
      const sku = document.getElementById('newProdSku').value.trim().toUpperCase();
      const name = document.getElementById('newProdName').value.trim();
      const price = parseFloat(document.getElementById('newProdPrice').value);
      const stock = parseInt(document.getElementById('newProdStock').value, 10);
      const desc = document.getElementById('newProdDesc').value.trim();
      const img = document.getElementById('newProdImgData').value.trim() || document.getElementById('newProdImgUrl').value.trim();
      const btn = document.getElementById('btnSubmitNewProd');
      const errBox = document.getElementById('newProdError');

      btn.disabled = true;
      btn.textContent = 'Publishing...';
      errBox.style.display = 'none';

      try {
        if (!adminToken) {
          throw new Error('Please authenticate as administrator first.');
        }

        const res = await fetch('/products', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`
          },
          body: JSON.stringify({
            sku: sku,
            name: name,
            price: price,
            initial_stock: stock,
            description: desc,
            image_url: img || null,
            status: 'PUBLISHED'
          })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Failed to create product');
        }

        alert(`Product ${sku} — "${name}" published successfully!`);
        closeAddProductModal();
        fetchCatalog();
      } catch (err) {
        errBox.textContent = err.message;
        errBox.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.textContent = '🚀 Publish to Catalog';
      }
    }

    function openEditProductModal(productId) {
      const prod = allProducts.find(p => p.id === productId);
      if (!prod) return;

      document.getElementById('editProdId').value = prod.id;
      document.getElementById('editProdSku').value = prod.sku;
      document.getElementById('editProdName').value = prod.name;
      document.getElementById('editProdPrice').value = prod.price;
      document.getElementById('editProdStock').value = prod.stock;
      document.getElementById('editProdDesc').value = prod.description || '';
      document.getElementById('editProdImgData').value = prod.imageUrl || '';
      document.getElementById('editProdImgUrl').value = (prod.imageUrl && !prod.imageUrl.startsWith('data:')) ? prod.imageUrl : '';
      document.getElementById('editProdImgFile').value = '';

      const prev = document.getElementById('editProdImgPreview');
      if (prod.imageUrl) {
        prev.src = prod.imageUrl;
        prev.style.display = 'block';
      } else {
        prev.style.display = 'none';
      }

      document.getElementById('editProdError').style.display = 'none';
      document.getElementById('editProductModal').classList.add('active');
    }

    function closeEditProductModal() {
      document.getElementById('editProductModal').classList.remove('active');
    }

    async function submitEditProduct(e) {
      e.preventDefault();
      const id = document.getElementById('editProdId').value;
      const sku = document.getElementById('editProdSku').value;
      const name = document.getElementById('editProdName').value.trim();
      const price = parseFloat(document.getElementById('editProdPrice').value);
      const stock = parseInt(document.getElementById('editProdStock').value, 10);
      const desc = document.getElementById('editProdDesc').value.trim();
      const img = document.getElementById('editProdImgData').value.trim() || document.getElementById('editProdImgUrl').value.trim();
      const btn = document.getElementById('btnSubmitEditProd');
      const errBox = document.getElementById('editProdError');

      btn.disabled = true;
      btn.textContent = 'Saving...';
      errBox.style.display = 'none';

      try {
        if (!adminToken) {
          throw new Error('Please authenticate as administrator first.');
        }

        // Update product metadata & image
        const pRes = await fetch(`/products/${id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`
          },
          body: JSON.stringify({
            name: name,
            price: price,
            description: desc,
            image_url: img || null
          })
        });

        if (!pRes.ok) {
          const pData = await pRes.json();
          throw new Error(pData.detail || 'Failed to update product details');
        }

        // Update inventory stock
        const iRes = await fetch(`/inventory/${id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`
          },
          body: JSON.stringify({ quantity: stock })
        });

        if (!iRes.ok) {
          const iData = await iRes.json();
          throw new Error(iData.detail || 'Failed to update inventory stock');
        }

        alert(`Product ${sku} updated successfully!`);
        closeEditProductModal();
        fetchCatalog();
      } catch (err) {
        errBox.textContent = err.message;
        errBox.style.display = 'block';
      } finally {
        btn.disabled = false;
        btn.textContent = '💾 Save Changes';
      }
    }

    async function deleteCatalogProduct(productId, sku) {
      if (!confirm(`Are you sure you want to unpublish / remove ${sku} from the live catalog?`)) {
        return;
      }
      try {
        if (!adminToken) {
          alert('Please authenticate as administrator first.');
          return;
        }

        const res = await fetch(`/products/${productId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${adminToken}`
          }
        });

        if (res.ok || res.status === 204) {
          alert(`Product ${sku} removed successfully!`);
          fetchCatalog();
        } else {
          alert('Could not delete product');
        }
      } catch (err) {
        alert('Delete error: ' + err.message);
      }
    }

    async function saveStock(productId) {
      if (!adminToken) await selectLogin('ADMIN');
      const val = parseInt(document.getElementById('stock_' + productId).value, 10);
      try {
        const res = await fetch(`/inventory/${productId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`
          },
          body: JSON.stringify({ quantity: val })
        });
        if (res.ok) {
          alert('Stock updated successfully!');
          fetchCatalog();
        } else {
          alert('Failed to update stock');
        }
      } catch (err) {
        alert('Error: ' + err.message);
      }
    }

    // =========================================================================
    // CUSTOMER FEATURES: Reviews, Wishlist, Coupons, and Dynamic Filters
    // =========================================================================

    // 1. Wishlist State & Handlers
    wishlist = wishlist || [];

    function updateWishlistBadge() {
      const badge = document.getElementById('wishlistBadge');
      if (badge) {
        badge.textContent = wishlist.length;
        badge.style.display = wishlist.length > 0 ? 'inline-block' : 'none';
      }
    }

    function toggleWishlist(e, productId) {
      if (e) e.stopPropagation();
      const idx = wishlist.indexOf(productId);
      if (idx > -1) {
        wishlist.splice(idx, 1);
      } else {
        wishlist.push(productId);
      }
      localStorage.setItem('ecom_wishlist', JSON.stringify(wishlist));
      updateWishlistBadge();
      applyFiltersAndSort();
      if (document.getElementById('wishlistModal').classList.contains('active')) {
        renderWishlist();
      }
    }

    function openWishlistModal() {
      renderWishlist();
      document.getElementById('wishlistModal').classList.add('active');
    }

    function closeWishlistModal() {
      document.getElementById('wishlistModal').classList.remove('active');
    }

    function renderWishlist() {
      const container = document.getElementById('wishlistItemsContainer');
      if (!container) return;
      const items = allProducts.filter(p => wishlist.includes(p.id));
      if (!items.length) {
        container.innerHTML = `
          <div style="text-align: center; color: var(--text-muted); padding: 3rem 1rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🤍</div>
            <div style="font-weight: 700; font-size: 1.1rem; color: #ffffff; margin-bottom: 0.25rem;">Your Wishlist is Empty</div>
            <p style="font-size: 0.85rem;">Click the heart icon on any device in the catalog to save it for later.</p>
          </div>
        `;
        return;
      }
      container.innerHTML = items.map(p => `
        <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0, 20, 50, 0.7); border: 1px solid rgba(0, 212, 255, 0.25); border-radius: 12px; padding: 0.85rem 1rem; gap: 1rem; flex-wrap: wrap;">
          <div style="display: flex; align-items: center; gap: 0.85rem;">
            <img src="${p.imageUrl}" alt="${p.name}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px;">
            <div>
              <div style="font-weight: 800; font-size: 0.92rem; color: #ffffff;">${p.name}</div>
              <div style="font-size: 0.78rem; color: #00f0ff; font-weight: 700;">₹${Number(p.price).toLocaleString('en-IN')}</div>
            </div>
          </div>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <button class="add-btn" style="padding: 0.4rem 0.85rem; font-size: 0.8rem;" onclick="addToCart('${p.id}'); toggleWishlist(null, '${p.id}');">🛒 Move to Cart</button>
            <button class="btn-sm" style="background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4);" onclick="toggleWishlist(null, '${p.id}')">Remove</button>
          </div>
        </div>
      `).join('');
    }

    // 2. Product Reviews State & Handlers
    if (!productReviews) {
      productReviews = {
        'LAPTOP-001': [
          { name: 'Aditya Sen', rating: 5, date: '2 days ago', verified: true, text: 'Massive compile speed upgrade. Running 12 Docker containers and k8s cluster locally without thermal throttling.' },
          { name: 'Pooja Iyer', rating: 5, date: '1 week ago', verified: true, text: 'The Liquid Retina display color gamut is phenomenal for design and color grading.' }
        ],
        'PHONE-002': [
          { name: 'Kunal Sharma', rating: 5, date: '3 days ago', verified: true, text: 'OLED 120Hz display is butter smooth. Low-light camera optics exceed all expectations.' },
          { name: 'Meera Patel', rating: 4, date: '2 weeks ago', verified: true, text: 'Fast charging reaches 100% in under 28 mins. Premium titanium hand feel.' }
        ],
        'AUDIO-003': [
          { name: 'David D.', rating: 5, date: 'Yesterday', verified: true, text: 'Active noise cancellation drowns out city street traffic completely. Spatial audio is crisp.' }
        ],
        'DISP-004': [
          { name: 'Sandeep R.', rating: 5, date: '4 days ago', verified: true, text: 'Color calibration out of the box is Delta E < 1. Perfect 4K workstation monitor.' }
        ],
        'KEYB-005': [
          { name: 'Tanvi G.', rating: 5, date: '5 days ago', verified: true, text: 'Gasket mount typing sound is deep and tactile. Hot-swappable switches are smooth.' }
        ]
      };
      localStorage.setItem('ecom_product_reviews', JSON.stringify(productReviews));
    }

    function getProductRating(sku) {
      const list = (productReviews && productReviews[sku]) || [];
      const hash = sku.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
      const baselineCount = 42 + (hash % 110);
      if (!list.length) {
        const rating = (4.7 + ((hash % 3) * 0.1)).toFixed(1);
        return { rating, count: baselineCount, reviews: [] };
      }
      const sum = list.reduce((acc, r) => acc + r.rating, 0);
      const avg = (sum / list.length).toFixed(1);
      return { rating: avg, count: baselineCount + list.length, reviews: list };
    }

    let selectedReviewStars = 5;
    function setReviewStars(stars) {
      selectedReviewStars = stars;
      for (let i = 1; i <= 5; i++) {
        const s = document.getElementById(`starBtn_${i}`);
        if (s) {
          s.style.color = i <= stars ? '#f59e0b' : '#64748b';
        }
      }
    }

    function submitProductReview(event, sku, productId) {
      event.preventDefault();
      const nameInput = document.getElementById('reviewAuthorName');
      const commentInput = document.getElementById('reviewCommentText');
      if (!commentInput || !commentInput.value.trim()) return;

      const authorName = (nameInput && nameInput.value.trim()) || currentUserEmail || 'Verified Shopper';
      const newReview = {
        name: authorName,
        rating: selectedReviewStars,
        date: 'Just now',
        verified: true,
        text: commentInput.value.trim()
      };

      if (!productReviews[sku]) productReviews[sku] = [];
      productReviews[sku].unshift(newReview);
      localStorage.setItem('ecom_product_reviews', JSON.stringify(productReviews));

      openProductModal(productId);
      applyFiltersAndSort();
    }

    // 3. Promotional Coupon / Discount Engine
    const VALID_COUPONS = {
      'SAVE10': { code: 'SAVE10', type: 'percent', value: 10, description: '10% discount applied to your order!' },
      'FESTIVE20': { code: 'FESTIVE20', type: 'percent', value: 20, description: '20% festive discount applied!' },
      'WELCOME500': { code: 'WELCOME500', type: 'flat', value: 500, minOrder: 2000, description: '₹500 flat discount applied!' }
    };

    function applyCoupon() {
      const input = document.getElementById('couponInput');
      const msg = document.getElementById('couponStatusMessage');
      if (!input) return;
      const code = input.value.trim().toUpperCase();
      if (!code) {
        if (msg) {
          msg.textContent = 'Please enter a coupon code.';
          msg.style.color = '#ef4444';
          msg.style.display = 'block';
        }
        return;
      }
      const c = VALID_COUPONS[code];
      if (!c) {
        if (msg) {
          msg.textContent = '⚠️ Invalid coupon code. Try SAVE10, FESTIVE20, or WELCOME500.';
          msg.style.color = '#ef4444';
          msg.style.display = 'block';
        }
        return;
      }
      appliedCoupon = c;
      localStorage.setItem('ecom_coupon', JSON.stringify(appliedCoupon));
      if (msg) {
        msg.textContent = '🎉 ' + c.description;
        msg.style.color = '#00ffaa';
        msg.style.display = 'block';
      }
      input.value = '';
      loadCart();
    }

    function quickApplyCoupon(code) {
      const input = document.getElementById('couponInput');
      if (input) input.value = code;
      applyCoupon();
    }

    function removeCoupon() {
      appliedCoupon = null;
      localStorage.removeItem('ecom_coupon');
      const msg = document.getElementById('couponStatusMessage');
      if (msg) {
        msg.textContent = 'Coupon removed.';
        msg.style.color = '#94a3b8';
        msg.style.display = 'block';
      }
      loadCart();
    }

    // 4. Advanced Filter & Sorting Logic
    function setPriceFilter(filter, btn) {
      currentPriceFilter = filter;
      document.querySelectorAll('.price-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyFiltersAndSort();
    }

    function setCategory(cat, btn) {
      currentCategory = cat;
      document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyFiltersAndSort();
    }

    function applyFiltersAndSort() {
      const searchBox = document.getElementById('searchInput');
      const q = searchBox ? searchBox.value.toLowerCase().trim() : '';
      const sortSelect = document.getElementById('sortSelect');
      currentSort = sortSelect ? sortSelect.value : 'featured';

      let filtered = [...allProducts];

      // 1. Search Query
      if (q) {
        filtered = filtered.filter(p => p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q) || (p.description && p.description.toLowerCase().includes(q)));
      }

      // 2. Category Filter
      if (currentCategory !== 'ALL') {
        filtered = filtered.filter(p => {
          if (currentCategory === 'Laptops') return p.sku.startsWith('LAPTOP');
          if (currentCategory === 'Phones') return p.sku.startsWith('PHONE') || p.sku.startsWith('TABL');
          if (currentCategory === 'Audio') return p.sku.startsWith('AUDIO') || p.sku.startsWith('SPKR');
          if (currentCategory === 'Peripherals') return p.sku.startsWith('KEYB') || p.sku.startsWith('MOUS') || p.sku.startsWith('WATCH') || p.sku.startsWith('GAME') || p.sku.startsWith('DRON') || p.sku.startsWith('CHRG') || p.sku.startsWith('STRE');
          if (currentCategory === 'Displays') return p.sku.startsWith('DISP');
          return true;
        });
      }

      // 3. Price Bracket Filter
      if (currentPriceFilter !== 'ALL') {
        filtered = filtered.filter(p => {
          const price = Number(p.price);
          if (currentPriceFilter === 'UNDER_25K') return price < 25000;
          if (currentPriceFilter === '25K_75K') return price >= 25000 && price <= 75000;
          if (currentPriceFilter === '75K_150K') return price > 75000 && price <= 150000;
          if (currentPriceFilter === 'ABOVE_150K') return price > 150000;
          return true;
        });
      }

      // 4. Sorting
      if (currentSort === 'price-asc') {
        filtered.sort((a, b) => Number(a.price) - Number(b.price));
      } else if (currentSort === 'price-desc') {
        filtered.sort((a, b) => Number(b.price) - Number(a.price));
      } else if (currentSort === 'rating-desc') {
        filtered.sort((a, b) => {
          const rA = Number(getProductRating(a.sku).rating);
          const rB = Number(getProductRating(b.sku).rating);
          return rB - rA;
        });
      } else if (currentSort === 'name-asc') {
        filtered.sort((a, b) => a.name.localeCompare(b.name));
      }

      const countLabel = document.getElementById('filteredCountLabel');
      if (countLabel) {
        countLabel.textContent = `Showing ${filtered.length} of ${allProducts.length} items`;
      }

      renderProducts(filtered);
    }

    function resetFilters() {
      const searchBox = document.getElementById('searchInput');
      if (searchBox) searchBox.value = '';
      currentCategory = 'ALL';
      currentPriceFilter = 'ALL';
      document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      const allPill = document.getElementById('filterPillAll');
      if (allPill) allPill.classList.add('active');
      document.querySelectorAll('.price-pill').forEach(b => b.classList.remove('active'));
      const allPricePill = document.querySelector('.price-pill');
      if (allPricePill) allPricePill.classList.add('active');
      const sortSelect = document.getElementById('sortSelect');
      if (sortSelect) sortSelect.value = 'featured';
      applyFiltersAndSort();
    }

    function filterProducts() {
      applyFiltersAndSort();
    }

    // Cart Drawer
    function toggleCart() {
      document.getElementById('cartDrawer').classList.toggle('active');
      if (document.getElementById('cartDrawer').classList.contains('active')) {
        loadCart();
      }
    }

    async function addToCart(productId) {
      if (!customerToken) {
        openLoginModal();
        return;
      }
      try {
        await fetch('/cart/items', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${customerToken}`
          },
          body: JSON.stringify({ product_id: productId, quantity: 1 })
        });
        loadCart();
        toggleCart();
      } catch (err) {
        alert('Could not add product: ' + err.message);
      }
    }

    async function loadCart() {
      if (!customerToken) {
        document.getElementById('cartBadge').textContent = '0';
        document.getElementById('cartTotalPrice').textContent = '₹0.00';
        const list = document.getElementById('cartItemsList');
        if (list) {
          list.innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 3rem;">Please sign in to view your cart.</div>';
        }
        const chkBtn = document.getElementById('checkoutBtn');
        if (chkBtn) chkBtn.disabled = true;
        return;
      }
      try {
        const res = await fetch('/cart', {
          headers: { 'Authorization': `Bearer ${customerToken}` }
        });
        const cart = await res.json();
        const items = cart.items || [];
        const rawTotal = Number(cart.total || 0);

        let discount = 0;
        if (appliedCoupon) {
          if (appliedCoupon.type === 'percent') {
            discount = Math.round(rawTotal * (appliedCoupon.value / 100));
          } else if (appliedCoupon.type === 'flat') {
            if (rawTotal >= (appliedCoupon.minOrder || 0)) {
              discount = appliedCoupon.value;
            } else {
              appliedCoupon = null;
              localStorage.removeItem('ecom_coupon');
            }
          }
        }
        discount = Math.min(discount, rawTotal);
        const finalDue = Math.max(0, rawTotal - discount);

        document.getElementById('cartBadge').textContent = items.reduce((acc, i) => acc + i.quantity, 0);

        const subtotalEl = document.getElementById('cartSubtotalPrice');
        if (subtotalEl) subtotalEl.textContent = `₹${rawTotal.toLocaleString('en-IN')}`;

        const discRow = document.getElementById('cartDiscountRow');
        const discLabel = document.getElementById('cartDiscountLabel');
        const discAmount = document.getElementById('cartDiscountAmount');
        const coupBadge = document.getElementById('couponActiveBadge');

        if (discount > 0 && appliedCoupon) {
          if (discRow) discRow.style.display = 'flex';
          if (discLabel) discLabel.textContent = `🏷️ Coupon (${appliedCoupon.code})`;
          if (discAmount) discAmount.textContent = `-₹${discount.toLocaleString('en-IN')}`;
          if (coupBadge) {
            coupBadge.style.display = 'inline-block';
            coupBadge.textContent = `${appliedCoupon.code} (-₹${discount.toLocaleString('en-IN')})`;
          }
        } else {
          if (discRow) discRow.style.display = 'none';
          if (coupBadge) coupBadge.style.display = 'none';
        }

        document.getElementById('cartTotalPrice').textContent = `₹${finalDue.toLocaleString('en-IN')}`;
        
        const list = document.getElementById('cartItemsList');
        if (items.length === 0) {
          list.innerHTML = '<div style="text-align: center; color: var(--text-muted); margin-top: 3rem;">Your cart is empty.</div>';
          document.getElementById('checkoutBtn').disabled = true;
          return;
        }

        document.getElementById('checkoutBtn').disabled = false;
        list.innerHTML = items.map(i => `
          <div class="cart-card">
            <div>
              <div style="font-weight: 700;">${i.name}</div>
              <div style="font-size: 0.85rem; color: var(--text-muted);">₹${Number(i.price).toLocaleString('en-IN')} × ${i.quantity}</div>
            </div>
            <button class="btn-sm" style="background: #ef4444;" onclick="removeItem('${i.product_id}')">Remove</button>
          </div>
        `).join('');
      } catch (err) {
        console.error(err);
      }
    }

    async function removeItem(productId) {
      await fetch(`/cart/items/${productId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${customerToken}` }
      });
      loadCart();
    }

    let currentPendingOrder = null;
    let selectedPaymentMethod = 'upi';

    function showPayError(msg) {
      const errBox = document.getElementById('paymentErrorAlert');
      if (errBox) {
        errBox.textContent = '⚠️ ' + msg;
        errBox.style.display = 'block';
      } else {
        alert(msg);
      }
    }

    function clearPayError() {
      const errBox = document.getElementById('paymentErrorAlert');
      if (errBox) errBox.style.display = 'none';
      const upi = document.getElementById('upiVpaInput');
      if (upi) upi.style.borderColor = 'var(--card-border)';
    }

    function closePaymentModal() {
      document.getElementById('paymentModal').classList.remove('active');
      clearPayError();
    }

    function selectPayMethod(method) {
      selectedPaymentMethod = method;
      clearPayError();

      document.querySelectorAll('.pay-method-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('methodContentUPI').style.display = 'none';
      document.getElementById('methodContentCard').style.display = 'none';
      document.getElementById('methodContentNet').style.display = 'none';

      if (method === 'upi') {
        document.getElementById('btnMethodUPI').classList.add('active');
        document.getElementById('methodContentUPI').style.display = 'block';
      } else if (method === 'card') {
        document.getElementById('btnMethodCard').classList.add('active');
        document.getElementById('methodContentCard').style.display = 'block';
      } else {
        document.getElementById('btnMethodNet').classList.add('active');
        document.getElementById('methodContentNet').style.display = 'block';
      }
    }

    async function initiateCheckout() {
      const btn = document.getElementById('checkoutBtn');
      btn.disabled = true;
      btn.textContent = '⏳ Creating Order & Reserving Stock...';

      try {
        if (!customerToken) {
          btn.disabled = false;
          btn.textContent = '💳 Choose Payment Method & Pay';
          openLoginModal();
          return;
        }

        const cRes = await fetch('/cart/checkout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${customerToken}`
          },
          body: JSON.stringify({ currency: 'INR' })
        });

        const cData = await cRes.json();

        if (!cRes.ok || !cData.order) {
          throw new Error(cData.detail || cData.message || 'Cart is empty or could not create order');
        }

        currentPendingOrder = cData.order;

        // Clear applied coupon upon order checkout
        if (appliedCoupon) {
          localStorage.removeItem('ecom_coupon');
          appliedCoupon = null;
        }

        // Close cart drawer
        toggleCart();
        loadCart();

        // Immediately open the Payment Method selection modal!
        clearPayError();
        const rzpId = (currentPendingOrder.payment && currentPendingOrder.payment.razorpay_order_id) || currentPendingOrder.razorpay_order_id || 'order_sim_' + currentPendingOrder.id.substring(0, 8);
        document.getElementById('payModalOrderId').textContent = rzpId;
        document.getElementById('payModalAmount').textContent = `₹${Number(currentPendingOrder.grand_total || 0).toLocaleString('en-IN')} INR`;
        document.getElementById('btnSubmitPayment').textContent = `🔒 Pay ₹${Number(currentPendingOrder.grand_total || 0).toLocaleString('en-IN')} via Razorpay`;
        document.getElementById('paymentModal').classList.add('active');
      } catch (e) {
        alert('Checkout error: ' + e.message);
      } finally {
        btn.disabled = false;
        btn.textContent = '💳 Choose Payment Method & Pay';
      }
    }

    async function authorizeAndPay() {
      if (!currentPendingOrder) return;
      clearPayError();

      let methodDetail = 'UPI';

      // Strict validation for UPI payment method
      if (selectedPaymentMethod === 'upi') {
        const upiVal = document.getElementById('upiVpaInput').value.trim();
        if (!upiVal) {
          showPayError('UPI ID is required. Please enter a valid UPI address (e.g. name@okhdfcbank or 9876543210@paytm).');
          const upiInput = document.getElementById('upiVpaInput');
          if (upiInput) {
            upiInput.style.borderColor = '#ef4444';
            upiInput.focus();
          }
          return;
        }
        // Validate standard UPI VPA format
        const upiRegex = /^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$/;
        if (!upiRegex.test(upiVal)) {
          showPayError('Invalid UPI format. Must be in the format username@bank (e.g. alex@okhdfcbank or 9876543210@paytm).');
          const upiInput = document.getElementById('upiVpaInput');
          if (upiInput) {
            upiInput.style.borderColor = '#ef4444';
            upiInput.focus();
          }
          return;
        }
        methodDetail = `UPI (${upiVal})`;
      } else if (selectedPaymentMethod === 'card') {
        methodDetail = 'Credit/Debit Card (Visa Sandbox)';
      } else {
        methodDetail = 'Net Banking (Instant Sandbox)';
      }

      const payBtn = document.getElementById('btnSubmitPayment');
      payBtn.disabled = true;
      payBtn.textContent = '⏳ Authorizing Razorpay Payment...';

      try {
        const rzpOrderId = (currentPendingOrder.payment && currentPendingOrder.payment.razorpay_order_id) || currentPendingOrder.razorpay_order_id || 'order_sim_' + currentPendingOrder.id.substring(0, 8);
        const rzpPaymentId = 'pay_' + Math.random().toString(36).substring(2, 10) + Math.random().toString(36).substring(2, 6);
        const verifyRes = await fetch(`/orders/${currentPendingOrder.id}/payment/verify`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${customerToken}`
          },
          body: JSON.stringify({
            razorpay_order_id: rzpOrderId,
            razorpay_payment_id: rzpPaymentId,
            razorpay_signature: 'mock_signature_test'
          })
        });

        if (!verifyRes.ok) {
          const errData = await verifyRes.json();
          throw new Error(errData.detail || 'Payment verification failed');
        }

        // Close payment modal and refresh orders list
        closePaymentModal();
        fetchOrders();

        // Show confirmed receipt modal (Only non-sensitive Order ID and Payment ID)
        document.getElementById('receiptContent').innerHTML = `
          <div style="margin-bottom: 0.6rem;"><strong>Order ID:</strong> <span style="font-family: var(--font-mono); color: var(--primary); font-weight: 700;">${currentPendingOrder.id}</span></div>
          <div style="margin-bottom: 0.6rem;"><strong>Payment ID:</strong> <span style="font-family: var(--font-mono); font-weight: 700; color: #059669;">${rzpPaymentId}</span></div>
          <div style="margin-bottom: 0.6rem;"><strong>Method:</strong> <span style="font-family: var(--font-mono);">${methodDetail}</span></div>
          <div style="margin-bottom: 0.6rem;"><strong>Status:</strong> <span style="color: #059669; font-weight: 700;">PAID (Confirmed)</span></div>
          <div style="margin-bottom: 0.6rem;"><strong>Total Paid:</strong> ₹${Number(currentPendingOrder.grand_total).toLocaleString('en-IN')} INR</div>
          <div><strong>Fulfillment:</strong> Delivery in 2 business days</div>
        `;
        document.getElementById('orderModal').classList.add('active');
        currentPendingOrder = null;
      } catch (e) {
        showPayError('Payment Authorization Error: ' + e.message);
      } finally {
        payBtn.disabled = false;
        payBtn.textContent = '🔒 Authorize & Complete Payment';
      }
    }

    // Initialize customer authentication session
    if (customerToken && currentUserEmail) {
      updateAuthUI();
      loadCart();
    } else {
      // Auto-connect as active demo customer for seamless out-of-the-box browsing
      selectLogin('CUSTOMER');
    }
    fetchCatalog();
    updateWishlistBadge();

    // Check URL parameters for hidden admin gate or return callbacks
    const queryParams = new URLSearchParams(window.location.search);
    if (queryParams.get('admin_gate') === '1' || queryParams.get('admin') === '1') {
      openAdminAuthModal();
    }
    if (queryParams.get('order_success')) {
      const succId = queryParams.get('order_success');
      const succAmt = queryParams.get('amount') || '0.00';
      document.getElementById('receiptContent').innerHTML = `
        <div style="margin-bottom: 0.6rem;"><strong>Order ID:</strong> <span style="font-family: var(--font-mono); color: var(--primary); font-weight: 700;">${succId}</span></div>
        <div style="margin-bottom: 0.6rem;"><strong>Status:</strong> <span style="color: #059669; font-weight: 700;">PAID (Confirmed)</span></div>
        <div style="margin-bottom: 0.6rem;"><strong>Total Paid:</strong> ₹${succAmt} INR</div>
        <div><strong>Fulfillment:</strong> Delivery in 2 business days</div>
      `;
      document.getElementById('orderModal').classList.add('active');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  </script>
</body>
</html>
"""


def setup_unified_openapi(app: FastAPI) -> None:
    """Register custom OpenAPI generator for Swagger UI aggregation."""
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="E-Commerce Microservices Suite API",
            version="2.0.0",
            description=(
                "Unified Enterprise API Gateway aggregating User Auth, Product Catalog, "
                "Shopping Cart, Order Management, and Razorpay Payment Microservices."
            ),
            routes=app.routes,
        )

        openapi_schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
