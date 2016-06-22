# Hangman

A hangman game that uses Google AppEngine, Datastore and Cloud Endpoints and a
Python backend API.

## Prerequisites

The backend API is written in Python 2.7 and requires the AppEngine SDK for
Python to be installed to run the app locally or deploy to Google Cloud.

##Installation

Clone this repository in your command line:
`git clone https://github.com/anirvan90/hangman.git`

##Files Included

* _app.yaml_ : App configurations
* _api.py_ : Contains API endpoints
* _cron.yaml_ : Cron job configurations
* _main.py_ : Cron job handler and functions
* _models.py_ : ndb.Models, protoRPC message classes and python helper functions
* _utils.py_ : Helper function to retrieve ndb.Models by URL Safe Keys.

##Set-Up

1. Update the value of `application` in `app.yaml` to an app ID that you have
registered in your Google AppEngine admin console.

2. Run the application in the Local Development Server through the AppEngine UI
or by running the following `python` command in your command line.
`dev_appserver.py DIR` where DIR is the path to the folder containing the
`app.yaml` file.

3. In your browser open the endpoints explorer at:
[localhost:8080/_ah/api/explorer]

##Game Description
This a simple one-player hangman game where a user is randomly assigned a target
word and has 7 attempts to guess the word correctly. 

###Rules
For each game a user is allowed a maximum of 7 incorrect tries (see scoring and
gameplay below). Words are assigned from the ndb.Word model, in which words can
be inputted through the add_word endpoint (see Endpoints). Only single word
targets are allowed with no special characters. Words are automatticaly
converted to UpperCase by design.

###Scoring
For each game a user is allowed a maximum of 7 incorrect attempts after which
the game will end and result in a score of 0. The maximum score a user can
achieve in a game is 10, in this case the user has guessed each letter correctly
without any incorrect guess attempts. Dependent on the number of incorrect
guesses, the game is scored. For example, 1 incorrect guess attempt but success
in guessing the word would yield a score of 9. See the table below:

| Incorrect Guesses | Score |
|:-----------------:|:-----:|
|         0         |   10  |
|         1         |   9   |
|         2         |   8   |
|         3         |   7   |
|         4         |   6   |
|         5         |   5   |
|         6         |   4   |
|         7         |   0   |

###Game Play
A user must create credentials (user_name and email) in order to play. A unique
username is required. Once a user is registered, a user may create a new 'Game'
entity by entering his/her unique user_name. Each 'Game' entity has a unique
urlsafe_key needed to access the game and make moves. This key is generated
automatically. In additon to the key, a word target is also randomly assigned.
This target is a Word in the form of a list of characters. To make a move, the
user (or front-end app) must enter the unique urlsafe_key to access the 'Game'
and provide a 'guess' character. The make_move endpoint checks whether the guess
is valid and places is it in the appropriate 'answer' or 'failed_attempts' list
and also appends it to the 'history' list to keep track of moves made. Each
'Game' has a maximum of 7 failed attempts allowed, after which the game ends.
If the user guesses the word correctly, the game ends, and an approciate score
is given. As soon as the 'Game' has ended a 'Score' entity is created that
stores the history of completed games with appropriate game states.
 
##Endpoints
- **create_user**
	- Path: user
	- Method: POST
	- Parameters: user_name, email
	- Returns: Message confirming creation of user
	- Description: Creates a new user. user_name provided must be unique. Will
	raise a ConflictException if user_name already exists.

- **new_game**
	- Path: game
	- Method: POST
	- Parameters: user_name
	- Returns: GameForm with initial game state
	- Description: Creates a new Game. user_name provided must correspond to an 
	an existing user - Will raise NotFoundException if user is not registered.

- **get_game**
	- Path: game/{urlsafe_key}
	- Method: GET
	- Parameters: urlsafe_key
	- Returns: GameForm with current game state
	- Description: Returns the current state of a Game.

- **make_move**
	- Path: game/{urlsafe_key}
	- Method: PUT
	- Parameters: urlsafe_key, guess
	- Returns: GameForm with new game state.
	- Description: Accepts a guess from the user and returns the updated state
	of the game. If this causes a game to end, Score will be created and User 
	entitiy will be updated accordingly.

- **get_user_games**
	- Path: games/user/{user_name}
	- Method: GET
	- Parameters: user_name, email
	- Returns: GameForms with current game state of each incomplete game
	- Description: Gets all the incomplete games associated with a certain user.

- **get_user_games_completed**
	- Path: games/completed/user/{user_name}
	- Method: GET
	- Parameters: user_name, email
	- Returns: GameForms with state of each completed game
	- Description: Gets all the completed games associated with a certain user.

- **cancel_game**
	- Path: game/{urlsafe_key}/cancel
	- Method: DELETE
	- Parameters: urlsafe_key
	- Returns: StringMessage with delete confirmation
	- Description: Will only cancel incomplete games. If game has ended will
	raise BadRequestException. If urlsafe_key is invalid will raise
	NotFoundException.

- **get_game_history**
	- Path: game/{urlsafe_key}/history
	- Method: GET
	- Parameters: urlsafe_key
	- Returns: StringMessage with history of guesses made by user.
	- Description: Will raise NotFoundException if urlsafe_key is invalid

- **get_high_scores**
	- Path: number of results
	- Method: GET
	- Parameters: user/leaderboard
	- Returns: UserForms of all registered users ordered by total_score
	- Description: Takes a leader board number from the user and shows the top
	registered players ordered by total_score. If user does not enter number,
	top 10 will be displayed.

- **get_user_rankings**
	- Path: user/rankings
	- Method: GET
	- Parameters: -
	- Returns: RankForms of all registered users ordered by best average score
	- Description: Average Score is calculated by total_score divided by
	total_played. Players who have earned in the most points in the least games
	will be ranked higher.

- **add_word**
	- Path: word
	- Method: POST
	- Parameters: word
	- Returns: StringMessage confirming word was added to datastore
	- Description: Accepts a word to added to the database of target words.
	Ideally this should only be open to game admins and front-end creators.

##ndb.Models

 * __User__
 	* Stores name(must be unique), email, wins, total_played, total_score and
average_score

 * __Game__
 	* Stores game states. Entities are assciated with the User model via
the KeyProperty

 * __Score__
 	* Stores results of each completed game.

 * __Word__
 	* Stores words in the datastore

##ProtoRPC MessageClasses
* __UserForm__
	* Representation of 'User' entity attributes (name, email, wins, 
	total_score, total_played and average_score) 
* __UserForms__
	* Multiple UserForm container.
* __GameForm__
	* Representation of a 'Game' entity state and attributes (user, game_over,
	attempts_remaining, target, target_length, history, answer, failed_attempts)
* __GameForms__
	* Multiple GameForm container.
* __MakeMoveForm__
	* In bound make_move form for guess attempts.
* __ScoreForm__
	* Representation of a completed games score attributes (name, date, won,
	guesses and points).
* __ScoreForms__
	* Multiple ScoreForm container.
* __RankForm__
	* Representation of a user's rank by average_score (name, tota_played,
	total_score, average_score).
* __RankForms__
	* Multiple RankForm container.
* __StringMessage__
	* General purpose string container.
* __WordForm__
	* In bound add_word form for entering a 'Word' into datastore.
