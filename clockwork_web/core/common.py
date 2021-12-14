from flask_login import current_user


def get_mila_email_username():
    return current_user.email.split("@")[0]
