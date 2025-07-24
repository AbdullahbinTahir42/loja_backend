from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta



app = FastAPI()


# @app.post("/register/", response_model=schemas.S_User, tags=["Authentication"])
# def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     """Registers a new user, hashes their password, and sets default roles."""
#     if get_user(db, email=user.email):
#         raise HTTPException(status_code=400, detail="Email already registered")
    
#     db_user = models.User(
#         email=user.email,
#         full_name=user.full_name,
#         phone_number=user.phone_number,
#         hashed_password=auth.get_password_hash(user.password),
#         role='candidate' # All new users are candidates by default
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# @app.post("/token", response_model=schemas.Token, tags=["Authentication"])
# async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     """Handles user login and returns a JWT access token."""
#     user = get_user(db, email=form_data.username)
#     if not user or not verify_password(form_data.password, user.hashed_password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    
#     access_token = create_access_token(
#         data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#     return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def home():
    return "ITS REALLY RUNNING!!!!!!"