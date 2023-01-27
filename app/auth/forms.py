# -*- coding: utf-8 -*-

from app import app_release

try:
    from flask_wtf import FlaskForm as Form
except:
    from flask_wtf import Form

from flask import flash, g
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField, validators
from wtforms.validators import Required, Length, Regexp, EqualTo, DataRequired, Email
from wtforms import ValidationError
from flask_babel import lazy_gettext

from ..models import admin_config, User


def _get_admin_config():
    """
    c = admin_config['users']['fields']
    return dict([(x, _l(c[x])) for x in c])
    """
    return admin_config['users']['fields']


class LoginForm(Form):
    login = StringField(lazy_gettext('Login'), validators=[Required(), Length(1, 64)])
    password = PasswordField(lazy_gettext('Password'), validators=[Required()])
    remember_me = BooleanField(lazy_gettext('Save connection'), default=True)
    submit = SubmitField(lazy_gettext('Log in'))


class ChangePasswordForm(Form):
    old_password = PasswordField(lazy_gettext('Old password'), validators=[Required()])
    password = PasswordField(lazy_gettext('New password'), validators=[Required(),
                                                          EqualTo('password2', message=lazy_gettext('Password must match'))])
    password2 = PasswordField(lazy_gettext('Password confirmation'), validators=[Required()])
    submit = SubmitField(lazy_gettext('Refresh'))


class ResetPasswordRequestForm(Form):
    email = StringField(lazy_gettext('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(lazy_gettext('Send request'))


class PasswordResetForm(Form):
    password = PasswordField(lazy_gettext('New password'), validators=[Required(),
                                                         EqualTo('password2', message=lazy_gettext('Password must match'))])
    password2 = PasswordField(lazy_gettext('Password confirmation'), validators=[Required()])
    submit = SubmitField(lazy_gettext('Update Login'))


class ChangeLoginForm(Form):
    login = StringField(lazy_gettext('Login'), validators=[Required(), Length(1, 64)])
    password = PasswordField(lazy_gettext('Password'), validators=[Required()])
    submit = SubmitField(lazy_gettext('Update Login'))

    def validate_login(self, field):
        if User.query.filter_by(login=field.data).first():
            raise ValidationError(lazy_gettext('Login already registered.'))


class RegistrationForm(Form):
    fields = _get_admin_config()
    
    role_choices = [(str(x[0]), x[1]) for x in User.get_roles()]

    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    login = StringField(fields['login'], validators=[DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Login must have only letters, numbers, dots or '
               'underscores')])
    family_name = StringField(fields['family_name'], [validators.required(), validators.Length(max=80)])
    first_name = StringField(fields['first_name'], [validators.required(), validators.Length(max=80)])
    last_name = StringField(fields['last_name'], [validators.Length(max=50)])
    role = SelectField(fields['role'], [validators.required()], choices=role_choices)
    password = PasswordField(lazy_gettext('Password'), validators=[Required(),
                                                          EqualTo('password2', message=lazy_gettext('Password must match'))])
    password2 = PasswordField(lazy_gettext('Password confirmation'), validators=[Required()])
    
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            error = 'Email already registered.'
            g.app_logger('RegistrationForm', error, is_warning=True)
            flash(error)
            raise ValidationError(error)

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            error ='Login already in use.'
            g.app_logger('RegistrationForm', error, is_warning=True)
            flash(error)
            raise ValidationError(error)
