from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer,HTTPAuthorizationCredentials
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
import schemas,auth,models
from database import SessionLocal, engine, Base
import logging
from jose import JWTError, jwt
import os
import shutil
import uuid




app = FastAPI()
origins = ["http://localhost:5173"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # Specifies the allowed origins
    allow_credentials=True,        # Allows cookies to be included in requests
    allow_methods=["*"],           # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],           # Allows all headers
)


Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AUTH_DEBUG")


IMAGES_UPLOAD_DIR = "images"

os.makedirs(IMAGES_UPLOAD_DIR, exist_ok=True)

app.mount(f"/{IMAGES_UPLOAD_DIR}", StaticFiles(directory=IMAGES_UPLOAD_DIR), name="images")

security = HTTPBearer(auto_error=False)

def get_db():
    """Dependency to get the database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(db: Session, email: str):
    """Fetch a user by email from the database."""
    return db.query(models.User).filter(models.User.email == email).first() 



async def get_current_active_user(
    # Correctly type hint the dependency result as an object
    auth_credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Decodes JWT token to get the current active user.
    """
    if auth_credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # The token is a string inside the .credentials attribute
    token = auth_credentials.credentials
    logger.info(f"🎫 Token received (first 20 chars): {token[:20]}...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str | None = payload.get("sub")
        
        if email is None:
            logger.error("❌ 'sub' claim (email) not found in token payload")
            raise credentials_exception
            
    except JWTError as e:
        logger.error(f"❌ JWT decode error: {e}")
        raise credentials_exception
    
    user = get_user(db, email=email)
    
    if user is None:
        logger.error(f"❌ User '{email}' not found in database")
        raise credentials_exception
        
    logger.info(f"✅ User authenticated successfully: {user.email}")
    return user

@app.get("/users/me", response_model=schemas.S_User, tags=["Authentication"])
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user)
):
    return current_user

def get_current_admin_user(user : models.User = Depends(get_current_active_user)):
    """Dependency to ensure the current user is an admin."""
    if user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.post("/register", response_model=schemas.S_User, tags=["Authentication"])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new user, hashes their password, and sets default roles."""
    if user.password != user.confirmPassword:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if get_user(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        password=auth.get_password_hash(user.password),
        role='consumer' # All new users are consumers by default
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login(
    # This is the crucial change. It correctly reads the form data.
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
):
    
    user = get_user(db, email=form_data.username)
    
    # 4. Use form_data.password for the password
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, 
        )
    
    
    access_token = auth.create_access_token(
        data={"sub": user.email}, 
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/admin/create/items", response_model=schemas.Item, tags=["Admin"])
def create_item(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_admin_user),
    # Change from a single JSON body to form fields
    name: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    quantity: int = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Creates a new item with an image upload.
    Accepts multipart/form-data.
    """
    if price < 0 or quantity < 0:
        raise HTTPException(status_code=400, detail="Price and quantity must be positive integers")
    # 1. Generate a unique filename to prevent conflicts
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(IMAGES_UPLOAD_DIR, unique_filename)

    # 2. Save the uploaded file to the server
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Create a dictionary with the item data from the form
    item_data = {
        "name": name,
        "description": description,
        "price": price,
        "quantity": quantity,
        "category": category
    }

    # 4. Create the SQLAlchemy model instance
    db_item = models.Item(**item_data, image_name=unique_filename)
    
    # 5. Add to the database and commit
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@app.get("/items", response_model=list[schemas.Item])
def get_items(db: Session = Depends(get_db)):
    """Retrieves the latest 5 items from the database."""
    items = db.query(models.Item).all()
    return items

@app.get("/items/men", response_model=list[schemas.Item])
def get_men_items(db: Session = Depends(get_db)):
    items = db.query(models.Item).filter(models.Item.category == "Men").all()
    return items

@app.get("/items/women", response_model=list[schemas.Item])
def get_women_items(db: Session = Depends(get_db)):
    items = db.query(models.Item).filter(models.Item.category == "Women").all()
    return items

@app.get("/items/accessories", response_model=list[schemas.Item])
def get_accessories_items(db: Session = Depends(get_db)):
    items = db.query(models.Item).filter(models.Item.category == "Accessories").all()
    return items

@app.get("/items/{item_id}", response_model=schemas.Item)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Retrieves a specific item by its ID."""
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/search/items", response_model=list[schemas.Item])
def search_items(q: str, db: Session = Depends(get_db)):
    """
    Searches for items by name, case-insensitively.
    """
    # The '%' are wildcards, so it finds partial matches
    search_query = f"%{q}%"
    
    # Use .ilike() for case-insensitive partial matching
    items = db.query(models.Item).filter(models.Item.name.ilike(search_query)).all()
    
    return items


@app.post("/user/cart", response_model=schemas.Cart, tags=["Cart"])
def add_to_cart(cart: schemas.CartCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    user_cart = models.Cart(
        user_id=current_user.id,
        item_id=cart.item_id,
        quantity=cart.quantity
    )
    db.add(user_cart)
    db.commit()
    db.refresh(user_cart)
    return user_cart


@app.get("/user/cart", response_model=list[schemas.Cart], tags=["Cart"])
def get_cart(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    """Retrieves the current user's cart."""
    cart_items = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).all()
    return cart_items


@app.delete("/user/cart/{cart_item_id}", response_model=schemas.Cart, tags=["Cart"])
def remove_from_cart(cart_item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    """Removes an item from the user's cart."""
    cart_item = db.query(models.Cart).filter(models.Cart.id == cart_item_id, models.Cart.user_id == current_user.id).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    return cart_item


@app.post("/order", response_model=schemas.Order)
def create_order(
    order: schemas.OrderCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
   
    
    # 1. Get all cart items for the currently authenticated user.
    cart_items = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).all()
    
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")
    
    # 2. Calculate the total amount based on the prices and quantities in the cart.
    total_amount = sum(item.item.price * item.quantity for item in cart_items)
    
    if total_amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Total amount must be positive")
    
    # 3. Create the main Order object with customer details.
    new_order = models.Order(
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_address=order.customer_address,
        status="pending",  # It's best practice to set a default status on the backend.
        total_amount=total_amount,
        customer_id=current_user.id
    )
    
    # 4. Create an OrderItem for each item in the cart and link it to the new Order.
    # The `cascade` option in your Order model's relationship will handle adding these.
    for item in cart_items:
        order_item = models.OrderItem(
            item_id=item.item_id,
            quantity=item.quantity,
            price=item.item.price  # Store the price at the time of the order.
        )
        item.item.quantity -= item.quantity
        # By appending to the relationship, SQLAlchemy knows to link this
        # OrderItem to the new_order when it's saved.
        new_order.items.append(order_item)

    # 5. Add the new_order (which now contains its associated items) to the session.
    db.add(new_order)
 
    db.query(models.Cart).filter(models.Cart.user_id == current_user.id).delete(synchronize_session=False)

    db.commit()

    db.refresh(new_order)
    
    return new_order


@app.get("/admin/stats", tags=["Admin"])
def get_admin_stats(db: Session = Depends(get_db), user: models.User = Depends(get_current_admin_user)):
    """
    Returns statistics for the admin dashboard.
    """
    total_users = db.query(models.User).count()
    total_items = db.query(models.Item).count()
    total_orders = db.query(models.Order).count()
    total_revenue = db.query(models.Order).filter(models.Order.status == "completed").with_entities(func.sum(models.Order.total_amount)).scalar() or 0
    
    return {
        "total_users": total_users,
        "total_items": total_items,
        "total_orders": total_orders,
        "total_revenue": total_revenue
    }

@app.get("/admin/orders", response_model=list[schemas.Order], tags=["Admin"])
def get_admin_orders(db: Session = Depends(get_db), user: models.User = Depends(get_current_admin_user)):
   
    orders = db.query(models.Order).all()
    return orders

@app.get("/admin/users", response_model=list[schemas.S_User], tags=["Admin"])
def get_admin_users(db: Session = Depends(get_db), user: models.User = Depends(get_current_admin_user)):
    """Retrieves all users for admin view."""
    users = db.query(models.User).filter(models.User.role != 'admin').all()
    
    return users

@app.get("/admin/order/items/{order_id}", response_model=list[schemas.OrderItem], tags=["Admin"])
def get_admin_order_items(order_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_admin_user)):
    """Retrieves all items for a specific order."""
    order_items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order_id).all()
    return order_items

@app.get("/")
def home():
    return "ITS REALLY RUNNING!!!!!!"