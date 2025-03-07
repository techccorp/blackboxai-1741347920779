from flask import Blueprint, render_template

# Create a blueprint for the sidebar routes
sidebar_bp = Blueprint('sidebar', __name__, template_folder='templates')

# Home route
@sidebar_bp.route('/home')
def home():
    return render_template('home.html')

# Search route
@sidebar_bp.route('/search')
def search():
    return render_template('search_recipe.html')

# Calendar route
@sidebar_bp.route('/calendar')
def calendar():
    return render_template('calendar.html')

# Finance routes
@sidebar_bp.route('/finance')
def finance_dashboard():
    return render_template('Finance/Finance_dashboard.html')

@sidebar_bp.route('/finance/dashboard')
def finance_dashboard_alias():
    return render_template('Finance/Finance_dashboard.html')

@sidebar_bp.route('/finance/stocktaking')
def finance_stocktaking():
    return render_template('Finance/Stocktaking.html')

@sidebar_bp.route('/finance/ordering')
def finance_ordering():
    return render_template('Finance/Ordering.html')

# Staff Management routes
@sidebar_bp.route('/staff-management')
def staff_dashboard():
    return render_template('Staff Management/staff_dashboard.html')

@sidebar_bp.route('/staff-management/dashboard')
def staff_dashboard_alias():
    return render_template('Staff Management/staff_dashboard.html')

@sidebar_bp.route('/staff-management/rostering')
def staff_rostering():
    return render_template('Staff Management/Rostering.html')

@sidebar_bp.route('/staff-management/holidays')
def staff_holidays():
    return render_template('Staff Management/Holidays.html')

# Menu Development routes
@sidebar_bp.route('/menu-development')
def menu_dashboard():
    return render_template('Menu Development/Dashboard.html')

@sidebar_bp.route('/menu-development/dashboard')
def menu_dashboard_alias():
    return render_template('Menu Development/Dashboard.html')

@sidebar_bp.route('/menu-development/recipe-costing')
def menu_recipe_costing():
    return render_template('Menu Development/Recipe_Costing.html')

@sidebar_bp.route('/menu-development/menu-costing')
def menu_menu_costing():
    return render_template('Menu Development/Menu_Costing.html')

@sidebar_bp.route('/menu-development/event-menus')
def menu_event_menus():
    return render_template('Menu Development/Event_Menus.html')

# Human Resources routes
@sidebar_bp.route('/human-resources')
def hr_dashboard():
    return render_template('Human Resources/Dashboard.html')

@sidebar_bp.route('/human-resources/staff-profiles')
def hr_staff_profiles():
    return render_template('Human Resources/Staff_Profiles.html')

@sidebar_bp.route('/human-resources/licensing')
def hr_licensing():
    return render_template('Human Resources/Licensing.html')

@sidebar_bp.route('/human-resources/education')
def hr_education():
    return render_template('Human Resources/Education.html')

# Admin routes
@sidebar_bp.route('/admin')
def admin_dashboard():
    return render_template('Admin/Dashboard.html')

@sidebar_bp.route('/admin/regulatory')
def admin_regulatory():
    return render_template('Admin/Regulatory.html')

@sidebar_bp.route('/admin/suppliers')
def admin_suppliers():
    return render_template('Admin/Suppliers.html')

@sidebar_bp.route('/admin/resources')
def admin_resources():
    return render_template('Admin/Resources.html')
