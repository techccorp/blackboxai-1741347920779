"""
Business entity and company models
"""
import re
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from typing import List, Optional, Literal
from .base import PyObjectId
from .locations import HeadOffice
from .venues import Venue

class BusinessEntityType(BaseModel):
    """
    Type of business entity and its properties
    
    There are three types of business entities:
    - multi-venue: Company with venues across multiple physical locations 
                  (e.g., restaurant chain with locations in different suburbs)
    - multi-outlet: Company with multiple venues at the same physical location
                   (e.g., hotel with restaurant, bar, and function spaces)
    - single-venue: Company with only one venue at one location
                   (e.g., standalone restaurant)
    
    Each type has specific constraints on venue and location counts.
    """
    entity_type: Literal["multi-venue", "multi-outlet", "single-venue"] = Field(...)
    outlet_count: Optional[int] = Field(None, ge=1)
    venue_count: Optional[int] = Field(None, ge=1)
    location_count: Optional[int] = Field(None, ge=1)

    @root_validator
    def validate_counts(cls, values):
        """
        Validate that venue and location counts are consistent with the entity type
        
        Rules:
        - multi-venue: multiple venues across multiple locations
        - multi-outlet: multiple venues at one location
        - single-venue: one venue at one location
        
        Returns:
            Dict: Validated values
        
        Raises:
            ValueError: If counts don't match entity type constraints
        """
        entity_type = values.get("entity_type")
        
        if entity_type == "multi-venue":
            if values.get("venue_count", 0) <= 1:
                raise ValueError("Multi-venue entity must have more than one venue")
            if values.get("location_count", 0) <= 1:
                raise ValueError("Multi-venue entity must have more than one location")
                
        elif entity_type == "multi-outlet":
            if values.get("venue_count", 0) <= 1:
                raise ValueError("Multi-outlet entity must have more than one venue")
            if values.get("location_count", 0) != 1:
                raise ValueError("Multi-outlet entity must have exactly one location")
                
        elif entity_type == "single-venue":
            if values.get("venue_count", 0) != 1:
                raise ValueError("Single-venue entity must have exactly one venue")
            if values.get("location_count", 0) != 1:
                raise ValueError("Single-venue entity must have exactly one location")
                
        return values

class BusinessEntity(BaseModel):
    """
    Main business entity model representing a company in the system
    
    A business entity can be one of three types:
    1. Single-venue: One venue at one location (e.g., a standalone restaurant)
    2. Multi-outlet: Multiple venues at one location (e.g., hotel with different venues)
    3. Multi-venue: Multiple venues across different locations (e.g., restaurant chain)
    
    The entity type is determined automatically based on the venues and their locations,
    but can also be explicitly set.
    """
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    company_id: str = Field(..., pattern=r'^CNY-\d{4}$')
    company_name: str = Field(..., min_length=2, max_length=100)
    director_name: str = Field(..., min_length=2, max_length=100)
    ACN: str = Field(..., pattern=r'^\d{3} \d{3} \d{3}$')
    admin_user_id: str = Field(..., pattern=r'^CNY-\d{4}-\d{4}$')
    entity_type: BusinessEntityType = None
    head_office: HeadOffice
    venues: List[Venue] = Field(..., min_items=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('company_id')
    def validate_company_id(cls, v):
        """Validate company ID format"""
        if not re.match(r'^CNY-\d{4}$', v):
            raise ValueError("Invalid company ID format")
        return v

    @validator('ACN')
    def format_ACN(cls, v):
        """
        Ensure ACN format consistency
        
        Formats an Australian Company Number (ACN) in the standard
        format with spaces: XXX XXX XXX
        """
        clean_acn = v.replace(" ", "")
        if len(clean_acn) != 9:
            raise ValueError("ACN must be 9 digits")
        return f"{clean_acn[:3]} {clean_acn[3:6]} {clean_acn[6:9]}"

    @validator('admin_user_id')
    def validate_admin_id(cls, v, values):
        """
        Validate admin user ID belongs to the company
        
        The admin user ID must start with the company ID prefix.
        """
        company_id = values.get('company_id', '')
        if company_id:
            company_prefix = company_id.split('-')[1]
            if not v.startswith(f"CNY-{company_prefix}"):
                raise ValueError("Admin ID must belong to the company")
        return v

    @root_validator
    def validate_entity_type(cls, values):
        """
        Validate and determine the entity type based on venues and locations
        
        This validator automatically determines the business entity type by analyzing:
        1. The number of venues
        2. The number of unique locations
        
        Entity type determination logic:
        - If multiple venues across multiple locations → multi-venue
        - If multiple venues at a single location → multi-outlet
        - If one venue at one location → single-venue
        
        If entity_type is already provided, it will update the counts while
        preserving the specified type.
        
        Returns:
            Dict: Validated values with entity_type
        """
        venues = values.get("venues", [])
        venue_count = len(venues)
        
        # Count unique locations
        locations = set()
        for venue in venues:
            location_id = venue.location.location_id if venue.location else None
            if location_id:
                locations.add(location_id)
            else:
                # If no location_id, treat each venue as its own location
                locations.add(venue.venue_id)
                
        location_count = len(locations)
        
        # Determine entity type if not explicitly set
        entity_type = values.get("entity_type")
        if not entity_type:
            if venue_count > 1 and location_count > 1:
                entity_type_value = "multi-venue"
            elif venue_count > 1 and location_count == 1:
                entity_type_value = "multi-outlet"
            else:
                entity_type_value = "single-venue"
                
            values["entity_type"] = BusinessEntityType(
                entity_type=entity_type_value,
                venue_count=venue_count,
                location_count=location_count
            )
        # If entity_type was set, update the counts
        else:
            values["entity_type"].venue_count = venue_count
            values["entity_type"].location_count = location_count
            
        return values

    def add_venue(self, venue: Venue) -> None:
        """
        Add a venue with validation
        
        Validates that:
        - Venue ID is unique
        - Entity type constraints are respected
        - For multi-outlet, all venues share the same location
        
        Args:
            venue: The venue to add
            
        Raises:
            ValueError: If venue doesn't satisfy the constraints
        """
        if any(v.venue_id == venue.venue_id for v in self.venues):
            raise ValueError("Venue ID must be unique")
            
        # Check entity type constraints
        if self.entity_type.entity_type == "single-venue" and len(self.venues) >= 1:
            raise ValueError("Cannot add multiple venues to a single-venue entity")
            
        # For multi-outlet, ensure new venue has the same location
        if self.entity_type.entity_type == "multi-outlet":
            if len(self.venues) > 0:
                existing_location = self.venues[0].location
                if venue.location != existing_location:
                    raise ValueError("All venues in a multi-outlet entity must share the same location")
                    
        self.venues.append(venue)
        self.updated_at = datetime.utcnow()
        
        # Update entity type if needed
        self._update_entity_type()
        
    def _update_entity_type(self):
        """
        Update entity type based on current venues and locations
        
        This method is called after adding or removing venues to ensure
        the entity_type accurately reflects the current state.
        
        Entity type classification rules:
        - multi-venue: Multiple venues across multiple locations
          (e.g., venues in different suburbs or cities)
        - multi-outlet: Multiple venues at a single location
          (e.g., restaurant and bar in the same hotel)
        - single-venue: One venue at one location
          (e.g., standalone restaurant)
        """
        venue_count = len(self.venues)
        
        # Count unique locations
        locations = set()
        for venue in self.venues:
            location_id = venue.location.location_id if venue.location else None
            if location_id:
                locations.add(location_id)
            else:
                locations.add(venue.venue_id)
                
        location_count = len(locations)
        
        # Determine entity type
        if venue_count > 1 and location_count > 1:
            entity_type_value = "multi-venue"
        elif venue_count > 1 and location_count == 1:
            entity_type_value = "multi-outlet"
        else:
            entity_type_value = "single-venue"
            
        # Update entity type
        self.entity_type = BusinessEntityType(
            entity_type=entity_type_value,
            venue_count=venue_count,
            location_count=location_count
        )

    class Config:
        allow_population_by_field_name = True
        json_encoders = {PyObjectId: str}
        schema_extra = {
            "example": {
                "_id": "67c1246d02971bbe2f6e6fe3",
                "company_id": "CNY-2976",
                "company_name": "Melbourne Venue Co",
                "director_name": "Bruce Wayne",
                "ACN": "345 352 452",
                "admin_user_id": "CNY-2976-2492",
                "entity_type": {
                    "entity_type": "multi-venue",
                    "venue_count": 2,
                    "location_count": 2
                },
                "head_office": {
                    "address": "56 City Road",
                    "suburb": "Southbank",
                    "state": "Victoria",
                    "post_code": "3006",
                    "contact": {
                        "phone": "+61396839999",
                        "email": "head_office@melbournevenueco.com.au"
                    }
                },
                "venues": [
                    {
                        "venue_id": "VEN-2976-30",
                        "venue_name": "Black Jacks Smokehouse",
                        "venue_manager_id": "EMP-2976-3087-308720",
                        "venue_manager_name": "Norville Rogers",
                        "location": {
                            "address": "550 Bourke St",
                            "suburb": "Melbourne",
                            "state": "Victoria",
                            "post_code": "3000",
                            "location_id": "LOC-2976-01",
                            "location_name": "CBD"
                        },
                        "workareas": [
                            {"work_area_name": "venue", "work_area_id": "WAI-2976-3087"},
                            {"work_area_name": "kitchen", "work_area_id": "WAI-2976-3088"},
                            {"work_area_name": "bar", "work_area_id": "WAI-2976-3089"}
                        ]
                    },
                    {
                        "venue_id": "VEN-2976-31",
                        "venue_name": "Gather & Graze",
                        "venue_manager_id": "EMP-2976-3187-318721",
                        "venue_manager_name": "Scooby Doo",
                        "location": {
                            "address": "100 Exhibition St",
                            "suburb": "Melbourne",
                            "state": "Victoria",
                            "post_code": "3000",
                            "location_id": "LOC-2976-02",
                            "location_name": "East End"
                        },
                        "workareas": [
                            {"work_area_name": "venue", "work_area_id": "WAI-2976-3187"},
                            {"work_area_name": "kitchen", "work_area_id": "WAI-2976-3188"},
                            {"work_area_name": "bar", "work_area_id": "WAI-2976-3189"},
                            {"work_area_name": "restaurant", "work_area_id": "WAI-2976-3190"}
                        ]
                    }
                ]
            }
        }
