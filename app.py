import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore_v1 import FieldFilter  # Import FieldFilter for the new syntax
from collections import Counter
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
import hashlib
from PIL import Image
import time
import random
import json
import os

# 🔥 Firebase Setup
if not firebase_admin._apps:
    try:
        service_account_path = "serviceAccountKey.json"
        if os.path.exists(service_account_path):
            with open(service_account_path, "r") as f:
                cred_dict = json.load(f)
            st.info("Using local serviceAccountKey.json")
        else:
            service_account_key = st.secrets["SERVICE_ACCOUNT_KEY"]
            if isinstance(service_account_key, str):
                cred_dict = json.loads(service_account_key)
            else:
                cred_dict = dict(service_account_key)
            st.info("Using secrets from st.secrets")

        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        st.success("Firebase initialized successfully!")
    except Exception as e:
        st.error(f"Error: {str(e)}")
        raise

db = firestore.client()

# 🚀 Session State Initialization Function
def initialize_session_state():
    default_state = {
        "user": None,
        "auth_mode": "Login",
        "cart": {},
        "page": "Menu",
        "spending_limit": {"Monthly": 0, "set_month": None},
        "total_spent": 0,
        "loyalty_points": 0,
        "badges": [],
        "show_popup": False,
        "chat_history": [],
        "spending_limit_edit_count": 0,
        "spending_limit_edits_this_month": 0,
        "reviews": [],
        "diet_plan": None,
        "meal_logs": [],
        "favorites": [],
        "meal_schedule": None,
        "custom_recipes": [],
        "confirmation_dialog": None
    }
    # Overwrite all keys in session_state with defaults
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value
# Initialize session state at the start
initialize_session_state()

# Define base ingredients and their nutritional profiles (simplified)
base_ingredients = {
    "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fats": 0.3, "tags": ["gluten-free"], "cost": 15, "category": "base"},
    "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fats": 1.1, "tags": ["high-carb"], "cost": 16, "category": "base"},
    "chicken": {"calories": 165, "protein": 31, "carbs": 0, "fats": 3.6, "tags": ["high-protein"], "cost": 20, "category": "protein"},
    "mutton": {"calories": 294, "protein": 25, "carbs": 0, "fats": 20, "tags": ["high-protein"], "cost": 30, "category": "protein"},
    "wheat": {"calories": 340, "protein": 13, "carbs": 72, "fats": 2.5, "tags": ["high-carb"], "cost": 14, "category": "base"},
    "cheese": {"calories": 403, "protein": 23, "carbs": 3.1, "fats": 33, "tags": ["dairy"], "cost": 15, "category": "topping"},
    "tomato": {"calories": 18, "protein": 0.9, "carbs": 3.9, "fats": 0.2, "tags": ["vegan", "vegetarian"], "cost": 12, "category": "vegetable"},
    "pepperoni": {"calories": 504, "protein": 19, "carbs": 1.5, "fats": 46, "tags": ["low-carb"], "cost": 25, "category": "protein"},
    "basil": {"calories": 23, "protein": 3, "carbs": 2.7, "fats": 0.6, "tags": ["vegan", "vegetarian"], "cost": 13, "category": "seasoning"},
    "beef": {"calories": 250, "protein": 26, "carbs": 0, "fats": 15, "tags": ["high-protein"], "cost": 25, "category": "protein"},
    "lentils": {"calories": 116, "protein": 9, "carbs": 20, "fats": 0.4, "tags": ["vegan", "vegetarian", "high-protein", "gluten-free"], "cost": 6, "category": "protein"},
    "spinach": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fats": 0.4, "tags": ["vegan", "vegetarian", "low-carb"], "cost": 23, "category": "vegetable"},
    "paneer": {"calories": 265, "protein": 18, "carbs": 3, "fats": 20, "tags": ["vegetarian", "high-protein", "dairy"], "cost": 20, "category": "protein"},
    "potato": {"calories": 77, "protein": 2, "carbs": 17, "fats": 0.1, "tags": ["vegan", "vegetarian", "gluten-free"], "cost": 20, "category": "vegetable"},
    "salmon": {"calories": 206, "protein": 22, "carbs": 0, "fats": 13, "tags": ["high-protein", "low-carb", "keto"], "cost": 40, "category": "protein"},
    "olive_oil": {"calories": 884, "protein": 0, "carbs": 0, "fats": 100, "tags": ["vegan", "vegetarian", "keto", "low-carb"], "cost": 10, "category": "seasoning"},
    "mushrooms": {"calories": 22, "protein": 3.1, "carbs": 3.3, "fats": 0.3, "tags": ["vegan", "vegetarian", "low-carb"], "cost": 15, "category": "vegetable"}
}


menu_items = {
    "Chicken Biryani": {
        "price": 100, "image": "images/chicken_biryani.jpg", "carbon_footprint": 2.5, "calories": 800,
        "protein": 35, "carbs": 90, "fats": 25, "vitamins": {"Vitamin A": 10, "Vitamin C": 5},
        "tags": ["high-protein"], "prep_time": 45, "ingredients": ["rice", "chicken", "tomato"]
    },
    "Mutton Biryani": {
        "price": 120, "image": "images/mutton_biryani.jpg", "carbon_footprint": 3.0, "calories": 850,
        "protein": 40, "carbs": 85, "fats": 30, "vitamins": {"Vitamin A": 15, "Vitamin C": 3},
        "tags": ["high-protein"], "prep_time": 60, "ingredients": ["rice", "mutton", "tomato"]
    },
    "Pizza": {
        "price": 150, "image": "images/pizza.jpg", "carbon_footprint": 4.0, "calories": 700,
        "protein": 25, "carbs": 80, "fats": 30, "vitamins": {"Vitamin A": 20, "Vitamin C": 10},
        "tags": ["high-carb"], "prep_time": 30, "ingredients": ["wheat", "cheese", "tomato"]
    },
    "Burger": {
        "price": 60, "image": "images/burger.jpg", "carbon_footprint": 2.0, "calories": 600,
        "protein": 20, "carbs": 50, "fats": 35, "vitamins": {"Vitamin A": 5, "Vitamin C": 2},
        "tags": ["high-carb"], "prep_time": 20, "ingredients": ["wheat", "beef", "tomato"]
    },
    "Pepperoni": {
        "price": 40, "image": "images/pepperoni.jpg", "carbon_footprint": 1.5, "calories": 300,
        "protein": 15, "carbs": 5, "fats": 25, "vitamins": {"Vitamin A": 2, "Vitamin C": 1},
        "tags": ["low-carb", "keto", "high-protein"], "prep_time": 25, "ingredients": ["pepperoni"]
    },
    "Margherita": {
        "price": 90, "image": "images/margherita.jpg", "carbon_footprint": 2.0, "calories": 500,
        "protein": 15, "carbs": 60, "fats": 20, "vitamins": {"Vitamin A": 15, "Vitamin C": 12},
        "tags": ["vegetarian", "vegan", "high-carb"], "prep_time": 30, "ingredients": ["wheat", "tomato", "basil"]
    },
    "Lentil Curry": {
        "price": 80, "image": "images/lentil_curry.jpg", "carbon_footprint": 1.8, "calories": 450,
        "protein": 20, "carbs": 60, "fats": 5, "vitamins": {"Vitamin A": 8, "Vitamin C": 15},
        "tags": ["vegan", "vegetarian", "high-protein", "gluten-free"], "prep_time": 40, 
        "ingredients": ["lentils", "tomato", "spinach"]
    },
    "Paneer Tikka": {
        "price": 110, "image": "images/paneer_tikka.jpg", "carbon_footprint": 2.2, "calories": 650,
        "protein": 25, "carbs": 20, "fats": 45, "vitamins": {"Vitamin A": 12, "Vitamin C": 8},
        "tags": ["vegetarian", "high-protein", "low-carb"], "prep_time": 35, 
        "ingredients": ["paneer", "tomato", "olive_oil"]
    },
    "Salmon Grilled": {
        "price": 140, "image": "images/salmon_grilled.jpg", "carbon_footprint": 2.8, "calories": 500,
        "protein": 30, "carbs": 5, "fats": 35, "vitamins": {"Vitamin D": 80, "Vitamin B12": 50},
        "tags": ["high-protein", "low-carb", "keto"], "prep_time": 25, 
        "ingredients": ["salmon", "olive_oil", "basil"]
    },
    "Aloo Gobi": {
        "price": 70, "image": "images/aloo_gobi.jpg", "carbon_footprint": 1.5, "calories": 400,
        "protein": 8, "carbs": 60, "fats": 15, "vitamins": {"Vitamin C": 30, "Vitamin A": 5},
        "tags": ["vegan", "vegetarian", "gluten-free"], "prep_time": 30, 
        "ingredients": ["potato", "tomato", "spinach"]
    },
    "Mushroom Risotto": {
        "price": 95, "image": "images/mushroom_risotto.jpg", "carbon_footprint": 2.0, "calories": 550,
        "protein": 12, "carbs": 85, "fats": 15, "vitamins": {"Vitamin D": 10, "Vitamin B2": 15},
        "tags": ["vegetarian", "gluten-free", "high-carb"], "prep_time": 40, 
        "ingredients": ["rice", "mushrooms", "cheese"]
    }
}

# 🔐 Authentication Functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(email, password):
    try:
        users_ref = db.collection("users").where(filter=FieldFilter("email", "==", email)).stream()
        user_data = next((user.to_dict() for user in users_ref), None)
        if user_data and user_data["password"] == hash_password(password):
            st.session_state["user"] = email
            load_user_data(email, user_data)
            st.success(f"Welcome, {email}! Today's special: Spaghetti 🍝")
            st.rerun()
        else:
            st.error("Oops! No free snacks for wrong passwords! 🍕 Try again.")
    except Exception as e:
        st.error(f"Login failed: {str(e)}")

def signup(email, password):
    # Check Firestore for existing email
    users_ref = db.collection("users").where(filter=FieldFilter("email", "==", email)).stream()
    firestore_exists = any(users_ref)
    
    # Check Firebase Authentication for existing email
    auth_exists = False
    try:
        auth.get_user_by_email(email)
        auth_exists = True
    except auth.UserNotFoundError:
        auth_exists = False

    if firestore_exists and not auth_exists:
        st.error("Email already exists in Firestore but not in Authentication. Please contact support or try resetting your password.")
        return
    elif auth_exists:
        st.error("Email already exists in Authentication! Try logging in.")
        return
    elif firestore_exists:
        st.error("Email already exists in Firestore! Try logging in.")
        return

    # Proceed with signup if email doesn’t exist in either
    hashed_pw = hash_password(password)
    current_month = datetime.now().strftime("%Y-%m")
    try:
        user = auth.create_user(email=email, password=password)
        db.collection("users").add({
            "email": email,
            "password": hashed_pw,
            "loyalty_points": 0,
            "badges": [],
            "spending_limit": {"Monthly": 0, "set_month": current_month},
            "spending_limit_edit_count": 0,
            "spending_limit_edits_this_month": 0,
            "diet_plan": None,
            "meal_logs": [],
            "favorites": [],
            "meal_schedule": None,
            "custom_recipes": []
        })
        st.success("Signup successful! Please log in.")
        st.session_state["auth_mode"] = "Login"
        st.rerun()
    except Exception as e:
        st.error(f"Signup failed: {str(e)}")

def reset_password(email, new_password):
    try:
        # Check Firebase Authentication first
        user = auth.get_user_by_email(email)
        
        # Then check Firestore
        users_ref = db.collection("users").where(filter=FieldFilter("email", "==", email)).stream()
        user_doc = next((user for user in users_ref), None)
        if not user_doc:
            st.error(f"The email {email} exists in Authentication but not in our database. Please contact support.")
            return False
        
        # Update password in Authentication and Firestore
        auth.update_user(user.uid, password=new_password)
        hashed_new_pw = hash_password(new_password)
        user_doc.reference.update({"password": hashed_new_pw})
        st.success(f"Password reset successfully for {email}! You can now log in with your new password.")
        st.session_state["show_reset_form"] = False
        st.rerun()
        return True
    except auth.UserNotFoundError:
        st.error(f"No account found for {email}. Please sign up first!")
        return False
    except Exception as e:
        st.error(f"Failed to reset password: {str(e)}. Please try again.")
        return False

def load_user_data(email, user_data):
    try:
        st.session_state["loyalty_points"] = user_data.get("loyalty_points", 0)
        st.session_state["badges"] = user_data.get("badges", [])
        st.session_state["spending_limit_edit_count"] = user_data.get("spending_limit_edit_count", 0)
        st.session_state["spending_limit_edits_this_month"] = user_data.get("spending_limit_edits_this_month", 0)
        st.session_state["diet_plan"] = user_data.get("diet_plan", None)
        st.session_state["meal_logs"] = user_data.get("meal_logs", [])
        st.session_state["favorites"] = user_data.get("favorites", [])
        st.session_state["meal_schedule"] = user_data.get("meal_schedule", None)
        st.session_state["custom_recipes"] = user_data.get("custom_recipes", [])
        spending_limit_data = user_data.get("spending_limit", {"Monthly": 0, "set_month": None})
        current_month = datetime.now().strftime("%Y-%m")
        if spending_limit_data["set_month"] != current_month:
            spending_limit_data["Monthly"] = 0
            spending_limit_data["set_month"] = current_month
            st.session_state["spending_limit_edits_this_month"] = 0  
            user_ref = db.collection("users").where(filter=FieldFilter("email", "==", email)).get()
            if user_ref:
                user_ref[0].reference.update({
                    "spending_limit": spending_limit_data,
                    "spending_limit_edits_this_month": 0
                })
        st.session_state["spending_limit"] = spending_limit_data  
    except Exception as e:
        st.error(f"An error occurred while loading user data: {str(e)}")

def logout():
    st.session_state["user"] = None
    initialize_session_state()
    st.success("Logged out successfully!")
    st.rerun()

# Enhanced CSS with Material Icons and Card Styling
st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
    body {
        font-family: 'Arial', sans-serif;
        background: url('https://source.unsplash.com/1600x900/?food') no-repeat center center fixed;
        background-size: cover;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stTextInput"] input {
        border: 2px solid #FF6F61;
        border-radius: 5px;
        padding: 8px;
        background-color: #fff;
    }
    div[data-testid="stButton"] button {
        background: #FF6F61;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 16px;
        transition: background 0.3s;
    }
    div[data-testid="stButton"] button:hover {
        background: #d35400;
    }
    .card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        padding: 15px;
        margin: 10px 0;
    }
    .sidebar-header {
        background: #FF6F61;
        color: white;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    .text-light { color: #333; }
    </style>
""", unsafe_allow_html=True)

# 🛒 Order Functions
def add_to_cart(item_name, price, carbon_footprint):
    if item_name in st.session_state["cart"]:
        st.session_state["cart"][item_name]["quantity"] += 1
    else:
        st.session_state["cart"][item_name] = {"price": price, "quantity": 1, "carbon_footprint": carbon_footprint}
    st.session_state["loyalty_points"] += 1
    check_loyalty_badges()
    check_spending_limit()
    st.success(f"{item_name} added to cart! +1 Loyalty Point")

def remove_from_cart(item_name):
    if item_name in st.session_state["cart"]:
        if st.session_state["cart"][item_name]["quantity"] > 1:
            st.session_state["cart"][item_name]["quantity"] -= 1
        else:
            del st.session_state["cart"][item_name]
        st.success(f"Removed one {item_name} from cart!")
        check_spending_limit()

def place_order():
    if st.session_state["cart"]:
        total_cost = sum(item["price"] * item["quantity"] for item in st.session_state["cart"].values())
        current_monthly_spent = calculate_total_spent()  # Get current monthly total before this order
        monthly_limit = st.session_state["spending_limit"].get("Monthly", 0)

        # Check if the order would exceed the monthly spending limit
        if monthly_limit > 0 and (current_monthly_spent + total_cost) > monthly_limit:
            st.session_state["confirmation_dialog"] = {
                "action": "exceed spending limit",
                "total_cost": total_cost,
                "limit": monthly_limit
            }
            return  # Wait for user confirmation before proceeding

        # If no limit is exceeded, proceed with placing the order
        total_carbon = sum(item["carbon_footprint"] * item["quantity"] for item in st.session_state["cart"].values())
        for item, details in st.session_state["cart"].items():
            db.collection("orders").add({
                "user_id": st.session_state["user"],
                "item": item,
                "price": details["price"] * details["quantity"],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "carbon_footprint": details["carbon_footprint"] * details["quantity"]
            })
        st.session_state["cart"] = {}
        check_spending_limit()  # Recheck after placing the order
        st.success(f"Order placed! Carbon Footprint: {total_carbon} kg CO2e")
        st.info("🎉 Order confirmation sent!")
    else:
        st.error("Your cart is empty!")

# Updated fetch_past_orders() to ensure consistent date format
def fetch_past_orders():
    if st.session_state["user"]:
        orders_ref = db.collection("orders").where("user_id", "==", st.session_state["user"]).stream()
        orders = []
        for order in orders_ref:
            order_dict = order.to_dict()
            # Use current date as fallback if date is missing or invalid
            date = order_dict.get("date", datetime.now().strftime("%Y-%m-%d"))
            if not isinstance(date, str) or "-" not in date:  # Handle non-string or malformed dates
                date = datetime.now().strftime("%Y-%m-%d")
            orders.append((
                order_dict.get("item", "Unknown"),
                order_dict.get("price", 0),
                date
            ))
        return orders
    return []

def predict_spending_limit():
    orders = fetch_past_orders()
    if not orders:
        return 0  # Default suggestion if no history

    # Calculate total spent per month
    monthly_spends = {}
    for _, price, date in orders:
        month = date[:7]  # Extract "YYYY-MM" from "YYYY-MM-DD"
        monthly_spends[month] = monthly_spends.get(month, 0) + price

    # Use median of past monthly spends as the predicted limit
    if monthly_spends:
        spends = list(monthly_spends.values())
        sorted_spends = sorted(spends)
        n = len(sorted_spends)
        median_spend = sorted_spends[n // 2] if n % 2 else (sorted_spends[n // 2 - 1] + sorted_spends[n // 2]) / 2
        # Suggest a slightly higher limit to account for variability (e.g., +10%)
        suggested_limit = int(median_spend * 1.1)
        return suggested_limit
    return 0

def calculate_total_spent():
    if st.session_state["user"]:
        current_month = datetime.now().strftime("%Y-%m")  # e.g., "2025-04"
        orders_ref = db.collection("orders").where("user_id", "==", st.session_state["user"]).stream()
        monthly_total = 0
        for order in orders_ref:
            order_dict = order.to_dict()
            order_date = order_dict.get("date", datetime.now().strftime("%Y-%m-%d"))
            if order_date.startswith(current_month):  # Only include orders from the current month
                monthly_total += order_dict.get("price", 0)
        return monthly_total  # Return total spent for the current month
    return 0

def check_spending_limit():
    monthly_total_spent = calculate_total_spent()  # Get total spent for the current month
    monthly_limit = st.session_state["spending_limit"].get("Monthly", 0)
    if monthly_total_spent > monthly_limit and monthly_limit > 0:
        st.session_state["show_popup"] = True
    else:
        st.session_state["show_popup"] = False
    return monthly_total_spent  # Optionally return for use elsewhere

def set_spending_limit(limit, sacrifice_type=None):
    current_month = datetime.now().strftime("%Y-%m")
    user_ref = db.collection("users").where("email", "==", st.session_state["user"]).get()[0].reference

    if st.session_state["spending_limit"]["set_month"] != current_month:
        st.session_state["spending_limit"]["set_month"] = current_month
        st.session_state["spending_limit_edits_this_month"] = 0
        user_ref.update({
            "spending_limit": st.session_state["spending_limit"],
            "spending_limit_edits_this_month": 0
        })

    if st.session_state["spending_limit_edits_this_month"] >= 2:
        st.error("⚠️ You’ve reached your limit of 2 spending limit changes this month. Try again next month!")
        return False

    if (st.session_state["loyalty_points"] == 0 and not st.session_state["badges"] and 
        st.session_state["spending_limit_edit_count"] == 0):
        st.session_state["spending_limit"]["Monthly"] = limit
        st.session_state["spending_limit_edit_count"] += 1
        st.session_state["spending_limit_edits_this_month"] += 1
        user_ref.update({
            "spending_limit": st.session_state["spending_limit"],
            "spending_limit_edit_count": st.session_state["spending_limit_edit_count"],
            "spending_limit_edits_this_month": st.session_state["spending_limit_edits_this_month"]
        })
        st.success("Great! Your new limit is saved. You’ll need points or badges for future changes.")
        return True

    if st.session_state["spending_limit"]["set_month"] == current_month and st.session_state["spending_limit"]["Monthly"] > 0:
        if sacrifice_type == "points" and st.session_state["loyalty_points"] >= 10:
            st.session_state["loyalty_points"] -= 10
            st.session_state["spending_limit"]["Monthly"] = limit
            st.session_state["spending_limit_edits_this_month"] += 1
            user_ref.update({
                "loyalty_points": st.session_state["loyalty_points"],
                "spending_limit": st.session_state["spending_limit"],
                "spending_limit_edits_this_month": st.session_state["spending_limit_edits_this_month"]
            })
            st.success(f"✅ Spending limit updated! 10 points have been deducted. You have {2 - st.session_state['spending_limit_edits_this_month']} edits left this month.")
            return True
        elif sacrifice_type == "badge" and st.session_state["badges"]:
            badge_order = ["Gold", "Silver", "Bronze"]
            badge_removed = None
            for badge in badge_order:
                if badge in st.session_state["badges"]:
                    st.session_state["badges"].remove(badge)
                    badge_removed = badge
                    break
            st.session_state["spending_limit"]["Monthly"] = limit
            st.session_state["spending_limit_edits_this_month"] += 1
            user_ref.update({
                "badges": st.session_state["badges"],
                "spending_limit": st.session_state["spending_limit"],
                "spending_limit_edits_this_month": st.session_state["spending_limit_edits_this_month"]
            })
            st.success(f"✅ Spending limit updated! The {badge_removed} badge has been removed. You have {2 - st.session_state['spending_limit_edits_this_month']} edits left this month.")
            return True
        else:
            if st.session_state["loyalty_points"] < 10:
                st.error("You don’t have enough points! You can try sacrificing a badge instead.")
            elif not st.session_state["badges"]:
                st.error("Oops! You need at least 10 points or 1 badge to edit your limit. Earn more points by ordering food, writing reviews, or referring friends!")
            return False
    else:
        st.session_state["spending_limit"]["Monthly"] = limit
        st.session_state["spending_limit_edits_this_month"] += 1
        user_ref.update({
            "spending_limit": st.session_state["spending_limit"],
            "spending_limit_edits_this_month": st.session_state["spending_limit_edits_this_month"]
        })
        st.success("Spending limit set for this month!")
        return True

    check_spending_limit()

def check_loyalty_badges():
    points = st.session_state["loyalty_points"]
    badges = st.session_state["badges"]
    if points >= 10 and "Bronze" not in badges:
        badges.append("Bronze")
        st.success("🎉 Earned Bronze Badge!")
    elif points >= 25 and "Silver" not in badges:
        badges.append("Silver")
        st.success("🎉 Earned Silver Badge!")
    elif points >= 50 and "Gold" not in badges:
        badges.append("Gold")
        st.success("🎉 Earned Gold Badge!")
    db.collection("users").where("email", "==", st.session_state["user"]).get()[0].reference.update({"badges": badges})

# 📝 Reviews & Ratings Functions
def submit_review(item, rating, comment):
    db.collection("reviews").add({
        "user_id": st.session_state["user"],
        "item": item,
        "rating": rating,
        "comment": comment,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    st.session_state["loyalty_points"] += 2
    user_ref = db.collection("users").where("email", "==", st.session_state["user"]).get()[0].reference
    user_ref.update({"loyalty_points": st.session_state["loyalty_points"]})
    st.success(f"Review submitted for {item}! You earned 2 loyalty points.")

def fetch_reviews():
    reviews_ref = db.collection("reviews").stream()
    reviews = []
    for review in reviews_ref:
        review_data = review.to_dict()
        reviews.append({
            "user_id": review_data["user_id"],
            "item": review_data["item"],
            "rating": review_data["rating"],
            "comment": review_data["comment"],
            "date": review_data["date"]
        })
    return reviews

def create_diet_plan(fitness_goal, dietary_preference, allergies):
    suitable_items = []
    allergies_list = [allergy.strip().lower() for allergy in allergies.split(",")] if allergies else []

    # Filter menu items based on dietary preferences and allergies
    for item, details in menu_items.items():
        # Check dietary preference
        if dietary_preference == "Vegetarian" and "vegetarian" not in details["tags"]:
            continue
        if dietary_preference == "Vegan" and "vegan" not in details["tags"]:
            continue
        
        # Check for allergens in ingredients
        item_ingredients = details["ingredients"]
        has_allergen = False
        for ingredient in item_ingredients:
            if any(allergy in ingredient.lower() for allergy in allergies_list):
                has_allergen = True
                break
        if has_allergen:
            continue
        
        suitable_items.append(item)

    if not suitable_items:
        return None

    diet_plan = {"Breakfast": None, "Lunch": None, "Dinner": None}

    # Define meal calorie and nutrient targets based on fitness goal
    if fitness_goal == "Weight Loss":
        # Low-calorie, balanced options
        for item in suitable_items:
            if not diet_plan["Breakfast"] and menu_items[item]["calories"] <= 400 and "low-carb" in menu_items[item]["tags"]:
                diet_plan["Breakfast"] = item
            elif not diet_plan["Lunch"] and 400 <= menu_items[item]["calories"] <= 600 and "low-carb" in menu_items[item]["tags"]:
                diet_plan["Lunch"] = item
            elif not diet_plan["Dinner"] and menu_items[item]["calories"] <= 500 and "low-carb" in menu_items[item]["tags"]:
                diet_plan["Dinner"] = item
            if all(diet_plan.values()):
                break
    elif fitness_goal == "Muscle Gain":
        # High-protein, higher-calorie options
        for item in suitable_items:
            if not diet_plan["Breakfast"] and menu_items[item]["protein"] >= 20 and menu_items[item]["calories"] >= 500:
                diet_plan["Breakfast"] = item
            elif not diet_plan["Lunch"] and menu_items[item]["protein"] >= 25 and menu_items[item]["calories"] >= 600:
                diet_plan["Lunch"] = item
            elif not diet_plan["Dinner"] and menu_items[item]["protein"] >= 20 and menu_items[item]["calories"] >= 500:
                diet_plan["Dinner"] = item
            if all(diet_plan.values()):
                break
    else:  # General Health
        # Balanced options
        for item in suitable_items:
            if not diet_plan["Breakfast"] and 300 <= menu_items[item]["calories"] <= 500:
                diet_plan["Breakfast"] = item
            elif not diet_plan["Lunch"] and 500 <= menu_items[item]["calories"] <= 700:
                diet_plan["Lunch"] = item
            elif not diet_plan["Dinner"] and 400 <= menu_items[item]["calories"] <= 600:
                diet_plan["Dinner"] = item
            if all(diet_plan.values()):
                break

    # Fallback: Assign any suitable item if a meal slot is empty
    for meal in diet_plan:
        if not diet_plan[meal] and suitable_items:
            diet_plan[meal] = suitable_items[0]
            suitable_items.pop(0)

    return diet_plan

def save_diet_plan(fitness_goal, dietary_preference, allergies):
    diet_plan = create_diet_plan(fitness_goal, dietary_preference, allergies)
    if diet_plan:
        st.session_state["diet_plan"] = diet_plan
        user_ref = db.collection("users").where("email", "==", st.session_state["user"]).get()[0].reference
        user_ref.update({
            "diet_plan": diet_plan,
            "diet_preferences": {
                "fitness_goal": fitness_goal,
                "dietary_preference": dietary_preference,
                "allergies": allergies
            }
        })
        st.success("Diet plan created successfully!")
    else:
        st.error("No suitable items found for your preferences. Please adjust your settings.")
    return diet_plan

# 🍽 Calorie & Nutritional Tracker
def log_meal(item, quantity):
    meal = menu_items[item]
    meal_log = {
        "item": item,
        "quantity": quantity,
        "calories": meal["calories"] * quantity,
        "protein": meal["protein"] * quantity,
        "carbs": meal["carbs"] * quantity,
        "fats": meal["fats"] * quantity,
        "vitamins": {k: v * quantity for k, v in meal["vitamins"].items()},
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state["meal_logs"].append(meal_log)
    user_ref = db.collection("users").where("email", "==", st.session_state["user"]).get()[0].reference
    user_ref.update({"meal_logs": st.session_state["meal_logs"]})
    st.success(f"Logged {quantity} {item}(s) to your tracker!")

def get_nutritional_summary():
    total_calories = sum(log["calories"] for log in st.session_state["meal_logs"])
    total_protein = sum(log["protein"] for log in st.session_state["meal_logs"])
    total_carbs = sum(log["carbs"] for log in st.session_state["meal_logs"])
    total_fats = sum(log["fats"] for log in st.session_state["meal_logs"])
    total_vitamins = {}
    for log in st.session_state["meal_logs"]:
        for vitamin, amount in log["vitamins"].items():
            total_vitamins[vitamin] = total_vitamins.get(vitamin, 0) + amount
    return {
        "calories": total_calories,
        "protein": total_protein,
        "carbs": total_carbs,
        "fats": total_fats,
        "vitamins": total_vitamins
    }

# New Feature: Order History Summary
def display_order_history_summary():
    summary = get_order_history_summary()
    st.markdown('<h2 class="text-light">📊 Order History Summary</h2>', unsafe_allow_html=True)
    
    # Text-based summary
    st.write(f"**Most Ordered Item:** {summary['most_ordered_item']}")
    st.write(f"**Average Order Value:** Rs{summary['average_order_value']:.2f}")
    
    # Total Spent by Month (Text)
    st.write("**Total Spent by Month:**")
    if summary["total_spent_by_month"]:
        for month, total in summary["total_spent_by_month"].items():
            st.write(f"- {month}: Rs{total}")
    else:
        st.write("No order history available.")
    
    # Bar Chart Visualization
    if summary["total_spent_by_month"]:
        st.subheader("Spending by Month")
        months = list(summary["total_spent_by_month"].keys())
        totals = list(summary["total_spent_by_month"].values())
        
        # Create bar chart
        plt.figure(figsize=(10, 6))
        plt.bar(months, totals, color='#FF6F61')  # Match app's theme color
        plt.xlabel("Month", fontsize=12)
        plt.ylabel("Total Spent (Rs)", fontsize=12)
        plt.title("Monthly Spending History", fontsize=14, pad=10)
        plt.xticks(rotation=45, ha="right")  # Rotate x-axis labels for readability
        plt.tight_layout()
        
        # Display chart in Streamlit
        st.pyplot(plt)
    else:
        st.info("No data available for visualization yet. Place some orders to see your spending trends!")

def get_ai_recommendation():
    past_orders = fetch_past_orders()
    if past_orders:
        items = [item for item, _, _ in past_orders]
        most_common = Counter(items).most_common(1)
        return f"Based on your orders, try {most_common[0][0] if most_common else 'Chicken Biryani'}!"
    return "Try our Chicken Biryani!"

# 🌱 Carbon Footprint Calculation
def calculate_carbon_footprint():
    total_carbon = sum(item["carbon_footprint"] * item["quantity"] for item in st.session_state["cart"].values())
    st.write(f"🌍 Estimated Carbon Footprint: {total_carbon} kg CO2e")
    if total_carbon > 5:
        st.warning("Consider eco-friendly options to reduce your footprint!")

# 🤖 Chatbot Response Functions
def get_gpt_response(user_input):
    edits_left = 2 - st.session_state["spending_limit_edits_this_month"]
    return get_mock_response(user_input)

def get_mock_response(user_input):
    user_input = user_input.lower().strip()
    edits_left = 2 - st.session_state["spending_limit_edits_this_month"]
    responses = {
        "what are today's special dishes": "Today’s specials are Chicken Biryani and Pizza! Would you like to add any to your cart?",
        "do you have any vegan options": "Yes, we have a vegan option: Margherita pizza. Would you like to add it to your cart?",
        "do you have any gluten-free options": "Unfortunately, we don’t have gluten-free options at the moment. Would you like to see the full menu?",
        "do you have any keto options": "Yes, Pepperoni is a keto-friendly option. Would you like to add it to your cart?",
        "can i see the full menu": "Sure! Our menu includes: Chicken Biryani (Rs100), Mutton Biryani (Rs120), Pizza (Rs150), Burger (Rs60), Pepperoni (Rs40), and Margherita (Rs90). Go to the Menu page to add items to your cart!",
        "what ingredients are used in chicken biryani": "Chicken Biryani includes basmati rice, chicken, spices like turmeric, cumin, coriander, yogurt, onions, and saffron. Would you like to add it to your cart?",
        "what ingredients are used in pizza": "Our Pizza includes a wheat crust, tomato sauce, mozzarella cheese, and toppings like pepperoni or veggies. Would you like to add it to your cart?",
        "what ingredients are used in burger": "The Burger has a beef patty, lettuce, tomato, onion, pickles, cheese, and a bun. Would you like to add it to your cart?",
        "what ingredients are used in pepperoni": "Pepperoni is made with pork, beef, paprika, garlic, and other spices. Would you like to add it to your cart?",
        "what ingredients are used in margherita": "Margherita pizza has a wheat crust, tomato sauce, fresh mozzarella, basil, and olive oil. Would you like to add it to your cart?",
        "what ingredients are used in mutton biryani": "Mutton Biryani includes basmati rice, mutton, spices like cloves, cardamom, cinnamon, yogurt, and onions. Would you like to add it to your cart?",
        "do you offer organic or locally sourced ingredients": "Yes, we source some ingredients locally, like vegetables and spices. However, not all items are organic. Would you like to know more about a specific dish?",
        "how do i place an order": "To place an order, go to the Menu page, click 'Add [Item]' for the dishes you want, then go to the Cart page and click 'Place Order'. Try it now!",
        "can i customize my order": "At the moment, we don’t support customizations through the app. However, you can mention special requests when you place your order, and we’ll do our best!",
        "what are the payment options": "We accept Credit/Debit cards, UPI, and Cash on Delivery. You can choose your preferred option when placing your order.",
        "do you offer home delivery": "Yes, we offer home delivery! It typically takes 30-45 minutes depending on your location. Would you like to place an order?",
        "what is the estimated delivery time": "Estimated delivery time is 30-45 minutes after placing your order, depending on your location and order volume.",
        "how can i track my order": "After placing your order, you’ll receive a confirmation with tracking details. Check your email or the Cart page for updates.",
        "can i schedule an order for later": "Currently, we don’t support scheduling orders for later. You can place your order now, and we’ll deliver it as soon as possible!",
        "what are your opening hours": "We’re open from 10 AM to 10 PM daily. Ready to place an order?",
        "where are you located": "We’re located at 123 Foodie Lane, Gourmet City. Come visit us or order online!",
        "do you have dine-in options": "Yes, we offer dine-in! Visit us at 123 Foodie Lane, Gourmet City, between 10 AM to 10 PM.",
        "is there parking available": "Yes, we have parking available at our location on 123 Foodie Lane. Come dine in with us!",
        "do you have any special offers or discounts": "We don’t have any special offers right now, but you can earn loyalty points with every order! Check the Loyalty section for more details.",
        "do you have nut-free options": "Yes, most of our dishes are nut-free, including Chicken Biryani, Mutton Biryani, and Pepperoni. However, Pizza and Burger may contain nuts. Please let us know if you have severe allergies.",
        "do you have dairy-free options": "Unfortunately, most of our dishes contain dairy (e.g., cheese in Pizza). Pepperoni might be a safer option, but please confirm with us if you have allergies.",
        "can i get a dish without cheese": "We can try to prepare Pizza or Burger without cheese if you mention it when ordering. Please note this in your order comments!",
        "can i get a dish without onions": "Yes, we can prepare dishes like Chicken Biryani or Mutton Biryani without onions upon request. Mention it when you place your order.",
        "do you offer calorie or nutritional information": "Yes! Here’s the nutritional info: Chicken Biryani (800 kcal, 35g protein, 90g carbs, 25g fats), Mutton Biryani (850 kcal, 40g protein, 85g carbs, 30g fats), Pizza (700 kcal, 25g protein, 80g carbs, 30g fats), Burger (600 kcal, 20g protein, 50g carbs, 35g fats), Pepperoni (300 kcal, 15g protein, 5g carbs, 25g fats), Margherita (500 kcal, 15g protein, 60g carbs, 20g fats). You can also track your meals in the Nutrition Tracker section!",
        "i have a problem with my order": "Sorry to hear that! Please email us at support@spendeats.com with your order details, and we’ll help you right away.",
        "how do i cancel or modify my order": "To cancel or modify your order, contact us at support@spendeats.com as soon as possible. We’ll do our best to assist you!",
        "how do i leave a review or give feedback": "You can leave a review in the Reviews section. Select an item, give a rating (1-5), and write your comment. You’ll earn 2 loyalty points for each review!",
        "do you have a loyalty program": "Yes! You earn 1 point per item ordered and 2 points for writing a review. Reach 10 points for a Bronze badge, 25 for Silver, and 50 for Gold. Check your points in the sidebar!",
        "how do i redeem my reward points": "You can use 10 points to edit your spending limit in the Spending Limit section. More rewards coming soon!",
        "are there any special promotions for members": "Not at the moment, but loyalty members earn badges and points with every order. Keep ordering to reach the next badge!",
        "i want to change my spending limit": (
            f"Sure! Since you're a new user, you get one free edit. What limit would you like to set?"
            if st.session_state["loyalty_points"] == 0 and not st.session_state["badges"] and st.session_state["spending_limit_edit_count"] == 0
            else (
                f"Sure! You can edit your spending limit 2 times per month. You have {edits_left} edit{'s' if edits_left != 1 else ''} left this month. "
                f"Would you like to use 10 points or sacrifice a badge?\n(Options: 🔹 Use 10 Points | 🏆 Sacrifice a Badge | ❌ Cancel)"
                if edits_left > 0
                else "⚠️ You’ve reached your limit of 2 spending limit changes this month. Try again next month!"
            )
        ),
        "use 10 points": (
            f"✅ Done! Your spending limit is updated, and 10 points have been deducted. You have {edits_left - 1 if edits_left > 0 else 0} edit{'s' if edits_left - 1 != 1 else ''} left this month."
            if st.session_state["loyalty_points"] >= 10 and edits_left > 0
            else "You don’t have enough points! You can try sacrificing a badge instead."
        ),
        "sacrifice a badge": (
            f"✅ Your spending limit is updated! The badge has been removed from your profile. You have {edits_left - 1 if edits_left > 0 else 0} edit{'s' if edits_left - 1 != 1 else ''} left this month."
            if st.session_state["badges"] and edits_left > 0
            else "Oops! You need at least 10 points or 1 badge to edit your limit. Earn more points by ordering food, writing reviews, or referring friends!"
        ),
        "cancel": "Edit cancelled.",
        "i want to change my spending limit again": (
            f"Sure! You can edit your spending limit 2 times per month. You have {edits_left} edit{'s' if edits_left != 1 else ''} left this month. "
            f"Would you like to use 10 points or sacrifice a badge?\n(Options: 🔹 Use 10 Points | 🏆 Sacrifice a Badge | ❌ Cancel)"
            if edits_left > 0
            else "⚠️ You’ve reached your limit of 2 spending limit changes this month. Try again next month!"
        ),
        "how do i write a review": "You can write a review in the Reviews section. Select an item, give a rating from 1 to 5, and add your comment. You’ll earn 2 loyalty points for each review!",
        "what is my diet plan": (
            f"Your current diet plan is:\nBreakfast: {st.session_state['diet_plan']['Breakfast']}\nLunch: {st.session_state['diet_plan']['Lunch']}\nDinner: {st.session_state['diet_plan']['Dinner']}"
            if st.session_state["diet_plan"]
            else "You don’t have a diet plan yet. Go to the Diet Plan section to create one!"
        ),
        "how do i track my meals": "Go to the Nutrition Tracker section, select an item from the menu, enter the quantity, and click 'Log Meal'. You can also view your total calories, macros, and vitamins there!",
        "what are my nutritional stats": (
            f"Here’s your nutritional summary:\nTotal Calories: {get_nutritional_summary()['calories']} kcal\nTotal Protein: {get_nutritional_summary()['protein']}g\nTotal Carbs: {get_nutritional_summary()['carbs']}g\nTotal Fats: {get_nutritional_summary()['fats']}g\nVitamins: {', '.join([f'{k}: {v}' for k, v in get_nutritional_summary()['vitamins'].items()])}"
            if st.session_state["meal_logs"]
            else "You haven’t logged any meals yet. Go to the Nutrition Tracker section to start logging!"
        ),
        "show me low-carb recipes": "Go to the Menu section and use the filters to select 'Low-Carb'. You’ll see items like Pepperoni (300 kcal, 5g carbs).",
        "show me keto recipes": "Go to the Menu section and use the filters to select 'Keto'. You’ll see items like Pepperoni (300 kcal, 5g carbs).",
        "show me gluten-free recipes": "Currently, we don’t have gluten-free options. Try filtering for Low-Carb or Keto recipes in the Menu section!",
        "show me high-protein recipes": "Go to the Menu section and use the filters to select 'High-Protein'. You’ll see items like Chicken Biryani (35g protein) and Mutton Biryani (40g protein).",
        "show me low-sodium recipes": "Go to the Menu section and use the filters to select 'Low-Sodium'. Note that some items may not be tagged yet; try Low-Carb or Vegan options!",
        "show me vegetarian recipes": "Go to the Menu section and use the filters to select 'Vegetarian'. You’ll see items like Margherita (500 kcal).",
        "show me vegan recipes": "Go to the Menu section and use the filters to select 'Vegan'. You’ll see items like Margherita (500 kcal).",
        "hello": "Hi! How can I assist you with SpendEATS today?",
        "help": "I can help with the menu, ordering, delivery, restaurant info, dietary needs, support, loyalty program, spending limit, reviews, diet plans, nutrition tracking, or recipe filters. What would you like to know?",
        "bye": "Goodbye! Visit SpendEATS again soon!",
        "default": "Sorry, I didn’t understand. Try asking about the menu, ordering, or type 'help' for assistance!"
    }

    if "ingredients are used in" in user_input:
        dish_name = user_input.split("ingredients are used in ")[-1].strip()
        return responses.get(f"what ingredients are used in {dish_name}", "I don’t have ingredient details for that dish. Try asking about Chicken Biryani, Pizza, or another menu item!")

    if "can i get a dish without" in user_input:
        ingredient = user_input.split("without ")[-1].strip()
        return responses.get(f"can i get a dish without {ingredient}", "We can try to prepare a dish without that ingredient. Please mention it in your order comments!")

    if user_input.isdigit() and "i want to change my spending limit" in st.session_state.chat_history[-2][1].lower():
        limit = int(user_input)
        if st.session_state["loyalty_points"] == 0 and not st.session_state["badges"] and st.session_state["spending_limit_edit_count"] == 0:
            set_spending_limit(limit)
            return "Great! Your new limit is saved. You’ll need points or badges for future changes."
        else:
            return "Please choose an option: 🔹 Use 10 Points | 🏆 Sacrifice a Badge | ❌ Cancel"

    if "use 10 points" in user_input and "i want to change my spending limit" in st.session_state.chat_history[-2][1].lower():
        limit_input = st.session_state.chat_history[-1][1]
        if limit_input.isdigit():
            limit = int(limit_input)
            success = set_spending_limit(limit, sacrifice_type="points")
            if success:
                return f"✅ Done! Your spending limit is updated to Rs{limit}, and 10 points have been deducted. You have {2 - st.session_state['spending_limit_edits_this_month']} edit{'s' if 2 - st.session_state['spending_limit_edits_this_month'] != 1 else ''} left this month."
            else:
                return "You don’t have enough points! You can try sacrificing a badge instead."
        else:
            return "Please provide a valid number for the new spending limit."

    if "sacrifice a badge" in user_input and "i want to change my spending limit" in st.session_state.chat_history[-2][1].lower():
        limit_input = st.session_state.chat_history[-1][1]
        if limit_input.isdigit():
            limit = int(limit_input)
            success = set_spending_limit(limit, sacrifice_type="badge")
            if success:
                return f"✅ Your spending limit is updated to Rs{limit}! The badge has been removed from your profile. You have {2 - st.session_state['spending_limit_edits_this_month']} edit{'s' if 2 - st.session_state['spending_limit_edits_this_month'] != 1 else ''} left this month."
            else:
                return "Oops! You need at least 10 points or 1 badge to edit your limit. Earn more points by ordering food, writing reviews, or referring friends!"
        else:
            return "Please provide a valid number for the new spending limit."

    return responses.get(user_input, responses["default"])

# 📌 UI with Tailwind CSS Integration (Simulated) and Pop-Up CSS
st.markdown(
    """
    <style>
    @import url('https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css');
    .bg-dark { background-color: #1a202c; }
    .btn { @apply bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600; }
    .modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }
    .modal-content {
        background-color: #2d3748;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        color: #e2e8f0;
        max-width: 400px;
        width: 80%;
    }
    .modal-close {
        background-color: #e53e3e;
        color: white;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# New Feature: Personalized Recipe Generator
def generate_custom_recipe(fitness_goal, dietary_preference, allergies, max_calories=None):
    if not st.session_state["diet_plan"]:
        st.error("Please create a diet plan first in the Diet Plan section!")
        return None

    # Infer available ingredients from past orders
    past_orders = fetch_past_orders()
    ordered_items = [item for item, _, _ in past_orders] if past_orders else []
    available_ingredients = set()
    for item in ordered_items:
        if item in menu_items:
            available_ingredients.update(menu_items[item]["ingredients"])
    
    # If no past orders, use all base ingredients as a fallback
    if not available_ingredients:
        available_ingredients = set(base_ingredients.keys())

    # Filter ingredients based on preferences and allergies
    suitable_ingredients = []
    allergies_list = [allergy.strip().lower() for allergy in allergies.split(",")] if allergies else []
    for ingredient, details in base_ingredients.items():
        if dietary_preference == "Vegetarian" and "vegetarian" not in details["tags"] and "vegan" not in details["tags"]:
            continue
        if dietary_preference == "Vegan" and "vegan" not in details["tags"]:
            continue
        if any(allergy in ingredient.lower() for allergy in allergies_list):
            continue
        if ingredient in available_ingredients:
            suitable_ingredients.append(ingredient)

    if not suitable_ingredients:
        st.error("No suitable ingredients available based on your past orders and preferences.")
        return None

    # Categorize suitable ingredients
    base_options = [ing for ing in suitable_ingredients if base_ingredients[ing]["category"] == "base"]
    protein_options = [ing for ing in suitable_ingredients if base_ingredients[ing]["category"] == "protein"]
    vegetable_options = [ing for ing in suitable_ingredients if base_ingredients[ing]["category"] == "vegetable"]
    seasoning_options = [ing for ing in suitable_ingredients if base_ingredients[ing]["category"] == "seasoning"]
    topping_options = [ing for ing in suitable_ingredients if base_ingredients[ing]["category"] == "topping"]

    # Ensure we have at least a base ingredient
    if not base_options:
        st.error("No base ingredients available to create a recipe.")
        return None

    # Select ingredients for the dish
    selected_ingredients = []
    cooking_steps = []
    total_cost = 0
    total_carbon_footprint = 0
    nutritional_profile = {"calories": 0, "protein": 0, "carbs": 0, "fats": 0, "vitamins": {}}

    # Step 1: Select a base ingredient (e.g., rice, pasta)
    base = random.choice(base_options)
    selected_ingredients.append(base)
    cooking_steps.append(f"Prepare the {base} according to package instructions (e.g., boil the {base} until tender).")
    total_cost += base_ingredients[base]["cost"]
    total_carbon_footprint += 0.5
    for nutrient in ["calories", "protein", "carbs", "fats"]:
        nutritional_profile[nutrient] += base_ingredients[base][nutrient]

    # Step 2: Add a protein if available and suitable
    if protein_options and (dietary_preference != "Vegan" or any("vegan" in base_ingredients[ing]["tags"] for ing in protein_options)):
        protein = random.choice(protein_options)
        selected_ingredients.append(protein)
        cooking_steps.append(f"Cook the {protein} (e.g., grill or pan-fry the {protein} until fully cooked).")
        total_cost += base_ingredients[protein]["cost"]
        total_carbon_footprint += 0.5
        for nutrient in ["calories", "protein", "carbs", "fats"]:
            nutritional_profile[nutrient] += base_ingredients[protein][nutrient]

    # Step 3: Add a vegetable
    if vegetable_options:
        vegetable = random.choice(vegetable_options)
        selected_ingredients.append(vegetable)
        cooking_steps.append(f"Chop the {vegetable} and sauté it in a pan until tender.")
        total_cost += base_ingredients[vegetable]["cost"]
        total_carbon_footprint += 0.5
        for nutrient in ["calories", "protein", "carbs", "fats"]:
            nutritional_profile[nutrient] += base_ingredients[vegetable][nutrient]

    # Step 4: Add a seasoning
    if seasoning_options:
        seasoning = random.choice(seasoning_options)
        selected_ingredients.append(seasoning)
        cooking_steps.append(f"Add the {seasoning} to the pan for flavor.")
        total_cost += base_ingredients[seasoning]["cost"]
        total_carbon_footprint += 0.5
        for nutrient in ["calories", "protein", "carbs", "fats"]:
            nutritional_profile[nutrient] += base_ingredients[seasoning][nutrient]

    # Step 5: Add a topping if available (e.g., cheese for non-vegan)
    if topping_options and dietary_preference != "Vegan":
        topping = random.choice(topping_options)
        selected_ingredients.append(topping)
        cooking_steps.append(f"Sprinkle the {topping} on top before serving.")
        total_cost += base_ingredients[topping]["cost"]
        total_carbon_footprint += 0.5
        for nutrient in ["calories", "protein", "carbs", "fats"]:
            nutritional_profile[nutrient] += base_ingredients[topping][nutrient]

    # Final cooking step
    cooking_steps.append("Combine all ingredients in a bowl or plate, mix well, and serve hot.")

    # Add vitamins
    for ingredient in selected_ingredients:
        if ingredient in ["tomato", "spinach"]:
            nutritional_profile["vitamins"]["Vitamin C"] = nutritional_profile["vitamins"].get("Vitamin C", 0) + 10
        if ingredient == "salmon":
            nutritional_profile["vitamins"]["Vitamin D"] = nutritional_profile["vitamins"].get("Vitamin D", 0) + 50

    # Adjust based on fitness goal
    if fitness_goal == "Weight Loss" and max_calories and nutritional_profile["calories"] > max_calories:
        scale_factor = max_calories / nutritional_profile["calories"]
        for nutrient in ["calories", "protein", "carbs", "fats"]:
            nutritional_profile[nutrient] *= scale_factor
        total_cost *= scale_factor
        total_carbon_footprint *= scale_factor
    elif fitness_goal == "Muscle Gain" and nutritional_profile["protein"] < 25 and protein_options:
        protein = random.choice(protein_options)
        if protein not in selected_ingredients:
            selected_ingredients.append(protein)
            cooking_steps.insert(-1, f"Add extra {protein} to increase protein content.")
            total_cost += base_ingredients[protein]["cost"]
            total_carbon_footprint += 0.5
            for nutrient in ["calories", "protein", "carbs", "fats"]:
                nutritional_profile[nutrient] += base_ingredients[protein][nutrient]
    elif fitness_goal == "General Health":
        total_macros = nutritional_profile["protein"] + nutritional_profile["carbs"] + nutritional_profile["fats"]
        if total_macros > 0:
            carb_ratio = nutritional_profile["carbs"] / total_macros
            if carb_ratio < 0.4 and "rice" in suitable_ingredients and "rice" not in selected_ingredients:
                selected_ingredients.append("rice")
                cooking_steps.insert(-1, f"Add extra rice to balance the macros.")
                total_cost += base_ingredients["rice"]["cost"]
                total_carbon_footprint += 0.5
                for nutrient in ["calories", "protein", "carbs", "fats"]:
                    nutritional_profile[nutrient] += base_ingredients["rice"][nutrient]

    # Assign tags based on ingredients
    tags = set()
    for ingredient in selected_ingredients:
        tags.update(base_ingredients[ingredient]["tags"])

    # Generate a descriptive recipe name
    prefixes = {
        "Weight Loss": "Light",
        "Muscle Gain": "Power",
        "General Health": "Balanced"
    }
    dish_type = "Pasta" if base == "pasta" else "Stir-Fry" if "protein" in [base_ingredients[ing]["category"] for ing in selected_ingredients] else "Bowl"
    main_ingredient = next((ing for ing in selected_ingredients if base_ingredients[ing]["category"] in ["protein", "vegetable"]), base)
    recipe_name = f"{prefixes[fitness_goal]} {main_ingredient.capitalize()} {dish_type}"

    custom_recipe = {
        "name": recipe_name,
        "ingredients": selected_ingredients,
        "calories": round(nutritional_profile["calories"]),
        "protein": round(nutritional_profile["protein"]),
        "carbs": round(nutritional_profile["carbs"]),
        "fats": round(nutritional_profile["fats"]),
        "tags": list(tags),
        "prep_time": len(selected_ingredients) * 5,  # 5 minutes per ingredient
        "vitamins": nutritional_profile["vitamins"],
        "price": round(total_cost * 1.2),  # 20% markup for preparation
        "carbon_footprint": round(total_carbon_footprint, 1),
        "instructions": cooking_steps
    }
    return custom_recipe
def save_custom_recipe(fitness_goal, dietary_preference, allergies, max_calories=None):
    recipe = generate_custom_recipe(fitness_goal, dietary_preference, allergies, max_calories)
    if recipe:
        st.session_state["custom_recipes"].append(recipe)
        user_ref = db.collection("users").where("email", "==", st.session_state["user"]).get()[0].reference
        user_ref.update({"custom_recipes": st.session_state["custom_recipes"]})
        st.success(f"New recipe '{recipe['name']}' created successfully!")
    return recipe

def display_custom_recipes():
    if st.session_state["custom_recipes"]:
        st.markdown('<h2 class="text-light">🍳 Personalized Recipes</h2>', unsafe_allow_html=True)
        for recipe in st.session_state["custom_recipes"]:
            # Use .get() to handle missing 'price' key
            price = recipe.get("price", "N/A")
            st.markdown(f"**{recipe['name']}** - Rs{price}", unsafe_allow_html=True)
            st.write(f"Ingredients: {', '.join(recipe['ingredients'])}")
            st.write(f"Calories: {recipe['calories']} kcal, Protein: {recipe['protein']}g, Carbs: {recipe['carbs']}g, Fats: {recipe['fats']}g")
            st.write(f"Tags: {', '.join(recipe['tags'])}, Prep Time: {recipe['prep_time']} mins")
            # Handle missing 'instructions' key for older recipes
            if "instructions" in recipe:
                st.write("**Preparation Steps (Prepared by SpendEATS):**")
                for i, step in enumerate(recipe['instructions'], 1):
                    st.write(f"{i}. {step}")
            st.markdown("---")
    else:
        st.write("No custom recipes yet. Generate one below!")

# New Feature: Order History Summary
def get_order_history_summary():
    if st.session_state["user"]:
        orders = fetch_past_orders()
        if not orders:
            return {
                "total_spent_by_month": {},
                "most_ordered_item": "None",
                "average_order_value": 0
            }
        
        total_spent_by_month = {}
        for item, price, date in orders:
            try:
                # Safely extract year and month from date
                date_parts = date.split("-")
                if len(date_parts) >= 2:
                    month = f"{date_parts[0]}-{date_parts[1]}"
                else:
                    # Fallback to current month if date is malformed
                    month = datetime.now().strftime("%Y-%m")
                total_spent_by_month[month] = total_spent_by_month.get(month, 0) + price
            except (AttributeError, ValueError):
                # Skip invalid dates or log them with a fallback
                month = datetime.now().strftime("%Y-%m")
                total_spent_by_month[month] = total_spent_by_month.get(month, 0) + price
        
        items = [item for item, _, _ in orders]
        most_ordered_item = Counter(items).most_common(1)[0][0] if items else "None"
        total_orders = len(orders)
        average_order_value = sum(price for _, price, _ in orders) / total_orders if total_orders > 0 else 0
        
        return {
            "total_spent_by_month": total_spent_by_month,
            "most_ordered_item": most_ordered_item,
            "average_order_value": average_order_value
        }
    return {
        "total_spent_by_month": {},
        "most_ordered_item": "None",
        "average_order_value": 0
    }

# 🌱 Smart Meal Scheduler
def generate_meal_schedule(availability, fitness_goal, dietary_preference, allergies):
    if not st.session_state["diet_plan"]:
        st.error("Please create a diet plan first in the Diet Plan section!")
        return None

    # --- Change 1: Get the current day and time ---
    current_datetime = datetime.now()
    current_day = current_datetime.strftime("%A")  # e.g., "Friday"
    current_hour = current_datetime.hour
    current_minute = current_datetime.minute
    current_time_in_hours = current_hour + current_minute / 60.0  # Convert current time to hours (e.g., 13:30 -> 13.5)

    schedule = {current_day: {"Breakfast": None, "Lunch": None, "Dinner": None}}  # Schedule for current day only

    available_items = list(menu_items.keys())
    
    # Filter items based on dietary preferences and allergies
    for item in list(available_items):
        details = menu_items[item]
        if dietary_preference == "Vegetarian" and "vegetarian" not in details["tags"]:
            available_items.remove(item)
            continue
        if dietary_preference == "Vegan" and "vegan" not in details["tags"]:
            available_items.remove(item)
            continue
        if "nuts" in allergies.lower() and item in ["Pizza", "Burger"]:
            available_items.remove(item)
            continue

    if not available_items:
        st.error("No suitable items found for your preferences. Please adjust your settings.")
        return None

    # Schedule meals for the current day
    for meal in ["Breakfast", "Lunch", "Dinner"]:
        meal_time = {
            "Breakfast": (7, 10),
            "Lunch": (12, 14),
            "Dinner": (18, 21)
        }[meal]
        available = False
        selected_slot = None

        # Check if the meal can be scheduled in any of the available time slots
        for start, end in availability.get(current_day, []):
            # Check if the meal time slot overlaps with the availability slot
            if start <= meal_time[0] < end or start < meal_time[1] <= end:
                # --- Change 2: Check if the end of the slot is in the future ---
                if end > current_time_in_hours:
                    available = True
                    selected_slot = (start, end)
                    break

        if not available:
            schedule[current_day][meal] = None
            continue

        # --- Change 3: Check if the meal can be prepared in time ---
        start, end = selected_slot
        earliest_possible_start = max(start, current_time_in_hours)

        # Prefer items from the diet plan
        preferred_item = st.session_state["diet_plan"].get(meal)
        if preferred_item and preferred_item in available_items:
            prep_time = menu_items[preferred_item]["prep_time"] / 60.0  # Convert prep time to hours
            # Check if the meal can be prepared and consumed within the slot
            if earliest_possible_start + prep_time <= end:
                schedule[current_day][meal] = preferred_item
                available_items.remove(preferred_item)
                continue
            else:
                st.warning(f"Cannot schedule {meal} with {preferred_item} as preparation time ({menu_items[preferred_item]['prep_time']} mins) exceeds the available time in the slot ({start}:00-{end}:00).")

        # Otherwise, select an item that fits the time slot
        for item in available_items[:]:
            prep_time = menu_items[item]["prep_time"] / 60.0  # Convert prep time to hours
            # Check if the meal can be prepared and consumed within the slot
            if earliest_possible_start + prep_time <= end:
                schedule[current_day][meal] = item
                available_items.remove(item)
                break

        if not schedule[current_day][meal] and available_items:
            # If no item fits due to prep time, assign the first available item as a fallback
            schedule[current_day][meal] = available_items[0]
            available_items.remove(schedule[current_day][meal])
            st.warning(f"{meal} scheduled with {schedule[current_day][meal]}, but preparation time may not fit perfectly within the slot ({start}:00-{end}:00).")

    return schedule
def save_meal_schedule(availability, fitness_goal, dietary_preference, allergies):
    schedule = generate_meal_schedule(availability, fitness_goal, dietary_preference, allergies)
    if schedule:
        # Check if any meals were scheduled
        current_day = list(schedule.keys())[0]
        meals_scheduled = any(schedule[current_day][meal] for meal in ["Breakfast", "Lunch", "Dinner"])
        if not meals_scheduled:
            st.warning("No meals could be scheduled. All available time slots have passed or preparation times exceed the slots. Please adjust your availability.")
            return schedule

        # Flatten the schedule dictionary
        firestore_compatible_schedule = {
            f"{current_day}_Breakfast": str(schedule[current_day]["Breakfast"]) if schedule[current_day]["Breakfast"] else "",
            f"{current_day}_Lunch": str(schedule[current_day]["Lunch"]) if schedule[current_day]["Lunch"] else "",
            f"{current_day}_Dinner": str(schedule[current_day]["Dinner"]) if schedule[current_day]["Dinner"] else ""
        }

        # Flatten the availability into a list of strings
        firestore_compatible_availability_slots = [f"{start}-{end}" for start, end in availability.get(current_day, [])] if availability else []

        # Flatten schedule_preferences
        firestore_compatible_preferences = {
            "fitness_goal": str(fitness_goal) if fitness_goal else "",
            "dietary_preference": str(dietary_preference) if dietary_preference else "",
            "allergies": str(allergies) if allergies else "",
            "availability_day": str(list(availability.keys())[0]) if availability else "",
            "availability_slots": firestore_compatible_availability_slots
        }

        # Save to session state
        st.session_state["meal_schedule"] = schedule

        # Update Firestore
        user_ref = db.collection("users").where("email", "==", st.session_state["user"]).get()[0].reference
        try:
            user_ref.update({
                "meal_schedule": firestore_compatible_schedule,
                "schedule_preferences": firestore_compatible_preferences
            })
            st.success("Smart Meal Schedule created successfully for today!")
            
            # Add scheduled meals to the cart
            meals_added = []
            for meal, item in schedule[current_day].items():
                if item:  # Only add if a meal is scheduled
                    item_details = menu_items[item]
                    price = item_details["price"]
                    carbon_footprint = item_details["carbon_footprint"]
                    add_to_cart(item, price, carbon_footprint)
                    meals_added.append(f"{item} (Rs{price}) for {meal}")
            
            # Provide feedback to the user
            if meals_added:
                st.success(f"The following meals have been added to your cart: {', '.join(meals_added)}.")
                if st.button("Go to Cart to Place Order", key="go_to_cart_after_schedule"):
                    st.session_state["page"] = "Cart"
                    st.rerun()
            else:
                st.info("No meals were scheduled, so nothing was added to the cart.")

        except Exception as e:
            st.error(f"Failed to save meal schedule to Firestore: {str(e)}")
    return schedule

def display_meal_schedule():
    if st.session_state["meal_schedule"]:
        st.markdown('<h2 class="text-light">📅 Today\'s Meal Schedule</h2>', unsafe_allow_html=True)
        current_day = datetime.now().strftime("%A")  # e.g., "Monday"
        current_date = datetime.now().strftime("%A, %b %d")  # e.g., "Monday, Mar 19"
        
        # Check if the schedule has the current day
        if current_day in st.session_state["meal_schedule"]:
            st.markdown(f"**{current_date}**", unsafe_allow_html=True)
            for meal, item in st.session_state["meal_schedule"][current_day].items():
                if item:
                    st.write(f"- {meal}: {item} (Prep Time: {menu_items[item]['prep_time']} mins)")
                else:
                    # --- Change 4: Update the message to be more specific ---
                    st.write(f"- {meal}: Not scheduled (time slot has passed or preparation time exceeds available slot)")
        else:
            st.write("No meal schedule set for today. Create one below!")
    else:
        st.write("No meal schedule set. Create one below!")
def show_confirmation_dialog(action, item=None, total_cost=None, limit=None):
    st.session_state["confirmation_dialog"] = {"action": action, "item": item, "total_cost": total_cost, "limit": limit}
    if action == "exceed spending limit":
        st.markdown(
            f"""
            <div class="modal">
                <div class="modal-content">
                    <h2>⚠ Spending Limit Warning!</h2>
                    <p>By placing this order, you will exceed your spending limit of Rs{limit}.</p>
                    <p>Total Cost of Order: Rs{total_cost}</p>
                    <p>What do you want to do?</p>
                    <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                        <button class="modal-close" onclick="st.session_state['confirmation_dialog'] = None; st.rerun()">Thanks for reminding</button>
                        <button class="btn" onclick="st.session_state['confirmation_dialog'] = None; st.rerun()">OK but I want to order</button>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="modal">
                <div class="modal-content">
                    <h2>Confirm Action</h2>
                    <p>Are you sure you want to {action}{' ' + item if item else ''}?</p>
                    <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                        <button class="btn" onclick="st.session_state['confirmation_dialog'] = None; st.rerun()">Yes</button>
                        <button class="modal-close" onclick="st.session_state['confirmation_dialog'] = None; st.rerun()">No</button>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def handle_confirmation():
    if st.session_state["confirmation_dialog"]:
        action = st.session_state["confirmation_dialog"]["action"]
        item = st.session_state["confirmation_dialog"].get("item")
        total_cost = st.session_state["confirmation_dialog"].get("total_cost")
        limit = st.session_state["confirmation_dialog"].get("limit")

        if action == "exceed spending limit":
            current_monthly_spent = calculate_total_spent()  # Get current monthly total
            st.markdown(f"**Warning**: By placing this order, you will exceed your monthly spending limit of Rs{limit}. Current Monthly Spent: Rs{current_monthly_spent}, Total Cost: Rs{total_cost}")
            st.write("What do you want to do?")
            unique_id = f"exceed_limit_{int(time.time())}"  # Unique key with timestamp
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Thanks for reminding", key=f"remind_{unique_id}"):
                    st.session_state["cart"] = {}  # Clear the cart
                    st.success("Cart cleared. You’re back within your monthly spending limit!")
                    st.session_state["confirmation_dialog"] = None
                    st.rerun()
            with col2:
                if st.button("OK but I want to order", key=f"proceed_{unique_id}"):
                    # Proceed with placing the order
                    total_carbon = sum(item["carbon_footprint"] * item["quantity"] for item in st.session_state["cart"].values())
                    for item, details in st.session_state["cart"].items():
                        db.collection("orders").add({
                            "user_id": st.session_state["user"],
                            "item": item,
                            "price": details["price"] * details["quantity"],
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "carbon_footprint": details["carbon_footprint"] * details["quantity"]
                        })
                    st.session_state["cart"] = {}
                    check_spending_limit()
                    st.success(f"Order placed! Carbon Footprint: {total_carbon} kg CO2e")
                    st.info("🎉 Order confirmation sent!")
                    st.session_state["confirmation_dialog"] = None
                    st.rerun()
        # Rest of the function remains unchanged for other actions
        elif action == "remove from favorites" and item:
            st.markdown(f"**Confirm Action**: Are you sure you want to remove {item} from favorites?")
            unique_id = f"{action}_{item}_{int(time.time())}"
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes", key=f"confirm_{unique_id}"):
                    if item in st.session_state["favorites"]:
                        st.session_state["favorites"].remove(item)
                        user_ref = db.collection("users").where("email", "==", st.session_state["user"]).get()
                        if user_ref:
                            user_ref[0].reference.update({"favorites": st.session_state["favorites"]})
                            st.success(f"{item} removed from Favorites!")
                        else:
                            st.error("Failed to update favorites: User not found.")
                    st.session_state["confirmation_dialog"] = None
                    st.rerun()
            with col2:
                if st.button("No", key=f"cancel_{unique_id}"):
                    st.session_state["confirmation_dialog"] = None
                    st.rerun()

# Main App Logic
if st.session_state["user"] is None:
    st.markdown('<h1 class="text-light" style="text-align: center;">🍽 SpendEATS - Bite Right, Spend Light</h1>', unsafe_allow_html=True)
    with st.container():
        with st.form(key="auth_form"):
            st.markdown('<span class="material-icons">email</span> Email', unsafe_allow_html=True)
            email = st.text_input("", placeholder="Enter your email", key="email_input")
            st.markdown('<span class="material-icons">lock</span> Password', unsafe_allow_html=True)
            password = st.text_input("", type="password", placeholder="Enter your password", key="password_input")
            remember_me = st.checkbox("Remember me", key="remember_me")
            submit_button = st.form_submit_button(label="Login" if st.session_state["auth_mode"] == "Login" else "Signup")

        if st.session_state["auth_mode"] == "Login":
            if st.button("Forgot Password?", key="reset_password_btn"):
                if email:
                    st.session_state["show_reset_form"] = True
                else:
                    st.error("Please enter your email first.")

            if st.session_state.get("show_reset_form", False):
                with st.form(key="reset_password_form"):
                    st.markdown('<span class="material-icons">lock</span> New Password', unsafe_allow_html=True)
                    new_password = st.text_input("", type="password", placeholder="Enter new password", key="new_password_reset")
                    st.markdown('<span class="material-icons">lock</span> Confirm Password', unsafe_allow_html=True)
                    confirm_password = st.text_input("", type="password", placeholder="Confirm new password", key="confirm_password_reset")
                    reset_submit = st.form_submit_button(label="Reset Password")
                    if reset_submit:
                        if new_password and new_password == confirm_password:
                            reset_password(email, new_password)
                        else:
                            st.error("Passwords do not match or are empty.")

        mode_switch_text = "New here? Sign Up!" if st.session_state["auth_mode"] == "Login" else "Already a member? Log In!"
        if st.button(mode_switch_text, key="switch_mode_btn"):
            st.session_state["auth_mode"] = "Signup" if st.session_state["auth_mode"] == "Login" else "Login"
            st.rerun()

        if submit_button:
            if email and password:
                if st.session_state["auth_mode"] == "Login":
                    login(email, password)
                else:
                    signup(email, password)
            else:
                st.error("Please fill in both email and password fields.")

if st.session_state["user"] is not None:
    with st.sidebar:
        st.markdown('<div class="sidebar-header">SpendEATS</div>', unsafe_allow_html=True)
        menu_option = option_menu(
            menu_title=None,
            options=["Menu", "Cart", "Spending Limit", "Diet Plan", "Nutrition Tracker", 
                     "Recommendations", "Profile", "Chatbot", "Reviews", "Favorites", 
                     "Order History", "Smart Meal Scheduler", "Personalized Recipe Generator"],
            icons=["", "cart", "wallet", "apple", "bar-chart", "lightbulb", 
                   "person", "chat", "star", "heart", "clock-history", "calendar", ""],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#FF6F61", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#FF6F61"},
            }
        )
        if st.button("Logout", key="logout_btn"):
            logout()
        st.markdown(f'<div class="text-light">💰 Total Spent: Rs{st.session_state["total_spent"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="text-light">🎖 Points: {st.session_state["loyalty_points"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="text-light">🏅 Badges: {", ".join(st.session_state["badges"])}</div>', unsafe_allow_html=True)

    if menu_option == "Cart":
        st.markdown('<h2 class="text-light">🛒 Your Cart</h2>', unsafe_allow_html=True)
        if not st.session_state["cart"]:
            st.write("Your cart is empty!")
        else:
            for item, details in st.session_state["cart"].items():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"{item} x {details['quantity']} - Rs{details['price'] * details['quantity']} (Carbon: {details['carbon_footprint'] * details['quantity']} kg CO2e)")
                with col2:
                    if st.button(f"Add More", key=f"cart_add_more_{item}"):
                        add_to_cart(item, details["price"], details["carbon_footprint"])
                with col3:
                    if st.button(f"Remove", key=f"cart_remove_{item}"):
                        st.session_state["confirmation_dialog"] = {"action": "remove from cart", "item": item}
            if st.button("Place Order", key="cart_place_order_btn"):
                place_order()
            total_carbon = sum(details["carbon_footprint"] * details["quantity"] for details in st.session_state["cart"].values())
            st.write(f"🌍 Total Carbon Footprint: {total_carbon} kg CO2e")
        handle_confirmation()
    
    elif menu_option == "Spending Limit":
        st.markdown('<h2 class="text-light">💰 Set Monthly Spending Limit</h2>', unsafe_allow_html=True)
        current_month = datetime.now().strftime("%Y-%m")
        monthly_spent = calculate_total_spent()  # Get current monthly total
        if st.session_state["spending_limit"]["set_month"] == current_month and st.session_state["spending_limit"]["Monthly"] > 0:
            st.write(f"Current limit for {current_month}: Rs{st.session_state['spending_limit']['Monthly']}")
            st.write(f"Current spent this month: Rs{monthly_spent}")
            edits_left = 2 - st.session_state["spending_limit_edits_this_month"]
            st.write(f"🛑 You have {edits_left} edit{'s' if edits_left != 1 else ''} left this month.")
        else:
            st.info("Set your spending limit for this month.")

        suggested_limit = predict_spending_limit()
        if suggested_limit > 0:
            st.write(f"📈 Based on your past spending, we suggest a limit of Rs{suggested_limit}.")
        else:
            st.write("📈 No past orders yet. Set a limit to get started!")

        if st.session_state["spending_limit"]["set_month"] == current_month and st.session_state["spending_limit"]["Monthly"] > 0:
            if (st.session_state["loyalty_points"] == 0 and not st.session_state["badges"] and 
                st.session_state["spending_limit_edit_count"] == 0):
                st.info("Since you're a new user, you get one free edit. What limit would you like to set?")
                limit = st.number_input("Enter new spending limit", min_value=0, value=suggested_limit, key="spending_limit_input")
                if st.button("Set Limit (Free)", key="spending_set_limit_free_btn"):
                    set_spending_limit(limit)
            else:
                st.warning(f"Want to change your spending limit? You have {edits_left} edits left this month. Use 10 points or sacrifice a badge!")
                st.write(f"Available Points: {st.session_state['loyalty_points']}")
                st.write(f"Available Badges: {', '.join(st.session_state['badges']) if st.session_state['badges'] else 'None'}")
                limit = st.number_input("Enter new spending limit", min_value=0, value=suggested_limit, key="spending_limit_input")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔹 Use 10 Points", key="spending_sacrifice_points_btn"):
                        set_spending_limit(limit, sacrifice_type="points")
                with col2:
                    if st.button("🏆 Sacrifice a Badge", key="spending_sacrifice_badge_btn"):
                        set_spending_limit(limit, sacrifice_type="badge")
                with col3:
                    if st.button("❌ Cancel", key="spending_cancel_btn"):
                        st.write("Edit cancelled.")
        else:
            limit = st.number_input("Enter spending limit", min_value=0, value=suggested_limit, key="spending_limit_input")
            if st.button("Set Limit", key="spending_set_limit_btn"):
                set_spending_limit(limit)
    
        handle_confirmation()

    elif menu_option == "Nutrition Tracker":
        st.markdown('<h2 class="text-light">🍽 Calorie & Nutritional Tracker</h2>', unsafe_allow_html=True)
        st.subheader("Log a Meal")
        item = st.selectbox("Select Item", list(menu_items.keys()), key="nutrition_log_item")
        quantity = st.number_input("Quantity", min_value=1, value=1, key="nutrition_log_quantity")
        if st.button("Log Meal", key="nutrition_log_meal_btn"):
            log_meal(item, quantity)
        st.subheader("Meal Logs")
        if st.session_state["meal_logs"]:
            for log in st.session_state["meal_logs"]:
                st.write(f"{log['date']}: {log['item']} x {log['quantity']} - {log['calories']} kcal, {log['protein']}g protein, {log['carbs']}g carbs, {log['fats']}g fats")
                st.write(f"Vitamins: {', '.join([f'{k}: {v}' for k, v in log['vitamins'].items()])}")
                st.markdown("---")
        else:
            st.write("No meals logged yet.")
        st.subheader("Nutritional Summary")
        summary = get_nutritional_summary()
        st.write(f"Total Calories: {summary['calories']} kcal")
        st.write(f"Total Protein: {summary['protein']}g")
        st.write(f"Total Carbs: {summary['carbs']}g")
        st.write(f"Total Fats: {summary['fats']}g")
        st.write(f"Vitamins: {', '.join([f'{k}: {v}' for k, v in summary['vitamins'].items()])}")

    elif menu_option == "Diet Plan":
        st.markdown('<h2 class="text-light">🥗 Customized Diet Plan</h2>', unsafe_allow_html=True)
        st.subheader("Create Your Diet Plan")
        fitness_goal = st.selectbox("Fitness Goal", ["Weight Loss", "Muscle Gain", "General Health"], key="diet_fitness_goal")
        dietary_preference = st.selectbox("Dietary Preference", ["None", "Vegetarian", "Vegan"], key="diet_dietary_preference")
        allergies = st.text_input("Allergies (e.g., nuts, dairy)", key="diet_allergies")
        if st.button("Generate Diet Plan", key="diet_generate_diet_btn"):
            save_diet_plan(fitness_goal, dietary_preference, allergies)
        st.subheader("Your Current Diet Plan")
        if st.session_state["diet_plan"]:
            for meal, item in st.session_state["diet_plan"].items():
                st.write(f"**{meal}**: {item if item else 'Not assigned'}")
        else:
            st.write("No diet plan set. Create one above!")

    elif menu_option == "Menu":
        st.markdown('<h2 class="text-light">📜 Menu</h2>', unsafe_allow_html=True)
        st.subheader("Filter Recipes")
        filter_options = ["Low-Carb", "Keto", "Gluten-Free", "High-Protein", "Low-Sodium", "Vegetarian", "Vegan"]
        selected_filters = st.multiselect("Select Dietary Filters", filter_options, key="menu_recipe_filters")
        filtered_items = menu_items.copy()
        if selected_filters:
            filtered_items = {}
            for item, details in menu_items.items():
                include_item = True
                for filter_option in selected_filters:
                    filter_tag = filter_option.lower().replace(" ", "-")
                    if filter_tag not in details["tags"]:
                        include_item = False
                        break
                if include_item:
                    filtered_items[item] = details
        if not filtered_items:
            st.warning("No items match your filters. Try adjusting your selection.")
        else:
            for item, details in filtered_items.items():
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.image(details["image"], width=80)
                with col2:
                    st.markdown(f'🍽 *{item}* - Rs{details["price"]} (Carbon: {details["carbon_footprint"]} kg CO2e)', unsafe_allow_html=True)
                    st.write(f"Calories: {details['calories']}, Protein: {details['protein']}g, Carbs: {details['carbs']}g, Fats: {details['fats']}g")
                with col3:
                    if st.button(f"Add {item}", key=f"menu_add_{item}"):
                        add_to_cart(item, details["price"], details["carbon_footprint"])
                    if st.button(f"Add to Favorites", key=f"menu_favorite_{item}"):
                        if item not in st.session_state["favorites"]:
                            st.session_state["favorites"].append(item)
                            st.success(f"{item} added to Favorites!")
                        else:
                            st.warning(f"{item} is already in Favorites!")

    elif menu_option == "Favorites":
        st.markdown('<h2 class="text-light">⭐ Favorites</h2>', unsafe_allow_html=True)
        if st.session_state["favorites"]:
            for item in st.session_state["favorites"]:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"⭐ {item}")
                with col2:
                    if st.button(f"Remove", key=f"favorites_remove_fav_{item}"):
                        st.session_state["confirmation_dialog"] = {"action": "remove from favorites", "item": item}
        else:
            st.write("No favorite items yet. Add items from the Menu page!")
        handle_confirmation()

    elif menu_option == "Order History":
        display_order_history_summary()

    elif menu_option == "Recommendations":
        st.markdown('<h2 class="text-light">🤖 Recommendations</h2>', unsafe_allow_html=True)
        recommendation = get_ai_recommendation()
        st.write(recommendation)

    elif menu_option == "Profile":
        st.markdown('<h2 class="text-light">👤 Profile</h2>', unsafe_allow_html=True)
        st.write(f"Email: {st.session_state['user']}")
        st.write(f"Total Spent: Rs{st.session_state['total_spent']}")
        st.write(f"Loyalty Points: {st.session_state['loyalty_points']}")
        st.write(f"Badges: {', '.join(st.session_state['badges'])}")
        if st.button("Simulate Payment", key="profile_pay_btn"):
            st.success("Payment of $10 processed via Stripe! (Mock)")

    elif menu_option == "Chatbot":
        st.markdown('<h2 class="text-light">🤖 SpendEATS Chatbot</h2>', unsafe_allow_html=True)
        st.write("Ask me anything about SpendEATS! Use the dropdown to explore common questions or type your query below.")
        chatbot_subcategories = {
            "Menu and Food Options": {
                "what are today's special dishes": "Today's specials are Chicken Biryani and Pizza! Would you like to add any to your cart?",
                "can i see the full menu": "Sure! Our menu includes: Chicken Biryani (Rs100), Mutton Biryani (Rs120), Pizza (Rs150), Burger (Rs60), Pepperoni (Rs40), and Margherita (Rs90). Go to the Menu page to add items to your cart!"
            },
            "Dietary Preferences and Restrictions": {
                "do you have any vegan options": "Yes, we have a vegan option: Margherita pizza. Would you like to add it to your cart?",
                "do you have any gluten-free options": "Unfortunately, we don’t have gluten-free options at the moment. Would you like to see the full menu?",
                "do you have any keto options": "Yes, Pepperoni is a keto-friendly option. Would you like to add it to your cart?",
                "do you have nut-free options": "Yes, most of our dishes are nut-free, including Chicken Biryani, Mutton Biryani, and Pepperoni. However, Pizza and Burger may contain nuts. Please let us know if you have severe allergies.",
                "do you have dairy-free options": "Unfortunately, most of our dishes contain dairy (e.g., cheese in Pizza). Pepperoni might be a safer option, but please confirm with us if you have allergies.",
                "can i get a dish without cheese": "We can try to prepare Pizza or Burger without cheese if you mention it when ordering. Please note this in your order comments!",
                "can i get a dish without onions": "Yes, we can prepare dishes like Chicken Biryani or Mutton Biryani without onions upon request. Mention it when you place your order.",
                "do you offer organic or locally sourced ingredients": "Yes, we source some ingredients locally, like vegetables and spices. However, not all items are organic. Would you like to know more about a specific dish?",
                "do you offer calorie or nutritional information": "Yes! Here’s the nutritional info: Chicken Biryani (800 kcal, 35g protein, 90g carbs, 25g fats), Mutton Biryani (850 kcal, 40g protein, 85g carbs, 30g fats), Pizza (700 kcal, 25g protein, 80g carbs, 30g fats), Burger (600 kcal, 20g protein, 50g carbs, 35g fats), Pepperoni (300 kcal, 15g protein, 5g carbs, 25g fats), Margherita (500 kcal, 15g protein, 60g carbs, 20g fats). You can also track your meals in the Nutrition Tracker section!"
            },
            "Recipe Filters": {
                "show me low-carb recipes": "Go to the Menu section and use the filters to select 'Low-Carb'. You’ll see items like Pepperoni (300 kcal, 5g carbs).",
                "show me keto recipes": "Go to the Menu section and use the filters to select 'Keto'. You’ll see items like Pepperoni (300 kcal, 5g carbs).",
                "show me gluten-free recipes": "Currently, we don’t have gluten-free options. Try filtering for Low-Carb or Keto recipes in the Menu section!",
                "show me high-protein recipes": "Go to the Menu section and use the filters to select 'High-Protein'. You’ll see items like Chicken Biryani (35g protein) and Mutton Biryani (40g protein).",
                "show me low-sodium recipes": "Go to the Menu section and use the filters to select 'Low-Sodium'. Note that some items may not be tagged yet; try Low-Carb or Vegan options!",
                "show me vegetarian recipes": "Go to the Menu section and use the filters to select 'Vegetarian'. You’ll see items like Margherita (500 kcal).",
                "show me vegan recipes": "Go to the Menu section and use the filters to select 'Vegan'. You’ll see items like Margherita (500 kcal)."
            },
            "Ordering Process": {
                "how do i place an order": "To place an order, go to the Menu page, click 'Add [Item]' for the dishes you want, then go to the Cart page and click 'Place Order'. Try it now!",
                "can i customize my order": "At the moment, we don’t support customizations through the app. However, you can mention special requests when you place your order, and we’ll do our best!",
                "what are the payment options": "We accept Credit/Debit cards, UPI, and Cash on Delivery. You can choose your preferred option when placing your order.",
                "can i schedule an order for later": "Currently, we don’t support scheduling orders for later. You can place your order now, and we’ll deliver it as soon as possible!",
                "how do i cancel or modify my order": "To cancel or modify your order, contact us at support@spendeats.com as soon as possible. We’ll do our best to assist you!"
            },
            "Delivery and Tracking": {
                "do you offer home delivery": "Yes, we offer home delivery! It typically takes 30-45 minutes depending on your location. Would you like to place an order?",
                "what is the estimated delivery time": "Estimated delivery time is 30-45 minutes after placing your order, depending on your location and order volume.",
                "how can i track my order": "After placing your order, you’ll receive a confirmation with tracking details. Check your email or the Cart page for updates."
            },
            "Restaurant Information": {
                "what are your opening hours": "We’re open from 10 AM to 10 PM daily. Ready to place an order?",
                "where are you located": "We’re located at 123 Foodie Lane, Gourmet City. Come visit us or order online!",
                "do you have dine-in options": "Yes, we offer dine-in! Visit us at 123 Foodie Lane, Gourmet City, between 10 AM to 10 PM.",
                "is there parking available": "Yes, we have parking available at our location on 123 Foodie Lane. Come dine in with us!"
            },
            "Promotions and Loyalty": {
                "do you have any special offers or discounts": "We don’t have any special offers right now, but you can earn loyalty points with every order! Check the Loyalty section for more details.",
                "do you have a loyalty program": "Yes! You earn 1 point per item ordered and 2 points for writing a review. Reach 10 points for a Bronze badge, 25 for Silver, and 50 for Gold. Check your points in the sidebar!",
                "how do i redeem my reward points": "You can use 10 points to edit your spending limit in the Spending Limit section. More rewards coming soon!",
                "are there any special promotions for members": "Not at the moment, but loyalty members earn badges and points with every order. Keep ordering to reach the next badge!"
            },
            "Support and Feedback": {
                "i have a problem with my order": "Sorry to hear that! Please email us at support@spendeats.com with your order details, and we’ll help you right away.",
                "how do i leave a review or give feedback": "You can leave a review in the Reviews section. Select an item, give a rating (1-5), and write your comment. You’ll earn 2 loyalty points for each review!"
            },
            "General Interaction": {
                "hello": "Hi! How can I assist you with SpendEATS today?",
                "help": "I can help with the menu, ordering, delivery, restaurant info, dietary needs, support, loyalty program, spending limit, reviews, diet plans, nutrition tracking, or recipe filters. What would you like to know?",
                "bye": "Goodbye! Visit SpendEATS again soon!"
            }
        }
        st.markdown('<div class="text-light">Explore Common Questions by Category</div>', unsafe_allow_html=True)
        selected_subcategory = st.selectbox("", list(chatbot_subcategories.keys()), key="chatbot_subcategory_dropdown")
        st.subheader(f"Questions in {selected_subcategory}")
        for query in chatbot_subcategories[selected_subcategory]:
            if st.button(query, key=f"chatbot_query_{query}"):
                st.session_state["chat_history"].append(("You", query))
                response = get_mock_response(query)
                st.session_state["chat_history"].append(("Bot", response))
                st.rerun()
        user_input = st.text_input("Or type your question here:", key="chatbot_user_input")
        if st.button("Ask", key="chatbot_ask_btn"):
            if user_input:
                st.session_state["chat_history"].append(("You", user_input))
                response = get_mock_response(user_input)
                st.session_state["chat_history"].append(("Bot", response))
                st.rerun()
        st.subheader("Chat History")
        if st.session_state["chat_history"]:
            for sender, message in st.session_state["chat_history"]:
                st.write(f"**{sender}:** {message}")
        else:
            st.write("No chat history yet. Ask a question to get started!")

    elif menu_option == "Reviews":
        st.markdown('<h2 class="text-light">📝 Reviews & Ratings</h2>', unsafe_allow_html=True)
        st.subheader("Submit a Review")
        with st.form(key="review_form"):
            item = st.selectbox("Select Item", list(menu_items.keys()), key="review_item")
            rating = st.slider("Rating", 1, 5, 3, key="review_rating")
            comment = st.text_area("Comment", key="review_comment")
            if st.form_submit_button("Submit Review"):
                submit_review(item, rating, comment)
                st.success("Review submitted successfully!")
        st.subheader("All Reviews")
        reviews = fetch_reviews()
        if reviews:
            for review in reviews:
                st.markdown(f"**{review['item']}** - {review['rating']}/5")
                st.write(f"By {review['user_id']} on {review['date']}")
                st.write(f"Comment: {review['comment']}")
                st.markdown("---")
        else:
            st.write("No reviews yet. Be the first to write one!")

    elif menu_option == "Smart Meal Scheduler":
        st.markdown('<h2 class="text-light">📅 Smart Meal Scheduler</h2>', unsafe_allow_html=True)
        st.subheader("Set Your Availability for Today")
        current_day = datetime.now().strftime("%A")
        availability = {}
        st.write(f"**{current_day}**")
        num_slots = st.number_input(f"Number of available time slots for today ({current_day})", min_value=0, max_value=5, value=0, key=f"scheduler_slots_{current_day}")
        day_slots = []
        for i in range(num_slots):
            col1, col2 = st.columns(2)
            with col1:
                start_time = st.number_input(f"Start Time (Hour, 0-23) - Slot {i+1}", min_value=0, max_value=23, value=8, key=f"scheduler_start_{current_day}_{i}")
            with col2:
                end_time = st.number_input(f"End Time (Hour, 0-23) - Slot {i+1}", min_value=0, max_value=23, value=10, key=f"scheduler_end_{current_day}_{i}")
            if start_time < end_time:
                day_slots.append((start_time, end_time))
            else:
                st.error(f"End time must be greater than start time for {current_day} slot {i+1}.")
        availability[current_day] = day_slots
        st.subheader("Preferences")
        fitness_goal = st.selectbox("Fitness Goal", ["Weight Loss", "Muscle Gain", "General Health"], key="scheduler_fitness_goal")
        dietary_preference = st.selectbox("Dietary Preference", ["None", "Vegetarian", "Vegan"], key="scheduler_dietary_preference")
        allergies = st.text_input("Allergies (e.g., nuts, dairy)", key="scheduler_allergies")
        if st.button("Generate Meal Schedule for Today", key="scheduler_generate_btn"):
            save_meal_schedule(availability, fitness_goal, dietary_preference, allergies)
        st.subheader("Your Meal Schedule for Today")
        display_meal_schedule()

    elif menu_option == "Personalized Recipe Generator":
        st.markdown('<h2 class="text-light">🍳 Personalized Recipe Generator</h2>', unsafe_allow_html=True)
        for recipe in st.session_state["custom_recipes"]:
            if "price" not in recipe or "carbon_footprint" not in recipe:
                total_cost = 0
                total_carbon_footprint = 0
                for ingredient in recipe["ingredients"]:
                    if ingredient in base_ingredients:
                        total_cost += base_ingredients[ingredient]["cost"]
                        total_carbon_footprint += 0.5
                recipe["price"] = round(total_cost * 1.2)
                recipe["carbon_footprint"] = round(total_carbon_footprint, 1)
            recipe["prep_time"] = len(recipe["ingredients"]) * 5
            cooking_steps = []
            base = next((ing for ing in recipe["ingredients"] if base_ingredients[ing]["category"] == "base"), None)
            if base:
                cooking_steps.append(f"Prepare the {base} according to package instructions (e.g., boil the {base} until tender).")
            protein = next((ing for ing in recipe["ingredients"] if base_ingredients[ing]["category"] == "protein"), None)
            if protein:
                cooking_steps.append(f"Cook the {protein} (e.g., grill or pan-fry the {protein} until fully cooked).")
            vegetable = next((ing for ing in recipe["ingredients"] if base_ingredients[ing]["category"] == "vegetable"), None)
            if vegetable:
                cooking_steps.append(f"Chop the {vegetable} and sauté it in a pan until tender.")
            cooking_steps.append("Combine all ingredients in a bowl or plate, mix well, and serve hot.")
            recipe["instructions"] = cooking_steps
            prefixes = {"Weight Loss": "Light", "Muscle Gain": "Power", "General Health": "Balanced"}
            fitness_goal = "General Health"
            if "low-calorie" in recipe["tags"]:
                fitness_goal = "Weight Loss"
            elif "high-protein" in recipe["tags"]:
                fitness_goal = "Muscle Gain"
            dish_type = "Bowl"
            if base == "pasta":
                dish_type = "Pasta"
            elif protein:
                dish_type = "Stir-Fry"
            main_ingredient = next((ing for ing in recipe["ingredients"] if base_ingredients[ing]["category"] in ["protein", "vegetable"]), recipe["ingredients"][0])
            recipe["name"] = f"{prefixes[fitness_goal]} {main_ingredient.capitalize()} {dish_type}"
        display_custom_recipes()
        with st.form("custom_recipe_form"):
            fitness_goal = st.selectbox("Fitness Goal", ["Weight Loss", "Muscle Gain", "General Health"])
            dietary_preference = st.selectbox("Dietary Preference", ["None", "Vegetarian", "Vegan"])
            allergies = st.text_input("Allergies (comma-separated)", placeholder="e.g., nuts, dairy")
            max_calories = st.number_input("Max Calories (optional)", min_value=0, value=0, step=50)
            generate_recipe = st.form_submit_button("Generate Recipe")
            if generate_recipe:
                max_calories = max_calories if max_calories > 0 else None
                save_custom_recipe(fitness_goal, dietary_preference, allergies, max_calories)

    if st.session_state["show_popup"]:
        with st.container():
            st.markdown("## ⚠ Spending Limit Exceeded!")
            st.write(f"You've exceeded your monthly spending limit of Rs{st.session_state['spending_limit']['Monthly']}")
            st.write(f"Total Spent: Rs{st.session_state['total_spent']}")
            if st.button("Close", key="popup_close_btn"):
                st.session_state["show_popup"] = False
                st.rerun()
