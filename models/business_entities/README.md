# Business Entities Model Package

This package provides comprehensive models for representing business entities in the MyCookBook application, focusing on organizational hierarchy, venue management, and employee data.

## Structure

The package is organized by domain:

```
models/business_entities/
├── __init__.py        # Exports all models
├── base.py            # Common types (PyObjectId, ContactInfo, etc.)
├── locations.py        # Address-related models
├── companies.py         # BusinessEntity models
├── venues.py           # Venue models
├── employment.py      # Employment-related models
├── employees.py        # Employee models with security features
└── compatibility.py   # Compatibility utilities
```

## Key Features

- **Multiple Entity Types**: Support for single-venue, multi-outlet, and multi-venue business structures
- **ID Validation**: Comprehensive validation for payroll IDs, linking IDs, and work area codes
- **Security**: Password management, security status tracking, and MFA capabilities
- **Backward Compatibility**: Utilities for migrating from older model formats

## Business Entity Types

The system supports three types of business entities:

1. **Single-venue**: One venue at one location (e.g., a standalone restaurant)
2. **Multi-outlet**: Multiple venues at a single location (e.g., hotel with different venues)
3. **Multi-venue**: Multiple venues across different locations (e.g., restaurant chain)

## Usage Examples

### Creating a New Employee

```python
from models.business_entities import EmployeeCreate, Employee, EmploymentDetails, PayRate

# Create employee instance
new_employee = EmployeeCreate(
    linking_id="EMP-2976-3088-520242",
    payroll_id="DB-520242",
    company_id="CNY-2976",
    company_name="Melbourne Venue Co",
    venue_id="VEN-2976-30",
    venue_name="Black Jacks Smoke House",
    work_area_id="WAI-2976-3088",
    work_area_name="Bar",
    role_id="FOH-MGT-304",
    role_name="Bar Manager",
    first_name="Penelope",
    last_name="Pittstop",
    # ... other fields
    password="SecurePassword123!",
    employment_details=EmploymentDetails(
        hired_date=datetime.now(),
        employment_type="full time",
        pay_type="salary",
        pay_rate=PayRate(
            per_annum_rate=85000
        )
    )
)

# Convert to Employee for database storage
# (In practice, this would involve hashing the password)
```

### Converting Between Old and New Formats

```python
from models.business_entities.compatibility import convert_business_user_to_employee

# Load old format from database
old_format_user = db.business_users.find_one({"payroll_id": "DB-520242"})

# Convert to new model
employee = convert_business_user_to_employee(old_format_user)

# Use the employee model with all its new features
if employee.check_password_age():
    print("Password needs to be updated")
```

## Validation Features

The models include extensive validation:

- Payroll IDs must match work areas (e.g., "DB-" for Bar)
- Work emails must correspond to payroll IDs
- Linking IDs must contain correct company and work area references
- Password policies (length, complexity, history)
- Entity type constraints (venue counts, location requirements)
