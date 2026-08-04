import hashlib
import json
import secrets
from collections import defaultdict
from datetime import datetime

from .config import (
    AUTO_CATEGORY_LABEL,
    DATA_PATH,
    SUPPORTED_LANGUAGES,
    SUPPORTED_THEMES,
    TRANSLATIONS,
)


def init_store() -> None:
    if not DATA_PATH.exists():
        save_data({"next_id": 1, "expenses": [], "budgets": {}, "users": {}})


def load_data() -> dict:
    init_store()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if "users" not in data:
        data["users"] = {}
    if "expenses" not in data:
        data["expenses"] = []
    if "budgets" not in data:
        data["budgets"] = {}
    if "goals" not in data:
        data["goals"] = {}
    if "next_id" not in data:
        data["next_id"] = 1
    for username, user in data["users"].items():
        user.setdefault("full_name", username)
        user.setdefault("mobile_number", "")
        user.setdefault("email", "")
        user.setdefault("date_of_birth", "")
        user.setdefault("theme", "light")
        user.setdefault("language", "en")
    return data


def save_data(data: dict) -> None:
    DATA_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def t(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))


def get_month_bounds(month: str) -> tuple[datetime, datetime]:
    start = datetime.strptime(f"{month}-01", "%Y-%m-%d")
    if start.month == 12:
        end = datetime(start.year + 1, 1, 1)
    else:
        end = datetime(start.year, start.month + 1, 1)
    return start, end


def previous_month(month: str) -> str:
    start, _ = get_month_bounds(month)
    if start.month == 1:
        prev = datetime(start.year - 1, 12, 1)
    else:
        prev = datetime(start.year, start.month - 1, 1)
    return prev.strftime("%Y-%m")


def validate_date(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")


def validate_month(value: str) -> str:
    return datetime.strptime(value, "%Y-%m").strftime("%Y-%m")


def parse_amount(value: str) -> float:
    amount = float(value)
    if amount < 0:
        raise ValueError("Amount must be non-negative.")
    return amount


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def validate_email(email: str) -> str:
    clean_email = email.strip().lower()
    if "@" not in clean_email or "." not in clean_email.split("@")[-1]:
        raise ValueError("Enter a valid email address")
    return clean_email


def validate_mobile_number(mobile_number: str) -> str:
    digits = "".join(character for character in mobile_number if character.isdigit())
    if len(digits) != 10:
        raise ValueError("Mobile number must contain exactly 10 digits")
    return digits


def validate_full_name(full_name: str) -> str:
    clean_name = " ".join(full_name.split())
    if len(clean_name) < 3:
        raise ValueError("Full name must be at least 3 characters")
    return clean_name


def normalize_username(username: str) -> str:
    clean_username = username.strip().lower()
    if len(clean_username) < 3 or not clean_username.replace("_", "").isalnum():
        raise ValueError("Username must be at least 3 characters and use letters, numbers, or underscores")
    return clean_username


def validate_passwords(password: str, confirm_password: str) -> str:
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    if password != confirm_password:
        raise ValueError("Password and confirm password must match")
    return password


def register_user(
    full_name: str,
    mobile_number: str,
    email: str,
    date_of_birth: str,
    username: str,
    password: str,
    confirm_password: str,
) -> tuple[bool, str]:
    try:
        clean_full_name = validate_full_name(full_name)
        clean_mobile_number = validate_mobile_number(mobile_number)
        clean_email = validate_email(email)
        clean_date_of_birth = validate_date(date_of_birth)
        clean_username = normalize_username(username)
        clean_password = validate_passwords(password, confirm_password)
    except ValueError as exc:
        return False, str(exc)

    data = load_data()
    if clean_username in data["users"]:
        return False, "Username already exists"
    if any(user.get("email") == clean_email for user in data["users"].values()):
        return False, "Email already exists"

    salt = secrets.token_hex(8)
    data["users"][clean_username] = {
        "full_name": clean_full_name,
        "mobile_number": clean_mobile_number,
        "email": clean_email,
        "date_of_birth": clean_date_of_birth,
        "salt": salt,
        "password_hash": hash_password(clean_password, salt),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # If this is the first real account, assign any old anonymous data to it.
    if len(data["users"]) == 1:
        for expense in data["expenses"]:
            expense.setdefault("username", clean_username)

        legacy_budgets = data["budgets"]
        if legacy_budgets and all(isinstance(value, (int, float)) for value in legacy_budgets.values()):
            data["budgets"] = {clean_username: legacy_budgets}

    save_data(data)
    return True, clean_username


def authenticate_user(username: str, password: str) -> bool:
    clean_username = username.strip().lower()
    data = load_data()
    user = data["users"].get(clean_username)
    if not user:
        return False
    return user["password_hash"] == hash_password(password, user["salt"])


def ensure_budget_shape(data: dict) -> dict:
    budgets = data.get("budgets", {})
    if budgets and all(isinstance(value, (int, float)) for value in budgets.values()):
        first_user = next(iter(data.get("users", {})), None)
        data["budgets"] = {first_user: budgets} if first_user else {}
    return data


def infer_category(note: str, selected_category: str) -> str:
    chosen = selected_category.strip().title()
    if chosen and chosen != AUTO_CATEGORY_LABEL:
        return chosen

    text = note.lower()
    keyword_map = {
        "Food": ["dominos", "pizza", "burger", "swiggy", "zomato", "restaurant", "cafe", "food"],
        "Transport": ["uber", "ola", "metro", "bus", "train", "fuel", "petrol", "diesel", "taxi"],
        "Utilities": ["electricity", "water", "wifi", "internet", "gas", "bill", "recharge"],
        "Medical": ["pharmacy", "medicine", "doctor", "hospital", "clinic", "medical"],
        "Entertainment": ["movie", "netflix", "spotify", "prime", "game", "concert"],
        "Education": ["course", "tuition", "book", "exam", "fees", "class"],
        "Groceries": ["milk", "vegetable", "grocery", "groceries", "supermarket", "mart"],
        "Rent": ["rent", "landlord", "lease"],
        "Savings": ["saving", "deposit", "investment", "sip"],
    }
    for category, keywords in keyword_map.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"


def reset_password(
    username: str,
    email: str,
    date_of_birth: str,
    new_password: str,
    confirm_password: str,
) -> tuple[bool, str]:
    try:
        clean_username = normalize_username(username)
        clean_email = validate_email(email)
        clean_date_of_birth = validate_date(date_of_birth)
        clean_password = validate_passwords(new_password, confirm_password)
    except ValueError as exc:
        return False, str(exc)

    data = load_data()
    user = data["users"].get(clean_username)
    if not user:
        return False, "No account found for that username"
    if user.get("email") != clean_email or user.get("date_of_birth") != clean_date_of_birth:
        return False, "Details do not match our records"

    salt = secrets.token_hex(8)
    user["salt"] = salt
    user["password_hash"] = hash_password(clean_password, salt)
    save_data(data)
    return True, clean_username


def add_expense(username: str, amount: float, category: str, note: str, expense_date: str) -> None:
    data = load_data()
    data = ensure_budget_shape(data)
    final_category = infer_category(note, category)
    data["expenses"].append(
        {
            "id": data["next_id"],
            "username": username,
            "amount": amount,
            "category": final_category,
            "note": note.strip(),
            "expense_date": expense_date,
        }
    )
    data["next_id"] += 1
    save_data(data)


def list_expenses(username: str, month: str | None = None) -> list[dict]:
    expenses = load_data()["expenses"]
    expenses = [expense for expense in expenses if expense.get("username") == username]
    if month:
        expenses = [expense for expense in expenses if expense["expense_date"].startswith(month)]
    return sorted(expenses, key=lambda item: (item["expense_date"], item["id"]), reverse=True)


def set_budget(username: str, month: str, amount: float) -> None:
    data = load_data()
    data = ensure_budget_shape(data)
    data["budgets"].setdefault(username, {})
    data["budgets"][username][month] = amount
    save_data(data)


def get_budget(username: str, month: str) -> float | None:
    data = ensure_budget_shape(load_data())
    value = data["budgets"].get(username, {}).get(month)
    return None if value is None else float(value)


def set_savings_goal(username: str, title: str, target_amount: float, saved_amount: float) -> None:
    data = load_data()
    data.setdefault("goals", {})
    existing = data["goals"].get(username, [])
    if isinstance(existing, dict):
        existing = [existing]
    existing.append(
        {
            "title": title.strip() or "Savings Goal",
            "target_amount": target_amount,
            "saved_amount": saved_amount,
        }
    )
    data["goals"][username] = existing
    save_data(data)


def get_savings_goals(username: str) -> list[dict]:
    goals = load_data().get("goals", {}).get(username)
    if not goals:
        return []
    if isinstance(goals, dict):
        goals = [goals]

    normalized: list[dict] = []
    for goal in goals:
        target_amount = float(goal.get("target_amount", 0))
        saved_amount = float(goal.get("saved_amount", 0))
        progress = 0.0 if target_amount <= 0 else min(saved_amount / target_amount, 1.0)
        remaining = max(target_amount - saved_amount, 0.0)
        normalized.append(
            {
                "title": goal.get("title", "Savings Goal"),
                "target_amount": target_amount,
                "saved_amount": saved_amount,
                "remaining": remaining,
                "progress": progress,
            }
        )
    return normalized


def get_budget_status(total_spent: float, budget: float | None) -> dict:
    if budget is None or budget <= 0:
        return {
            "label": "Set Budget",
            "class_name": "status-warning",
            "progress_class": "progress-warning",
            "progress_percent": 0.0,
            "message": "Add a monthly budget to see progress alerts.",
        }
    ratio = total_spent / budget if budget else 0.0
    if ratio >= 1:
        return {
            "label": "Over Budget",
            "class_name": "status-over",
            "progress_class": "progress-over",
            "progress_percent": 100.0,
            "message": f"You have exceeded your budget by {money(total_spent - budget)}.",
        }
    if ratio >= 0.8:
        return {
            "label": "Warning",
            "class_name": "status-warning",
            "progress_class": "progress-warning",
            "progress_percent": ratio * 100,
            "message": f"You have used {ratio * 100:.0f}% of your budget.",
        }
    return {
        "label": "Safe Zone",
        "class_name": "status-safe",
        "progress_class": "progress-safe",
        "progress_percent": ratio * 100,
        "message": f"You are within budget with {money(budget - total_spent)} remaining.",
    }


def generate_smart_insights(username: str, month: str, expenses: list[dict], by_category: dict[str, float]) -> list[str]:
    insights: list[str] = []
    if not expenses:
        return ["Add a few expenses this month to unlock smart spending insights."]

    weekend_food = 0.0
    weekday_food = 0.0
    subscriptions: dict[str, int] = defaultdict(int)
    for expense in expenses:
        weekday = datetime.strptime(expense["expense_date"], "%Y-%m-%d").weekday()
        amount = float(expense["amount"])
        category = expense["category"]
        note = expense.get("note", "").lower()
        if category in {"Food", "Groceries"}:
            if weekday >= 5:
                weekend_food += amount
            else:
                weekday_food += amount
        for recurring in ("netflix", "spotify", "prime", "youtube", "subscription"):
            if recurring in note:
                subscriptions[recurring.title()] += 1

    if weekend_food > weekday_food and weekend_food > 0:
        insights.append(f"You spend more on food on weekends: {money(weekend_food)} vs {money(weekday_food)} on weekdays.")

    prev_total, _ = month_summary(username, previous_month(month))
    current_total = sum(float(expense["amount"]) for expense in expenses)
    if prev_total > 0 and current_total > prev_total * 1.2:
        insights.append(f"Spending increased sharply from {money(prev_total)} last month to {money(current_total)} this month.")

    if by_category:
        top_category, top_amount = max(by_category.items(), key=lambda item: item[1])
        insights.append(f"Your top category this month is {top_category} at {money(top_amount)}.")
        if top_category == "Food":
            insights.append(f"You spent {money(top_amount)} on food. Try limiting it to {money(top_amount * 0.5)} next month.")
        if top_category == "Entertainment":
            insights.append(f"Entertainment is high at {money(top_amount)}. Cutting one outing could reduce spending quickly.")

    if subscriptions:
        recurring_name = max(subscriptions.items(), key=lambda item: item[1])[0]
        insights.append(f"{recurring_name} looks recurring. Review whether you still need this subscription.")

    return insights[:4]


def month_summary(username: str, month: str) -> tuple[float, dict[str, float]]:
    rows = [
        expense
        for expense in load_data()["expenses"]
        if expense.get("username") == username and expense["expense_date"].startswith(month)
    ]
    total = 0.0
    by_category: dict[str, float] = defaultdict(float)
    for row in rows:
        amount = float(row["amount"])
        total += amount
        by_category[row["category"]] += amount
    return total, dict(sorted(by_category.items(), key=lambda item: item[1], reverse=True))


def daily_summary(username: str, month: str) -> dict[str, float]:
    rows = [
        expense
        for expense in load_data()["expenses"]
        if expense.get("username") == username and expense["expense_date"].startswith(month)
    ]
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        totals[row["expense_date"]] += float(row["amount"])
    return dict(sorted(totals.items()))


def get_month_context(username: str, month: str) -> dict:
    total_spent, by_category = month_summary(username, month)
    budget = get_budget(username, month)
    remaining = None if budget is None else budget - total_spent
    expenses = list_expenses(username, month)
    budget_status = get_budget_status(total_spent, budget)
    insights = generate_smart_insights(username, month, expenses, by_category)
    savings_goals = get_savings_goals(username)
    return {
        "username": username,
        "month": month,
        "total_spent": total_spent,
        "budget": budget,
        "remaining": remaining,
        "by_category": by_category,
        "expenses": expenses,
        "budget_status": budget_status,
        "insights": insights,
        "savings_goals": savings_goals,
    }


def get_user_profile(username: str) -> dict | None:
    return load_data()["users"].get(username)


def get_user_preferences(username: str | None) -> dict:
    if not username:
        return {"theme": "light", "language": "en"}
    profile = get_user_profile(username) or {}
    theme = profile.get("theme", "light")
    language = profile.get("language", "en")
    if theme not in SUPPORTED_THEMES:
        theme = "light"
    if language not in SUPPORTED_LANGUAGES:
        language = "en"
    return {"theme": theme, "language": language}


def set_user_preferences(username: str, theme: str, language: str) -> None:
    data = load_data()
    user = data["users"].get(username)
    if not user:
        return
    user["theme"] = theme if theme in SUPPORTED_THEMES else "light"
    user["language"] = language if language in SUPPORTED_LANGUAGES else "en"
    save_data(data)


def money(value: float | None) -> str:
    if value is None:
        return "Not set"
    return f"Rs. {value:,.2f}"


