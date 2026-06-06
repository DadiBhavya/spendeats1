# 🍽 SpendEATS — Bite Right, Spend Light

> A smart food ordering web app that helps you eat well, track nutrition, and stay within budget — all in one place.

---

##  Overview

**SpendEATS** is a feature-rich food ordering platform built with **Streamlit** and **Firebase**. It goes beyond a typical food app by combining meal planning, nutritional tracking, spending management, and personalized recipe generation — helping users make healthier and more budget-conscious food choices.

---

## Features

| Feature | Description |
|---|---|
| 🔐 **Authentication** | Secure signup, login, and password reset via Firebase Auth + Firestore |
| 🛒 **Menu & Cart** | Browse menu items, filter by dietary tags, add to cart, and place orders |
| 💰 **Spending Limit Manager** | Set monthly spending limits; uses loyalty points or badges to allow edits |
| 🎖 **Loyalty & Badges** | Earn points per order/review; unlock Bronze, Silver, and Gold badges |
| 🥗 **Diet Plan Generator** | Auto-generates Breakfast/Lunch/Dinner plans based on fitness goals and dietary preferences |
| 🍽 **Nutrition Tracker** | Log meals and track daily calories, protein, carbs, fats, and vitamins |
| 📅 **Smart Meal Scheduler** | Schedules meals around your availability and prep times for the current day |
| 🍳 **Personalized Recipe Generator** | Creates custom recipes from your past orders, fitness goal, and dietary preferences |
| 📊 **Order History Summary** | View spending trends with monthly bar charts and most-ordered items |
| ⭐ **Favorites** | Save and manage your favorite menu items |
| 📝 **Reviews & Ratings** | Submit reviews with ratings, earn loyalty points, view all community reviews |
| 🤖 **Chatbot** | Rule-based chatbot for menu help, dietary queries, ordering guidance, and more |
| 🌱 **Carbon Footprint Tracker** | View estimated CO₂ impact per item and for your full cart |

---

## Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend / Database**: [Firebase Firestore](https://firebase.google.com/docs/firestore)
- **Authentication**: [Firebase Authentication](https://firebase.google.com/docs/auth)
- **Visualization**: Matplotlib
- **UI Components**: `streamlit-option-menu`, PIL (Pillow)
- **Language**: Python 3.9+

---

##  Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/spendeats.git
cd spendeats
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key packages:**
```
streamlit
firebase-admin
streamlit-option-menu
matplotlib
Pillow
google-cloud-firestore
```

### 3. Set Up Firebase

1. Go to the [Firebase Console](https://console.firebase.google.com/) and create a project.
2. Enable **Firestore Database** and **Authentication (Email/Password)**.
3. Download your **Service Account Key** (`serviceAccountKey.json`) from Project Settings → Service Accounts.

### 4. Configure Credentials

**Option A – Local Development:**

Place `serviceAccountKey.json` in the root of the project directory.

**Option B – Streamlit Cloud Deployment:**

Add your service account JSON as a secret in your Streamlit app settings:

```toml
# .streamlit/secrets.toml
SERVICE_ACCOUNT_KEY = '''{ your full JSON here }'''
```

### 5. Add Menu Images

Place food images in an `images/` folder at the project root. Expected filenames:

```
images/chicken_biryani.jpg
images/mutton_biryani.jpg
images/pizza.jpg
images/burger.jpg
images/pepperoni.jpg
images/margherita.jpg
images/lentil_curry.jpg
images/paneer_tikka.jpg
images/salmon_grilled.jpg
images/aloo_gobi.jpg
images/mushroom_risotto.jpg
```

### 6. Run the App

```bash
streamlit run app.py
```

---

## Project Structure

```
spendeats/
├── app.py                  # Main application file
├── serviceAccountKey.json  # Firebase credentials (DO NOT commit this)
├── images/                 # Menu item images
├── .streamlit/
│   └── secrets.toml        # Streamlit secrets (for cloud deployment)
├── requirements.txt
└── README.md
```

---

## Security Notice

> ⚠️ **Never commit `serviceAccountKey.json` to your repository.**

Add it to your `.gitignore`:

```
serviceAccountKey.json
.streamlit/secrets.toml
```

---

## How Key Features Work

### Spending Limit System
- First edit is free for new users.
- Subsequent edits cost **10 loyalty points** or **1 badge** (highest tier sacrificed first).
- Maximum **2 edits per month** per user.

### Loyalty Points & Badges
- +1 point per item added to cart
- +2 points per review submitted
- Thresholds: Bronze (10 pts) → Silver (25 pts) → Gold (50 pts)

### Diet Plan & Meal Scheduler
- Filters menu items by fitness goal (Weight Loss / Muscle Gain / General Health), dietary preference, and allergies.
- Meal Scheduler respects real-time clock — only schedules meals in future time slots.

### Recipe Generator
- Derives available ingredients from the user's past orders.
- Builds a recipe by combining base + protein + vegetable + seasoning + topping categories.
- Adjusts nutritional profile based on fitness goal.

---

## Deployment

Deploy easily on **Streamlit Community Cloud**:

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Add `SERVICE_ACCOUNT_KEY` under **Secrets** in the app settings.
4. Click **Deploy**.

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---


---

## 👤 Author

Built with ❤️ as a personal project. Feel free to reach out or open an issue if you have questions!
