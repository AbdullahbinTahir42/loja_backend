🛒 E-commerce Store API
A modern, production-ready backend for an e-commerce platform built with FastAPI. This API handles product management, user authentication, shopping cart logic, and order processing—with a dedicated Admin Panel for store operations and analytics.

✨ Features
🔐 Secure JWT Authentication
User registration and login with hashed passwords and token-based session management.

👤 Role-Based Access Control (RBAC)
Separate permissions for consumers and administrators.

🛍️ Product Catalog
Full CRUD support with image uploads, category filters, and search functionality.

🛒 Shopping Cart System
Add, view, and remove items from your cart before checkout.

🧾 Order Processing
Seamless order creation that clears the cart and updates inventory.

📊 Admin Dashboard
View revenue, users, and orders, and manage store data from a centralized admin interface.

🛠️ Tech Stack
Framework: FastAPI

ORM: SQLAlchemy (compatible with PostgreSQL, SQLite, etc.)

Auth: python-jose for JWT, passlib[bcrypt] for password hashing

Validation: Pydantic

File Handling: Static image uploads

Server: Uvicorn

🚀 Getting Started
✅ Prerequisites
Python 3.8+

A relational database (PostgreSQL or SQLite)

📦 Installation
Clone the repository

bash
Copy
Edit
git clone [<your-repository-url>](https://github.com/AbdullahbinTahir42/remote_job)
Set up a virtual environment

On Windows:

bash
python -m venv venv
.\venv\Scripts\activate
On macOS/Linux:

bash

python3 -m venv venv
source venv/bin/activate
Install dependencies
(You can generate a requirements.txt later. For now:)

bash

pip install fastapi uvicorn sqlalchemy python-jose[cryptography] passlib[bcrypt] python-multipart
Configure environment variables

Example auth.py:

python

SECRET_KEY = "your-very-secret-key-that-is-long-and-random"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
Run the server

bash

uvicorn main:app --reload
Visit: http://127.0.0.1:8000/docs for Swagger UI.

📚 API Overview
🔐 Authentication
Method	Path	Description	Auth
POST	/register	Register new users	❌
POST	/token	Get JWT access token	❌
GET	/users/me	Get current user's profile	✅

🛍️ Products
Method	Path	Description	Auth
GET	/items	List all products	❌
GET	/items/{category}	Filter products by category	❌
GET	/items/{item_id}	Product details by ID	❌
GET	/search/items?q=	Search products by name	❌

🛒 Cart
Method	Path	Description	Auth
POST	/user/cart	Add item to cart	✅
GET	/user/cart	View user's cart	✅
DELETE	/user/cart/{id}	Remove item from cart	✅

🧾 Orders
Method	Path	Description	Auth
POST	/order	Create order from current cart	✅
GET	/user/orders	Get current user's order history	✅
GET	/user/order/items/{id}	View items in a specific order	✅

🛠️ Admin Panel
⚠️ Admin role required

Method	Path	Description
POST	/admin/create/items	Create a new product (with image upload)
GET	/admin/stats	View revenue, user count, and orders
GET	/admin/orders	View all orders
GET	/admin/users	List all registered users
GET	/admin/order/items/{id}	View items in any order
POST	/admin/order/{id}	Update order status (e.g., 'shipped')

📎 Notes
You can move secret keys and sensitive variables to a .env file and use python-dotenv to load them securely.

Future enhancements could include:

Payment gateway integration

Email notifications

Wishlist support

Multi-vendor architecture
