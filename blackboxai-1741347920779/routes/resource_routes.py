from flask import Blueprint, render_template, request

# Define the resource Blueprint
resource = Blueprint('resource', __name__)

@resource.route('/center')
def center():
    """
    Displays the Resource Library page.
    """
    return render_template('resources/resource_center.html', title='Resource Library')

# -------------------------------
# VENUE Routes
# -------------------------------
@resource.route('/resources/venue/history', endpoint='venue_history')
def venue_history():
    """
    Renders the Venue History page.
    """
    return render_template('resources/venue/history.html', title='Venue - History')

@resource.route('/resources/venue/sequence', endpoint='venue_sequence')
def venue_sequence():
    """
    Renders the Venue Sequence of Service page.
    """
    return render_template('resources/venue/sequence.html', title='Venue - Sequence of Service')

@resource.route('/resources/venue/emergency', endpoint='venue_emergency')
def venue_emergency():
    """
    Renders the Venue Emergency Procedures page.
    """
    return render_template('resources/venue/emergency.html', title='Venue - Emergency Procedures')

# -------------------------------
# EMPLOYMENT Routes
# -------------------------------
@resource.route('/resources/employment/fair_work', endpoint='employment_fair_work')
def employment_fair_work():
    """
    Renders the Fair Work page.
    """
    return render_template('resources/employment/fair_work.html', title='Employment - Fair Work')

@resource.route('/resources/employment/payroll/award_rates', endpoint='payroll_award')
def payroll_award():
    """
    Renders the Payroll Award Rates page.
    """
    return render_template('resources/employment/payroll/award_rates.html', title='Employment - Payroll Award Rates')

@resource.route('/resources/employment/payroll/leave_entitlements', endpoint='payroll_leave')
def payroll_leave():
    """
    Renders the Payroll Leave Entitlements page.
    """
    return render_template('resources/employment/payroll/leave_entitlements.html', title='Employment - Payroll Leave Entitlements')

# -------------------------------
# KITCHEN Routes
# -------------------------------
# Butchery Subsection
@resource.route('/resources/kitchen/butchery/beef', endpoint='kitchen_butchery_beef')
def kitchen_butchery_beef():
    """
    Renders the Kitchen Butchery Beef page.
    """
    return render_template('resources/kitchen/butchery/beef_catalouge.html', title='Kitchen - Butchery: Beef')

@resource.route('/resources/kitchen/butchery/lamb', endpoint='kitchen_butchery_lamb')
def kitchen_butchery_lamb():
    """
    Renders the Kitchen Butchery Lamb page.
    """
    return render_template('resources/kitchen/butchery/lamb.html', title='Kitchen - Butchery: Lamb')

@resource.route('/resources/kitchen/butchery/pork', endpoint='kitchen_butchery_pork')
def kitchen_butchery_pork():
    """
    Renders the Kitchen Butchery Pork page.
    """
    return render_template('resources/kitchen/butchery/pork.html', title='Kitchen - Butchery: Pork')

@resource.route('/resources/kitchen/butchery/poultry', endpoint='kitchen_butchery_poultry')
def kitchen_butchery_poultry():
    """
    Renders the Kitchen Butchery Poultry page.
    """
    return render_template('resources/kitchen/butchery/poultry.html', title='Kitchen - Butchery: Poultry')

@resource.route('/resources/kitchen/butchery/game', endpoint='kitchen_butchery_game')
def kitchen_butchery_game():
    """
    Renders the Kitchen Butchery Game page.
    """
    return render_template('resources/kitchen/butchery/game.html', title='Kitchen - Butchery: Game')

# Produce Subsection
@resource.route('/resources/kitchen/produce/winter', endpoint='kitchen_produce_winter')
def kitchen_produce_winter():
    """
    Renders the Kitchen Produce Winter page.
    """
    return render_template('resources/kitchen/produce/winter.html', title='Kitchen - Produce: Winter')

@resource.route('/resources/kitchen/produce/spring', endpoint='kitchen_produce_spring')
def kitchen_produce_spring():
    """
    Renders the Kitchen Produce Spring page.
    """
    return render_template('resources/kitchen/produce/spring.html', title='Kitchen - Produce: Spring')

@resource.route('/resources/kitchen/produce/summer', endpoint='kitchen_produce_summer')
def kitchen_produce_summer():
    """
    Renders the Kitchen Produce Summer page.
    """
    return render_template('resources/kitchen/produce/summer.html', title='Kitchen - Produce: Summer')

@resource.route('/resources/kitchen/produce/autumn', endpoint='kitchen_produce_autumn')
def kitchen_produce_autumn():
    """
    Renders the Kitchen Produce Autumn page.
    """
    return render_template('resources/kitchen/produce/autumn.html', title='Kitchen - Produce: Autumn')

# Forms
@resource.route('/resources/kitchen/forms/temp_logs', endpoint='kitchen_forms_temp_logs')
def kitchen_forms_temp_logs():
    """
    Renders the Kitchen Forms - Temp Logs page.
    """
    return render_template('resources/kitchen/forms/temp_logs.html', title='Kitchen - Forms: Temp Logs')

# -------------------------------
# RESTAURANT Routes
# -------------------------------
@resource.route('/resources/restaurant/cocktails', endpoint='restaurant_cocktails')
def restaurant_cocktails():
    """
    Renders the Restaurant Cocktails page.
    """
    return render_template('resources/restaurant/cocktails.html', title='Restaurant - Cocktails')

@resource.route('/resources/restaurant/beers', endpoint='restaurant_beers')
def restaurant_beers():
    """
    Renders the Restaurant Beers page.
    """
    return render_template('resources/restaurant/beers.html', title='Restaurant - Beers')

# Wines
@resource.route('/resources/restaurant/wines/red', endpoint='restaurant_wines_red')
def restaurant_wines_red():
    """
    Renders the Restaurant Wines - Red page.
    """
    return render_template('resources/restaurant/wines/red.html', title='Restaurant - Wines: Red')

@resource.route('/resources/restaurant/wines/white', endpoint='restaurant_wines_white')
def restaurant_wines_white():
    """
    Renders the Restaurant Wines - White page.
    """
    return render_template('resources/restaurant/wines/white.html', title='Restaurant - Wines: White')

@resource.route('/resources/restaurant/wines/dessert', endpoint='restaurant_wines_dessert')
def restaurant_wines_dessert():
    """
    Renders the Restaurant Wines - Dessert page.
    """
    return render_template('resources/restaurant/wines/dessert.html', title='Restaurant - Wines: Dessert')

@resource.route('/resources/restaurant/wines/sparkling', endpoint='restaurant_wines_sparkling')
def restaurant_wines_sparkling():
    """
    Renders the Restaurant Wines - Sparkling page.
    """
    return render_template('resources/restaurant/wines/sparkling.html', title='Restaurant - Wines: Sparkling')

@resource.route('/resources/restaurant/wines/fortified', endpoint='restaurant_wines_fortified')
def restaurant_wines_fortified():
    """
    Renders the Restaurant Wines - Fortified page.
    """
    return render_template('resources/restaurant/wines/fortified.html', title='Restaurant - Wines: Fortified')

# Spirits
@resource.route('/resources/restaurant/spirits/rums', endpoint='restaurant_spirits_rums')
def restaurant_spirits_rums():
    """
    Renders the Restaurant Spirits - Rums page.
    """
    return render_template('resources/restaurant/spirits/rums.html', title='Restaurant - Spirits: Rums')

@resource.route('/resources/restaurant/spirits/whiskey', endpoint='restaurant_spirits_whiskey')
def restaurant_spirits_whiskey():
    """
    Renders the Restaurant Spirits - Whiskey page.
    """
    return render_template('resources/restaurant/spirits/whiskey.html', title='Restaurant - Spirits: Whiskey')

@resource.route('/resources/restaurant/spirits/bourbon', endpoint='restaurant_spirits_bourbon')
def restaurant_spirits_bourbon():
    """
    Renders the Restaurant Spirits - Bourbon page.
    """
    return render_template('resources/restaurant/spirits/bourbon.html', title='Restaurant - Spirits: Bourbon')

@resource.route('/resources/restaurant/spirits/gin', endpoint='restaurant_spirits_gin')
def restaurant_spirits_gin():
    """
    Renders the Restaurant Spirits - Gin page.
    """
    return render_template('resources/restaurant/spirits/gin.html', title='Restaurant - Spirits: Gin')

@resource.route('/resources/restaurant/spirits/tequila', endpoint='restaurant_spirits_tequila')
def restaurant_spirits_tequila():
    """
    Renders the Restaurant Spirits - Tequila page.
    """
    return render_template('resources/restaurant/spirits/tequila.html', title='Restaurant - Spirits: Tequila')

@resource.route('/resources/restaurant/aperitifs', endpoint='restaurant_aperitifs')
def restaurant_aperitifs():
    """
    Renders the Restaurant Aperitifs page.
    """
    return render_template('resources/restaurant/aperitifs.html', title='Restaurant - Aperitifs')

# -------------------------------
# COMPLIANCE Routes
# -------------------------------
@resource.route('/resources/compliance/food_safety', endpoint='compliance_food_safety')
def compliance_food_safety():
    """
    Renders the Compliance - Food Safety page.
    """
    return render_template('resources/compliance/food_safety.html', title='Compliance - Food Safety')

@resource.route('/resources/compliance/ohs', endpoint='compliance_ohs')
def compliance_ohs():
    """
    Renders the Compliance - OHS page.
    """
    return render_template('resources/compliance/ohs.html', title='Compliance - OHS')

@resource.route('/resources/compliance/rsa', endpoint='compliance_rsa')
def compliance_rsa():
    """
    Renders the Compliance - RSA page.
    """
    return render_template('resources/compliance/rsa.html', title='Compliance - RSA')

@resource.route('/resources/compliance/first_aid', endpoint='compliance_first_aid')
def compliance_first_aid():
    """
    Renders the Compliance - First Aid page.
    """
    return render_template('resources/compliance/first_aid.html', title='Compliance - First Aid')

# -------------------------------
# GOVERNMENT Routes
# -------------------------------
@resource.route('/resources/government', endpoint='government_main')
def government_main():
    """
    Renders the Government page.
    """
    return render_template('resources/government/index.html', title='Government')

# -------------------------------
# SUPPLIERS Routes
# -------------------------------
@resource.route('/resources/suppliers/kitchen', endpoint='suppliers_kitchen')
def suppliers_kitchen():
    """
    Renders the Suppliers - Kitchen page.
    """
    return render_template('resources/suppliers/kitchen.html', title='Suppliers - Kitchen')

@resource.route('/resources/suppliers/restaurant', endpoint='suppliers_restaurant')
def suppliers_restaurant():
    """
    Renders the Suppliers - Restaurant page.
    """
    return render_template('resources/suppliers/restaurant.html', title='Suppliers - Restaurant')
