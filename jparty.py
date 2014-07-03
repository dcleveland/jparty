from flask import Flask, request, url_for, abort, render_template
from collections import defaultdict
import json
import math
import os
import sqlite3
import sys
import re

import jparty_queries as queries
import jparty_settings as settings


app = Flask(__name__)

QUESTION_STRUCT = {
  'clue': 0,
  'answer': 1,
  'category': 2,
  'value': 3,
  'dd': 4,
  'round': 5,
}

CLUE_STRUCT = {
  'id': 0,
  'round': 1,
  'question': 2,
  'answer': 3,
  'value': 4,
  'category': 5,
  'dd': 6,
  'game': 7,
  'position': 8,
  'picked': 9,
  'game_date': 10
}


def CategorySearch(query):
  """Function to get categories that match a given query. Very simple logic."""
  conn = sqlite3.connect(settings.DATABASE_)
  cur = conn.cursor()
  query = queries.CATEGORY_SEARCH % "%".join((" " + query + " ").split(" "))
  results = [(x[0], x[1]) for x in cur.execute(query).fetchall()]
  return results


def GetGame(game_date):
  """Get game data for a game from a given date."""
  conn = sqlite3.connect(settings.DATABASE_)
  cur = conn.cursor()
  game_data = cur.execute(queries.CLUES_BY_DATE % game_date).fetchall()
  return BuildGameDict(game_data)


def GetDates():
  """Get the 100 most recent game dates."""
  conn = sqlite3.connect(settings.DATABASE_)
  cur = conn.cursor()
  cur.execute(("SELECT game_date from clues GROUP BY game_date ORDER BY "
               "game_date DESC;"))
  dates = [d[0] for d in cur.fetchall()[0:500]]
  return dates


def BuildCategoryDict(cat_data):
  """Organize data for a single category."""
  values = settings.VALUES
  n_cols = len(cat_data) / 5
  if n_cols > 6:
    cat_data = cat_data[0:29]
  cat_dict = dict([(n, defaultdict(dict)) for n in range(1, min([n_cols, 6]))])
  # return cat_dict
  for n, clue in enumerate(cat_data):
    q = clue[CLUE_STRUCT['question']].replace('"', '&quot')
    a = clue[CLUE_STRUCT['answer']].replace('"', '&quot')
    row = GetRowFromIndex(clue[CLUE_STRUCT['position']])
    clue_dict = {
        'question': q,
        'answer': a,
        'picked': clue[CLUE_STRUCT['picked']],
        'value': clue[CLUE_STRUCT['value']],
        'dd': 0,
        'row': row
    }
    good_value = settings.VALUES[str(clue[CLUE_STRUCT['round']])][row]
    if clue_dict['value'] != int(good_value):
      clue_dict['dd'] = 1
      clue_dict['value'] = int(good_value)
    this_val = str(clue_dict['value'])
    this_cat = n / 6
    if this_cat not in cat_dict:
      cat_dict[this_cat] = defaultdict(dict)
      print "balls."
    cat_dict[this_cat][this_val] = clue_dict
  print n
  return cat_dict

def BuildGameDict(game_data):
  """Function to organize the data for a single game."""
  values = settings.VALUES
  game_dict = {
      '1': defaultdict(dict),
      '2': defaultdict(dict),
      '3': defaultdict(dict)
  }
  categories = {}
  for clue in game_data:
    q = clue[CLUE_STRUCT['question']].replace('"', '&quot')
    a = clue[CLUE_STRUCT['answer']].replace('"', '&quot')
    clue_dict = {
        'question': q,
        'answer': a,
        'picked': clue[CLUE_STRUCT['picked']],
        'value': clue[CLUE_STRUCT['value']],
        'dd': 0
    }
    row = GetRowFromIndex(clue[CLUE_STRUCT['position']])
    good_value = settings.VALUES[str(clue[CLUE_STRUCT['round']])][row]
    if clue_dict['value'] != int(good_value):
      clue_dict['dd'] = 1
      clue_dict['value'] = int(good_value)
    this_val = str(clue_dict['value'])
    this_cat = clue[CLUE_STRUCT['category']]  
    this_round = str(clue[CLUE_STRUCT['round']])
    game_dict[this_round][this_cat][this_val] = clue_dict
  for x in ['1', '2']:
    categories[x] = list(set([c[5] for c in game_data if c[1] == int(x)]))
    game_dict[x] = dict(game_dict[x])
  categories['3'] = [game_dict['3'].keys()]
  return game_dict, categories

def GetRowFromIndex(index):
  """Useful for determining clue value for daily doubles."""
  return (index/6) % 6

@app.route("/random")
def RandomQuestion():
  conn = sqlite3.connect(settings.DATABASE_)
  cur = conn.cursor()
  data = cur.execute(settings.RANDOM_QUESTION).fetch_one()
  q = {
    "clue": data[QUESTION_STRUCT["clue"]],
    "answer": data[QUESTION_STRUCT["answer"]],
    "category": data[QUESTION_STRUCT["category"]],
    "value": data[QUESTION_STRUCT["value"]],
    "dd": data[QUESTION_STRUCT["dd"]],
    "round": data[QUESTION_STRUCT["round"]],
  }
  return render_template("random.html", question=q)

@app.route("/next_date/d=<date>")
def next_date(date):
  conn = sqlite3.connect(settings.DATABASE_)
  cur = conn.cursor()
  n_date = cur.execute(queries.NEXT_DATE % date).fetchall()[0][0]
  return json.dumps(n_date)


# Request handler to get data for a specific game.
@app.route("/game/id=<game_date>")
def game_view(game_date):
  data, categories = GetGame(game_date)
  result = {"rounds": data, "categories": categories, "vals": settings.VALUES}
  return json.dumps(result)


# Request handler for category searches. Only called via ajax and/or testing.
@app.route("/category/c=<category>")
def showCategory(category):
  conn = sqlite3.connect(settings.DATABASE_)
  cur = conn.cursor()
  cat_data = cur.execute(queries.CLUES_BY_CAT % category).fetchall()
  print len(cat_data)
  data = BuildCategoryDict(cat_data)
  # return json.dumps(data)
  result = {"cols": data, "category": category, "vals": settings.VALUES}
  return json.dumps(result)


# Handler to return the first and last available game dates.
@app.route("/date_range")
def getDateRange():
  conn = sqlite3.connect(settings.DATABASE_)
  cur = conn.cursor()
  q = queries.DATE_RANGE
  max_d, min_d = cur.execute(q).fetchall()[0]
  return json.dumps({'max': max_d, 'min': min_d})


@app.route("/cat_dates/c=<category>")
def getCategoryDates(category):
  conn = sqlite3.connect(settings.DATABASE_)
  cur = conn.cursor()
  q = queries.CATEGORY_DATES % category
  dates = [d[0] for d in cur.execute(q).fetchall()]
  return json.dumps(dates)

@app.route("/cat_grids/c=<category>")
def getCategoryByDate(category):
  conn = sqlite3.connect(settings.DATABASE_)
  cur = conn.cursor()
  q = queries.CATEGORY_BY_DATE % (category)
  results = cur.execute(q).fetchall()
  cols = list(set([r[CLUE_STRUCT["game_date"]] for r in results]))
  n_cols = len(cols)
  n_rounds = int(math.ceil(n_cols/6.))
  data = dict([(x, []) for x in cols])
  rounds = dict([(x, []) for x in range(0, n_rounds)])
  for r in results:
    r = list(r)
    row = GetRowFromIndex(r[CLUE_STRUCT['position']])
    good_value = settings.VALUES[str(r[CLUE_STRUCT['round']])][row]
    if r[CLUE_STRUCT["value"]] != int(good_value):
      r[CLUE_STRUCT["value"]] = good_value
    data[r[CLUE_STRUCT["game_date"]]].append(r)
  i = 0
  for x in range(0, n_cols):
    if len(rounds[i]) == 6:
      i += 1
    if len(data[cols[x]]) < 5:
      this_round = data[cols[x]][0][CLUE_STRUCT["round"]]
      good_vals = settings.VALUES[str(this_round)]
      for n, v in enumerate(data[cols[x]]):

        try:
          if str(v[CLUE_STRUCT["value"]]) != good_vals[n]:
            data[cols[x]].insert(n, ["X"])
            if len(data[cols[x]]) == 5:
              break
        except:
          print data[cols[x]]
    rounds[i].append(data[cols[x]])
  data_dict = {'nrounds': len(rounds), 'grids': [rounds[x] for x in rounds]}
  return json.dumps(data_dict)

# Handler to retrieve valid game dates.
@app.route("/dates")
def dates():
  data = GetDates()
  return json.dumps(data)


# Handler to return search results for a category search.
@app.route("/search/q=<query>")
def search(query):
  results = CategorySearch(query)
  return json.dumps(results)


# Main request handler.
@app.route("/jparty")
def index():
  dates = GetDates()
  return render_template("index.html", dates=dates)


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8080, debug=True)
  # app.run()