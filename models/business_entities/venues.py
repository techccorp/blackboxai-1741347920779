"""
Venue and work area models for business entities
"""
import re
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from .locations import VenueLocation

class WorkArea(BaseModel):
    """
    Work area within a venue
    
    Examples include: bar, kitchen, restaurant, venue (general area)
    Each work area has a specific ID format and must be one of the recognized areas.
    """
    work_area_name: str = Field(..., min_length=2, max_length=50)
    work_area_id: str = Field(..., pattern=r'^WAI-\d{4}-\d{4}$')

    @field_validator('work_area_name')
    def validate_work_area_name(cls, v):
        """
        Validate that the work area is one of the recognized types
        
        Valid work areas correspond to the area codes used in payroll IDs.
        """
        valid_areas = [
            "admin", "bar", "cleaners", "functions", "guest services",
            "house keeping", "kitchen", "maintenance", "operations",
            "restaurant", "store room", "venue"
        ]
        if v.lower() not in valid_areas:
            raise ValueError(f"Work area must be one of: {', '.join(valid_areas)}")
        return v

    @field_validator('work_area_id')
    def validate_work_area_id(cls, v):
        # Add validation logic for work_area_id here if needed
        return v

class Venue(BaseModel):
    """
    Venue model representing a business location
    
    A venue is a specific business establishment (e.g., restaurant, bar)
    that belongs to a company and has one or more work areas.
    """
    venue_id: str = Field(..., pattern=r'^VEN-\d{4}-\d{2}$')
    venue_name: str = Field(..., min_length=2, max_length=100)
    venue_manager_id: str = Field(..., pattern=r'^EMP-\d{4}-\d{4}-\d{6}$')
    venue_manager_name: str = Field(..., min_length=2, max_length=100)
    location: Optional[VenueLocation] = None
    workareas: List[WorkArea] = Field(..., min_items=1)

    @field_validator('venue_id')
    def validate_venue_id(cls, v):
        """Validate venue ID format"""
        if not re.match(r'^VEN-\d{4}-\d{2}$', v):
            raise ValueError("Invalid venue ID format")
        return v

    @field_validator('venue_manager_id')
    def validate_manager_id(cls, v):
        """Validate manager ID format"""
        if not re.match(r'^EMP-\d{4}-\d{4}-\d{6}$', v):
            raise ValueError("Invalid manager ID format")
        return v

    @model_validator
    def validate_workareas(cls, values):
        """
        Ensure venue has required standard work areas
        
        Every venue must have at least a "venue" work area, and
        no duplicate work areas are allowed.
        """
        print("validate_workareas:", values)
        required_areas = ["venue"]
        workareas = values.get("workareas", [])
        work_area_names = [wa.work_area_name.lower() for wa in workareas]
        
        for area in required_areas:
            if area not in work_area_names:
                raise ValueError(f"Venue must have '{area}' work area")
        
        # Check for duplicate work areas
        if len(work_area_names) != len(set(work_area_names)):
            raise ValueError("Duplicate work areas are not allowed")
        
        print("validate_workareas: valid")
        return values