"""
Location and address models for business entities
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from .base import ContactInfo

class Address(BaseModel):
    """Base address model with standard Australian address fields"""
    address: str = Field(..., min_length=5, max_length=200)
    suburb: str = Field(..., min_length=2, max_length=50)
    state: str = Field(..., min_length=2, max_length=50)
    post_code: str = Field(..., pattern=r'^\d{4}$')

class HeadOffice(Address):
    """
    Head office location for a business entity
    
    Extends the base address model with contact information
    """
    contact: ContactInfo

class VenueLocation(Address):
    """
    Physical location for a venue
    
    A venue location represents a physical address where one or more venues
    can be situated. This is particularly important for multi-outlet entities
    where multiple venues share the same location.
    """
    location_id: Optional[str] = Field(None, pattern=r'^LOC-\d{4}-\d{2}$')