from typing import Optional, List, Dict, Any
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from bson.errors import InvalidId
from models.businessUsers_models import BusinessUser
from utils.auth.passwordManager_utils import PasswordManager as SecurityUtils
import logging

logger = logging.getLogger(__name__)

class BusinessUserService:
    def __init__(self, client: MongoClient):
        self.db = client.get_database("MyCookBook")
        self.collection = self.db.business_users
        
    def create_indexes(self):
        try:
            self.collection.create_index("payroll_id", unique=True)
            self.collection.create_index("linking_id", unique=True)
            self.collection.create_index("work_email", unique=True)
            self.collection.create_index("venue_id")
            self.collection.create_index("work_area_id")
            logger.info("Indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
            raise

    def create_user(self, user: BusinessUser) -> BusinessUser:
        user_dict = user.dict(by_alias=True, exclude={'id'})
        try:
            result = self.collection.insert_one(user_dict)
            if not result.acknowledged:
                raise RuntimeError("Insert operation not acknowledged by MongoDB")
            return self.get_user_by_id(result.inserted_id)
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error: {str(e)}")
            raise ValueError("User with this payroll ID, linking ID, or email already exists") from e

    def get_user_by_id(self, user_id: str) -> Optional[BusinessUser]:
        try:
            obj_id = ObjectId(user_id)
        except InvalidId:
            raise ValueError("Invalid user ID format")
        
        user = self.collection.find_one({"_id": obj_id})
        return BusinessUser(**user) if user else None

    def get_user_by_payroll_id(self, payroll_id: str) -> Optional[BusinessUser]:
        if not payroll_id.startswith('D') or len(payroll_id) != 9:
            raise ValueError("Invalid payroll ID format")
        
        user = self.collection.find_one({"payroll_id": payroll_id})
        return BusinessUser(**user) if user else None

    def authenticate_user(self, payroll_id: str, password: str) -> Optional[BusinessUser]:
        user = self.get_user_by_payroll_id(payroll_id)
        if not user:
            return None
        if not SecurityUtils.verify_password(password, user.password):
            return None
        return user

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[BusinessUser]:
        try:
            obj_id = ObjectId(user_id)
        except InvalidId:
            raise ValueError("Invalid user ID format")
        
        if 'password' in update_data:
            update_data['password'] = SecurityUtils.hash_password(update_data['password'])
        
        updated_user = self.collection.find_one_and_update(
            {"_id": obj_id},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        return BusinessUser(**updated_user) if updated_user else None

    def delete_user(self, user_id: str) -> bool:
        try:
            obj_id = ObjectId(user_id)
        except InvalidId:
            raise ValueError("Invalid user ID format")
        
        result = self.collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0

    def get_users_by_venue(self, venue_id: str) -> List[BusinessUser]:
        users = list(self.collection.find({"venue_id": venue_id}))
        return [BusinessUser(**user) for user in users]

    def update_leave_balances(self, user_id: str, updates: Dict[str, float]) -> bool:
        try:
            obj_id = ObjectId(user_id)
        except InvalidId:
            raise ValueError("Invalid user ID format")
        
        result = self.collection.update_one(
            {"_id": obj_id},
            {"$set": {f"leave_entitlements.{k}": v for k, v in updates.items()}}
        )
        return result.modified_count > 0
