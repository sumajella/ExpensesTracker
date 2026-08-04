import html
import math
from datetime import datetime

from .config import AUTO_CATEGORY_LABEL, CSS, DEFAULT_CATEGORIES
from .services import (
    get_month_context,
    get_user_preferences,
    get_user_profile,
    t,
)


def money(value: float | None) -> str:
    if value is None:
        return "Not set"
    return f"Rs. {value:,.2f}"


def render_stat_amount(value: float | None) -> str:
    if value is None:
        return '<span class="stat-amount-number">Not set</span>'
    return (
        '<span class="stat-amount-currency">Rs.</span>'
        f'<span class="stat-amount-number">{value:,.2f}</span>'
    )


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def render_summary_pills(by_category: dict[str, float]) -> str:
    if not by_category:
        return '<div class="empty">No expenses recorded for this month yet.</div>'

    cards = []
    for category, amount in by_category.items():
        cards.append(
            f"""
            <div class="summary-pill">
                <strong>{esc(category)}</strong>
                <div>{money(amount)}</div>
            </div>
            """
        )
    return "".join(cards)


def render_expense_rows(expenses: list[dict]) -> str:
    if not expenses:
        return '<tr><td colspan="4" class="empty">No entries yet for this month.</td></tr>'

    rows = []
    for expense in expenses:
        rows.append(
            f"""
            <tr>
                <td>{esc(expense['expense_date'])}</td>
                <td>{esc(expense['category'])}</td>
                <td>{money(float(expense['amount']))}</td>
                <td>{esc(expense['note'] or '-')}</td>
            </tr>
            """
        )
    return "".join(rows)


def render_goal_panel(goals: list[dict]) -> str:
    if not goals:
        return '<div class="empty">Set a savings goal to track your progress.</div>'

    cards = []
    for goal in goals:
        progress_percent = goal["progress"] * 100
        cards.append(
            f"""
            <div class="goal-progress">
                <div class="progress-track">
                    <div class="progress-fill progress-safe" style="width:{progress_percent:.1f}%"></div>
                </div>
                <div class="goal-summary">
                    <div class="goal-metric">
                        <strong>Goal</strong>
                        <div>{esc(goal["title"])}</div>
                    </div>
                    <div class="goal-metric">
                        <strong>Saved</strong>
                        <div>{money(goal["saved_amount"])}</div>
                    </div>
                    <div class="goal-metric">
                        <strong>Remaining</strong>
                        <div>{money(goal["remaining"])}</div>
                    </div>
                </div>
            </div>
            """
        )
    return "".join(cards)


def render_detail_header(title: str, month: str, back_path: str = "/") -> str:
    return f"""
    <section class="hero">
        <div class="hero-card">
            <div class="eyebrow">Living Expenses Tracker</div>
            <h1>{esc(title)}</h1>
            <p><a href="{esc(back_path)}?month={esc(month)}">Back to dashboard</a></p>
        </div>
    </section>
    """


def render_top_nav(month: str | None = None, authenticated: bool = False, lang: str = "en") -> str:
    month_query = f"?month={esc(month)}" if month else ""
    if authenticated:
        return f"""
        <nav class="topbar" aria-label="Main navigation">
            <a class="nav-link" href="/{month_query}">{esc(t(lang, "dashboard"))}</a>
            <a class="nav-link" href="/category-summary{month_query}">{esc(t(lang, "category_summary"))}</a>
            <a class="nav-link" href="/expenses-list{month_query}">{esc(t(lang, "expenses"))}</a>
            <a class="nav-link" href="/real-time-data{month_query}">{esc(t(lang, "real_time_data"))}</a>
            <a class="nav-link" href="/profile{month_query}">{esc(t(lang, "profile"))}</a>
        </nav>
        """
    return f"""
    <nav class="topbar" aria-label="Main navigation">
        <a class="nav-link" href="/">{esc(t(lang, "home"))}</a>
        <a class="nav-link" href="/register">{esc(t(lang, "register"))}</a>
        <a class="nav-link" href="/login">{esc(t(lang, "login"))}</a>
        <a class="nav-link" href="/forgot-password">{esc(t(lang, "forgot_password"))}</a>
    </nav>
    """


def polar_to_cartesian(center_x: float, center_y: float, radius: float, angle: float) -> tuple[float, float]:
    return (
        center_x + radius * math.cos(angle),
        center_y + radius * math.sin(angle),
    )


def donut_segment_path(
    center_x: float,
    center_y: float,
    outer_radius: float,
    inner_radius: float,
    start_angle: float,
    end_angle: float,
) -> str:
    start_outer_x, start_outer_y = polar_to_cartesian(center_x, center_y, outer_radius, start_angle)
    end_outer_x, end_outer_y = polar_to_cartesian(center_x, center_y, outer_radius, end_angle)
    start_inner_x, start_inner_y = polar_to_cartesian(center_x, center_y, inner_radius, start_angle)
    end_inner_x, end_inner_y = polar_to_cartesian(center_x, center_y, inner_radius, end_angle)
    large_arc = 1 if end_angle - start_angle > math.pi else 0
    return (
        f"M {start_outer_x:.2f} {start_outer_y:.2f} "
        f"A {outer_radius:.2f} {outer_radius:.2f} 0 {large_arc} 1 {end_outer_x:.2f} {end_outer_y:.2f} "
        f"L {end_inner_x:.2f} {end_inner_y:.2f} "
        f"A {inner_radius:.2f} {inner_radius:.2f} 0 {large_arc} 0 {start_inner_x:.2f} {start_inner_y:.2f} Z"
    )


def render_category_bar_chart(by_category: dict[str, float]) -> str:
    items = [(category, float(by_category.get(category, 0.0))) for category in DEFAULT_CATEGORIES]
    if not any(amount > 0 for _, amount in items):
        return '<div class="empty">No data available for the chart yet.</div>'

    colors = [
        "#ff8f5a",
        "#ffb347",
        "#8dd3c7",
        "#80b1d3",
        "#bebada",
        "#fb8072",
        "#b3de69",
        "#fccde5",
        "#bc80bd",
    ]
    total = sum(amount for _, amount in items) or 1
    center_x = 220
    center_y = 220
    outer_radius = 150
    inner_radius = 82
    svg_width = 440
    svg_height = 440

    segments = []
    legends = []
    labels = []
    current_angle = -math.pi / 2
    non_zero_items = [(category, amount) for category, amount in items if amount > 0]
    highest_category, highest_amount = max(non_zero_items, key=lambda item: item[1])
    lowest_category, lowest_amount = min(non_zero_items, key=lambda item: item[1])
    for index, (category, amount) in enumerate(items):
        fraction = amount / total if amount > 0 else 0
        color = colors[index % len(colors)]
        percent = (fraction * 100) if amount > 0 else 0
        if amount > 0:
            sweep = fraction * 2 * math.pi
            start_angle = current_angle
            end_angle = current_angle + sweep
            mid_angle = start_angle + (sweep / 2)
            label_radius = (outer_radius + inner_radius) / 2
            label_x = center_x + label_radius * math.cos(mid_angle)
            label_y = center_y + label_radius * math.sin(mid_angle)
            path = donut_segment_path(
                center_x,
                center_y,
                outer_radius,
                inner_radius,
                start_angle,
                end_angle,
            )
            segments.append(
                f"""
                <path
                    class="donut-segment"
                    d="{path}"
                    fill="{color}"
                    style="animation-delay:{index * 0.08:.2f}s;"
                />
                """
            )
            font_size = 12 if percent >= 8 else 10
            labels.append(
                f"""
                <text x="{label_x:.2f}" y="{label_y:.2f}" text-anchor="middle" dominant-baseline="middle" font-size="{font_size}" font-weight="700" fill="#ffffff">
                    {percent:.1f}%
                </text>
                """
            )
            current_angle = end_angle
        legends.append(
            f'<span><span class="legend-dot" style="background:{color};"></span>{esc(category)} - <strong style="color:{color}; margin-left:6px;">{money(amount)}</strong></span>'
        )

    return f"""
    <div class="donut-layout">
        <div class="chart-wrap">
            <svg viewBox="0 0 {svg_width} {svg_height}" role="img" aria-label="Expense category donut chart">
                <circle class="donut-track" cx="{center_x}" cy="{center_y}" r="{outer_radius}" fill="none" stroke="#d9e3ee" stroke-width="{outer_radius - inner_radius}" />
                {''.join(segments)}
                {''.join(labels)}
                <circle cx="{center_x}" cy="{center_y}" r="{inner_radius}" fill="#ffffff" />
                <text x="{center_x}" y="{center_y + 6}" text-anchor="middle" font-size="18" fill="#526072">Expense</text>
            </svg>
        </div>
        <div class="chart-legend">
            {''.join(legends)}
        </div>
    </div>
    <div class="chart-meta">
        <div class="meta-pill">
            <strong>Total</strong>
            <div>{money(total)}</div>
        </div>
    </div>
    <div class="chart-meta">
        <div class="meta-pill">
            <strong>High Category</strong>
            <div>{esc(highest_category)} - {money(highest_amount)}</div>
        </div>
        <div class="meta-pill">
            <strong>Lower Category</strong>
            <div>{esc(lowest_category)} - {money(lowest_amount)}</div>
        </div>
    </div>
    """


def render_daily_line_chart(by_day: dict[str, float]) -> str:
    if not by_day:
        return '<div class="empty">No data available for the graph yet.</div>'

    items = list(by_day.items())
    max_value = max(amount for _, amount in items) or 1
    width = 860
    height = 340
    left_pad = 50
    right_pad = 20
    top_pad = 25
    bottom_pad = 60
    usable_width = width - left_pad - right_pad
    usable_height = height - top_pad - bottom_pad
    step = usable_width / max(1, len(items) - 1)

    points = []
    labels = []
    for index, (day, amount) in enumerate(items):
        x = left_pad + (step * index if len(items) > 1 else usable_width / 2)
        y = top_pad + usable_height - ((amount / max_value) * usable_height)
        points.append(f"{x},{y}")
        labels.append(
            f"""
            <circle cx="{x}" cy="{y}" r="5" fill="#17517f" />
            <text x="{x}" y="{height - 20}" text-anchor="middle" font-size="12" fill="#526072">{esc(day[-2:])}</text>
            """
        )

    return f"""
    <div class="chart-wrap">
        <svg viewBox="0 0 {width} {height}" role="img" aria-label="Daily expense trend graph">
            <line x1="{left_pad}" y1="{top_pad + usable_height}" x2="{width - right_pad}" y2="{top_pad + usable_height}" stroke="#cfd8e3" stroke-width="2" />
            <polyline fill="none" stroke="#17517f" stroke-width="4" points="{' '.join(points)}" />
            {''.join(labels)}
        </svg>
    </div>
    """


def render_auth_page(message: str = "", lang: str = "en", theme: str = "light") -> str:
    flash_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Login | Living Expenses Tracker</title>
    <style>{CSS}</style>
</head>
<body class="{esc(theme)}">
    <main class="page">
        {render_top_nav(lang=lang)}
        {flash_html}
        <section class="hero">
            <div class="hero-card">
                <div class="eyebrow">{esc(t(lang, "private_expense_dashboard"))}</div>
                <h1>{esc(t(lang, "expenses_tracker"))}</h1>
            </div>
        </section>
    </main>
</body>
</html>
"""


def render_register_page(message: str = "", lang: str = "en", theme: str = "light") -> str:
    flash_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Register | Living Expenses Tracker</title>
    <style>{CSS}</style>
</head>
<body class="{esc(theme)}">
    <main class="page">
        {render_top_nav(lang=lang)}
        {flash_html}
        <section class="hero">
            <div class="hero-card">
                <div class="eyebrow">{esc(t(lang, "create_account"))}</div>
                <h1>{esc(t(lang, "register"))}</h1>
                <p>Fill in your details to create a personal account for the living-expenses tracker.</p>
                <p><a href="/login">{esc(t(lang, "already_have_account"))}</a></p>
            </div>
            <section class="panel">
                <h2>{esc(t(lang, "registration_details"))}</h2>
                <form method="post" action="/register">
                    <div class="form-grid">
                        <div class="field-full">
                            <label for="register_full_name">{esc(t(lang, "full_name"))}</label>
                            <input id="register_full_name" name="full_name" type="text" minlength="3" required>
                        </div>
                        <div>
                            <label for="register_mobile_number">{esc(t(lang, "mobile_number"))}</label>
                            <input id="register_mobile_number" name="mobile_number" type="tel" required>
                        </div>
                        <div>
                            <label for="register_email">{esc(t(lang, "email_id"))}</label>
                            <input id="register_email" name="email" type="email" required>
                        </div>
                        <div>
                            <label for="register_date_of_birth">{esc(t(lang, "date_of_birth"))}</label>
                            <input id="register_date_of_birth" name="date_of_birth" type="date" required>
                        </div>
                        <div>
                            <label for="register_username">{esc(t(lang, "username"))}</label>
                            <input id="register_username" name="username" type="text" minlength="3" required>
                        </div>
                        <div>
                            <label for="register_password">{esc(t(lang, "password"))}</label>
                            <input id="register_password" name="password" type="password" minlength="6" required>
                        </div>
                        <div>
                            <label for="register_confirm_password">{esc(t(lang, "confirm_password"))}</label>
                            <input id="register_confirm_password" name="confirm_password" type="password" minlength="6" required>
                        </div>
                        <div class="field-full">
                            <button type="submit">{esc(t(lang, "register"))}</button>
                        </div>
                    </div>
                </form>
            </section>
        </section>
    </main>
</body>
</html>
"""


def render_login_page(message: str = "", lang: str = "en", theme: str = "light") -> str:
    flash_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Login | Living Expenses Tracker</title>
    <style>{CSS}</style>
</head>
<body class="{esc(theme)}">
    <main class="page">
        {render_top_nav(lang=lang)}
        {flash_html}
        <section class="hero">
            <div class="hero-card">
                <div class="eyebrow">{esc(t(lang, "welcome_back"))}</div>
                <h1>{esc(t(lang, "login"))}</h1>
                <p>Enter your username and password to open your dashboard.</p>
                <p><a href="/register">{esc(t(lang, "need_account"))}</a></p>
            </div>
            <section class="panel">
                <h2>{esc(t(lang, "login_details"))}</h2>
                <form method="post" action="/login">
                    <div class="form-grid">
                        <div class="field-full">
                            <label for="login_username">{esc(t(lang, "username"))}</label>
                            <input id="login_username" name="username" type="text" required>
                        </div>
                        <div class="field-full">
                            <label for="login_password">{esc(t(lang, "password"))}</label>
                            <input id="login_password" name="password" type="password" required>
                        </div>
                        <div class="field-full">
                            <button type="submit">{esc(t(lang, "login"))}</button>
                        </div>
                    </div>
                </form>
                <p class="muted" style="margin-top: 12px;">
                    {esc(t(lang, "forgot_password"))}?
                    <a href="/forgot-password">{esc(t(lang, "reset_password"))}</a>
                </p>
            </section>
        </section>
    </main>
</body>
</html>
"""


def render_forgot_password_page(message: str = "", lang: str = "en", theme: str = "light") -> str:
    flash_html = f'<div class="flash">{esc(message)}</div>' if message else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Forgot Password | Living Expenses Tracker</title>
    <style>{CSS}</style>
</head>
<body class="{esc(theme)}">
    <main class="page">
        {render_top_nav(lang=lang)}
        {flash_html}
        <section class="hero">
            <div class="hero-card">
                <div class="eyebrow">{esc(t(lang, "forgot_password"))}</div>
                <h1>{esc(t(lang, "reset_password_title"))}</h1>
                <p>{esc(t(lang, "forgot_password_help"))}</p>
                <p><a href="/">{esc(t(lang, "back_to_login"))}</a></p>
            </div>
            <div class="panel">
                <h2>{esc(t(lang, "reset_password"))}</h2>
                <form method="post" action="/forgot-password">
                    <div class="form-grid">
                        <div class="field-full">
                            <label for="forgot_username">{esc(t(lang, "username"))}</label>
                            <input id="forgot_username" name="username" type="text" required>
                        </div>
                        <div class="field-full">
                            <label for="forgot_email">{esc(t(lang, "email_id"))}</label>
                            <input id="forgot_email" name="email" type="email" required>
                        </div>
                        <div class="field-full">
                            <label for="forgot_date_of_birth">{esc(t(lang, "date_of_birth"))}</label>
                            <input id="forgot_date_of_birth" name="date_of_birth" type="date" required>
                        </div>
                        <div>
                            <label for="forgot_new_password">{esc(t(lang, "password"))}</label>
                            <input id="forgot_new_password" name="new_password" type="password" minlength="6" required>
                        </div>
                        <div>
                            <label for="forgot_confirm_password">{esc(t(lang, "confirm_password"))}</label>
                            <input id="forgot_confirm_password" name="confirm_password" type="password" minlength="6" required>
                        </div>
                        <div class="field-full">
                            <button type="submit">{esc(t(lang, "reset_password"))}</button>
                        </div>
                    </div>
                </form>
            </div>
        </section>
    </main>
</body>
</html>
"""


def render_dashboard(username: str, month: str, flash_message: str = "") -> str:
    context = get_month_context(username, month)
    profile = get_user_profile(username) or {}
    prefs = get_user_preferences(username)
    lang = prefs["language"]
    theme = prefs["theme"]
    display_name = profile.get("full_name") or username
    month_input = esc(context["month"])
    flash_html = f'<div class="flash">{esc(flash_message)}</div>' if flash_message else ""

    category_options = []
    category_options.append(f'<option value="{esc(AUTO_CATEGORY_LABEL)}">{esc(t(lang, "auto_detect"))}</option>')
    for category in DEFAULT_CATEGORIES:
        category_options.append(f'<option value="{esc(category)}">{esc(category)}</option>')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Living Expenses Tracker</title>
    <style>{CSS}</style>
</head>
<body class="{esc(theme)}">
    <main class="page">
        {render_top_nav(context["month"], True, lang)}
        {flash_html}
        <section class="hero">
            <div class="hero-card">
                <div class="eyebrow">{esc(t(lang, "living_expenses_tracker"))}</div>
                <h1>{esc(display_name)}</h1>
                <p>Keep rent, groceries, transport, and everyday spending in one place with a clean local dashboard.</p>
                <form class="month-picker" method="get" action="/">
                    <div>
                        <label for="month">{esc(t(lang, "current_month"))}</label>
                        <input id="month" name="month" type="month" value="{month_input}">
                    </div>
                    <div>
                        <button type="submit">{esc(t(lang, "view_month"))}</button>
                    </div>
                </form>
                <div class="budget-progress">
                    <div class="status-row">
                        <strong>{esc(t(lang, "budget_vs_reality"))}</strong>
                        <span class="status-badge {context['budget_status']['class_name']}">{esc(context['budget_status']['label'])}</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill {context['budget_status']['progress_class']}" style="width:{context['budget_status']['progress_percent']:.1f}%"></div>
                    </div>
                    <p class="muted">{esc(context['budget_status']['message'])}</p>
                </div>
            </div>
            <div class="stats">
                <div class="stat spent">
                    <strong>{esc(t(lang, "total_spent"))}</strong>
                    <span>{render_stat_amount(context["total_spent"])}</span>
                    <div>All recorded expenses for {month_input}</div>
                </div>
                <div class="stat budget">
                    <strong>{esc(t(lang, "budget"))}</strong>
                    <span>{render_stat_amount(context["budget"])}</span>
                    <div>Target limit for the selected month</div>
                </div>
                <div class="stat remain">
                    <strong>{esc(t(lang, "remaining"))}</strong>
                    <span>{render_stat_amount(context["remaining"])}</span>
                    <div>Budget left after current expenses</div>
                </div>
            </div>
        </section>

        <section class="grid">
            <section class="panel">
                <h2>{esc(t(lang, "add_expense"))}</h2>
                <form method="post" action="/expenses">
                    <div class="form-grid">
                        <div>
                            <label for="amount">{esc(t(lang, "amount"))}</label>
                            <input id="amount" name="amount" type="number" step="0.01" min="0" required>
                        </div>
                        <div>
                            <label for="category">{esc(t(lang, "category"))}</label>
                            <select id="category" name="category">
                                {''.join(category_options)}
                            </select>
                        </div>
                        <div>
                            <label for="expense_date">{esc(t(lang, "date"))}</label>
                            <input id="expense_date" name="expense_date" type="date" value="{esc(datetime.now().strftime('%Y-%m-%d'))}" required>
                        </div>
                        <div class="field-full">
                            <label for="note">{esc(t(lang, "note"))}</label>
                            <input id="note" name="note" type="text" maxlength="120" placeholder="Swiggy order, Uber ride, electricity bill...">
                        </div>
                        <input type="hidden" name="month" value="{month_input}">
                        <div class="field-full">
                            <button type="submit">{esc(t(lang, "save_expense"))}</button>
                        </div>
                    </div>
                </form>
                <div class="chip-list">
                    {''.join(f'<span class="chip">{esc(category)}</span>' for category in DEFAULT_CATEGORIES)}
                </div>
            </section>

            <section class="panel">
                <h2>{esc(t(lang, "set_monthly_budget"))}</h2>
                <p class="muted">Update the spending target for this month and instantly see what remains.</p>
                <form method="post" action="/budget">
                    <div class="form-grid">
                        <div>
                            <label for="budget_month">{esc(t(lang, "month"))}</label>
                            <input id="budget_month" name="month" type="month" value="{month_input}" required>
                        </div>
                        <div>
                            <label for="budget_amount">{esc(t(lang, "budget_amount"))}</label>
                            <input id="budget_amount" name="amount" type="number" step="0.01" min="0" required>
                        </div>
                        <div class="field-full">
                            <button type="submit">{esc(t(lang, "save_budget"))}</button>
                        </div>
                    </div>
                </form>
            </section>
        </section>

        <section class="grid">
            <section class="panel">
                <h2>{esc(t(lang, "smart_insights"))}</h2>
                <div class="insight-list">
                    {''.join(f'<div class="insight-card">{esc(insight)}</div>' for insight in context["insights"])}
                </div>
            </section>

            <section class="panel goal-card">
                <h2>{esc(t(lang, "savings_goal"))}</h2>
                <form method="post" action="/goal">
                    <div class="form-grid">
                        <div class="field-full">
                            <label for="goal_title">{esc(t(lang, "goal_name"))}</label>
                            <input id="goal_title" name="title" type="text" placeholder="Buy phone, emergency fund..." required>
                        </div>
                        <div>
                            <label for="goal_target_amount">{esc(t(lang, "target_amount"))}</label>
                            <input id="goal_target_amount" name="target_amount" type="number" step="0.01" min="0" required>
                        </div>
                        <div>
                            <label for="goal_saved_amount">{esc(t(lang, "saved_amount"))}</label>
                            <input id="goal_saved_amount" name="saved_amount" type="number" step="0.01" min="0" required>
                        </div>
                        <input type="hidden" name="month" value="{month_input}">
                        <div class="field-full">
                            <button type="submit">{esc(t(lang, "save_goal"))}</button>
                        </div>
                    </div>
                </form>
                <p class="muted" style="margin-top:12px;">Add another saving goal any time to track multiple targets.</p>
                {render_goal_panel(context["savings_goals"])}
            </section>
        </section>

    </main>
</body>
</html>
"""


def render_category_summary_page(username: str, month: str, flash_message: str = "") -> str:
    context = get_month_context(username, month)
    prefs = get_user_preferences(username)
    flash_html = f'<div class="flash">{esc(flash_message)}</div>' if flash_message else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Category Summary</title>
    <style>{CSS}</style>
</head>
<body class="{esc(prefs['theme'])}">
    <main class="page">
        {render_top_nav(month, True, prefs['language'])}
        {flash_html}
        {render_detail_header(f"Category Summary - {month}", month)}
        <section class="panel">
            <h2>Category Summary</h2>
            <div class="category-summary">
                {render_summary_pills(context["by_category"])}
            </div>
        </section>
    </main>
</body>
</html>
"""


def render_expenses_page(username: str, month: str, flash_message: str = "") -> str:
    context = get_month_context(username, month)
    prefs = get_user_preferences(username)
    flash_html = f'<div class="flash">{esc(flash_message)}</div>' if flash_message else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Expenses</title>
    <style>{CSS}</style>
</head>
<body class="{esc(prefs['theme'])}">
    <main class="page">
        {render_top_nav(month, True, prefs['language'])}
        {flash_html}
        {render_detail_header(f"Expenses for {month}", month)}
        <section class="table-card">
            <h2>Expenses for {esc(month)}</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Category</th>
                        <th>Amount</th>
                        <th>Note</th>
                    </tr>
                </thead>
                <tbody>
                    {render_expense_rows(context["expenses"])}
                </tbody>
            </table>
        </section>
    </main>
</body>
</html>
"""


def render_real_time_data_page(username: str, month: str, flash_message: str = "") -> str:
    context = get_month_context(username, month)
    prefs = get_user_preferences(username)
    flash_html = f'<div class="flash">{esc(flash_message)}</div>' if flash_message else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Real-Time Data</title>
    <style>{CSS}</style>
</head>
<body class="{esc(prefs['theme'])}">
    <main class="page">
        {render_top_nav(month, True, prefs['language'])}
        {flash_html}
        {render_detail_header(f"Real-Time Data - {month}", month)}
        <section class="chart-card panel">
            <h2>Real-Time Expenses Bar Chart</h2>
            <p class="muted">Category-wise spending for {esc(month)}.</p>
            {render_category_bar_chart(context["by_category"])}
        </section>
    </main>
</body>
</html>
"""


def render_profile_page(username: str, month: str, flash_message: str = "") -> str:
    profile = get_user_profile(username) or {}
    prefs = get_user_preferences(username)
    lang = prefs["language"]
    theme = prefs["theme"]
    flash_html = f'<div class="flash">{esc(flash_message)}</div>' if flash_message else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{esc(t(lang, "profile"))}</title>
    <style>{CSS}</style>
</head>
<body class="{esc(theme)}">
    <main class="page">
        {render_top_nav(month, True, lang)}
        {flash_html}
        {render_detail_header(t(lang, "profile"), month)}
        <section class="grid">
            <section class="panel">
                <h2>{esc(t(lang, "personal_details"))}</h2>
                <div class="goal-summary">
                    <div class="goal-metric">
                        <strong>{esc(t(lang, "full_name"))}</strong>
                        <div>{esc(profile.get("full_name", username))}</div>
                    </div>
                    <div class="goal-metric">
                        <strong>{esc(t(lang, "mobile_number"))}</strong>
                        <div>{esc(profile.get("mobile_number", "-"))}</div>
                    </div>
                    <div class="goal-metric">
                        <strong>{esc(t(lang, "email_id"))}</strong>
                        <div>{esc(profile.get("email", "-"))}</div>
                    </div>
                    <div class="goal-metric">
                        <strong>{esc(t(lang, "date_of_birth"))}</strong>
                        <div>{esc(profile.get("date_of_birth", "-"))}</div>
                    </div>
                    <div class="goal-metric">
                        <strong>{esc(t(lang, "username"))}</strong>
                        <div>{esc(username)}</div>
                    </div>
                </div>
            </section>

            <section class="panel">
                <h2>{esc(t(lang, "settings"))}</h2>
                <form method="post" action="/preferences">
                    <div class="form-grid">
                        <div>
                            <label for="language">{esc(t(lang, "language"))}</label>
                            <select id="language" name="language">
                                <option value="en"{" selected" if lang == "en" else ""}>English</option>
                                <option value="hi"{" selected" if lang == "hi" else ""}>Hindi</option>
                            </select>
                        </div>
                        <div>
                            <label for="theme">{esc(t(lang, "theme"))}</label>
                            <select id="theme" name="theme">
                                <option value="light"{" selected" if theme == "light" else ""}>{esc(t(lang, "light_mode"))}</option>
                                <option value="dark"{" selected" if theme == "dark" else ""}>{esc(t(lang, "dark_mode"))}</option>
                            </select>
                        </div>
                        <input type="hidden" name="month" value="{esc(month)}">
                        <div class="field-full">
                            <button type="submit">{esc(t(lang, "save_preferences"))}</button>
                        </div>
                    </div>
                </form>

                <h2 style="margin-top:24px;">{esc(t(lang, "account_actions"))}</h2>
                <form method="post" action="/logout">
                    <button type="submit">{esc(t(lang, "logout"))}</button>
                </form>
            </section>
        </section>
    </main>
</body>
</html>
"""


