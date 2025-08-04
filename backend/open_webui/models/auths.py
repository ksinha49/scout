"""
Modification Log:
------------------
| Date       | Author         | MOD TAG            | Description                                                                                         |
|------------|----------------|--------------------|-----------------------------------------------------------------------------------------------------|
| 2024-11-05 | AAK7S          | CWE-312            | Replaced clear-text logging of sensitive information with generic logging messages.                 |
|            |                |                    | **Old Code:** Logged user emails and API keys in plain text.                                        |
|            |                |                    | **New Code:** Logs replaced with general action messages, omitting sensitive details.               |

"""
import logging
import uuid
from typing import Optional

from open_webui.internal.db import Base, get_db
from open_webui.models.users import UserModel, Users
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, String, Text
from open_webui.utils.auth import verify_password

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# DB MODEL
####################


class Auth(Base):
    __tablename__ = "auth"

    id = Column(String, primary_key=True)
    email = Column(String)
    password = Column(Text)
    active = Column(Boolean)


class AuthModel(BaseModel):
    id: str
    email: str
    password: str
    active: bool = True


####################
# Forms
####################


class Token(BaseModel):
    token: str
    token_type: str


class ApiKey(BaseModel):
    api_key: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    profile_image_url: str


class SigninResponse(Token, UserResponse):
    pass


class SigninForm(BaseModel):
    email: str
    password: str


class LdapForm(BaseModel):
    user: str
    password: str


class ProfileImageUrlForm(BaseModel):
    profile_image_url: str


class UpdateProfileForm(BaseModel):
    profile_image_url: str
    name: str


class UpdatePasswordForm(BaseModel):
    password: str
    new_password: str


class SignupForm(BaseModel):
    name: str
    email: str
    password: str
    profile_image_url: Optional[str] = "/user.png"


class AddUserForm(SignupForm):
    role: Optional[str] = "pending"


class AuthsTable:
    def insert_new_auth(
        self,
        email: str,
        password: str,
        name: str,
        profile_image_url: str = "/user.png",
        role: str = "pending",
        oauth_sub: Optional[str] = None,
    ) -> Optional[UserModel]:
        email = email.lower()
        id = str(uuid.uuid4())

        user = Users.insert_new_user(
            id, name, email, profile_image_url, role, oauth_sub
        )
        if not user:
            log.warning("Failed to create new user.")
            return None
        if user.id != id:
            return user

        with get_db() as db:
            log.info("Inserting new authentication record.")
            auth = AuthModel(
                **{"id": id, "email": email, "password": password, "active": True}
            )
            result = Auth(**auth.model_dump())
            db.add(result)
            db.commit()
            db.refresh(result)

            if result:
                log.info("New authentication and user record created successfully.")
                return user
            else:
                log.warning("Failed to create new authentication record.")
                return None

    def authenticate_user(self, email: str, password: str) -> Optional[UserModel]:
        ## MOD: CWE-312 removing sensitive data from logs
        #log.info(f"authenticate_user_by_trusted_header: {email}")
        log.info(f"Authenticating user with email.")
        try:
            email = email.lower()
            with get_db() as db:
                auth = db.query(Auth).filter_by(email=email, active=True).first()
                if auth:
                    if verify_password(password, auth.password):
                        user = Users.get_user_by_id(auth.id)
                        log.info("User authenticated successfully.")
                        return user
                    else:
                        log.warning("Authentication failed: Incorrect password.")
                        return None
                else:
                    log.warning("Authentication failed: User not found or inactive.")
                    return None
        except Exception as e:
            log.error(f"Error during user authentication: {e}")
            return None

    def authenticate_user_by_api_key(self, api_key: str) -> Optional[UserModel]:
        ## MOD: CWE-312 removing sensitive data from logs
        #log.info(f"Authenticating user by API key: {api_key}")
        log.info(f"Authenticating user by API key")
        
        if not api_key:
            log.warning("Authentication failed: API key not provided.")
            return None

        try:
            user = Users.get_user_by_api_key(api_key)
            if user:
                log.info("User authenticated successfully via API key.")
            else:
                log.warning("Authentication failed: Invalid API key.")
            return user if user else None
        except Exception as e:
            log.error(f"Error during API key authentication: {e}")
            return False

    def authenticate_user_by_trusted_header(self, email: str) -> Optional[UserModel]:
        ## MOD: CWE-312 removing sensitive data from log
        #log.info(f"Authenticating user by trusted header with email: {masked_email}")
        log.info(f"Authenticating user by trusted header with email.")
        try:
            email = email.lower()
            with get_db() as db:
                auth = db.query(Auth).filter_by(email=email, active=True).first()
                if auth:
                    user = Users.get_user_by_id(auth.id)
                    log.info("User authenticated successfully by trusted header.")
                    return user
                else:
                    log.warning("Authentication failed: User not found or inactive.")
        except Exception as e:
            log.error(f"Error during trusted header authentication: {e}")
            return None

    def update_user_password_by_id(self, id: str, new_password: str) -> bool:
        try:
            with get_db() as db:
                result = (
                    db.query(Auth).filter_by(id=id).update({"password": new_password})
                )
                db.commit()
                if result == 1:
                    log.info("User password updated successfully.")
                    return True
                else:
                    log.warning("Password update failed: User not found.")
                    return False
        except Exception as e:
            log.error(f"Error during password update: {e}")
            return False

    def update_email_by_id(self, id: str, email: str) -> bool:
        masked_email = f"{email[:3]}****@{email.split('@')[-1]}"  # Mask the email for logging
        try:
            with get_db() as db:
                result = db.query(Auth).filter_by(id=id).update({"email": email})
                db.commit()
                if result == 1:
                    log.info(f"User email updated successfully to {masked_email}.")
                    return True
                else:
                    log.warning("Email update failed: User not found.")
                    return False
        except Exception as e:
            log.error(f"Error during email update: {e}")
            return False

    def delete_auth_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                # Delete User
                result = Users.delete_user_by_id(id)

                if result:
                    db.query(Auth).filter_by(id=id).delete()
                    db.commit()

                    log.info("Authentication and user record deleted successfully.")
                    return True
                else:
                    log.warning("Failed to delete authentication record: User not found.")
                    return False
        except Exception as e:
            log.error(f"Error during authentication deletion: {e}")
            return False


Auths = AuthsTable()
