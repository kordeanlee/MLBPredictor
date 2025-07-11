import ast
import time
import datetime
import statsapi
from IPython.display import clear_output

YELLOW = "\033[33m"
ORANGE = "\033[38;5;208m"
RED = "\033[31m"
RESET = "\033[0m"
SLEEP_TIME = 3

def load_data(file_path):
    data_dict = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            key_part, value_part = line.split(":", 1)
            data_dict[ast.literal_eval(key_part.strip())] = ast.literal_eval(value_part.strip())
    return data_dict

historical_data = load_data("/Users/dean/Documents/Stats.txt")

def get_away_team_win_prob(historical_data, inning, inning_half, outs, bases, away_score, home_score):
    relative_score = (away_score - home_score) if inning_half == 0 else (home_score - away_score)
    query_key = (inning, inning_half, outs, bases, relative_score)
    if query_key not in historical_data:
        return None
    batting_wins, total_games = historical_data[query_key]
    away_wins = batting_wins if inning_half == 0 else (total_games - batting_wins)
    win_percent = away_wins * 100 / total_games
    return away_wins, total_games, win_percent

def get_today_games():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    schedule = statsapi.schedule(start_date=yesterday, end_date=today)
    return [game for game in schedule if game.get("status") == "In Progress"]

def get_game_state(game_id):
    game_data = statsapi.get("game", {"gamePk": game_id})
    linescore = game_data.get("liveData", {}).get("linescore", {})
    teams = linescore.get('teams', {})
    inning = linescore.get("currentInning", 0)
    inning_half = 0 if linescore.get("inningHalf", "").lower() == "top" else 1
    outs = linescore.get("outs", 0)
    bases = (
        int(bool(linescore.get("offense", {}).get("first"))),
        int(bool(linescore.get("offense", {}).get("second"))),
        int(bool(linescore.get("offense", {}).get("third")))
    )
    away_score = teams.get("away", {}).get("runs", 0)
    home_score = teams.get("home", {}).get("runs", 0)
    return inning, inning_half, outs, bases, away_score, home_score

def probability_to_american_odds(probability):
    if probability >= 100.0 or probability <= 0.0:
        return "X"
    return f"{int(round(-100 * probability / (100 - probability)))}" if probability > 50 else f"+{int(round(100 * (100 - probability) / probability))}"

def format_outs(outs):
    return ' '.join('⬥' if i < outs else '⬦' for i in range(3))

def format_bases(bases):
    return ' '.join('⬥' if base else '⬦' for base in bases[::-1])

def get_inning_color(inning):
    return YELLOW if inning < 4 else ORANGE if inning < 7 else RED

while True:
    clear_output(wait=True)
    live_games = get_today_games()
    if not live_games:
        print("No live games at the moment.\n")
        break
    for game_info in live_games:
        game_state = get_game_state(game_info['game_id'])
        inning, inning_half, outs, bases, away_score, home_score = game_state
        inning_half_symbol = "▲" if inning_half == 0 else "▼"
        color = get_inning_color(inning)
        print(f"\n⚾ {color}{game_info['away_name']} @ {game_info['home_name']}{RESET}")
        print(f"{color}──────────────────────────────────────────────────𓆏{RESET}")
        print(f"[{away_score} - {home_score}]: {inning_half_symbol} {inning} [Bases: {format_bases(bases)}] [Outs: {format_outs(outs)}]")
        result = get_away_team_win_prob(historical_data, inning, inning_half, outs, bases, away_score, home_score)
        if result is None:
            print("Awaiting Next Inning...")
        else:
            wins, games, pct = result
            odds = probability_to_american_odds(pct)
            print(f"{game_info['away_name']}: [{wins}/{games}] [{pct:.2f}%] [{odds}]")
    time.sleep(SLEEP_TIME)
