from bson import ObjectId
from datetime import datetime, time, timedelta
from typing import Optional, List, Dict, Any

class Shift:
    """Represents a single shift for an employee"""
    def __init__(self, 
                 linking_id: str, 
                 venue_id: str,
                 date: datetime,
                 start_time: time = None,
                 end_time: time = None,
                 role: str = None,
                 is_rdo: bool = False,
                 notes: str = None,
                 status: str = "scheduled",  # scheduled, confirmed, completed
                 _id: str = None):
        self.linking_id = linking_id
        self.venue_id = venue_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.role = role
        self.is_rdo = is_rdo
        self.notes = notes
        self.status = status
        self._id = ObjectId(_id) if _id else ObjectId()
    
    @property
    def duration_hours(self) -> float:
        """Calculate shift duration in hours"""
        if self.is_rdo:
            return 0
        
        # Convert times to datetime for calculation
        start_dt = datetime.combine(self.date.date(), self.start_time)
        end_dt = datetime.combine(self.date.date(), self.end_time)
        
        # Handle overnight shifts
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
            
        duration = end_dt - start_dt
        return duration.total_seconds() / 3600
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Shift':
        """Create a Shift object from a dictionary"""
        # Handle date and time conversions
        date = data.get('date')
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        
        start_time = data.get('start_time')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00')).time()
        
        end_time = data.get('end_time')
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00')).time()
        
        return cls(
            linking_id=data.get('linking_id'),
            venue_id=data.get('venue_id'),
            date=date,
            start_time=start_time,
            end_time=end_time,
            role=data.get('role'),
            is_rdo=data.get('is_rdo', False),
            notes=data.get('notes'),
            status=data.get('status', 'scheduled'),
            _id=data.get('_id')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Shift object to a dictionary"""
        return {
            '_id': str(self._id),
            'linking_id': self.linking_id,
            'venue_id': self.venue_id,
            'date': self.date.isoformat(),
            'start_time': self.start_time.isoformat() if not self.is_rdo and self.start_time else None,
            'end_time': self.end_time.isoformat() if not self.is_rdo and self.end_time else None,
            'role': self.role,
            'is_rdo': self.is_rdo,
            'notes': self.notes,
            'status': self.status,
            'duration_hours': self.duration_hours if not self.is_rdo else 0
        }


class Roster:
    """Manager for employee roster shifts"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db[db.app.config['COLLECTION_PAYROLL_ROSTERED_HOURS']]
    
    def get_roster_for_venue(self, 
                            venue_id: str, 
                            start_date: datetime,
                            end_date: datetime,
                            linking_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all shifts for a venue within a date range"""
        query = {
            'venue_id': venue_id,
            'date': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        
        if linking_id:
            query['linking_id'] = linking_id
            
        shifts = list(self.collection.find(query))
        return [Shift.from_dict(shift).to_dict() for shift in shifts]
    
    def get_employee_shifts(self, 
                          linking_id: str, 
                          start_date: datetime,
                          end_date: datetime,
                          venue_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all shifts for an employee within a date range"""
        query = {
            'linking_id': linking_id,
            'date': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        
        if venue_id:
            query['venue_id'] = venue_id
            
        shifts = list(self.collection.find(query))
        return [Shift.from_dict(shift).to_dict() for shift in shifts]
    
    def add_shift(self, shift: Shift) -> str:
        """Add a new shift to the roster"""
        shift_dict = shift.to_dict()
        # Convert date strings to datetime objects for MongoDB storage
        if 'date' in shift_dict and isinstance(shift_dict['date'], str):
            shift_dict['date'] = datetime.fromisoformat(shift_dict['date'].replace('Z', '+00:00'))
        
        result = self.collection.insert_one(shift_dict)
        return str(result.inserted_id)
    
    def update_shift(self, shift_id: str, updated_data: Dict[str, Any]) -> bool:
        """Update an existing shift"""
        # Convert date strings to datetime objects for MongoDB storage
        if 'date' in updated_data and isinstance(updated_data['date'], str):
            updated_data['date'] = datetime.fromisoformat(updated_data['date'].replace('Z', '+00:00'))
            
        result = self.collection.update_one(
            {'_id': ObjectId(shift_id)},
            {'$set': updated_data}
        )
        return result.modified_count > 0
    
    def delete_shift(self, shift_id: str) -> bool:
        """Delete a shift from the roster"""
        result = self.collection.delete_one({'_id': ObjectId(shift_id)})
        return result.deleted_count > 0
    
    def get_week_roster(self, venue_id: str, week_start_date: datetime) -> Dict[str, List[Dict[str, Any]]]:
        """Get roster data organized by employee for a week"""
        # Calculate the end date (7 days from start)
        week_end_date = week_start_date + timedelta(days=6)
        
        # Get all shifts for the venue in this week
        all_shifts = self.get_roster_for_venue(venue_id, week_start_date, week_end_date)
        
        # Organize shifts by employee
        roster_by_employee = {}
        for shift in all_shifts:
            linking_id = shift['linking_id']
            if linking_id not in roster_by_employee:
                roster_by_employee[linking_id] = {
                    'linking_id': linking_id,
                    'shifts': []
                }
            roster_by_employee[linking_id]['shifts'].append(shift)
        
        return roster_by_employee
