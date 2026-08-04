import secrets
from datetime import datetime
from http import cookies
from urllib.parse import parse_qs

from .config import SESSION_COOKIE, SESSIONS
from .services import (
    add_expense,
    authenticate_user,
    init_store,
    parse_amount,
    register_user,
    reset_password,
    set_budget,
    set_savings_goal,
    set_user_preferences,
    validate_date,
    validate_month,
    get_user_preferences,
)
from .views import (
    render_auth_page,
    render_category_summary_page,
    render_expenses_page,
    render_forgot_password_page,
    render_login_page,
    render_dashboard,
    render_profile_page,
    render_real_time_data_page,
    render_register_page,
)


def read_form_data(environ: dict) -> dict[str, str]:
    try:
        size = int(environ.get("CONTENT_LENGTH", "0") or "0")
    except ValueError:
        size = 0
    body = environ["wsgi.input"].read(size).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[0] for key, values in parsed.items()}


def redirect(location: str, start_response) -> list[bytes]:
    start_response("303 See Other", [("Location", location)])
    return [b""]


def redirect_with_cookie(location: str, cookie_value: str, start_response) -> list[bytes]:
    start_response("303 See Other", [("Location", location), ("Set-Cookie", cookie_value)])
    return [b""]


def build_session_cookie(session_id: str) -> str:
    morsel = cookies.SimpleCookie()
    morsel[SESSION_COOKIE] = session_id
    morsel[SESSION_COOKIE]["path"] = "/"
    morsel[SESSION_COOKIE]["httponly"] = True
    morsel[SESSION_COOKIE]["samesite"] = "Lax"
    return morsel.output(header="").strip()


def clear_session_cookie() -> str:
    morsel = cookies.SimpleCookie()
    morsel[SESSION_COOKIE] = ""
    morsel[SESSION_COOKIE]["path"] = "/"
    morsel[SESSION_COOKIE]["expires"] = "Thu, 01 Jan 1970 00:00:00 GMT"
    morsel[SESSION_COOKIE]["max-age"] = 0
    return morsel.output(header="").strip()


def get_current_user(environ) -> str | None:
    raw_cookie = environ.get("HTTP_COOKIE", "")
    if not raw_cookie:
        return None
    jar = cookies.SimpleCookie()
    jar.load(raw_cookie)
    session_cookie = jar.get(SESSION_COOKIE)
    if not session_cookie:
        return None
    return SESSIONS.get(session_cookie.value)


def create_session(username: str) -> str:
    session_id = secrets.token_urlsafe(24)
    SESSIONS[session_id] = username
    return session_id


def handle_register(form_data: dict[str, str], start_response) -> list[bytes]:
    success, result = register_user(
        form_data.get("full_name", ""),
        form_data.get("mobile_number", ""),
        form_data.get("email", ""),
        form_data.get("date_of_birth", ""),
        form_data.get("username", ""),
        form_data.get("password", ""),
        form_data.get("confirm_password", ""),
    )
    if not success:
        return redirect(f"/register?message={result.replace(' ', '+')}", start_response)

    session_id = create_session(result)
    current_month = datetime.now().strftime("%Y-%m")
    return redirect_with_cookie(
        f"/?month={current_month}&message=Welcome",
        build_session_cookie(session_id),
        start_response,
    )


def handle_login(form_data: dict[str, str], start_response) -> list[bytes]:
    username = form_data.get("username", "").strip().lower()
    password = form_data.get("password", "")
    if not authenticate_user(username, password):
        return redirect("/login?message=Invalid+username+or+password", start_response)

    session_id = create_session(username)
    current_month = datetime.now().strftime("%Y-%m")
    return redirect_with_cookie(
        f"/?month={current_month}&message=Welcome",
        build_session_cookie(session_id),
        start_response,
    )


def handle_forgot_password(form_data: dict[str, str], start_response) -> list[bytes]:
    success, result = reset_password(
        form_data.get("username", ""),
        form_data.get("email", ""),
        form_data.get("date_of_birth", ""),
        form_data.get("new_password", ""),
        form_data.get("confirm_password", ""),
    )
    if not success:
        return redirect(f"/forgot-password?message={result.replace(' ', '+')}", start_response)
    return redirect(f"/?message=Password+reset+successful+for+{result}", start_response)


def handle_add_expense(username: str, form_data: dict[str, str], start_response) -> list[bytes]:
    selected_month = form_data.get("month") or datetime.now().strftime("%Y-%m")
    try:
        amount = parse_amount(form_data["amount"])
        category = form_data["category"]
        note = form_data.get("note", "")
        expense_date = validate_date(form_data["expense_date"])
        add_expense(username, amount, category, note, expense_date)
        return redirect(f"/?month={selected_month}&message=Expense saved", start_response)
    except (KeyError, ValueError):
        return redirect(f"/?month={selected_month}&message=Please enter a valid expense", start_response)


def handle_set_budget(username: str, form_data: dict[str, str], start_response) -> list[bytes]:
    selected_month = form_data.get("month") or datetime.now().strftime("%Y-%m")
    try:
        month = validate_month(form_data["month"])
        amount = parse_amount(form_data["amount"])
        set_budget(username, month, amount)
        return redirect(f"/?month={month}&message=Budget updated", start_response)
    except (KeyError, ValueError):
        return redirect(f"/?month={selected_month}&message=Please enter a valid budget", start_response)


def handle_set_goal(username: str, form_data: dict[str, str], start_response) -> list[bytes]:
    selected_month = form_data.get("month") or datetime.now().strftime("%Y-%m")
    try:
        title = form_data["title"]
        target_amount = parse_amount(form_data["target_amount"])
        saved_amount = parse_amount(form_data["saved_amount"])
        set_savings_goal(username, title, target_amount, saved_amount)
        return redirect(f"/?month={selected_month}&message=Savings goal updated", start_response)
    except (KeyError, ValueError):
        return redirect(f"/?month={selected_month}&message=Please enter a valid savings goal", start_response)


def handle_set_preferences(username: str, form_data: dict[str, str], start_response) -> list[bytes]:
    selected_month = form_data.get("month") or datetime.now().strftime("%Y-%m")
    set_user_preferences(
        username,
        form_data.get("theme", "light"),
        form_data.get("language", "en"),
    )
    return redirect(f"/?month={selected_month}&message=Preferences updated", start_response)


def application(environ, start_response):
    init_store()
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET").upper()
    current_user = get_current_user(environ)
    public_lang = "en"
    public_theme = "light"
    if current_user:
        prefs = get_user_preferences(current_user)
        public_lang = prefs["language"]
        public_theme = prefs["theme"]

    if path == "/" and method == "GET":
        params = parse_qs(environ.get("QUERY_STRING", ""))
        message = params.get("message", [""])[0].replace("+", " ")
        if not current_user:
            body = render_auth_page(message, public_lang, public_theme).encode("utf-8")
        else:
            month = params.get("month", [datetime.now().strftime("%Y-%m")])[0]
            try:
                month = validate_month(month)
            except ValueError:
                month = datetime.now().strftime("%Y-%m")
            body = render_dashboard(current_user, month, message).encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    if path == "/category-summary" and method == "GET":
        if not current_user:
            return redirect("/?message=Please+login+first", start_response)
        params = parse_qs(environ.get("QUERY_STRING", ""))
        month = params.get("month", [datetime.now().strftime("%Y-%m")])[0]
        message = params.get("message", [""])[0].replace("+", " ")
        try:
            month = validate_month(month)
        except ValueError:
            month = datetime.now().strftime("%Y-%m")
        body = render_category_summary_page(current_user, month, message).encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    if path == "/expenses-list" and method == "GET":
        if not current_user:
            return redirect("/?message=Please+login+first", start_response)
        params = parse_qs(environ.get("QUERY_STRING", ""))
        month = params.get("month", [datetime.now().strftime("%Y-%m")])[0]
        message = params.get("message", [""])[0].replace("+", " ")
        try:
            month = validate_month(month)
        except ValueError:
            month = datetime.now().strftime("%Y-%m")
        body = render_expenses_page(current_user, month, message).encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    if path == "/real-time-data" and method == "GET":
        if not current_user:
            return redirect("/?message=Please+login+first", start_response)
        params = parse_qs(environ.get("QUERY_STRING", ""))
        month = params.get("month", [datetime.now().strftime("%Y-%m")])[0]
        message = params.get("message", [""])[0].replace("+", " ")
        try:
            month = validate_month(month)
        except ValueError:
            month = datetime.now().strftime("%Y-%m")
        body = render_real_time_data_page(current_user, month, message).encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    if path == "/profile" and method == "GET":
        if not current_user:
            return redirect("/?message=Please+login+first", start_response)
        params = parse_qs(environ.get("QUERY_STRING", ""))
        month = params.get("month", [datetime.now().strftime("%Y-%m")])[0]
        message = params.get("message", [""])[0].replace("+", " ")
        try:
            month = validate_month(month)
        except ValueError:
            month = datetime.now().strftime("%Y-%m")
        body = render_profile_page(current_user, month, message).encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    if path == "/register" and method == "GET":
        params = parse_qs(environ.get("QUERY_STRING", ""))
        message = params.get("message", [""])[0].replace("+", " ")
        body = render_register_page(message, public_lang, public_theme).encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    if path == "/login" and method == "GET":
        params = parse_qs(environ.get("QUERY_STRING", ""))
        message = params.get("message", [""])[0].replace("+", " ")
        body = render_login_page(message, public_lang, public_theme).encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    if path == "/forgot-password" and method == "GET":
        params = parse_qs(environ.get("QUERY_STRING", ""))
        message = params.get("message", [""])[0].replace("+", " ")
        body = render_forgot_password_page(message, public_lang, public_theme).encode("utf-8")
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
        return [body]

    if path == "/register" and method == "POST":
        form_data = read_form_data(environ)
        return handle_register(form_data, start_response)

    if path == "/login" and method == "POST":
        form_data = read_form_data(environ)
        return handle_login(form_data, start_response)

    if path == "/forgot-password" and method == "POST":
        form_data = read_form_data(environ)
        return handle_forgot_password(form_data, start_response)

    if path == "/logout" and method == "POST":
        raw_cookie = environ.get("HTTP_COOKIE", "")
        if raw_cookie:
            jar = cookies.SimpleCookie()
            jar.load(raw_cookie)
            session_cookie = jar.get(SESSION_COOKIE)
            if session_cookie and session_cookie.value in SESSIONS:
                del SESSIONS[session_cookie.value]
        return redirect_with_cookie("/?message=Logged+out", clear_session_cookie(), start_response)

    if path == "/expenses" and method == "POST":
        if not current_user:
            return redirect("/?message=Please+login+first", start_response)
        form_data = read_form_data(environ)
        return handle_add_expense(current_user, form_data, start_response)

    if path == "/budget" and method == "POST":
        if not current_user:
            return redirect("/?message=Please+login+first", start_response)
        form_data = read_form_data(environ)
        return handle_set_budget(current_user, form_data, start_response)

    if path == "/goal" and method == "POST":
        if not current_user:
            return redirect("/?message=Please+login+first", start_response)
        form_data = read_form_data(environ)
        return handle_set_goal(current_user, form_data, start_response)

    if path == "/preferences" and method == "POST":
        if not current_user:
            return redirect("/?message=Please+login+first", start_response)
        form_data = read_form_data(environ)
        return handle_set_preferences(current_user, form_data, start_response)

    body = b"<h1>404 Not Found</h1>"
    start_response("404 Not Found", [("Content-Type", "text/html; charset=utf-8")])
    return [body]


class ExpenseTrackerApp:
    def __call__(self, environ, start_response):
        return application(environ, start_response)

    def run(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        print(f"Serving Living Expenses Tracker at http://{host}:{port}")
        with make_server(host, port, self) as server:
            server.serve_forever()


app = ExpenseTrackerApp()


