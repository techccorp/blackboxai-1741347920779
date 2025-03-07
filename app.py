# -------------------------------------#
#               /app.py               #
# -------------------------------------#
import os
import time
import logging
import traceback
from datetime import datetime
from io import BytesIO
import json
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory, Response, send_file, g
from pymongo import MongoClient, ASCENDING, DESCENDING  # Added missing imports
from flask_cors import CORS
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, PyMongoError
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import gridfs

from services.auth.id_service import IDService, IDGenerationError, InvalidIDError
from config import get_config, RedisConfig
from config.base_config import config as Config

# -------------------------------------#
#        Import blueprints            #
# -------------------------------------#
from routes.auth_routes import auth
from routes.allergen_routes import allergens
from routes.error_routes import error_routes
from routes.finance_routes import finance
from routes.common_routes import common
from routes.google_routes import google_api
from routes.employment_routes import employment
from routes.product_routes import products
from routes.recipeSearch_routes import recipe_search
from routes.googleTasks_routes import google_tasks
from routes.notes_routes import notes
from routes.resource_routes import resource
from routes.businessUsers_routes import business_users
from routes.business.routes import business
from modules import module_manager

# Initialize logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize configurations
config = get_config()

# Initialize MongoDB and Redis configurations
try:
    # Configure MongoDB settings first
    from config.mongoDB_config import get_mongo_client
    logger.info("MongoDB configuration loaded")

    # Initialize Redis configuration
    redis_config = RedisConfig()
    redis_config.validate_config()
    logger.info("Redis configuration loaded")
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    raise
except Exception as e:
    logger.error(f"Configuration initialization failed: {str(e)}")
    raise

def create_app(config_class=None):
    """Application factory function"""
    if config_class is None:
        config_class = config
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Set default configuration values
    app.config.setdefault('CORS_METHODS', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    app.config.setdefault('CORS_ORIGINS', '*')  
    app.config.setdefault('CORS_ALLOW_HEADERS', ['Content-Type', 'Authorization', 'X-Requested-With'])
    app.config.setdefault('UPLOAD_FOLDER', 'uploads')
    app.config.setdefault('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
    app.config.setdefault('GRIDFS_BUCKET_NAME', 'fs')
    app.config.setdefault('SERVER_NAME', 'localhost:5000')
    app.config.setdefault('PREFERRED_URL_SCHEME', 'http')
    app.config.setdefault('APPLICATION_ROOT', '/')
    
    # Initialize security components
    csrf = CSRFProtect(app)
    CORS(app, resources={r"/*": {
        "origins": app.config['CORS_ORIGINS'],
        "methods": app.config['CORS_METHODS'],
        "allow_headers": app.config['CORS_ALLOW_HEADERS']
    }})

    # Initialize core services
    retries = 3
    retry_delay = 5
    last_error = None

    for attempt in range(retries):
        try:
            # Initialize MongoDB client
            mongo_client = get_mongo_client()
            if not mongo_client:
                raise ConnectionFailure("Failed to initialize MongoDB client")
                
            # Set up app.mongo proxy
            app.mongo = type('', (), {})()
            app.mongo.client = mongo_client
            app.mongo.db = mongo_client[Config.MONGO_DBNAME]
            
            # Test connection
            mongo_client.admin.command('ping')
            logger.info("MongoDB connection established")

            # GridFS initialization
            app.fs = gridfs.GridFS(app.mongo.db, collection=app.config['GRIDFS_BUCKET_NAME'])
            logger.info("GridFS initialized")

            # ID Service initialization
            app.id_service = IDService(app.mongo.db)
            logger.info("ID Service initialized")
            
            # Successfully initialized all services
            break

        except (ConnectionFailure, ServerSelectionTimeoutError, IDGenerationError) as e:
            last_error = e
            if attempt < retries - 1:  # Don't sleep on last attempt
                logger.warning(f"Database initialization attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            continue
        except Exception as e:
            logger.critical(f"Unexpected error during initialization: {str(e)}")
            raise

    if last_error:
        logger.critical(f"Database initialization failed after {retries} attempts: {str(last_error)}")
        if app.config.get('ENV') == 'production':
            logger.info("Restarting application in production mode...")
            time.sleep(5)
            return create_app(config_class)
        raise last_error

    # Register components
    register_blueprints(app)
    configure_encoders(app)
    configure_error_handlers(app)
    configure_request_hooks(app)
    register_core_routes(app)

    # Initialize modules
    try:
        # Ensure MongoDB is available before initializing modules
        if not hasattr(app, 'mongo') or not hasattr(app.mongo, 'db'):
            logger.error("MongoDB not properly initialized")
            raise RuntimeError("MongoDB connection not available")
            
        module_manager.init_app(app)
        logger.info("Module system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize module system: {str(e)}")
        logger.debug(f"Module initialization error details: {traceback.format_exc()}")

    # Set REDIRECT_URI
    app.config['REDIRECT_URI'] = "http://localhost:5000/login/authorized"
    logger.info(f"Configured REDIRECT_URI: {app.config['REDIRECT_URI']}")

    return app

def register_blueprints(app):
   """Register all application blueprints"""
   # -------------------------------------#
   #         Register blueprints         #
   # -------------------------------------#
   try:
       app.register_blueprint(auth)
       app.register_blueprint(allergens)
       app.register_blueprint(error_routes)
       app.register_blueprint(finance)
       app.register_blueprint(common)
       app.register_blueprint(employment)
       app.register_blueprint(google_api)
       app.register_blueprint(products)
       app.register_blueprint(recipe_search)
       app.register_blueprint(google_tasks)
       app.register_blueprint(notes)
       app.register_blueprint(resource)
       app.register_blueprint(business_users)
       app.register_blueprint(business)
       
       logger.info("All blueprints registered successfully")
   except Exception as e:
       logger.error(f"Error registering blueprints: {str(e)}")
       raise

def configure_encoders(app):
   """Configure custom JSON encoders"""
   class EnhancedJSONEncoder(json.JSONEncoder):
       def default(self, obj):
           if isinstance(obj, ObjectId):
               return str(obj)
           if isinstance(obj, datetime):
               return obj.isoformat()
           return super().default(obj)
   
   app.json_encoder = EnhancedJSONEncoder
   logger.info("Custom JSON encoder configured")

def configure_error_handlers(app):
   """Register global error handlers"""
   @app.errorhandler(404)
   def page_not_found(e):
       logger.warning(f"404 Error: {request.url}")
       return render_template('errors/404.html'), 404

   @app.errorhandler(500)
   def internal_server_error(e):
       logger.error(f"500 Error: {str(e)}")
       return render_template('errors/500.html'), 500

   @app.errorhandler(IDGenerationError)
   def handle_id_error(e):
       logger.error(f"ID Generation Failure: {str(e)}")
       return jsonify({"error": "ID generation failed", "code": 500}), 500
   
   logger.info("Error handlers configured")

def configure_request_hooks(app):
   """Configure request lifecycle handlers"""
   @app.before_request
   def before_request_handler():
       g.start_time = datetime.utcnow()
       if hasattr(app, 'id_service'):
           try:
               g.request_id = app.id_service.generate_business_request_id()
           except Exception as e:
               logger.warning(f"Could not generate request ID: {str(e)}")
               g.request_id = f"req-{datetime.utcnow().timestamp()}"
       
       os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

   @app.after_request
   def apply_security_headers(response):
       """Apply security headers to all responses"""
       headers = {
           'X-Content-Type-Options': 'nosniff',
           'X-Frame-Options': 'DENY',
           'X-XSS-Protection': '1; mode=block',
           'Content-Security-Policy': "default-src 'self'",
           'Referrer-Policy': 'strict-origin-when-cross-origin'
       }
       response.headers.update(headers)
       return response

   @app.teardown_appcontext
   def teardown_db(exception):
       """Clean up database connections"""
       if hasattr(g, 'mongo_client'):
           g.mongo_client.close()
   
   logger.info("Request lifecycle hooks configured")

def register_core_routes(app):
   """Register essential system routes"""
   @app.route('/')
   def index():
       return render_template('index.html')

   @app.route('/login')
   def login():
       if hasattr(app, 'google'):
           redirect_uri = app.config.get('REDIRECT_URI')
           return app.google.authorize_redirect(redirect_uri)
       return render_template('login.html')

   @app.route('/logout')
   def logout():
       session.pop('user', None)
       return redirect(url_for('index'))

   @app.route('/login/authorized')
   def authorized():
       if hasattr(app, 'google'):
           try:
               token = app.google.authorize_access_token()
               resp = app.google.get('userinfo')
               user_info = resp.json()
               session['user'] = user_info
               return jsonify(user_info)
           except Exception as e:
               logger.error(f"OAuth error: {str(e)}")
               return redirect(url_for('login'))
       return jsonify({"error": "OAuth not configured"}), 500

   @app.route('/login/google', methods=['POST'])
   def login_google():
       token = request.json.get('id_token')
       if token:
           session['user'] = token  # Replace with your logic
           return jsonify(success=True, redirect_url=url_for('index'))
       return jsonify(success=False, message='Invalid token.')

   @app.route('/upload', methods=['POST'])
   def upload_image():
       """Handle file uploads with GridFS integration"""
       if 'file' not in request.files:
           return jsonify({"error": "No file part"}), 400
           
       file = request.files['file']
       if file.filename == '':
           return jsonify({"error": "No selected file"}), 400

       if file and allowed_file(file.filename):
           try:
               timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
               filename = secure_filename(f"{timestamp}_{file.filename}")
               
               # Save to GridFS
               file_id = app.fs.put(
                   file, 
                   filename=filename, 
                   content_type=file.content_type
               )
               
               # Also save to disk as backup
               file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
               os.makedirs(os.path.dirname(file_path), exist_ok=True)
               file.seek(0)  # Reset file position after GridFS write
               file.save(file_path)
               
               return jsonify({
                   "id": str(file_id),
                   "filename": filename,
                   "url": url_for('get_image', filename=filename)
               }), 201
           except Exception as e:
               logger.error(f"Upload failed: {str(e)}")
               return jsonify({"error": "File upload failed"}), 500

       return jsonify({"error": "Invalid file type"}), 400

   @app.route('/image/<filename>')
   def get_image(filename):
       """Serve images from GridFS or filesystem"""
       try:
           # Try GridFS first
           file = app.fs.find_one({'filename': filename})
           if file:
               return send_file(
                   BytesIO(file.read()), 
                   mimetype=file.content_type or 'image/jpeg',
                   download_name=filename
               )
           
           # Fallback to filesystem
           file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
           if os.path.exists(file_path):
               return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
           
           logger.warning(f"Image not found: {filename}")
           return jsonify({"error": "Image not found"}), 404
       except Exception as e:
           logger.error(f"Image retrieval failed for {filename}: {str(e)}")
           return jsonify({"error": f"Error retrieving image: {str(e)}"}), 500

   def allowed_file(filename):
       return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
   
   logger.info("Core routes registered")

if __name__ == '__main__':
   # Set environment variables for Flask configuration
   os.environ['SERVER_NAME'] = 'localhost:5000'
   os.environ['PREFERRED_URL_SCHEME'] = 'http'
   os.environ['APPLICATION_ROOT'] = '/'
   
   app = create_app()
   app.run(
       host='127.0.0.1',  # Use loopback address
       port=5000,  # Use port 5000 which is typically available
       debug=config.DEBUG,
       ssl_context=config.ssl_context if config.USE_SSL else None
   )
