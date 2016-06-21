"""main.py - This file contains handlers that are called by cronjobs"""

import logging
import webapp2
from google.appengine.api import app_identity, mail
from api import SVHangmanAPI
from models import User, Game

class SendReminderEmail(webapp2.RequestHandler):
	def get(self):
		"""Send Email reminder email to each user with an email
		and unfinished games. Called every day using cron job"""
		app_id = app_identity.get_application_id()
		users = User.query(User.email != None)
		for user in users:
			games = Game.query(Game.user == user.key, Game.game_over == False)
			subject = "This is a reminder!"
			body = "Hello {}, you have some unfinished games.".format(user.name)

			mail.send_mail('noreply@{}.appspot.com'.format(app_id),
							user.email,
							subject,
							body)

app = webapp2.WSGIApplication([
	('/crons/send_reminder', SendReminderEmail)], debug=True)

		