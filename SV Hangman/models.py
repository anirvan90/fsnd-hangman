"""models.py - This file contains the class definitiions for the Datastore
entities used by the Game. Because these classes are also regular Python
they can include other methods."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

class User(ndb.Model):
	"""User Profile"""
	name = ndb.StringProperty(required=True)
	email = ndb.StringProperty(required=True)
	wins = ndb.IntegerProperty(default=0)
	total_played = ndb.IntegerProperty(default=0)
	total_score = ndb.IntegerProperty(default=0)
	average_score = ndb.FloatProperty(default=0.0)

	def add_win(self):
		"""Adds a win to a user profile and update scores on profile"""
		self.wins += 1
		self.total_played +=1
		self.average_score = self.total_score/self.total_played
		self.put()

	def add_loss(self):
		"""Add a loss to a user profile and update scores on profile"""
		self.total_played += 1
		self.average_score = self.total_score/self.total_played
		self.put()

	def update_score(self, scr):
		"""Update a users total score"""
		self.total_score += scr
		self.put()

	def to_form(self):
		"""Returns user form representation of each user"""
		form = UserForm()
		form.name = self.name
		form.email = self.email
		form.wins = self.wins
		form.total_played = self.total_played
		form.average_score = self.average_score
		form.total_score = self.total_score
		return form

	def to_rank_form(self):
		"""Returns rank form representation of user"""
		form = RankForm()
		form.name = self.name
		form.total_played = self.total_played
		form.total_score = self.total_score
		form.average_score = self.average_score
		return form

class UserForm(messages.Message):
	"""User Form"""
	name = messages.StringField(1, required=True)
	email = messages.StringField(2)
	wins = messages.IntegerField(3, required=True)
	total_played = messages.IntegerField(4, required=True)
	average_score = messages.FloatField(5, required=True)
	total_score = messages.IntegerField(6, required=True)

class UserForms(messages.Message):
	"""Returns multiple UserForms"""
	items = messages.MessageField(UserForm, 1, repeated=True)

class Game(ndb.Model):
	"""Game Object"""
	user = ndb.KeyProperty(required=True, kind=User)
	game_over = ndb.BooleanProperty(required=True, default=False)
	attempts_remaining = ndb.IntegerProperty(required=True, default=7)
	target = ndb.PickleProperty(required=True)
	target_length = ndb.IntegerProperty(required=True)
	history = ndb.PickleProperty(required=True, default=[])
	answer = ndb.PickleProperty(required=True, default=[])
	failed_tries = ndb.PickleProperty(required=True, default=[])

	@classmethod
	def new_game(cls, user):
		"""Creates and returns new games"""
		items = Word.query().fetch()
		word_target = random.choice(items)
		game = Game(user=user,
			        target=word_target.word_list,
			        attempts_remaining=7,
			        game_over=False,
			        target_length=len(word_target.word_list))
		game.history=[]
		game.failed_tries = []
		game.answer=["_"]*len(word_target.word_list)
		game.put()
		return game

	def to_form(self, message):
		"""Returns the GameForm representation of the game"""
		form = GameForm()
		form.urlsafe_key = self.key.urlsafe()
		form.user_name = self.user.get().name
		form.attempts_remaining = self.attempts_remaining
		form.game_over = self.game_over
		form.history = str(self.history)
		form.answer = str(self.answer)
		form.failed_tries = str(self.failed_tries)
		form.message = message
		return form

	def end_game(self, won=False):
		"""End the current game and call relevant win/loss functions"""
		self.game_over = True
		self.put()

		score = Score(user=self.user, date=date.today(), won=won,
					   guesses=self.attempts_remaining)
		if won:
			self.user.get().update_score(score.guesses+3)
			self.user.get().add_win()
			score.points=score.guesses+3
			score.put()
		else:
			self.user.get().add_loss()
			score.put()

class Score (ndb.Model):
	"""Score Object"""
	user = ndb.KeyProperty(required=True, kind='User')
	date = ndb.DateProperty(required=True)
	won = ndb.BooleanProperty(required=True)
	guesses = ndb.IntegerProperty(required=True)
	points = ndb.IntegerProperty(required=True, default=0)

	def to_form(self):
		return ScoreForm(user_name=self.User.get().name, won=self.won,
						 date=str(self.date), guesses=self.guesses,
						 points=self.points)

class GameForm(messages.Message):
	"""GameForm - Form Representation of GameState"""
	urlsafe_key = messages.StringField(1, required=True)
	attempts_remaining = messages.IntegerField(2, required=True)
	game_over = messages.BooleanField(3, required=True)
	message = messages.StringField(4, required=True)
	user_name = messages.StringField(5, required=True)
	history = messages.StringField(6, required=True)
	answer = messages.StringField(7, required=True)
	failed_tries = messages.StringField(8, required= True)

class GameForms(messages.Message):
	"""Return multiple GameForms"""
	items = messages.MessageField(GameForm, 1, repeated=True)

class StringMessage(messages.Message):
	"""Outbound Message String"""
	message = messages.StringField(1, required=True)

class Word(ndb.Model):
	"""Table of words"""
	word = ndb.StringProperty(required=True)
	word_list = ndb.PickleProperty(repeated=True)

class WordForm(messages.Message):
	"""In-Bound Word"""
	word = messages.StringField(1, required=True)

class MakeMoveForm(messages.Message):
	"""Used to make a move in an existing game."""
	guess = messages.StringField(1, required=True)

class ScoreForm(messages.Message):
	"""ScoreForm for outbound score info"""
	user_name = messages.StringField(1, required=True)
	date = messages.StringField(2, required=True)
	won = messages.BooleanField(3, required=True)
	guesses = messages.IntegerField(4, required=True)
	points = messages.IntegerField(5, required=True)

class ScoreForms(messages.Message):
	items = messages.MessageField(ScoreForm, 1, repeated=True)

class RankForm(messages.Message):
	"""RankForm for Rank Information"""
	name = messages.StringField(1, required=True)
	total_played = messages.IntegerField(2, required=True)
	total_score = messages.IntegerField(3, required=True)
	average_score = messages.FloatField(4, required=True)

class RankForms(messages.Message):
	"""Multiple Rank Forms"""
	items = messages.MessageField(RankForm, 1, repeated=True)




