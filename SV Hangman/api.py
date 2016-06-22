"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to 
move game logic to another file. Ideally the API will be simple, concerned 
primarily with communication to and from the API's users."""

import logging
import endpoints
import string
import random
from protorpc import messages, remote, message_types
from google.appengine.api import memcache
from google.appengine.ext import ndb

from models import User, Word, Game, Score
from models import StringMessage, UserForm, WordForm, GameForm, \
                   MakeMoveForm, GameForms, UserForms, RankForm, RankForms 

from utils import get_by_urlsafe

USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                        email=messages.StringField(2))

NEW_GAME_REQUEST = endpoints.ResourceContainer(
                        user_name=messages.StringField(1))

GET_GAME_REQUEST = endpoints.ResourceContainer(
                        urlsafe_key=messages.StringField(1))

MAKE_MOVE_REQUEST = endpoints.ResourceContainer(MakeMoveForm,
                        urlsafe_key=messages.StringField(1))

HIGH_SCORE_REQUEST = endpoints.ResourceContainer(
                        number_of_results = messages.IntegerField(1))

@endpoints.api(name='sv_hangman', version='v1')
class SVHangmanAPI(remote.Service):
    """Silicon Valley Hangman Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self,request):
        """Create a user. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates a New Game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist.')
        game = Game.new_game(user.key)
        print game.target
        return game.to_form('Good luck playing Silicon Valley Hangman!!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Get current game state"""
        game = get_by_urlsafe(request.urlsafe_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game Not Found')
        else: 
            if game.game_over:
                return game.to_form(message="This Game has ended!")
            else:
                return game.to_form(message="Game in Progress!")

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_key, Game)
        guess = request.guess.upper()
        if game.game_over:
            raise endpoints.NotFoundException('This Game Has Ended!')
        if len(guess) != 1 or guess <'A' or guess > 'Z':
            raise endpoints.BadRequestException('Please enter a valid guess!')
        if guess in game.failed_tries or guess in game.answer:
            return game.to_form(message='You have already tried that!')
        else:
            if guess in game.target:
                game.history.append(guess)
                #Go through target and to add 'guess' character and remove '_'
                for ind, tar in enumerate(game.target):
                    if guess == tar:
                        game.answer.pop(ind)
                        game.answer.insert(ind, guess)
                game.put()
                if game.answer == game.target:
                    game.end_game(True)
                    return game.to_form(message="You Won!!")
                else:        
                    return game.to_form(message="You guessed correct!")
            else:
                if game.attempts_remaining <= 1:
                    game.attempts_remaining = 0
                    game.end_game(False)
                    return game.to_form(message="Game Over! The word was: %s"
                                        % game.target)
                else:    
                    game.failed_tries.append(guess)
                    game.history.append(guess)
                    game.attempts_remaining -= 1
                    game.put()
                    return game.to_form(message='Uh-Oh. Try Again.')

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Get all of an individual users active games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A user with that name does not exist!')
        games = Game.query(Game.user == user.key, Game.game_over == False)
        return GameForms(items=[game.to_form(
                message="Game In Progress") for game in games])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/completed/user/{user_name}',
                      name='get_user_games_completed',
                      http_method='GET')
    def get_user_games_completed(self, request):
        """Get all of an individual users completed games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A user with that name does not exist!')
        games = Game.query(Game.user == user.key, Game.game_over == True)
        return GameForms(items=[game.to_form(
            message="Game Complete") for game in games])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_key}/cancel',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Cancels existing game if game has NOT ended."""
        game = get_by_urlsafe(request.urlsafe_key, Game)
        if game and not game.game_over:
            game.key.delete()
            return StringMessage(message='Game with key: {} deleted.'.
                                format(request.urlsafe_key))
        elif game and game.game_over:
            raise endpoints.BadRequestException('Game is already over!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Returns History of moves made"""
        game = get_by_urlsafe(request.urlsafe_key, Game)

        if not game:
            raise endpoints.NotFoundException('Game Not Found!')
        else:
            return StringMessage(message="Moves Made: %s" % game.history)

    @endpoints.method(request_message=HIGH_SCORE_REQUEST,
                      response_message=UserForms,
                      path='user/leader_board',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Return a leader board of top scorers"""
        result_count = 10
        if request.number_of_results is not None:
            result_count = request.number_of_results
    
        return UserForms(items=
            [user.to_form() for user in User.query().order(-User.total_score).
            fetch(result_count)])

    @endpoints.method(request_message=message_types.VoidMessage,
                      response_message=RankForms,
                      path='user/rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return all user rankings"""
        users = User.query().order(-User.average_score)
        return RankForms(items=
            [user.to_rank_form() for user in users])
   
    @endpoints.method(request_message=WordForm,
                      response_message=StringMessage,
                      path='word',
                      name='add_word',
                      http_method='POST')
    def add_word(self, request):
        """Add word to list of words"""
        if Word.query(Word.word == request.word).get():
            raise endpoints.ConflictException('That word is in the list!')
        else:
            word_list = []
            temp = request.word.upper()
            for i in temp:
                if i ==" " or i < 'A' or i > 'Z':
                    raise endpoints.BadRequestException(
                                'Please Enter One Word!')
                else:
                    word_list.append(i)
            w = Word(word=request.word, word_list=word_list)
            w.put()
        return StringMessage(message='Added %s to the list!' % request.word)


api = endpoints.api_server([SVHangmanAPI])
