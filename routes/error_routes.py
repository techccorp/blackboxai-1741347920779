from flask import Blueprint, render_template

error_routes = Blueprint('error_routes', __name__)

@error_routes.app_errorhandler(404)
def error_404(error):
    '''
    Handles 404 error (page not found)
    '''
    return render_template('errors/404.html', error=True, 
                           title="Page not found"), 404


@error_routes.app_errorhandler(500)
def error_500(error):
    '''
    Handles 500 error (internal server error)
    '''
    return render_template('errors/500.html', error=True,
                           title="Internal Server Error"), 500