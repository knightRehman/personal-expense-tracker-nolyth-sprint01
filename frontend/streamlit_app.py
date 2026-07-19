"""
Streamlit frontend for the Personal Expense Tracker.

This is a thin client: every piece of data comes from the FastAPI backend
over HTTP. No business logic or persistence happens here — the UI's job is
to collect input, call the API, and render the response.

Run:
    streamlit run streamlit_app.py

Make sure the backend is already running (default: http://127.0.0.1:8000).
"""
import os
from datetime import date

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def auth_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path, **kwargs):
    return requests.get(f"{API_URL}{path}", headers=auth_headers(), **kwargs)


def api_post(path, **kwargs):
    return requests.post(f"{API_URL}{path}", headers=auth_headers(), **kwargs)


def api_put(path, **kwargs):
    return requests.put(f"{API_URL}{path}", headers=auth_headers(), **kwargs)


def api_delete(path, **kwargs):
    return requests.delete(f"{API_URL}{path}", headers=auth_headers(), **kwargs)


def show_api_error(response):
    """Translate a non-2xx FastAPI response into a readable Streamlit error."""
    try:
        body = response.json()

        # Our custom validation handler (see backend/app/main.py) returns:
        # {"detail": "Validation failed.", "errors": [{"field": ..., "message": ...}]}
        if isinstance(body, dict) and "errors" in body and isinstance(body["errors"], list):
            for err in body["errors"]:
                field = err.get("field", "")
                message = err.get("message", err)
                st.error(f"{field}: {message}" if field else str(message))
            return

        detail = body.get("detail", body) if isinstance(body, dict) else body
        if isinstance(detail, list):  # FastAPI's default validation error shape
            for err in detail:
                st.error(f"{err.get('field', '')}: {err.get('message', err)}")
        else:
            st.error(str(detail))
    except ValueError:
        st.error(f"Request failed ({response.status_code}).")


def backend_reachable():
    try:
        requests.get(f"{API_URL}/", timeout=3)
        return True
    except requests.exceptions.ConnectionError:
        return False


if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.username = None


# ---------------------------------------------------------------------------
# Sidebar: connection status + auth
# ---------------------------------------------------------------------------

st.sidebar.title("💸 Expense Tracker")

if not backend_reachable():
    st.sidebar.error(f"Cannot reach the API at {API_URL}. Start the backend first.")
    st.error(
        f"⚠️ Backend not reachable at **{API_URL}**.\n\n"
        "Run this in another terminal:\n\n"
        "```\ncd backend\nuvicorn app.main:app --reload\n```"
    )
    st.stop()

if st.session_state.token is None:
    st.sidebar.subheader("Log in or register")
    tab_login, tab_register = st.sidebar.tabs(["Log in", "Register"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in")
            if submitted:
                resp = api_post("/auth/login", data={"username": username, "password": password})
                if resp.status_code == 200:
                    st.session_state.token = resp.json()["access_token"]
                    st.session_state.username = username
                    st.rerun()
                else:
                    show_api_error(resp)

    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username", key="reg_username")
            new_password = st.text_input(
                "Choose a password (min 6 characters)", type="password", key="reg_password"
            )
            submitted = st.form_submit_button("Create account")
            if submitted:
                resp = api_post(
                    "/auth/register", json={"username": new_username, "password": new_password}
                )
                if resp.status_code == 201:
                    st.success("Account created! Switch to the Log in tab.")
                else:
                    show_api_error(resp)

    st.info("👋 Log in or register in the sidebar to start tracking expenses.")
    st.stop()

# Logged in from here on
st.sidebar.success(f"Logged in as **{st.session_state.username}**")
if st.sidebar.button("Log out"):
    st.session_state.token = None
    st.session_state.username = None
    st.rerun()


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.title("Personal Expense Tracker")

tab_expenses, tab_categories, tab_summary = st.tabs(["📋 Expenses", "🏷️ Categories", "📊 Summary"])

# ---- Categories tab (loaded first since expenses form depends on it) ----

with tab_categories:
    st.subheader("Your categories")

    with st.form("add_category_form", clear_on_submit=True):
        cat_name = st.text_input("New category name")
        add_cat = st.form_submit_button("Add category")
        if add_cat:
            if not cat_name.strip():
                st.warning("Category name can't be empty.")
            else:
                resp = api_post("/categories/", json={"name": cat_name.strip()})
                if resp.status_code == 201:
                    st.success(f"Added category '{cat_name}'.")
                    st.rerun()
                else:
                    show_api_error(resp)

    cat_resp = api_get("/categories/")
    categories = cat_resp.json() if cat_resp.status_code == 200 else []

    if not categories:
        st.info("No categories yet. Add one above to get started.")
    else:
        for cat in categories:
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{cat['name']}**")
            if col2.button("Delete", key=f"del_cat_{cat['id']}"):
                del_resp = api_delete(f"/categories/{cat['id']}")
                if del_resp.status_code == 204:
                    st.success(f"Deleted '{cat['name']}'.")
                    st.rerun()
                else:
                    show_api_error(del_resp)

# ---- Expenses tab ----

with tab_expenses:
    st.subheader("Add an expense")

    if not categories:
        st.warning("Create a category first (see the Categories tab).")
    else:
        cat_lookup = {c["name"]: c["id"] for c in categories}
        with st.form("add_expense_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            amount = col1.number_input("Amount", min_value=0.01, step=0.5, format="%.2f")
            cat_name = col2.selectbox("Category", options=list(cat_lookup.keys()))
            exp_date = col3.date_input("Date", value=date.today())
            description = st.text_input("Description (optional)")
            submitted = st.form_submit_button("Add expense")
            if submitted:
                resp = api_post(
                    "/expenses/",
                    json={
                        "amount": amount,
                        "description": description or None,
                        "date": str(exp_date),
                        "category_id": cat_lookup[cat_name],
                    },
                )
                if resp.status_code == 201:
                    st.success("Expense added.")
                    st.rerun()
                else:
                    show_api_error(resp)

    st.divider()
    st.subheader("Your expenses")

    filter_col1, filter_col2 = st.columns(2)
    filter_cat = filter_col1.selectbox(
        "Filter by category", options=["All"] + [c["name"] for c in categories]
    )
    params = {}
    if filter_cat != "All":
        params["category_id"] = next(c["id"] for c in categories if c["name"] == filter_cat)

    exp_resp = api_get("/expenses/", params=params)
    if exp_resp.status_code == 200:
        expenses = exp_resp.json()
        if not expenses:
            st.info("No expenses recorded yet.")
        else:
            df = pd.DataFrame(
                [
                    {
                        "id": e["id"],
                        "Date": e["date"],
                        "Category": e["category"]["name"],
                        "Amount": e["amount"],
                        "Description": e["description"] or "",
                    }
                    for e in expenses
                ]
            )
            st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)

            with st.expander("Delete an expense"):
                options = {f"#{e['id']} — {e['category']['name']} — {e['amount']}": e["id"] for e in expenses}
                choice = st.selectbox("Select expense to delete", options=list(options.keys()))
                if st.button("Delete selected expense"):
                    del_resp = api_delete(f"/expenses/{options[choice]}")
                    if del_resp.status_code == 204:
                        st.success("Expense deleted.")
                        st.rerun()
                    else:
                        show_api_error(del_resp)
    else:
        show_api_error(exp_resp)

# ---- Summary tab ----

with tab_summary:
    st.subheader("Spending summary")
    sum_resp = api_get("/expenses/summary")
    if sum_resp.status_code == 200:
        summary = sum_resp.json()
        st.metric("Total spent", f"{summary['total_spent']:.2f}")
        if summary["by_category"]:
            df = pd.DataFrame(summary["by_category"]).rename(
                columns={"category": "Category", "total": "Total", "count": "# Expenses"}
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.bar_chart(df.set_index("Category")["Total"])
        else:
            st.info("No expenses yet — nothing to summarize.")
    else:
        show_api_error(sum_resp)
