from flask_login import UserMixin


class User(UserMixin):
    # user id is set as username
    def __init__(self, user_data):

        for key, value in user_data.items():
            if key == "username":
                self.id = value
                self.username = value
                continue
            setattr(self, key, value)
