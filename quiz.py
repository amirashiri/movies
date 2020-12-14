from flask import Flask, render_template, request
import time
from datetime import datetime, timedelta
from shutil import copyfile
import os
import csv
from dataclasses import dataclass, field
import random

app = Flask(__name__, static_folder='static')

@app.route('/')
def home():
    global active_games
    message = f"Games currently running: {active_games}"
    return render_template('home.html', active_games=active_games, message=message)

@app.route('/create_game/<int:level>')
def create_game(level):
    global games, active_games
    valid_game_code = False
    while not valid_game_code:
        game_code = random.randint(1000, 9999)
        valid_game_code = game_code not in games
    # before creating new games, take this opportunity to remove inactive ones
    clear_games()
    game = Game(game_level=level)
    games[game_code] = game
    active_games += 1
    player = game.add_player()
    return render_template('create_game.html', game_code=game_code, player=player, players=game.number_of_players())

@app.route('/start_game/<int:game_code>/<int:player>')
def start_game(game_code, player):
    global games
    game = games[game_code]
    game.start()
    return show_question(game_code=game_code, player=player)

@app.route('/wait_for_joining/<int:game_code>/<int:player>')
def wait_for_joining(game_code, player):
    global games
    game = games[game_code]
    return render_template('create_game.html', game_code=game_code, player=player, players=game.number_of_players())

@app.route('/join_game/')
def join_game():
    global games
    if len(games) == 0:
        game_code = 0
    else:
        game_code = list(games.keys())[0]
    return render_template('join_game.html', game_code=game_code)

@app.route('/join_validation/<int:game_code>')
def join_validation(game_code):
    global games
    if game_code not in games:
        message = 'Invalid game code'
        return render_template('join_game.html', game_code=game_code, message=message)
    game = games[game_code]
    player = game.add_player()
    return render_template('join_success.html', game_code=game_code, player=player)

@app.route('/wait_for_game_start/<int:game_code>/<int:player>')
def wait_for_game_start(game_code, player):
    global games
    game = games[game_code]
    if game.is_on():
        return show_question(game_code=game_code, player=player)
    else:
        return render_template('join_success.html', game_code=game_code, player=player)

@app.route('/show_question/<int:game_code>/<int:player>')
def show_question(game_code, player):
    global games
    game = games[game_code]
    # the first player asking for a new question after already answering the last question of the quiz -
    # triggers ending the game
    if game.is_on() and game.last_answer_number(player) == game.total_questions():
        game.end()
    if not game.is_on():
        return show_summary(game_code, player)
    # while game is on, the first player requesting a new question triggers advancing the game to the next question
    if game.last_answer_number(player) == game.current_question():
        game.new_question()
    question_info = f"question {game.current_question()} out of {game.total_questions()}"
    return render_template('question.html', game_code=game_code, player=player, video_source=game.video_source(),
                           question_info=question_info, question_delay=question_delay)

@app.route('/get_answer/<int:game_code>/<int:player>/<int:answer>')
def get_answer(game_code, player, answer):
    global games
    game = games[game_code]
    game.save_answer(player, answer)
    return wait_for_answers(game_code, player)

@app.route('/wait_for_answers/<int:game_code>/<int:player>')
def wait_for_answers(game_code, player):
    global games, answer_delay, question_delay
    game = games[game_code]
    last_answer = game.last_answer(player)

    # if everyone already answered or player's time is up - show the answer screen
    if game.question_is_due() or last_answer == 0:
        player_success_info = 'You are correct!' if game.is_answer_correct(last_answer) else str()
        if game.number_of_players() == 1:
            all_players_success_info = str()
        else:
            correct_answers_from_others = game.correct_answers(game.current_question()) -\
                                          game.is_answer_correct(last_answer)
            all_players_success_info = f"correct answers from others: {correct_answers_from_others}"
        return render_template('answer.html', game_code=game_code,\
                               player=player,\
                               poster_source=game.poster_source(),\
                               answer_delay=answer_delay,\
                               player_success_info=player_success_info,\
                               all_players_success_info=all_players_success_info)

    else: # keep on waiting for other players' answers
        time_remains = max(
            0,
            int(question_delay - (datetime.now() - game.current_question_start_time()).total_seconds())
        )
        time_info = f"maximum seconds remaining: {time_remains}"
        players_info = f"answered so far: {game.players_answered_yet()} players"
        return render_template('wait_for_answers.html', game_code=game_code, player=player,
                               time_info=time_info, players_info=players_info)

@app.route('/get_answer/<int:game_code>/<int:player>')
def show_summary(game_code, player):
    global games
    game = games[game_code]
    scores = game.scores()
    if not bool(scores):
        game.calc_scores()
        scores = game.scores()
    all_players_scores_info = game.winner_info() if game.number_of_players() > 1 else str()
    x = game.winner_info() if game.number_of_players() > 1 else str()
    scores_dict = dict(scores)
    if player in scores_dict:
        player_score_info = f"You had {scores_dict[player]} correct answers out of {game.total_questions()}"
    else:
        player_score_info = str()
    return render_template('summary.html', game_code=game_code, player=player, level=game.level(),
                           player_score_info=player_score_info, all_players_scores_info=all_players_scores_info)

@dataclass
class Game:
    game_level: int = 1
    players: int = 0
    answers: dict = field(default_factory=dict)
    game_is_on = False
    game_start_time: datetime = datetime.now()
    curr_question: int = 0
    curr_question_start_time: datetime = datetime.now()
    game_scores: list = field(default_factory=list)
    game_winner_info: str = str()

    def start(self):
        self.game_is_on = True
        self.game_start_time = datetime.now()

    def end(self):
        global active_games
        self.game_is_on = False
        active_games -= 1

    def is_on(self):
        return self.game_is_on

    def start_time(self):
        return self.game_start_time

    def current_question(self):
        return self.curr_question

    def total_questions(self):
        return len(movies[self.game_level])

    def video_source(self):
        global movies
        return(movies[self.game_level][self.current_question()]['video_source'])

    def poster_source(self):
        global movies
        return(movies[self.game_level][self.current_question()]['poster_source'])

    def add_player(self):
        self.players += 1
        return self.players

    def number_of_players(self):
        return self.players

    def new_question(self):
        self.curr_question += 1
        self.curr_question_start_time = datetime.now()

    def current_question_start_time(self):
        return self.curr_question_start_time

    def save_answer(self, player, answer):
        if player not in self.answers:
            self.answers[player] = {}
        self.answers[player][self.current_question()] = \
            {'answer': answer, 'is_correct': self.is_answer_correct(answer)}

    def is_answer_correct(self, answer):
        return answer == movies[self.game_level][self.current_question()]['correct_answer']

    def correct_answers(self, question):
        correct_answers = 0
        for player in range(1, self.number_of_players() + 1):
            if player in self.answers:
                if question in self.answers[player]:
                    if self.answers[player][question]['is_correct']:
                        correct_answers += 1
        return correct_answers

    def last_answer(self, player):
        if player not in self.answers:
            return -1
        return self.answers[player][self.current_question()]['answer']

    def last_answer_number(self, player):
        if player not in self.answers:
            return 0
        return max(self.answers[player].keys())

    def players_answered_yet(self):
        players_answered = 0
        for player in range(1, self.number_of_players() + 1):
            if player in self.answers:
                if self.current_question() in self.answers[player]:
                    players_answered += 1
        return players_answered

    def question_is_due(self):
        # check if question time is due
        global question_delay, comm_delay
        if datetime.now() - self.current_question_start_time() >\
            timedelta(seconds=question_delay + comm_delay):
            return True

        # check if all players already answered
        players_answered = 0
        for player in range(1, self.number_of_players()+1):
            if player not in self.answers:
                break
            if self.current_question() not in self.answers[player]:
                break
            players_answered += 1
        return players_answered == self.number_of_players()

    def calc_scores(self):
        scores = dict()
        for player in self.answers:
            scores[player] = sum(player_answer['is_correct'] for player_answer in self.answers[player].values())
        if len(scores) == 0:
            return

        self.game_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner, top_score = self.game_scores[0]
        self.game_winner_info = f"Top score, with {top_score} correct answers: PLAYER {winner}"
        for player, score in self.game_scores[1:]:
            if score != top_score:
                break
            self.game_winner_info = f"{self.game_winner_info}, PLAYER {player}"

    def scores(self):
        return self.game_scores

    def winner_info(self):
        return self.game_winner_info

    def level(self):
        return self.game_level

def load_movies():
    global movies
    static_dir_prefix = "./static"
    movies_dir = '/movies/'
    posters_dir = '/posters/'
    movie_type = '.mp4'
    poster_type = '.jpg'
    movie_list_file = 'movies.csv'

    with open(static_dir_prefix + movies_dir + movie_list_file) as movies_file:
        for line in csv.reader(movies_file):
            level, question_number, clip_file, correct_answer = line
            if int(level) not in movies:
                movies[int(level)] = {}
            movies[int(level)][int(question_number)] = {
                "video_source": movies_dir + clip_file + movie_type,
                "poster_source": posters_dir + clip_file + poster_type,
                "correct_answer": int(correct_answer)
            }

# remove old games if overall time allocated for their questions (+1 for summary screen) is due
def clear_games():
    global games, question_delay, answer_delay, comm_delay
    for game in list(games):
        if datetime.now() - games[game].start_time() > \
                timedelta(seconds=sum([question_delay, answer_delay, comm_delay]) * (games[game].total_questions()+1)):
            games.pop(game)


movies = {}
games = {}
active_games = 0
question_delay = 15  # seconds for each question until time is up
answer_delay = 3  # seconds to remain in screen after showing each answer
comm_delay = 10  # maximum communication delay allowed before moving to next question
load_movies()
