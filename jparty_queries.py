# Get all categories
ALL_CATEGORIES = """SELECT name FROM category GROUP BY name"""
# Get clues for a given category
CLUES_BY_CAT = """SELECT * FROM clues WHERE category = '%s' and round != 3 ORDER BY game_date, round, value;"""
# Get clues for a given clue value
CLUES_BY_VALUE = """SELECT * FROM clues WHERE value = %s;"""
# Get clues for a given game date
CLUES_BY_DATE = """SELECT * FROM clues WHERE game_date = "%s";"""
# Get final jeopardy
FINAL_JEOPARDY_CLUES = """SELECT * FROM clues where round = 3;"""
# Get first round clues
FIRST_ROUND_CLUES = """SELECT * FROM clues where round = 1;"""
# Get second round clues
SECOND_ROUND_CLUES = """SELECT * FROM clues where round = 2;"""
# Get all game dates
SHOW_DATES = """SELECT game_date from games ORDER BY game_date;"""
# Get categories that match a query.
CATEGORY_SEARCH = """SELECT category, COUNT(*) as cnt FROM clues WHERE category LIKE "%s" AND round != 3 GROUP BY category ORDER BY cnt DESC;"""
# GET oldest and newest game dates.
DATE_RANGE = """SELECT MAX(game_date) as max, MIN(game_date) as min FROM clues"""
# Get next highest date for a given game_date
NEXT_DATE = """SELECT MIN(game_date) from clues WHERE game_date > "%s";"""
# Get all game_dates for a given category
CATEGORY_DATES = """SELECT game_date, round as cnt from clues WHERE category = "%s" AND round != 3 GROUP BY game_date, round ORDER BY round;"""
# Get category clues for a specific game date
CATEGORY_BY_DATE = """SELECT * FROM clues WHERE category = "%s" AND round != 3 ORDER BY round, game_date, position;"""