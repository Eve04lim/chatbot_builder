from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('docs', __name__, url_prefix='/docs')

@bp.route('/api')
@login_required
def api_documentation():
    return render_template('docs/api.html')

@bp.route('/api/test')
@login_required
def api_test():
    return render_template('docs/api_test.html')