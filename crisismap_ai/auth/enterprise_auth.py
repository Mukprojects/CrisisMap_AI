"""
Enterprise Authentication & Authorization System.

This module provides enterprise-grade authentication, authorization,
role-based access control, and security features.
"""

import os
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import jwt
import bcrypt
from passlib.context import CryptContext
from passlib.hash import pbkdf2_sha256
import pyotp
import qrcode
from io import BytesIO
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import redis
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from authlib.integrations.requests_client import OAuth2Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class UserRole(Enum):
    """User roles with hierarchical permissions."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    ANALYST = "analyst"
    OPERATOR = "operator"
    VIEWER = "viewer"
    API_USER = "api_user"
    GUEST = "guest"


class Permission(Enum):
    """Granular permissions for different operations."""
    # Data permissions
    READ_ALL_DATA = "read_all_data"
    READ_PUBLIC_DATA = "read_public_data"
    WRITE_DATA = "write_data"
    DELETE_DATA = "delete_data"
    
    # AI & Analytics
    USE_AI_MODELS = "use_ai_models"
    TRAIN_MODELS = "train_models"
    ACCESS_PREDICTIONS = "access_predictions"
    MODIFY_MODELS = "modify_models"
    
    # Administration
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_API_KEYS = "manage_api_keys"
    
    # Monitoring & Alerts
    VIEW_MONITORING = "view_monitoring"
    MANAGE_ALERTS = "manage_alerts"
    ACCESS_REAL_TIME = "access_real_time"
    
    # Reports & Export
    GENERATE_REPORTS = "generate_reports"
    EXPORT_DATA = "export_data"
    SCHEDULED_REPORTS = "scheduled_reports"


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    jwt_secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 12
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    mfa_required_for_admin: bool = True
    session_timeout_minutes: int = 60
    encryption_key: Optional[str] = None
    
    def __post_init__(self):
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key().decode()


# Database Models
class User(Base):
    """User model with enhanced security features."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.VIEWER.value)
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    organization = Column(String(200))
    department = Column(String(100))
    
    # Security fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(32))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Login tracking
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # Additional metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class APIKey(Base):
    """API key model for programmatic access."""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(10), nullable=False)
    
    # Permissions and restrictions
    permissions = Column(JSON, default=list)
    rate_limit_per_minute = Column(Integer, default=60)
    allowed_ips = Column(JSON, default=list)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_used = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class UserSession(Base):
    """User session tracking."""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)
    
    # Session information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_fingerprint = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_activity = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class AuditLog(Base):
    """Comprehensive audit logging."""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    action = Column(String(100), nullable=False)
    
    # Request information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    endpoint = Column(String(255))
    method = Column(String(10))
    
    # Event details
    details = Column(JSON, default=dict)
    result = Column(String(20))  # success, failure, error
    error_message = Column(Text)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class EnterpriseAuthSystem:
    """Enterprise-grade authentication and authorization system."""
    
    def __init__(self, config: SecurityConfig = None):
        """Initialize the authentication system."""
        self.config = config or SecurityConfig()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.fernet = Fernet(self.config.encryption_key.encode())
        self.redis_client = self._setup_redis()
        self.db_session = self._setup_database()
        
        # Role-based permissions mapping
        self.role_permissions = self._setup_role_permissions()
        
        # OAuth providers configuration
        self.oauth_providers = self._setup_oauth_providers()
        
        logger.info("🔐 Enterprise Authentication System initialized")
    
    def _setup_redis(self) -> redis.Redis:
        """Setup Redis for session management and rate limiting."""
        try:
            return redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD'),
                db=0,
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            return None
    
    def _setup_database(self):
        """Setup database connection."""
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./crisismap_auth.db')
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    
    def _setup_role_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Define role-based permission mappings."""
        return {
            UserRole.SUPER_ADMIN: list(Permission),  # All permissions
            UserRole.ADMIN: [
                Permission.READ_ALL_DATA,
                Permission.WRITE_DATA,
                Permission.USE_AI_MODELS,
                Permission.ACCESS_PREDICTIONS,
                Permission.MANAGE_USERS,
                Permission.VIEW_AUDIT_LOGS,
                Permission.MANAGE_API_KEYS,
                Permission.VIEW_MONITORING,
                Permission.MANAGE_ALERTS,
                Permission.ACCESS_REAL_TIME,
                Permission.GENERATE_REPORTS,
                Permission.EXPORT_DATA,
            ],
            UserRole.ANALYST: [
                Permission.READ_ALL_DATA,
                Permission.WRITE_DATA,
                Permission.USE_AI_MODELS,
                Permission.ACCESS_PREDICTIONS,
                Permission.VIEW_MONITORING,
                Permission.ACCESS_REAL_TIME,
                Permission.GENERATE_REPORTS,
                Permission.EXPORT_DATA,
            ],
            UserRole.OPERATOR: [
                Permission.READ_ALL_DATA,
                Permission.USE_AI_MODELS,
                Permission.ACCESS_PREDICTIONS,
                Permission.VIEW_MONITORING,
                Permission.MANAGE_ALERTS,
                Permission.ACCESS_REAL_TIME,
            ],
            UserRole.VIEWER: [
                Permission.READ_PUBLIC_DATA,
                Permission.VIEW_MONITORING,
                Permission.ACCESS_REAL_TIME,
            ],
            UserRole.API_USER: [
                Permission.READ_PUBLIC_DATA,
                Permission.USE_AI_MODELS,
                Permission.ACCESS_PREDICTIONS,
            ],
            UserRole.GUEST: [
                Permission.READ_PUBLIC_DATA,
            ]
        }
    
    def _setup_oauth_providers(self) -> Dict[str, Dict]:
        """Setup OAuth provider configurations."""
        return {
            'google': {
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI'),
                'authorization_url': 'https://accounts.google.com/o/oauth2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
                'scope': ['openid', 'email', 'profile']
            },
            'microsoft': {
                'client_id': os.getenv('MICROSOFT_CLIENT_ID'),
                'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET'),
                'redirect_uri': os.getenv('MICROSOFT_REDIRECT_URI'),
                'authorization_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
                'scope': ['openid', 'profile', 'email']
            },
            'okta': {
                'client_id': os.getenv('OKTA_CLIENT_ID'),
                'client_secret': os.getenv('OKTA_CLIENT_SECRET'),
                'redirect_uri': os.getenv('OKTA_REDIRECT_URI'),
                'authorization_url': os.getenv('OKTA_AUTHORIZATION_URL'),
                'token_url': os.getenv('OKTA_TOKEN_URL'),
                'userinfo_url': os.getenv('OKTA_USERINFO_URL'),
                'scope': ['openid', 'profile', 'email']
            }
        }
    
    # User Management
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.VIEWER,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new user with enhanced security validation."""
        try:
            # Validate input
            self._validate_password(password)
            
            # Check if user already exists
            existing_user = self.db_session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this username or email already exists"
                )
            
            # Hash password
            password_hash = self.pwd_context.hash(password)
            
            # Create user
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role.value,
                **kwargs
            )
            
            self.db_session.add(user)
            self.db_session.commit()
            self.db_session.refresh(user)
            
            # Log audit event
            await self._log_audit_event(
                user_id=user.id,
                event_type="user_management",
                action="user_created",
                details={"username": username, "email": email, "role": role.value}
            )
            
            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat()
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Tuple[Dict[str, Any], str, str]:
        """Authenticate user with enhanced security checks."""
        try:
            # Find user
            user = self.db_session.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user:
                await self._log_audit_event(
                    event_type="authentication",
                    action="login_failed",
                    details={"username": username, "reason": "user_not_found"},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    result="failure"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Check if user is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                await self._log_audit_event(
                    user_id=user.id,
                    event_type="authentication",
                    action="login_failed",
                    details={"username": username, "reason": "account_locked"},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    result="failure"
                )
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is temporarily locked due to multiple failed login attempts"
                )
            
            # Verify password
            if not self.pwd_context.verify(password, user.password_hash):
                # Increment failed attempts
                user.failed_login_attempts += 1
                
                # Lock account if max attempts reached
                if user.failed_login_attempts >= self.config.max_login_attempts:
                    user.locked_until = datetime.utcnow() + timedelta(
                        minutes=self.config.lockout_duration_minutes
                    )
                
                self.db_session.commit()
                
                await self._log_audit_event(
                    user_id=user.id,
                    event_type="authentication",
                    action="login_failed",
                    details={"username": username, "reason": "invalid_password"},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    result="failure"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Check if user is active
            if not user.is_active:
                await self._log_audit_event(
                    user_id=user.id,
                    event_type="authentication",
                    action="login_failed",
                    details={"username": username, "reason": "account_inactive"},
                    ip_address=ip_address,
                    user_agent=user_agent,
                    result="failure"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is inactive"
                )
            
            # Reset failed login attempts on successful authentication
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            self.db_session.commit()
            
            # Generate tokens
            access_token = self._create_access_token(user)
            refresh_token = self._create_refresh_token(user)
            
            # Create session
            session_token = await self._create_user_session(
                user, ip_address, user_agent
            )
            
            # Log successful login
            await self._log_audit_event(
                user_id=user.id,
                event_type="authentication",
                action="login_success",
                details={"username": username},
                ip_address=ip_address,
                user_agent=user_agent,
                result="success"
            )
            
            user_info = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "permissions": [p.value for p in self.get_user_permissions(user.role)],
                "mfa_enabled": user.mfa_enabled,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            
            return user_info, access_token, refresh_token
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
    
    def _create_access_token(self, user: User) -> str:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(
            minutes=self.config.access_token_expire_minutes
        )
        
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "permissions": [p.value for p in self.get_user_permissions(user.role)],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
    
    def _create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token."""
        expire = datetime.utcnow() + timedelta(
            days=self.config.refresh_token_expire_days
        )
        
        payload = {
            "sub": str(user.id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
    
    async def _create_user_session(
        self,
        user: User,
        ip_address: str = None,
        user_agent: str = None
    ) -> str:
        """Create and store user session."""
        session_token = secrets.token_urlsafe(32)
        expire = datetime.utcnow() + timedelta(
            minutes=self.config.session_timeout_minutes
        )
        
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expire
        )
        
        self.db_session.add(session)
        self.db_session.commit()
        
        # Store in Redis for fast lookup
        if self.redis_client:
            self.redis_client.setex(
                f"session:{session_token}",
                self.config.session_timeout_minutes * 60,
                str(user.id)
            )
        
        return session_token
    
    def get_user_permissions(self, role: Union[str, UserRole]) -> List[Permission]:
        """Get permissions for a user role."""
        if isinstance(role, str):
            role = UserRole(role)
        
        return self.role_permissions.get(role, [])
    
    def has_permission(self, user_role: Union[str, UserRole], permission: Permission) -> bool:
        """Check if a user role has a specific permission."""
        user_permissions = self.get_user_permissions(user_role)
        return permission in user_permissions
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            
            # Check token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Get user from database
            user_id = payload.get("sub")
            user = self.db_session.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    # Multi-Factor Authentication
    def setup_mfa(self, user_id: str) -> Dict[str, Any]:
        """Setup MFA for a user."""
        try:
            user = self.db_session.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Generate secret
            secret = pyotp.random_base32()
            user.mfa_secret = self.fernet.encrypt(secret.encode()).decode()
            
            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                user.email,
                issuer_name="CrisisMap AI"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            self.db_session.commit()
            
            return {
                "secret": secret,
                "qr_code": f"data:image/png;base64,{qr_code_base64}",
                "manual_entry_key": secret
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"MFA setup error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to setup MFA"
            )
    
    def verify_mfa(self, user_id: str, totp_code: str) -> bool:
        """Verify MFA TOTP code."""
        try:
            user = self.db_session.query(User).filter(User.id == user_id).first()
            if not user or not user.mfa_secret:
                return False
            
            # Decrypt secret
            secret = self.fernet.decrypt(user.mfa_secret.encode()).decode()
            
            # Verify TOTP
            totp = pyotp.TOTP(secret)
            return totp.verify(totp_code, valid_window=1)
            
        except Exception as e:
            logger.error(f"MFA verification error: {e}")
            return False
    
    def enable_mfa(self, user_id: str, totp_code: str) -> bool:
        """Enable MFA after verification."""
        if self.verify_mfa(user_id, totp_code):
            user = self.db_session.query(User).filter(User.id == user_id).first()
            user.mfa_enabled = True
            self.db_session.commit()
            return True
        return False
    
    # API Key Management
    async def create_api_key(
        self,
        user_id: str,
        name: str,
        permissions: List[str] = None,
        expires_days: int = 365
    ) -> Dict[str, Any]:
        """Create API key for a user."""
        try:
            user = self.db_session.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Generate API key
            key = f"ck_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            key_prefix = key[:8]
            
            # Set expiration
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            # Create API key record
            api_key = APIKey(
                user_id=user.id,
                name=name,
                key_hash=key_hash,
                key_prefix=key_prefix,
                permissions=permissions or [],
                expires_at=expires_at
            )
            
            self.db_session.add(api_key)
            self.db_session.commit()
            self.db_session.refresh(api_key)
            
            # Log audit event
            await self._log_audit_event(
                user_id=user.id,
                event_type="api_management",
                action="api_key_created",
                details={"key_name": name, "key_prefix": key_prefix}
            )
            
            return {
                "id": str(api_key.id),
                "name": name,
                "key": key,  # Only returned once
                "key_prefix": key_prefix,
                "permissions": permissions,
                "expires_at": expires_at.isoformat(),
                "created_at": api_key.created_at.isoformat()
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"API key creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key"
            )
    
    async def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """Verify API key and return user information."""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            db_key = self.db_session.query(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True,
                APIKey.expires_at > datetime.utcnow()
            ).first()
            
            if not db_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired API key"
                )
            
            # Update last used
            db_key.last_used = datetime.utcnow()
            self.db_session.commit()
            
            # Get user
            user = self.db_session.query(User).filter(User.id == db_key.user_id).first()
            
            return {
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role,
                "api_key_id": str(db_key.id),
                "api_key_name": db_key.name,
                "permissions": db_key.permissions
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API key verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key verification failed"
            )
    
    # OAuth Integration
    async def oauth_login(self, provider: str, code: str) -> Tuple[Dict[str, Any], str, str]:
        """Handle OAuth login flow."""
        try:
            if provider not in self.oauth_providers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported OAuth provider"
                )
            
            provider_config = self.oauth_providers[provider]
            
            # Exchange code for token
            oauth = OAuth2Session(
                provider_config['client_id'],
                provider_config['client_secret'],
                redirect_uri=provider_config['redirect_uri']
            )
            
            token = oauth.fetch_token(
                provider_config['token_url'],
                code=code
            )
            
            # Get user info
            response = oauth.get(provider_config['userinfo_url'])
            user_info = response.json()
            
            # Find or create user
            email = user_info.get('email')
            user = self.db_session.query(User).filter(User.email == email).first()
            
            if not user:
                # Create new user
                username = email.split('@')[0]
                # Ensure unique username
                base_username = username
                counter = 1
                while self.db_session.query(User).filter(User.username == username).first():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                user = User(
                    username=username,
                    email=email,
                    password_hash="oauth",  # No password for OAuth users
                    first_name=user_info.get('given_name', ''),
                    last_name=user_info.get('family_name', ''),
                    is_verified=True,
                    role=UserRole.VIEWER.value
                )
                
                self.db_session.add(user)
                self.db_session.commit()
                self.db_session.refresh(user)
            
            # Update last login
            user.last_login = datetime.utcnow()
            self.db_session.commit()
            
            # Generate tokens
            access_token = self._create_access_token(user)
            refresh_token = self._create_refresh_token(user)
            
            user_data = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "permissions": [p.value for p in self.get_user_permissions(user.role)]
            }
            
            return user_data, access_token, refresh_token
            
        except Exception as e:
            logger.error(f"OAuth login error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth authentication failed"
            )
    
    # Audit Logging
    async def _log_audit_event(
        self,
        event_type: str,
        action: str,
        user_id: str = None,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict = None,
        ip_address: str = None,
        user_agent: str = None,
        endpoint: str = None,
        method: str = None,
        result: str = "success",
        error_message: str = None
    ):
        """Log audit event."""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                details=details or {},
                result=result,
                error_message=error_message
            )
            
            self.db_session.add(audit_log)
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Audit logging error: {e}")
    
    # Password validation
    def _validate_password(self, password: str):
        """Validate password against security requirements."""
        if len(password) < self.config.password_min_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be at least {self.config.password_min_length} characters long"
            )
        
        if self.config.password_require_uppercase and not any(c.isupper() for c in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter"
            )
        
        if self.config.password_require_numbers and not any(c.isdigit() for c in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one number"
            )
        
        if self.config.password_require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one special character"
            )


# FastAPI Security Dependencies
security = HTTPBearer()

def get_auth_system() -> EnterpriseAuthSystem:
    """Get authentication system instance."""
    return EnterpriseAuthSystem()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_system: EnterpriseAuthSystem = Depends(get_auth_system)
) -> Dict[str, Any]:
    """Get current authenticated user."""
    token = credentials.credentials
    return await auth_system.verify_token(token)

async def require_permission(permission: Permission):
    """Dependency to require specific permission."""
    def permission_checker(current_user: Dict = Depends(get_current_user)):
        user_role = UserRole(current_user["role"])
        auth_system = get_auth_system()
        
        if not auth_system.has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission {permission.value} required"
            )
        return current_user
    
    return permission_checker

async def require_role(required_role: UserRole):
    """Dependency to require specific role or higher."""
    role_hierarchy = [
        UserRole.GUEST,
        UserRole.API_USER,
        UserRole.VIEWER,
        UserRole.OPERATOR,
        UserRole.ANALYST,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN
    ]
    
    def role_checker(current_user: Dict = Depends(get_current_user)):
        user_role = UserRole(current_user["role"])
        
        if role_hierarchy.index(user_role) < role_hierarchy.index(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role.value} or higher required"
            )
        return current_user
    
    return role_checker


# Global auth system instance
_auth_system = None

def get_enterprise_auth() -> EnterpriseAuthSystem:
    """Get global authentication system instance."""
    global _auth_system
    if _auth_system is None:
        _auth_system = EnterpriseAuthSystem()
    return _auth_system