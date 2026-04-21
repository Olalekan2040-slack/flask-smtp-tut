from itsdangerous import URLSafeTimedSerializer
from flask import current_app, url_for, render_template
from flask_mail import Message
from . import mail

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm-salt')

def confirm_verification_token(token, expiration=3600):  # 1 hour
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=expiration)
        return email
    except:
        return False

def send_verification_email(user):
    token = generate_verification_token(user.email)
    confirm_url = url_for('routes.verify_email', token=token, _external=True)
    
    html = render_template('verify_email.html', confirm_url=confirm_url)
    
    msg = Message(
        subject='Confirm Your Email Address',
        recipients=[user.email],
        html=html
    )
    mail.send(msg)