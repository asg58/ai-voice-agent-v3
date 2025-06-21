"""
User service for GraphQL API
"""
import logging
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_all_users():
    """
    Get all users
    
    Returns:
        list: List of User objects
    """
    db = next(get_db())
    return db.query(User).all()


def get_user_by_id(user_id: int):
    """
    Get a user by ID
    
    Args:
        user_id (int): User ID
    
    Returns:
        User: User object
    """
    db = next(get_db())
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(username: str):
    """
    Get a user by username
    
    Args:
        username (str): Username
    
    Returns:
        User: User object
    """
    db = next(get_db())
    return db.query(User).filter(User.username == username).first()


def create_user(username: str, email: str, password: str, is_active: bool = True, is_superuser: bool = False):
    """
    Create a new user
    
    Args:
        username (str): Username
        email (str): Email
        password (str): Password
        is_active (bool, optional): Is active. Defaults to True.
        is_superuser (bool, optional): Is superuser. Defaults to False.
    
    Returns:
        User: Created user
    """
    db = next(get_db())
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        if existing_user.username == username:
            raise ValueError(f"Username '{username}' already exists")
        else:
            raise ValueError(f"Email '{email}' already exists")
    
    # Create new user
    hashed_password = pwd_context.hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_active=is_active,
        is_superuser=is_superuser
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"Created user: {username}")
    return user


def update_user(user_id: int, username: str = None, email: str = None, password: str = None, 
                is_active: bool = None, is_superuser: bool = None):
    """
    Update an existing user
    
    Args:
        user_id (int): User ID
        username (str, optional): Username. Defaults to None.
        email (str, optional): Email. Defaults to None.
        password (str, optional): Password. Defaults to None.
        is_active (bool, optional): Is active. Defaults to None.
        is_superuser (bool, optional): Is superuser. Defaults to None.
    
    Returns:
        User: Updated user
    """
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    # Update fields if provided
    if username is not None:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user and existing_user.id != user_id:
            raise ValueError(f"Username '{username}' already exists")
        user.username = username
    
    if email is not None:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user and existing_user.id != user_id:
            raise ValueError(f"Email '{email}' already exists")
        user.email = email
    
    if password is not None:
        user.hashed_password = pwd_context.hash(password)
    
    if is_active is not None:
        user.is_active = is_active
    
    if is_superuser is not None:
        user.is_superuser = is_superuser
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"Updated user: {user.username}")
    return user


def delete_user(user_id: int):
    """
    Delete a user
    
    Args:
        user_id (int): User ID
    
    Returns:
        bool: True if successful
    """
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    db.delete(user)
    db.commit()
    
    logger.info(f"Deleted user: {user.username}")
    return True


def verify_password(plain_password: str, hashed_password: str):
    """
    Verify password
    
    Args:
        plain_password (str): Plain password
        hashed_password (str): Hashed password
    
    Returns:
        bool: True if password is correct
    """
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    """
    Authenticate user
    
    Args:
        username (str): Username
        password (str): Password
    
    Returns:
        User: User object if authentication is successful, None otherwise
    """
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user