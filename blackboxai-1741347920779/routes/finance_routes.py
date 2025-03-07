from flask import Blueprint, render_template

finance = Blueprint('finance', __name__)

@finance.route('/financial_hub')
def financial_hub():
    return render_template('finance/financial_hub.html', title='Financial Hub')

@finance.route('/ordering')
def ordering():
    return render_template('finance/ordering.html', title='Ordering')
    
@finance.route('/stocktake')
def stocktake():
    return render_template('finance/stocktake.html', title='stocktake')
