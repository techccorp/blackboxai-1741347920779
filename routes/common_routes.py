from flask import Blueprint, render_template, request

# Define the common Blueprint
common = Blueprint('common', __name__)

@common.route('/doc_library')
def doc_library():
    """
    Displays the Resource Library page.
    """
    return render_template('common/doc_library.html', title='Resource Library')
    
@common.route('/notes')
def notes():
    """
    Displays the Resource Library page.
    """
    return render_template('common/notes.html', title='Notes')
    
@common.route('/allergen_search') 
def allergen_search(): 
    """
    Displays the Resource Library page.
    """
    return render_template('common/allergen_search.html', title='Allergen Search')

@common.route('/recipe_search/')
@common.route('/recipe_search')
def recipe_search():
    """
    Displays the search page with an active tab.
    """
    active_tab = request.args.get('tab', 'my_recipes')  # Default to 'my_recipes'
    return render_template('recipe/recipe_search.html', title='Recipe Search', active_tab=active_tab)

@common.route('/recipe_coster/')
@common.route('/recipe_coster')
def recipe_coster():
    """
    Displays the recipe_coster.html page.
    """
    return render_template('recipe/recipe_coster.html')

@common.route('/employee_profile')
def employee_profile():
    """
    Displays the employee_profile.html page.
    """
    return render_template('common/employee_profile.html', title='Employee Profile')

@common.route('/recipe_generator')
def recipe_generator():
    """
    Displays the recipe_generator page.
    """
    return render_template('recipe/recipe_generator.html', title='Recipe Generator')

@common.route('/recipe_specials')
def recipe_specials():
    """
    Displays the recipe_specials page.
    """
    return render_template('recipe/recipe_specials.html', title='Specials')

@common.route('/event_menus')
def event_menus():
    """
    Displays the event_menus page.
    """
    return render_template('recipe/event_menus.html', title='Event Menus')

@common.route('/ordering')
def ordering():
    """
    Displays the Ordering page.
    """
    return render_template('finance/ordering.html', title='Ordering')

@common.route('/roster')
def roster():
    """
    Displays the Roster page (original route).
    """
    return render_template('finance/roster.html', title='Roster')

@common.route('/calendar')
def calendar():
    """
    Displays the calendar page.
    """
    return render_template('common/calendar.html', title='calendar')

@common.route('/profile')
def profile():
    """
    Displays the profile page.
    """
    return render_template('common/profile.html', title='profile')

@common.route('/staff_dashboard')
def staff_dashboard():
    """
    Displays the staff_dashboard.
    """
    return render_template('common/staff_dashboard.html', title='Dashboard')

# ------------------------------------------------------------
# Newly Added Routes Based on the Provided Snippet
# ------------------------------------------------------------

@common.route('/news_feed')
def news_feed():
    """
    Displays the News Feed page.
    """
    return render_template('common/news_feed.html', title='News Feed')

@common.route('/google_feature/tasks')
def google_feature_tasks():
    """
    Displays the tasks page under google_feature.
    """
    return render_template('common/google_feature/tasks.html', title='Tasks')

@common.route('/locations')
def locations():
    """
    Displays the Locations page.
    """
    return render_template('common/locations.html', title='Locations')

@common.route('/employee/people')
def employee_people():
    """
    Displays the People page under Employee.
    """
    return render_template('common/employee/people.html', title='People')

@common.route('/employee/roster')
def employee_roster():
    """
    Displays the Employee Roster page.
    Distinct from the top-level /roster route.
    """
    return render_template('common/employee/roster.html', title='Employee Roster')

@common.route('/employee/timesheets')
def employee_timesheets():
    """
    Displays the Employee Timesheets page.
    """
    return render_template('common/employee/timesheets.html', title='Employee Timesheets')

# This belongs logically in a `finance` blueprint, but included here per request.
@common.route('/finance/reports')
def finance_payroll_reports():
    """
    Displays the Finance Reports page.
    Ideally should be under a finance blueprint, but shown here as requested.
    """
    return render_template('common/employee/reports.html', title='Reports')
    
# ------------------------------------------------------------
# Google Api Page Routes 
# ------------------------------------------------------------

@common.route('/google_feature/googleKeep')
def google_keep():
    return render_template('common/google_feature/googleKeep.html', title='Google Keep')
