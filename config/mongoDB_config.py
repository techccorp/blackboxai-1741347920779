# ------------------------------------------------------------
#                  config/mongoDB_config.py
# ------------------------------------------------------------
"""
MongoDB configuration and connection management module.

This module provides a centralized configuration for MongoDB connections,
collection definitions, schemas, and utility functions for database operations
"""
from pymongo import MongoClient, ASCENDING, DESCENDING, IndexModel
from pymongo.errors import (ConnectionFailure, 
                          ServerSelectionTimeoutError, 
                          DuplicateKeyError,
                          OperationFailure,
                          AutoReconnect)
import logging
import os
import time
from datetime import datetime
from decimal import Decimal
from bson.objectid import ObjectId
from dotenv import load_dotenv
import uuid
from .base_config import config as Config

# Configure module logger
logger = logging.getLogger(__name__)

# MongoDB Connection Settings from Config
MONGO_URI = Config.MONGO_URI
MONGO_DBNAME = Config.MONGO_DBNAME

# Collection Names
COLLECTION_TAGS = 'tags'
COLLECTION_GLOBAL_RECIPES = 'global_recipes'
COLLECTION_USER_RECIPES = 'user_recipes'
COLLECTION_PRODUCT_LIST = 'product_list'
COLLECTION_ALLERGENS = 'allergens'
COLLECTION_USER_NOTES = 'user_notes'
COLLECTION_MEATSPACE = 'meatspace'

# Business Onboarding Collections
COLLECTION_BUSINESS_ENTITIES = Config.COLLECTION_BUSINESSES
COLLECTION_BUSINESS_VENUES = Config.COLLECTION_BUSINESS_VENUES
COLLECTION_BUSINESS_USERS = Config.COLLECTION_BUSINESS_USERS
COLLECTION_BUSINESS_CONFIG = 'business_config'
COLLECTION_BUSINESS_ROLES = Config.COLLECTION_BUSINESS_ROLES
COLLECTION_ROLE_IDS = 'role_ids'
COLLECTION_EMPLOYMENT_ROLES = Config.COLLECTION_EMPLOYMENT_ROLES

# Collection Indexes - Only define for collections that need indexes
COLLECTION_INDEXES = {
    COLLECTION_BUSINESS_ENTITIES: [
        IndexModel([("business_id", ASCENDING)], unique=True),
        IndexModel([("created_at", DESCENDING)])
    ],
    COLLECTION_BUSINESS_VENUES: [
        IndexModel([("venue_id", ASCENDING)], unique=True),
        IndexModel([("business_id", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)]),
        IndexModel([("workareas.work_area_id", ASCENDING)])
    ],
    COLLECTION_BUSINESS_USERS: [
        IndexModel([("user_id", ASCENDING)], unique=True, sparse=True),  # sparse index allows multiple null values
        IndexModel([("business_id", ASCENDING)]),
        IndexModel([("venue_id", ASCENDING)]),
        IndexModel([("work_area_id", ASCENDING)]),
        IndexModel([("role_id", ASCENDING)]),
        IndexModel([("work_email", ASCENDING)]),
        IndexModel([("employment_details.hired_date", ASCENDING)]),
        IndexModel([("created_at", DESCENDING)])
    ]
}

def get_client_options():
    """Get MongoDB client options based on configuration"""
    client_options = {
        'serverSelectionTimeoutMS': Config.MONGO_SOCKET_TIMEOUT_MS,
        'maxPoolSize': Config.MONGO_MAX_POOL_SIZE,
        'minPoolSize': Config.MONGO_MIN_POOL_SIZE,
        'connectTimeoutMS': Config.MONGO_CONNECT_TIMEOUT_MS,
        'retryWrites': True,
        'w': 'majority'
    }
    
    # Add TLS options for MongoDB Atlas (SRV) connections
    if Config.MONGO_URI.startswith('mongodb+srv://'):
        client_options.update({
            'tls': True,
            'tlsAllowInvalidCertificates': True  # For self-signed certs
        })
    elif Config.MONGO_TLS:
        client_options.update({
            'tls': True,
            'tlsCAFile': Config.MONGO_TLS_CA_FILE if Config.MONGO_TLS_CA_FILE else None
        })
    
    return client_options

def init_mongo(max_retries=3, retry_delay=5):
    """
    Initialize MongoDB connection with enhanced index handling and retry logic.
    
    Args:
        max_retries (int): Maximum number of connection attempts
        retry_delay (int): Delay in seconds between retries
        
    Returns:
        MongoClient or None: Initialized MongoDB client if successful
    """
    retries = 0
    last_error = None
    
    while retries < max_retries:
        try:
            # Initialize client with options
            client = MongoClient(Config.MONGO_URI, **get_client_options())
        
            # Test connection
            client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB at {Config.MONGO_URI}")
            
            db = client[Config.MONGO_DBNAME]
            
            # Set up collections and indexes
            for collection_name, indexes in COLLECTION_INDEXES.items():
                if collection_name not in db.list_collection_names():
                    db.create_collection(collection_name)
                    logger.info(f"Created collection: {collection_name}")
                
                collection = db[collection_name]
                existing_indexes = collection.index_information()
                
                # Remove conflicting indexes
                for index in indexes:
                    index_name = index.document['name']
                    if index_name in existing_indexes:
                        # Check if specs match
                        existing_spec = existing_indexes[index_name]
                        if existing_spec != index.document:
                            logger.warning(f"Removing conflicting index: {index_name}")
                            collection.drop_index(index_name)
                
                # Create new indexes with proper error handling
                try:
                    created_indexes = collection.create_indexes(indexes)
                    logger.info(f"Created/Updated {len(created_indexes)} indexes for {collection_name}")
                except OperationFailure as e:
                    if e.code == 85:  # IndexOptionsConflict
                        logger.warning(f"Index conflict for {collection_name}, dropping existing indexes")
                        # Drop all non-_id indexes
                        for index_name in existing_indexes:
                            if index_name != '_id_':
                                collection.drop_index(index_name)
                        # Retry creating indexes
                        created_indexes = collection.create_indexes(indexes)
                        logger.info(f"Successfully recreated {len(created_indexes)} indexes for {collection_name}")
                    else:
                        raise
            
            return client
            
        except (ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect) as e:
            last_error = e
            retries += 1
            if retries < max_retries:
                logger.warning(f"MongoDB connection attempt {retries} failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            continue
        except OperationFailure as e:
            if e.code == 86:  # IndexKeySpecsConflict
                logger.warning("Index conflict detected, attempting automatic resolution...")
                if client:
                    client.close()
                return handle_index_conflict()
            logger.error(f"MongoDB Operation Error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected MongoDB Error: {str(e)}")
            return None
            
    if last_error:
        logger.error(f"Failed to connect to MongoDB after {max_retries} attempts: {str(last_error)}")
    return None

def handle_index_conflict(max_retries=3, retry_delay=5):
    """
    Advanced index conflict resolution with retry logic
    
    Args:
        max_retries (int): Maximum number of resolution attempts
        retry_delay (int): Delay in seconds between retries
        
    Returns:
        MongoClient or None: Initialized MongoDB client if successful
    """
    retries = 0
    last_error = None
    
    while retries < max_retries:
        try:
            # Initialize client with options
            client = MongoClient(Config.MONGO_URI, **get_client_options())
            db = client[Config.MONGO_DBNAME]
            
            for collection_name, indexes in COLLECTION_INDEXES.items():
                collection = db[collection_name]
                existing_indexes = collection.index_information()
                
                for index in indexes:
                    index_spec = index.document
                    index_name = index_spec['name']
                    
                    # Check for name conflicts
                    if index_name in existing_indexes:
                        existing_index = existing_indexes[index_name]
                        if existing_index != index_spec:
                            logger.info(f"Recreating mismatched index: {index_name}")
                            collection.drop_index(index_name)
                            collection.create_indexes([index])
            
            logger.info("Index conflict resolution completed")
            return client
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            last_error = e
            retries += 1
            if retries < max_retries:
                logger.warning(f"Resolution attempt {retries} failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            continue
        except Exception as e:
            logger.error(f"Index conflict resolution failed: {str(e)}")
            if client:
                client.close()
            return None
    
    if last_error:
        logger.error(f"Failed to resolve index conflicts after {max_retries} attempts: {str(last_error)}")
    return None

def get_db():
    """
    Get MongoDB database instance.
    
    Returns:
        Database: MongoDB database instance if connection successful, None otherwise
        
    Raises:
        ConnectionFailure: If connection to MongoDB fails
        ServerSelectionTimeoutError: If server selection times out
    """
    try:
        client = get_mongo_client()
        return client[Config.MONGO_DBNAME] if client else None
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"MongoDB connection error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {str(e)}")
        return None

def get_collection(collection_name):
    """
    Get a specific MongoDB collection.
    
    Args:
        collection_name: Name of the collection to retrieve
        
    Returns:
        Collection: MongoDB collection if found, None otherwise
    """
    db = get_db()
    if db and collection_name in db.list_collection_names():
        return db[collection_name]
    return None

# Initialize MongoDB client lazily
MONGO_CLIENT = None

def get_mongo_client():
    """Get or initialize MongoDB client"""
    global MONGO_CLIENT
    if MONGO_CLIENT is None:
        try:
            MONGO_CLIENT = init_mongo()
            if not MONGO_CLIENT:
                logger.error("Failed to initialize MongoDB client")
                raise RuntimeError("MongoDB client initialization failed")
            logger.info("MongoDB configuration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB configuration: {str(e)}")
            raise
    return MONGO_CLIENT
