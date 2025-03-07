# --------------------------------------------------------#
#                   utils/__init__.py                     #
# --------------------------------------------------------#
"""
Utility modules for Le Repertoire application.
Provides centralized access to all utility functions and classes.
"""
# ---------------------------------------#
#     Allergen Management Utilities      #
# ---------------------------------------#
from .allergen_utils import (
    lookup_allergen,
    get_allergen_by_id,
    create_allergen,
    update_allergen,
    delete_allergen,
    search_allergens,
    validate_allergen_data,
    AllergenError
)
# ---------------------------------------#
#      Recipe and Search Utilities       #
# ---------------------------------------#    
from .recipe_utils import (
    lookup_ingredient,
    lookup_tag,
    lookup_cuisine,
    lookup_method,
    lookup_dietary,
    lookup_mealtype,
    lookup_recipeIngredient,
    lookup_globalRecipe,
    lookup_allergen
)
# ---------------------------------------#
#      Time Management Utilities         #
# ---------------------------------------#    
from .time_utils import (
    timeago,
    generate_timestamp,
    format_datetime,
    parse_datetime
)
# ---------------------------------------#
#       Note Management Utilities        #
# ---------------------------------------#    
from .notes_utils import (
    create_user_note,
    get_user_notes,
    get_user_note_by_id,
    update_user_note,
    delete_user_note
)
# ---------------------------------------#
#     Business Management Utilities      #
# ---------------------------------------#    
from .business_utils import (
    lookup_business,
    lookup_venue,
    lookup_work_area,
    create_business,
    add_venue_to_business,
    add_work_area_to_venue,
    assign_user_to_business,
    assign_user_to_work_area,
    get_business_hierarchy,
    update_business_status,
    validate_business_structure
)
# ---------------------------------------#
#       Google Integration Utilities     #
# ---------------------------------------#    
from .google_utils import (
    validate_google_token,
    get_google_service,
    KeepService  # Import the KeepService class
)
# ---------------------------------------#
#           Security Utilities           #
# ---------------------------------------#    
from .security_utils import (
    generate_random_string,
    generate_secure_token,
    generate_id_with_prefix,
    hash_string,
    constant_time_compare,
    generate_session_id,
    sanitize_input,
    log_security_event
)
# ---------------------------------------#
#          Validation Utilities          #
# ---------------------------------------#    
from .validation_utils import (
    validate_request_data,
    validate_id_format,
    validate_uuid,
    validate_email,
    validate_date_format,
    validate_phone_number,
    validate_required_fields,
    validate_field_length,
    validate_numeric_range,
    validate_business_data,
    validate_venue_data,
    validate_work_area_data
)
# ---------------------------------------#
#           Database Utilities           #
# ---------------------------------------#    
from .db_utils import (
    safe_object_id,
    format_mongo_doc,
    create_mongo_query,
    handle_mongo_error,
    sanitize_mongo_query,
    build_aggregation_pipeline,
    update_timestamp_fields,
    get_collection_stats,
    ensure_indexes,
    bulk_write_operations,
    get_distinct_values,
    execute_transaction
)
# ---------------------------------------#
#            Error Handling Utilities    #
# ---------------------------------------#    
from .error_utils import (
    AppError,
    ValidationError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    DatabaseError,
    handle_error,
    log_error,
    format_error_response,
    validate_or_raise,
    assert_found,
    assert_valid,
    assert_permitted,
    get_error_context
)
# ---------------------------------------#
#            Logging Utilities           #
# ---------------------------------------#    
from .logging_utils import (
    CustomJSONFormatter,
    setup_logging,
    log_event,
    log_api_request,
    log_security_event,
    cleanup_logs,
    get_log_stats
)
# ---------------------------------------#
#        Request Processing Utilities    #
# ---------------------------------------#    
from .request_utils import (
    get_request_data,
    validate_request_data,
    format_response,
    paginate_results,
    parse_query_params,
    validate_content_type,
    rate_limit,
    log_request_info,
    get_client_ip,
    get_pagination_params,
    get_sort_params,
    get_filter_params,
    validate_request_size
)
# ---------------------------------------#
#      Session Management Utilities      #
# ---------------------------------------#    
from .session_utils import SessionManager
# ---------------------------------------#
#              Rate Limiting             #
# ---------------------------------------#
from .rate_limiter import RateLimiter
# ---------------------------------------#
#             Audit Logging              #
# ---------------------------------------#
from .audit_logger import AuditLogger
# ---------------------------------------#
#             Payroll Utilities          #
# ---------------------------------------#
from .payroll.taxRates_utils import (
    calculate_tax,
    calculate_period_amount,
    calculate_annual_salary,
    calculate_hourly_rate
)

from .payroll.accrualRates_utils import (
    calculate_service_period,
    calculate_leave_accrual,
    get_leave_summary,
    map_user_leave_data,
    get_user_leave_summary
)

__all__ = [
    # ---------------------------------------#
    #            Allergen Utils              #
    # ---------------------------------------#
    'lookup_allergen', 'get_allergen_by_id', 'create_allergen',
    'update_allergen', 'delete_allergen', 'search_allergens',
    'validate_allergen_data', 'AllergenError',
    
    # ---------------------------------------#
    #            Recipe Utils                #
    # ---------------------------------------#
    'lookup_ingredient', 'lookup_tag', 'lookup_cuisine', 'lookup_method',
    'lookup_dietary', 'lookup_mealtype', 'lookup_recipeIngredient',
    'lookup_globalRecipe', 'lookup_allergen',
    
    # ---------------------------------------#
    #              Time Utils                #
    # ---------------------------------------#
    'timeago', 'generate_timestamp', 'format_datetime', 'parse_datetime',
    
    # ---------------------------------------#
    #               Notes Utils              #
    # ---------------------------------------#
    'create_user_note', 'get_user_notes', 'get_user_note_by_id',
    'update_user_note', 'delete_user_note',
    
    # ---------------------------------------#
    #             Business Utils             #
    # ---------------------------------------#
    'lookup_business', 'lookup_venue', 'lookup_work_area', 'create_business',
    'add_venue_to_business', 'add_work_area_to_venue', 'assign_user_to_business',
    'assign_user_to_work_area', 'get_business_hierarchy', 'update_business_status',
    'validate_business_structure',
    
    # ---------------------------------------#
    #             Google Utils               #
    # ---------------------------------------#
    'validate_google_token', 'get_google_service', 'KeepService',
    
    # ---------------------------------------#
    #            Security Utils              #
    # ---------------------------------------#
    'generate_random_string', 'generate_secure_token', 'generate_id_with_prefix',
    'hash_string', 'constant_time_compare', 'generate_session_id',
    'sanitize_input', 'log_security_event',
    
    # ---------------------------------------#
    #            Validation Utils            #
    # ---------------------------------------#
    'validate_request_data', 'validate_id_format', 'validate_uuid',
    'validate_email', 'validate_date_format', 'validate_phone_number',
    'validate_required_fields', 'validate_field_length', 'validate_numeric_range',
    'validate_business_data', 'validate_venue_data', 'validate_work_area_data',
    
    # ---------------------------------------#
    #            Database Utils              #
    # ---------------------------------------#
    'safe_object_id', 'format_mongo_doc', 'create_mongo_query',
    'handle_mongo_error', 'sanitize_mongo_query', 'build_aggregation_pipeline',
    'update_timestamp_fields', 'get_collection_stats', 'ensure_indexes',
    'bulk_write_operations', 'get_distinct_values', 'execute_transaction',
    
    # ---------------------------------------#
    #              Error Utils               #
    # ---------------------------------------#
    'AppError', 'ValidationError', 'AuthenticationError', 'PermissionError',
    'NotFoundError', 'DatabaseError', 'handle_error', 'log_error',
    'format_error_response', 'validate_or_raise', 'assert_found',
    'assert_valid', 'assert_permitted', 'get_error_context',
    
    # ---------------------------------------#
    #              Logging Utils             #
    # ---------------------------------------#
    'CustomJSONFormatter', 'setup_logging', 'log_event', 'log_api_request',
    'log_security_event', 'cleanup_logs', 'get_log_stats',
    
    # ---------------------------------------#
    #              Request Utils             #
    # ---------------------------------------#
    'get_request_data', 'validate_request_data', 'format_response',
    'paginate_results', 'parse_query_params', 'validate_content_type',
    'rate_limit', 'log_request_info', 'get_client_ip', 'get_pagination_params',
    'get_sort_params', 'get_filter_params', 'validate_request_size',
    
    # ---------------------------------------#
    #             Session Utils              #
    # ---------------------------------------#
    'SessionManager',
    
    # ---------------------------------------#
    #             Rate Limiter               #
    # ---------------------------------------#
    'RateLimiter',
    
    # ---------------------------------------#
    #             Audit Logger               #
    # ---------------------------------------#
    'AuditLogger',
    
    # ---------------------------------------#
    #             Payroll Utils              #
    # ---------------------------------------#
    # Tax-related functions
    'calculate_tax',
    'calculate_period_amount',
    'calculate_annual_salary',
    'calculate_hourly_rate',
    
    # Accrual-related functions
    'calculate_service_period',
    'calculate_leave_accrual',
    'get_leave_summary',
    'map_user_leave_data',
    'get_user_leave_summary'
]