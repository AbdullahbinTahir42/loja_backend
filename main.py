from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer,HTTPAuthorizationCredentials
from typing import Annotated
from sqlalchemy.orm import Session
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
    db_item = models.Items(**item_data, image_name=unique_filename)
    
    # 5. Add to the database and commit
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@app.get("/items", response_model=list[schemas.Item])
def get_items(db: Session = Depends(get_db)):
    """Retrieves the latest 5 items from the database."""
    items = db.query(models.Items).limit(5).all()
    return items

@app.get("/items/men", response_model=list[schemas.Item])
def get_men_items(db: Session = Depends(get_db)):
    items = db.query(models.Items).filter(models.Items.category == "Men").all()
    return items

@app.get("/items/women", response_model=list[schemas.Item])
def get_women_items(db: Session = Depends(get_db)):
    items = db.query(models.Items).filter(models.Items.category == "Women").all()
    return items

@app.get("/items/accessories", response_model=list[schemas.Item])
def get_accessories_items(db: Session = Depends(get_db)):
    items = db.query(models.Items).filter(models.Items.category == "Accessories").all()
    return items

@app.get("/items/{item_id}", response_model=schemas.Item)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Retrieves a specific item by its ID."""
    item = db.query(models.Items).filter(models.Items.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/")
def home():
    return "ITS REALLY RUNNING!!!!!!"