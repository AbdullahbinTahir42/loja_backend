from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
import schemas,auth,models
from database import SessionLocal, engine, Base



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
    """Handles user login and returns a JWT access token."""
    
    # 3. Use form_data.username to get the email from the form
    # The React frontend is already sending the email in the 'username' field
    user = get_user(db, email=form_data.username)
    
    # 4. Use form_data.password for the password
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard practice for 401 errors
        )
    
    # Make sure your create_access_token function is correctly imported from your auth module
    access_token = auth.create_access_token(
        data={"sub": user.email}, 
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
@app.get("/")
def home():
    return "ITS REALLY RUNNING!!!!!!"