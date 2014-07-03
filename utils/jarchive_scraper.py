"""Script to scrape j-archive.com pages to get Jeopardy! game data.

Decided to use BeautifulSoup after reading through whymarrh's scripts
(github.com/whymarrh/jeopardy-parser). Quite a similar implementation to those
with some adjustments/modifications.


"""

from bs4 import BeautifulSoup
import mechanize
import re
import codecs
import sys
from collections import defaultdict

# Constants
SEASON_REGEX = r".*?season=(\d+)"
AIRED_REGEX = r"#(\d+),.*(\d{4}-\d{2}-\d{2})"
GAME_REGEX = r".*showgame.php\?game_id=(\d+)"

ROUND_TO_ID = {
  # Mapping of rounds to j-archive's html ids.
  1: "jeopardy_round",
  2: "double_jeopardy_round",
  3: "final_jeopardy_round"
}

# Some classes
class Clue(object):
  def __init__(self):
      self.id = 0
      self.round = 0
      self.question = ""
      self.answer = ""
      self.value = 0
      self.category = ""
      self.dd = 0
      self.game = ""
      self.position = 0
      self.picked = 0
      self.game_date = ""


class Category(object):
  def __init__(self):
      self.id = 0
      self.round = 0
      self.game_id = 0
      self.name = ""


class Game(object):
  def __init__(self):
    self.id = 0
    self.game_date = ""
    self.n_questions = 0
    self.players = None


class Player(object):
  def __init__(self):
    self.id = 0
    self.name = ""
    self.games = None
    self.wins = 0


# Scraping/parsing functions.
def ProcessGame(url):
  """Function to process a jeopardy game. Extracts categories, clues, players,
  and game information. Inserts records into sqlite3 tables."""
  soup = BeautifulSoup(mechanize.Browser().open(url))
  if soup.find("p", {"class": "error"}):
    return False
  else:
    bs = soup
  game = Game()
  game_clues = list()
  game_categories = list()
  game_players = GetPlayers(bs)
  game_id = int(re.search("game_id=(\d+)", url).groups()[0])
  game_date = bs.find("title").get_text().split(" ")[-1]
  game.game_date = game_date
  game.players = [p.name for p in game_players]
  for rnd in range(1, 3):
    this_round = bs.find(id = ROUND_TO_ID[rnd])
    try:
      categories = this_round.find_all("td", class_ = "category_name")
      categories = [x.get_text() for x in categories]
      for c in categories:
        cat = Category()
        cat.round = rnd
        cat.game_id = game_id
        cat.name = c
        game_categories.append(cat)
      clues = this_round.find_all("td", class_ = "clue")
      for i, c in enumerate(clues):
        clue = Clue()
        # These values are always available:
        clue.round = rnd
        clue.category = categories[i % 6]
        # clue_value is only unavailable on daily doubles final jeopardy.
        val = c.find("td", class_ = "clue_value")
        if not val:
          val = c.find_all("td", class_ = "clue_value_daily_double")
          if val:
            clue.dd = 1
            digit_regex = re.compile("\d")
            val_text = val[0].get_text()
            digit_index = val_text.index(digit_regex.findall(val_text)[0])
            clean_val = val_text[digit_index:].replace(",", "")
            clue.value = int(clean_val)
          else:
            # question wasn't picked OR final jeopardy
            continue
        else:
          clue.value = int(val.get_text().replace("$", "").replace(",", ""))
        clue.game = game_id
        clue.game_date = game_date
        clue.position = i
        picked = c.find("td", class_ = "clue_order_number")
        if picked:
          clue.picked = int(picked.find("a").get_text())
          clue.question = c.find("td", class_ = "clue_text").get_text()
          mouseover = c.find("div", onmouseover = True)
          clue.answer = BeautifulSoup(mouseover.get("onmouseover"),
                                      "lxml").find("em", class_
                                      = "correct_response").get_text()
        game_clues.append(clue)
    except:
        pass
  # Get final jeopardy
  final = Clue()
  fj = bs.find("table", class_ = "final_round")
  if fj:
    final.game_id = game_id
    final.game_date = game_date
    final.round = 3
    f_ans = fj.find("div", onmouseover = True)
    f_mouse = BeautifulSoup(f_ans.get("onmouseover"), "lxml")
    em = f_mouse.find("em", class_ = "\\\"correct_response\\\"")
    final.answer = em.get_text()
    final.question = fj.find("td", class_ = "clue_text").get_text()
    final.category = fj.find("td", class_ = "category_name").get_text()
    game_clues.append(final)
  game.n_questions = len(game_clues)
  data = {
      "categories": game_categories,
      "clues": game_clues,
      "games": [game],
      "players": game_players
  }
  return data

def GetPlayers(soup):
  players = list()
  pdiv = soup.find("div", id = "contestants")
  if pdiv:
    ps = pdiv.find_all("p")
    for p in ps:
      player = Player()
      link = p.find("a")
      player.name = link.get_text()
      player_page = link.get("href")
      bs2 = BeautifulSoup(mechanize.Browser().open(player_page).read())
      links = bs2.find("div", id = "content").find_all("a")
      try:
        player.games = [int(re.search(GAME_REGEX, l.get("href")).groups()[0])
                        for l in links if re.search(GAME_REGEX, l.get("href"))]
        player.wins = len(player.games) - 1
      except:
        pass
      players.append(player)
  return players

def InsertGame(conn, **data):
  """Function to insert all of the data from a single game into the db."""
  cur = conn.cursor()
  for k in data:
    records = data[k]
    cur.execute("SELECT * FROM %s" % k).fetchone()
    cols = [i[0] for i in cur.description]
    for r in records:
      repeated = [j for j in r.__dict__ if type(r.__dict__[j]) == list]
      # one of the fields is a repeated field.
      if repeated:
        for n, g in enumerate(r.__dict__[repeated[0]]):
          row = list()
          rowid = cur.execute("SELECT MAX(id) FROM %s" % k).fetchall()[0][0]
          if not rowid:
            rowid = 1
          else:
            rowid += 1
          r.id = rowid
          for c in cols:
            if c == repeated[0]:
              row.append(r.__dict__[c][n])
            else:
              row.append(r.__dict__[c])
          qs = ",".join(["?" for c in cols])  # add 1 for the id column
          cur.execute("INSERT OR IGNORE INTO %s VALUES(%s);" % (k, qs), row)
      else:
        row = list()
        rowid = cur.execute("SELECT MAX(id) FROM %s" % k).fetchall()[0][0]
        if not rowid:
          rowid = 1
        else:
          rowid += 1
        r.id = rowid
        for c in cols:
          row.append(r.__dict__[c])
        qs = ",".join(["?" for c in cols])
        cur.execute("INSERT OR IGNORE INTO %s VALUES(%s);" % (k, qs), row)
        conn.commit()