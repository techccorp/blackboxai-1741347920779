"""
permissions_system.py
---------------------
This module implements a production‐ready permissions system for our application.
It defines a PermissionSystem class that holds permission configurations for the following
role classifications:
  - Executive Management
  - Senior Management
  - Management
  - Dept Manager
  - Sub-Dept Manager
  - Employee

Permissions are defined as a nested dictionary where each classification groups permissions
into categories (e.g. "Work Management", "Scheduling & Approval", etc.). Higher-level roles have a
superset of permissions relative to lower-level roles.
  
Usage:
    ps = PermissionSystem()
    # Get the full permission set for "employee"
    employee_perms = ps.get_permissions("employee")
    # Check if an "employee" can "ApproveTimesheets_WorkArea"
    if ps.has_permission("employee", "ApproveTimesheets_WorkArea"):
        # allow action
        pass
"""

# utils/permissions_system.py
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PermissionSystem:
    """
    PermissionSystem manages role-based permissions for the application.
    """
    def __init__(self):
        # Define permissions for each role classification.
        self.permissions = {
            "executive management": {
                "Work Management": {
                    "ViewAllShifts": True,
                    "ViewAllShiftsLinkedToWorkArea": True,
                    "ViewAllShiftsLinkedToPayroll": True,
                    "StartAllShifts": True,
                    "StartAllShiftsLinkedToPayroll": True,
                    "Clock in and out": True,
                    "ManageAllTasks": True,
                    "ManageAllTasksLinkedToWorkArea": True,
                    "ManageAllTasksLinkedToPayroll": True,
                    "PostToNewsFeed_Company": True,
                    "PostToNewsFeed_Venue": True,
                    "PostToNewsFeed_WorkArea": True,
                },
                "Scheduling & Approval": {
                    "ScheduleTeamMembers_Company": True,
                    "ScheduleTeamMembers_Venue": True,
                    "ScheduleTeamMembers_WorkArea": True,
                    "ApproveTimesheets_Company": True,
                    "ApproveTimesheets_Venue": True,
                    "ApproveTimesheets_WorkArea": True,
                    "ApproveLeaveRequests_Company": True,
                    "ApproveLeaveRequests_Venue": True,
                    "ApproveLeaveRequests_WorkArea": True,
                    "CreateJournals": True,
                },
                "Employee & Role Management": {
                    "Add/edit team members": True,
                    "ViewTeamMemberCosts_Company": True,
                    "ViewTeamMemberCosts_Venue": True,
                    "ViewTeamMemberCosts_WorkArea": True,
                    "Onboard new hire": True,
                    "assignEmployeeToVenueAndWorkArea": True,
                },
                "Data & Reports": {
                    "Export timesheets": True,
                    "AccessReports_Company": True,
                    "AccessReports_Venue": True,
                    "AccessReports_WorkArea": True,
                    "accessUserDashboardLinkedToCompany": True,
                    "accessUserDashboardLinkedToVenue": True,
                    "accessUserDashboardLinkedToPayroll": True,
                },
                "System & Integrations": {
                    "Set up Kiosk": True,
                    "Manage integrations": True,
                    "Edit locations": True,
                    "Create locations": True,
                },
                "Recipe & Resource Management": {
                    "editAndSubmitRecipes": True,
                    "editAndSubmitRecipesLinkedToPayroll": True,
                    "accessResourceCentreReadOnly": True,
                    "accessAllergenSearch": True,
                    "accessRecipeSearch": True,
                    "accessRecipeGenerator": True,
                },
                "Administrative & Permissions": {
                    "editAllRostersRequireVenueApproval": True,
                    "approveEmployeeLeaveWithVenueApproval": True,
                    "accessAndEditCalendarLinkedToCompany": True,
                    "accessAndEditCalendarLinkedToVenue": True,
                    "accessAndEditCalendarLinkedToWorkArea": True,
                    "accessAndEditCalendarLinkedToPayroll": True,
                    "accessAndEditNotesLinkedToPayroll": True,
                    "allAccess": True,
                },
                "Confidential Data Access": {
                    "View and manage documents": True,
                    "viewAndManageDocumentsLinkedToPayroll": True,
                    "View and hire candidates": True,
                },
            },
            "senior management": {
                "Work Management": {
                    "ViewAllShifts": True,
                    "ViewAllShiftsLinkedToWorkArea": True,
                    "ViewAllShiftsLinkedToPayroll": True,
                    "StartAllShifts": True,
                    "StartAllShiftsLinkedToPayroll": True,
                    "Clock in and out": True,
                    "ManageAllTasks": True,
                    "ManageAllTasksLinkedToWorkArea": True,
                    "ManageAllTasksLinkedToPayroll": True,
                    "PostToNewsFeed_Company": True,
                    "PostToNewsFeed_Venue": True,
                    "PostToNewsFeed_WorkArea": True,
                },
                "Scheduling & Approval": {
                    "ScheduleTeamMembers_Company": True,
                    "ScheduleTeamMembers_Venue": True,
                    "ScheduleTeamMembers_WorkArea": True,
                    "ApproveTimesheets_Company": True,
                    "ApproveTimesheets_Venue": True,
                    "ApproveTimesheets_WorkArea": True,
                    "ApproveLeaveRequests_Company": True,
                    "ApproveLeaveRequests_Venue": True,
                    "ApproveLeaveRequests_WorkArea": True,
                    "CreateJournals": True,
                },
                "Employee & Role Management": {
                    "Add/edit team members": True,
                    "ViewTeamMemberCosts_Company": True,
                    "ViewTeamMemberCosts_Venue": True,
                    "ViewTeamMemberCosts_WorkArea": True,
                    "Onboard new hire": True,
                    "assignEmployeeToVenueAndWorkArea": True,
                },
                "Data & Reports": {
                    "Export timesheets": True,
                    "AccessReports_Company": True,
                    "AccessReports_Venue": True,
                    "AccessReports_WorkArea": True,
                    "accessUserDashboardLinkedToCompany": True,
                    "accessUserDashboardLinkedToVenue": True,
                    "accessUserDashboardLinkedToPayroll": True,
                },
                "System & Integrations": {
                    "Set up Kiosk": False,
                    "Manage integrations": True,
                    "Edit locations": True,
                    "Create locations": True,
                },
                "Recipe & Resource Management": {
                    "editAndSubmitRecipes": True,
                    "editAndSubmitRecipesLinkedToPayroll": True,
                    "accessResourceCentreReadOnly": True,
                    "accessAllergenSearch": True,
                    "accessRecipeSearch": True,
                    "accessRecipeGenerator": True,
                },
                "Administrative & Permissions": {
                    "editAllRostersRequireVenueApproval": True,
                    "approveEmployeeLeaveWithVenueApproval": True,
                    "accessAndEditCalendarLinkedToCompany": True,
                    "accessAndEditCalendarLinkedToVenue": True,
                    "accessAndEditCalendarLinkedToWorkArea": True,
                    "accessAndEditCalendarLinkedToPayroll": True,
                    "accessAndEditNotesLinkedToPayroll": True,
                    "allAccess": False,
                },
                "Confidential Data Access": {
                    "View and manage documents": True,
                    "viewAndManageDocumentsLinkedToPayroll": True,
                    "View and hire candidates": True,
                },
            },
            "management": {
                "Work Management": {
                    "ViewAllShifts": True,
                    "ViewAllShiftsLinkedToWorkArea": True,
                    "ViewAllShiftsLinkedToPayroll": False,
                    "StartAllShifts": True,
                    "StartAllShiftsLinkedToPayroll": False,
                    "Clock in and out": True,
                    "ManageAllTasks": True,
                    "ManageAllTasksLinkedToWorkArea": True,
                    "ManageAllTasksLinkedToPayroll": False,
                    "PostToNewsFeed_Company": True,
                    "PostToNewsFeed_Venue": True,
                    "PostToNewsFeed_WorkArea": False,
                },
                "Scheduling & Approval": {
                    "ScheduleTeamMembers_Company": True,
                    "ScheduleTeamMembers_Venue": True,
                    "ScheduleTeamMembers_WorkArea": True,
                    "ApproveTimesheets_Company": False,
                    "ApproveTimesheets_Venue": False,
                    "ApproveTimesheets_WorkArea": False,
                    "ApproveLeaveRequests_Company": False,
                    "ApproveLeaveRequests_Venue": False,
                    "ApproveLeaveRequests_WorkArea": False,
                    "CreateJournals": False,
                },
                "Employee & Role Management": {
                    "Add/edit team members": True,
                    "ViewTeamMemberCosts_Company": False,
                    "ViewTeamMemberCosts_Venue": False,
                    "ViewTeamMemberCosts_WorkArea": False,
                    "Onboard new hire": False,
                    "assignEmployeeToVenueAndWorkArea": False,
                },
                "Data & Reports": {
                    "Export timesheets": False,
                    "AccessReports_Company": False,
                    "AccessReports_Venue": False,
                    "AccessReports_WorkArea": False,
                    "accessUserDashboardLinkedToCompany": False,
                    "accessUserDashboardLinkedToVenue": False,
                    "accessUserDashboardLinkedToPayroll": False,
                },
                "System & Integrations": {
                    "Set up Kiosk": False,
                    "Manage integrations": False,
                    "Edit locations": False,
                    "Create locations": False,
                },
                "Recipe & Resource Management": {
                    "editAndSubmitRecipes": False,
                    "editAndSubmitRecipesLinkedToPayroll": False,
                    "accessResourceCentreReadOnly": True,
                    "accessAllergenSearch": True,
                    "accessRecipeSearch": True,
                    "accessRecipeGenerator": True,
                },
                "Administrative & Permissions": {
                    "editAllRostersRequireVenueApproval": False,
                    "approveEmployeeLeaveWithVenueApproval": False,
                    "accessAndEditCalendarLinkedToCompany": False,
                    "accessAndEditCalendarLinkedToVenue": False,
                    "accessAndEditCalendarLinkedToWorkArea": False,
                    "accessAndEditCalendarLinkedToPayroll": False,
                    "accessAndEditNotesLinkedToPayroll": False,
                    "allAccess": False,
                },
                "Confidential Data Access": {
                    "View and manage documents": False,
                    "viewAndManageDocumentsLinkedToPayroll": False,
                    "View and hire candidates": False,
                },
            },
            "dept manager": {
                "Work Management": {
                    "ViewAllShifts": True,
                    "ViewAllShiftsLinkedToWorkArea": True,
                    "ViewAllShiftsLinkedToPayroll": True,
                    "StartAllShifts": True,
                    "StartAllShiftsLinkedToPayroll": True,
                    "Clock in and out": True,
                    "ManageAllTasks": True,
                    "ManageAllTasksLinkedToWorkArea": True,
                    "ManageAllTasksLinkedToPayroll": True,
                    "PostToNewsFeed_Company": True,
                    "PostToNewsFeed_Venue": True,
                    "PostToNewsFeed_WorkArea": True,
                },
                "Scheduling & Approval": {
                    "ScheduleTeamMembers_Company": True,
                    "ScheduleTeamMembers_Venue": True,
                    "ScheduleTeamMembers_WorkArea": True,
                    "ApproveTimesheets_Company": True,
                    "ApproveTimesheets_Venue": True,
                    "ApproveTimesheets_WorkArea": True,
                    "ApproveLeaveRequests_Company": True,
                    "ApproveLeaveRequests_Venue": True,
                    "ApproveLeaveRequests_WorkArea": True,
                    "CreateJournals": True,
                },
                "Employee & Role Management": {
                    "Add/edit team members": True,
                    "ViewTeamMemberCosts_Company": True,
                    "ViewTeamMemberCosts_Venue": True,
                    "ViewTeamMemberCosts_WorkArea": True,
                    "Onboard new hire": True,
                    "assignEmployeeToVenueAndWorkArea": True,
                },
                "Data & Reports": {
                    "Export timesheets": True,
                    "AccessReports_Company": True,
                    "AccessReports_Venue": True,
                    "AccessReports_WorkArea": True,
                    "accessUserDashboardLinkedToCompany": True,
                    "accessUserDashboardLinkedToVenue": True,
                    "accessUserDashboardLinkedToPayroll": True,
                },
                "System & Integrations": {
                    "Set up Kiosk": False,
                    "Manage integrations": False,
                    "Edit locations": False,
                    "Create locations": False,
                },
                "Recipe & Resource Management": {
                    "editAndSubmitRecipes": True,
                    "editAndSubmitRecipesLinkedToPayroll": True,
                    "accessResourceCentreReadOnly": True,
                    "accessAllergenSearch": True,
                    "accessRecipeSearch": True,
                    "accessRecipeGenerator": True,
                },
                "Administrative & Permissions": {
                    "editAllRostersRequireVenueApproval": True,
                    "approveEmployeeLeaveWithVenueApproval": True,
                    "accessAndEditCalendarLinkedToCompany": True,
                    "accessAndEditCalendarLinkedToVenue": True,
                    "accessAndEditCalendarLinkedToWorkArea": True,
                    "accessAndEditCalendarLinkedToPayroll": True,
                    "accessAndEditNotesLinkedToPayroll": True,
                    "allAccess": False,
                },
                "Confidential Data Access": {
                    "View and manage documents": True,
                    "viewAndManageDocumentsLinkedToPayroll": True,
                    "View and hire candidates": True,
                },
            },
            "sub-dept manager": {
                "Work Management": {
                    "ViewAllShifts": True,
                    "ViewAllShiftsLinkedToWorkArea": True,
                    "ViewAllShiftsLinkedToPayroll": False,
                    "StartAllShifts": True,
                    "StartAllShiftsLinkedToPayroll": False,
                    "Clock in and out": True,
                    "ManageAllTasks": True,
                    "ManageAllTasksLinkedToWorkArea": False,
                    "ManageAllTasksLinkedToPayroll": False,
                    "PostToNewsFeed_Company": True,
                    "PostToNewsFeed_Venue": True,
                    "PostToNewsFeed_WorkArea": False,
                },
                "Scheduling & Approval": {
                    "ScheduleTeamMembers_Company": False,
                    "ScheduleTeamMembers_Venue": False,
                    "ScheduleTeamMembers_WorkArea": False,
                    "ApproveTimesheets_Company": False,
                    "ApproveTimesheets_Venue": False,
                    "ApproveTimesheets_WorkArea": False,
                    "ApproveLeaveRequests_Company": False,
                    "ApproveLeaveRequests_Venue": False,
                    "ApproveLeaveRequests_WorkArea": False,
                    "CreateJournals": False,
                },
                "Employee & Role Management": {
                    "Add/edit team members": False,
                    "ViewTeamMemberCosts_Company": False,
                    "ViewTeamMemberCosts_Venue": False,
                    "ViewTeamMemberCosts_WorkArea": False,
                    "Onboard new hire": False,
                    "assignEmployeeToVenueAndWorkArea": False,
                },
                "Data & Reports": {
                    "Export timesheets": False,
                    "AccessReports_Company": False,
                    "AccessReports_Venue": False,
                    "AccessReports_WorkArea": False,
                    "accessUserDashboardLinkedToCompany": False,
                    "accessUserDashboardLinkedToVenue": False,
                    "accessUserDashboardLinkedToPayroll": False,
                },
                "System & Integrations": {
                    "Set up Kiosk": False,
                    "Manage integrations": False,
                    "Edit locations": False,
                    "Create locations": False,
                },
                "Recipe & Resource Management": {
                    "editAndSubmitRecipes": False,
                    "editAndSubmitRecipesLinkedToPayroll": False,
                    "accessResourceCentreReadOnly": True,
                    "accessAllergenSearch": True,
                    "accessRecipeSearch": True,
                    "accessRecipeGenerator": True,
                },
                "Administrative & Permissions": {
                    "editAllRostersRequireVenueApproval": False,
                    "approveEmployeeLeaveWithVenueApproval": False,
                    "accessAndEditCalendarLinkedToCompany": False,
                    "accessAndEditCalendarLinkedToVenue": False,
                    "accessAndEditCalendarLinkedToWorkArea": False,
                    "accessAndEditCalendarLinkedToPayroll": False,
                    "accessAndEditNotesLinkedToPayroll": False,
                    "allAccess": False,
                },
                "Confidential Data Access": {
                    "View and manage documents": False,
                    "viewAndManageDocumentsLinkedToPayroll": False,
                    "View and hire candidates": False,
                },
            },
            "employee": {
                "Work Management": {
                    "ViewAllShifts": False,
                    "ViewAllShiftsLinkedToWorkArea": True,
                    "ViewAllShiftsLinkedToPayroll": True,
                    "StartAllShifts": False,
                    "StartAllShiftsLinkedToPayroll": True,
                    "Clock in and out": True,
                    "ManageAllTasks": False,
                    "ManageAllTasksLinkedToWorkArea": False,
                    "ManageAllTasksLinkedToPayroll": True,
                    "PostToNewsFeed_Company": False,
                    "PostToNewsFeed_Venue": False,
                    "PostToNewsFeed_WorkArea": True,
                },
                "Scheduling & Approval": {
                    "ScheduleTeamMembers_Company": False,
                    "ScheduleTeamMembers_Venue": False,
                    "ScheduleTeamMembers_WorkArea": False,
                    "ApproveTimesheets_Company": False,
                    "ApproveTimesheets_Venue": False,
                    "ApproveTimesheets_WorkArea": False,
                    "ApproveLeaveRequests_Company": False,
                    "ApproveLeaveRequests_Venue": False,
                    "ApproveLeaveRequests_WorkArea": False,
                    "CreateJournals": False,
                },
                "Employee & Role Management": {
                    "Add/edit team members": False,
                    "ViewTeamMemberCosts_Company": False,
                    "ViewTeamMemberCosts_Venue": False,
                    "ViewTeamMemberCosts_WorkArea": False,
                    "Onboard new hire": False,
                    "assignEmployeeToVenueAndWorkArea": False,
                },
                "Data & Reports": {
                    "Export timesheets": False,
                    "AccessReports_Company": False,
                    "AccessReports_Venue": False,
                    "AccessReports_WorkArea": False,
                    "accessUserDashboardLinkedToCompany": False,
                    "accessUserDashboardLinkedToVenue": False,
                    "accessUserDashboardLinkedToPayroll": True,
                },
                "System & Integrations": {
                    "Set up Kiosk": False,
                    "Manage integrations": False,
                    "Edit locations": False,
                    "Create locations": False,
                },
                "Recipe & Resource Management": {
                    "editAndSubmitRecipes": False,
                    "editAndSubmitRecipesLinkedToPayroll": True,
                    "accessResourceCentreReadOnly": True,
                    "accessAllergenSearch": True,
                    "accessRecipeSearch": True,
                    "accessRecipeGenerator": True,
                },
                "Administrative & Permissions": {
                    "editAllRostersRequireVenueApproval": False,
                    "approveEmployeeLeaveWithVenueApproval": False,
                    "accessAndEditCalendarLinkedToCompany": False,
                    "accessAndEditCalendarLinkedToVenue": False,
                    "accessAndEditCalendarLinkedToWorkArea": False,
                    "accessAndEditCalendarLinkedToPayroll": True,
                    "accessAndEditNotesLinkedToPayroll": True,
                    "allAccess": False,
                },
                "Confidential Data Access": {
                    "View and manage documents": False,
                    "viewAndManageDocumentsLinkedToPayroll": True,
                    "View and hire candidates": False,
                },
            },
        }
    
    def get_permissions(self, classification):
        """
        Returns the permission dictionary for the given role classification.
        
        Args:
            classification (str): The role classification.
        
        Returns:
            dict: Permissions for the given classification.
        """
        key = classification.lower().strip()
        perms = self.permissions.get(key, {})
        logger.debug(f"Permissions for '{key}': {perms}")
        return perms
    
    def has_permission(self, classification, permission):
        """
        Checks whether the given role classification has the specified permission enabled.
        
        Args:
            classification (str): The role classification.
            permission (str): The permission key to check.
        
        Returns:
            bool: True if allowed, otherwise False.
        """
        perms = self.get_permissions(classification)
        for group, perms_dict in perms.items():
            if permission in perms_dict:
                allowed = perms_dict[permission]
                logger.debug(f"Permission check for '{classification}' on '{permission}': {allowed}")
                return allowed
        logger.debug(f"Permission '{permission}' not found for classification '{classification}'.")
        return False
    
    def set_permissions(self, classification, permissions_dict):
        """
        Sets (or updates) the permissions for the given role classification.
        
        Args:
            classification (str): The role classification.
            permissions_dict (dict): The permissions dictionary.
        """
        key = classification.lower().strip()
        self.permissions[key] = permissions_dict
        logger.info(f"Permissions updated for '{key}'.")
    
    def add_permission(self, classification, permission, value):
        """
        Adds or updates a single permission for the given role classification.
        
        Args:
            classification (str): The role classification.
            permission (str): The permission key.
            value (bool): The permission value.
        """
        key = classification.lower().strip()
        if key not in self.permissions:
            self.permissions[key] = {}
        for group in self.permissions[key]:
            if permission in self.permissions[key][group]:
                self.permissions[key][group][permission] = value
                logger.info(f"Permission '{permission}' updated to {value} for classification '{key}' in group '{group}'.")
                return
        if "Miscellaneous" not in self.permissions[key]:
            self.permissions[key]["Miscellaneous"] = {}
        self.permissions[key]["Miscellaneous"][permission] = value
        logger.info(f"Permission '{permission}' set to {value} for classification '{key}' in group 'Miscellaneous'.")
