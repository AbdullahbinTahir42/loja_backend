from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
import schemas,auth,models
from database import SessionLocal, engine, Base



app = FastAPI()
origins = ['http://localhost:5173/']


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


@app.post("/register/", response_model=schemas.UserCreate, tags=["Authentication"])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new user, hashes their password, and sets default roles."""
    if get_user(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=auth.get_password_hash(user.password),
        role='candidate' # All new users are candidates by default
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Handles user login and returns a JWT access token."""
    user = get_user(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def home():
    return "ITS REALLY RUNNING!!!!!!"