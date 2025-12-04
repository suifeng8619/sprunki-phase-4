from flask_login import LoginManager, login_required, login_user
from werkzeug.security import generate_password_hash, check_password_hash

from get_app import app
from apps.models.admin_model import adminUser
from flask import redirect, url_for, flash, render_template, Blueprint
from flask_login import logout_user, current_user
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, EqualTo
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from flask_ckeditor import CKEditor, CKEditorField

login_manager = LoginManager(app)
# admin 由admin项目使用了
admin_bp = Blueprint('admin_url', import_name=__name__, url_prefix='/admin')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=150)])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=150)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


# User loader
@login_manager.user_loader
def load_user(user_id):
    return adminUser.objects(pk=user_id).first()


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = adminUser.objects(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=True)
            return redirect(url_for('admin.index'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('admin_url.admin_login'))

    return render_template('admin/admin_login.html', form=form)


@admin_bp.route('/register', methods=['GET', 'POST'])
def admin_register():
    form = RegisterForm()
    print(11111)
    if form.validate_on_submit():
        print(1231)
        user = adminUser.objects(username=form.username.data).first()
        # 用户存在就提示存在
        if user:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('admin_url.admin_register'))
        hashed_password = generate_password_hash(form.password.data, method='sha256')

        # Create a new user
        user = adminUser(username=form.username.data, password=hashed_password)
        user.save()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('admin_url.admin_login'))

    return render_template('admin/admin_register.html', form=form)


@admin_bp.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('admin_url.admin_login'))
