#-----------------------------------------#
#           app/home_routes.py            #
#-----------------------------------------#

from flask import Blueprint, render_template, current_app

home_bp = Blueprint('home', __name__, url_prefix='/home')

@home_bp.route('/', methods=['GET'])
def home_page():
    """
    Serves the home page.
    """
    try:
        return render_template('home.html')
    except Exception as e:
        current_app.logger.error("Error rendering home page: %s", e)
        return "Internal server error", 500
