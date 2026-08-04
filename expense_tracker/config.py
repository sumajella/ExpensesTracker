import html
import json
import hashlib
import math
import secrets
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from http import cookies
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server


DATA_PATH = Path("expenses_data.json")
DEFAULT_CATEGORIES = [
    "Rent",
    "Groceries",
    "Food",
    "Utilities",
    "Transport",
    "Medical",
    "Entertainment",
    "Education",
    "Savings",
    "Other",
]
SESSION_COOKIE = "expense_tracker_session"
SESSIONS: dict[str, str] = {}
AUTO_CATEGORY_LABEL = "Auto Detect"
SUPPORTED_LANGUAGES = {"en": "English", "hi": "Hindi"}
SUPPORTED_THEMES = {"light": "Light", "dark": "Dark"}

TRANSLATIONS = {
    "en": {
        "home": "Home",
        "register": "Register",
        "login": "Login",
        "forgot_password": "Forgot Password",
        "dashboard": "Dashboard",
        "category_summary": "Category Summary",
        "expenses": "Expenses",
        "real_time_data": "Real-Time Data",
        "logout": "Logout",
        "expenses_tracker": "EXPENSES TRACKER",
        "private_expense_dashboard": "Private Expense Dashboard",
        "create_account": "Create Account",
        "registration_details": "Registration details",
        "full_name": "Full name",
        "mobile_number": "Mobile number",
        "email_id": "Email id",
        "date_of_birth": "Date of birth",
        "username": "Username",
        "password": "Password",
        "confirm_password": "Confirm password",
        "already_have_account": "Already have an account? Login",
        "need_account": "Need an account? Register",
        "welcome_back": "Welcome Back",
        "login_details": "Login details",
        "reset_password": "Reset password",
        "reset_password_title": "Reset your password and get back to your budget.",
        "forgot_password_help": "Enter your username, email id, and date of birth to verify your account, then choose a new password.",
        "back_to_login": "Back to login",
        "living_expenses_tracker": "Living Expenses Tracker",
        "current_month": "Current month",
        "view_month": "View month",
        "budget_vs_reality": "Budget vs Reality",
        "total_spent": "Total spent",
        "budget": "Budget",
        "remaining": "Remaining",
        "add_expense": "Add expense",
        "amount": "Amount",
        "category": "Category",
        "date": "Date",
        "note": "Note",
        "save_expense": "Save expense",
        "set_monthly_budget": "Set monthly budget",
        "month": "Month",
        "budget_amount": "Budget amount",
        "save_budget": "Save budget",
        "smart_insights": "Smart Insights",
        "savings_goal": "Savings Goal",
        "goal_name": "Goal name",
        "target_amount": "Target amount",
        "saved_amount": "Saved amount",
        "save_goal": "Save goal",
        "preferences": "Preferences",
        "profile": "Profile",
        "personal_details": "Personal Details",
        "settings": "Settings",
        "account_actions": "Account Actions",
        "language": "Language",
        "theme": "Theme",
        "light_mode": "Light",
        "dark_mode": "Dark",
        "save_preferences": "Save preferences",
        "auto_detect": "Auto Detect",
    },
    "hi": {
        "home": "होम",
        "register": "रजिस्टर",
        "login": "लॉगिन",
        "forgot_password": "पासवर्ड भूल गए",
        "dashboard": "डैशबोर्ड",
        "category_summary": "श्रेणी सारांश",
        "expenses": "खर्च",
        "real_time_data": "रीयल-टाइम डेटा",
        "logout": "लॉगआउट",
        "expenses_tracker": "खर्च ट्रैकर",
        "private_expense_dashboard": "निजी खर्च डैशबोर्ड",
        "create_account": "खाता बनाएं",
        "registration_details": "पंजीकरण विवरण",
        "full_name": "पूरा नाम",
        "mobile_number": "मोबाइल नंबर",
        "email_id": "ईमेल आईडी",
        "date_of_birth": "जन्म तिथि",
        "username": "यूज़रनेम",
        "password": "पासवर्ड",
        "confirm_password": "पासवर्ड पुष्टि करें",
        "already_have_account": "पहले से खाता है? लॉगिन करें",
        "need_account": "खाता चाहिए? रजिस्टर करें",
        "welcome_back": "फिर से स्वागत है",
        "login_details": "लॉगिन विवरण",
        "reset_password": "पासवर्ड रीसेट करें",
        "reset_password_title": "अपना पासवर्ड रीसेट करें और बजट पर वापस आएं।",
        "forgot_password_help": "यूज़रनेम, ईमेल आईडी और जन्म तिथि दर्ज करें, फिर नया पासवर्ड चुनें।",
        "back_to_login": "लॉगिन पर वापस जाएं",
        "living_expenses_tracker": "लिविंग एक्सपेंस ट्रैकर",
        "current_month": "वर्तमान महीना",
        "view_month": "महीना देखें",
        "budget_vs_reality": "बजट बनाम वास्तविकता",
        "total_spent": "कुल खर्च",
        "budget": "बजट",
        "remaining": "शेष",
        "add_expense": "खर्च जोड़ें",
        "amount": "राशि",
        "category": "श्रेणी",
        "date": "तारीख",
        "note": "नोट",
        "save_expense": "खर्च सहेजें",
        "set_monthly_budget": "मासिक बजट सेट करें",
        "month": "महीना",
        "budget_amount": "बजट राशि",
        "save_budget": "बजट सहेजें",
        "smart_insights": "स्मार्ट सुझाव",
        "savings_goal": "बचत लक्ष्य",
        "goal_name": "लक्ष्य नाम",
        "target_amount": "लक्ष्य राशि",
        "saved_amount": "बचाई गई राशि",
        "save_goal": "लक्ष्य सहेजें",
        "preferences": "पसंद",
        "profile": "प्रोफ़ाइल",
        "personal_details": "व्यक्तिगत विवरण",
        "settings": "सेटिंग्स",
        "account_actions": "अकाउंट विकल्प",
        "language": "भाषा",
        "theme": "थीम",
        "light_mode": "लाइट",
        "dark_mode": "डार्क",
        "save_preferences": "पसंद सहेजें",
        "auto_detect": "ऑटो डिटेक्ट",
    },
}

CSS = """
body {
    margin: 0;
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    background: #ffffff;
    color: #1f2937;
}
body.dark {
    background: #0f172a;
    color: #e5eef8;
}
.page {
    max-width: 1180px;
    margin: 0 auto;
    padding: 32px 20px 64px;
}
.topbar {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 10px;
    margin-bottom: 18px;
    flex-wrap: wrap;
}
.nav-link {
    display: inline-flex;
    align-items: center;
    padding: 10px 16px;
    border-radius: 999px;
    border: 1px solid #dbe5ef;
    background: #ffffff;
    color: #10213a;
    text-decoration: none;
    font-size: 0.92rem;
    font-weight: 700;
    box-shadow: 0 8px 20px rgba(16, 33, 58, 0.06);
}
.nav-link:hover {
    background: #f7fafc;
}
body.dark .nav-link {
    background: #162235;
    color: #e5eef8;
    border-color: #2a3b57;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.28);
}
body.dark .nav-link:hover {
    background: #1c2b43;
}
.nav-logout {
    width: auto;
    padding: 10px 16px;
    border-radius: 999px;
    box-shadow: none;
}
.hero {
    display: grid;
    grid-template-columns: 1.2fr 1.1fr;
    gap: 20px;
    margin-bottom: 24px;
}
.hero-card,
.panel,
.table-card {
    background: rgba(255, 255, 255, 0.78);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.7);
    border-radius: 24px;
    box-shadow: 0 18px 50px rgba(31, 41, 55, 0.08);
}
body.dark .hero-card,
body.dark .panel,
body.dark .table-card {
    background: rgba(19, 31, 51, 0.94);
    border-color: #26374f;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.34);
}
.hero-card {
    padding: 28px;
}
.eyebrow {
    display: inline-block;
    padding: 8px 12px;
    border-radius: 999px;
    background: #fff0dc;
    color: #9a5b16;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
h1 {
    font-size: clamp(2.2rem, 4vw, 4.3rem);
    line-height: 0.95;
    margin: 16px 0 10px;
    color: #10213a;
}
body.dark h1,
body.dark .panel h2,
body.dark .table-card h2,
body.dark label,
body.dark .summary-pill strong,
body.dark .goal-metric strong,
body.dark .meta-pill strong {
    color: #f3f7fb;
}
.hero p,
.muted {
    color: #526072;
}
body.dark .hero p,
body.dark .muted,
body.dark th,
body.dark .nav-card p,
body.dark .summary-pill,
body.dark .goal-metric,
body.dark .insight-card,
body.dark .meta-pill,
body.dark td,
body.dark .empty {
    color: #b8c7da;
}
.month-picker {
    display: flex;
    gap: 12px;
    align-items: end;
    flex-wrap: wrap;
    margin-top: 18px;
}
.auth-switch {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 18px;
}
.auth-badge {
    padding: 10px 16px;
    border-radius: 999px;
    background: #10213a;
    color: #ffffff;
    font-size: 0.9rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(180px, 1fr));
    gap: 18px;
}
.stat {
    padding: 24px 22px;
    border-radius: 20px;
    min-height: 220px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.stat strong {
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.stat span {
    display: block;
    max-width: 100%;
    font-size: clamp(0.85rem, 1.4vw, 1.4rem);
    font-weight: 800;
    line-height: 1.1;
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: break-word;
}
.stat-amount-currency,
.stat-amount-number {
    display: block;
}
.stat-amount-number {
    margin-top: 2px;
}
.spent {
    background: linear-gradient(180deg, #ffe7db 0%, #ffd3bd 100%);
    color: #8f3d10;
}
.budget {
    background: linear-gradient(180deg, #e8f6db 0%, #d1f0b9 100%);
    color: #2e6d1d;
}
.remain {
    background: linear-gradient(180deg, #deefff 0%, #c5e5ff 100%);
    color: #17517f;
}
.grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
}
.panel {
    padding: 22px;
}
.panel h2,
.table-card h2 {
    margin: 0 0 14px;
    color: #10213a;
}
label {
    display: block;
    font-size: 0.9rem;
    font-weight: 700;
    margin-bottom: 8px;
    color: #314254;
}
input,
select,
button {
    width: 100%;
    box-sizing: border-box;
    border-radius: 14px;
    border: 1px solid #d5deeb;
    padding: 12px 14px;
    font-size: 0.98rem;
}
body.dark input,
body.dark select {
    background: #132238;
    color: #f3f7fb;
    border-color: #2a3b57;
}
input:focus,
select:focus {
    outline: 2px solid #92c9ff;
    border-color: #92c9ff;
}
.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}
.field-full {
    grid-column: 1 / -1;
}
button {
    border: none;
    background: linear-gradient(135deg, #ff8f5a 0%, #ff6d4d 100%);
    color: white;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 12px 20px rgba(255, 109, 77, 0.22);
}
button:hover {
    filter: brightness(1.02);
}
.chip-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 12px;
}
.chip {
    padding: 8px 12px;
    border-radius: 999px;
    background: #f3f7fb;
    color: #44576b;
    font-size: 0.88rem;
    border: 1px solid #dde8f3;
}
body.dark .chip,
body.dark .summary-pill,
body.dark .goal-metric,
body.dark .insight-card,
body.dark .meta-pill {
    background: #132238;
    border-color: #2a3b57;
}
.table-card {
    padding: 22px;
}
table {
    width: 100%;
    border-collapse: collapse;
    overflow: hidden;
}
th,
td {
    padding: 14px 10px;
    text-align: left;
    border-bottom: 1px solid #ebeff4;
}
th {
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #5c6c7e;
}
body.dark table,
body.dark th,
body.dark td {
    border-color: #25364d;
}
body.dark tbody tr:hover {
    background: rgba(37, 54, 77, 0.65);
}
tbody tr:hover {
    background: rgba(239, 245, 252, 0.7);
}
.empty {
    padding: 28px 8px 12px;
    color: #6b7b8f;
}
.category-summary {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 14px;
}
.summary-pill {
    padding: 14px;
    border-radius: 16px;
    background: #f7fafc;
    border: 1px solid #e5edf4;
}
.summary-pill strong {
    display: block;
    margin-bottom: 6px;
    color: #334155;
}
.flash {
    margin-bottom: 18px;
    padding: 14px 16px;
    border-radius: 16px;
    background: #ecfdf3;
    color: #11613b;
    border: 1px solid #bde8cf;
}
body.dark .flash {
    background: #133423;
    color: #8fe1ad;
    border-color: #25563b;
}
.budget-progress {
    margin-top: 18px;
}
.status-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 10px;
}
.status-badge {
    padding: 8px 12px;
    border-radius: 999px;
    font-size: 0.84rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.status-safe {
    background: #e9f9ef;
    color: #1f7a43;
}
.status-warning {
    background: #fff6df;
    color: #9a6a09;
}
.status-over {
    background: #fdeaea;
    color: #b42323;
}
.progress-track {
    width: 100%;
    height: 16px;
    border-radius: 999px;
    background: #e9eff6;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.35s ease;
}
.progress-safe {
    background: linear-gradient(90deg, #39b36e 0%, #74d99a 100%);
}
.progress-warning {
    background: linear-gradient(90deg, #f1b341 0%, #ffd36d 100%);
}
.progress-over {
    background: linear-gradient(90deg, #e25b5b 0%, #ff8b8b 100%);
}
.insight-list {
    display: grid;
    gap: 12px;
}
.insight-card {
    padding: 14px 16px;
    border-radius: 16px;
    background: #f7fafc;
    border: 1px solid #e5edf4;
    color: #314254;
}
.goal-card {
    margin-top: 20px;
}
.goal-progress {
    margin-top: 12px;
}
.goal-summary {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-top: 12px;
}
.goal-metric {
    padding: 14px;
    border-radius: 16px;
    background: #f7fafc;
    border: 1px solid #e5edf4;
}
.goal-metric strong {
    display: block;
    margin-bottom: 6px;
    color: #334155;
}
.nav-cards {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 20px;
    margin-top: 20px;
}
.nav-card {
    display: block;
    text-decoration: none;
    color: inherit;
    padding: 22px;
}
.nav-card h2 {
    margin: 0 0 10px;
    color: #10213a;
}
.nav-card p {
    margin: 0;
    color: #526072;
}
.page-link {
    display: inline-block;
    margin-top: 14px;
    font-weight: 700;
    color: #ff6d4d;
}
.chart-card {
    padding: 22px;
    margin-top: 20px;
}
.chart-wrap {
    width: 100%;
    overflow-x: auto;
}
.chart-wrap svg {
    width: 100%;
    min-width: 720px;
    height: auto;
    display: block;
}
.donut-layout {
    display: grid;
    grid-template-columns: minmax(320px, 1fr) minmax(220px, 280px);
    gap: 24px;
    align-items: center;
}
.chart-legend {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 0;
    color: #526072;
    font-size: 0.92rem;
}
.chart-legend span {
    display: flex;
    align-items: center;
}
.legend-dot {
    width: 12px;
    height: 12px;
    border-radius: 999px;
    display: inline-block;
    margin-right: 8px;
    flex: 0 0 12px;
}
.chart-meta {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-top: 18px;
}
.meta-pill {
    padding: 16px;
    border-radius: 18px;
    border: 1px solid #e5edf4;
    background: #f7fafc;
}
.meta-pill strong {
    display: block;
    margin-bottom: 6px;
    color: #334155;
}
.donut-segment {
    transform-box: fill-box;
    transform-origin: center;
    animation: chart-grow 1s ease forwards;
}
.donut-track {
    opacity: 0.28;
}
@keyframes chart-grow {
    from {
        stroke-dasharray: 0 999;
        opacity: 0.35;
    }
    to {
        opacity: 1;
    }
}
@media (max-width: 900px) {
    .hero,
    .grid,
    .stats,
    .form-grid,
    .nav-cards,
    .goal-summary {
        grid-template-columns: 1fr;
    }
    .donut-layout {
        grid-template-columns: 1fr;
    }
    h1 {
        line-height: 1.05;
    }
}
"""


