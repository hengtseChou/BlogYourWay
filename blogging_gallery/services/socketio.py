from flask import request, session
from flask_login import current_user, logout_user
from flask_socketio import SocketIO

from blogging_gallery.services.log import my_logger

socketio = SocketIO()


# @socketio.on("disconnect")
# def logout_on_disconnect():
#     if current_user.is_authenticated:
#         username = current_user.username
#         logout_user()
#         session.pop("user_current_tab", None)
#         my_logger.debug("Logout via socketio disconnect.")
#         my_logger.user.logout(username=username, request=request)
