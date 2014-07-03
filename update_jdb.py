"""update_jdb.py

Update the jeopardy game database with the most recent game.

Cron job runs daily to check for new games."""

from optparse import OptionParser
import sqlite3
import sys

from jarchive_scraper import *
import jparty_settings as settings

def GetLatestGame(connection):
  cur = connection.cursor()
  try:
    last_id = cur.execute("SELECT MAX(game_id) from categories").fetchall()[0][0]
    return last_id + 1
  except:
    # DB is empty, first game ID = 173
    return 173


def LoadOptions():
  """Load command line options."""
  parser = OptionParser()
  parser.add_option("-g", "--game_id", dest="game_id")
  parser.add_option("-m", "--max_id", dest="max_id")
  cl_options = parser.parse_args()[0]
  return cl_options


if __name__ == "__main__":
  options = LoadOptions()
  conn = sqlite3.connect(settings.DATABASE_)
  if options.game_id:
    game_id = options.game_id
  else:
    game_id = GetLatestGame(conn)
  if options.max_id:
    max_id = options.max_id
  else:
    max_id = 10000
  while True:
    game_data = ProcessGame(settings.GAME_URL % game_id)
    if game_data:
      if len(game_data['clues']) > 0:
        sys.stdout.write("\rAdding game %s to the database." % game_id)
        sys.stdout.flush()
        InsertGame(conn, **game_data)
        game_id = GetLatestGame(conn)
      else:
        game_id = str(int(game_id) + 1)      
    else:
      sys.exit("All games updated.")
    if game_id == max_id:
      break

