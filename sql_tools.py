import MySQLdb
import MySQLdb.constants as const
from config import *
from sql_tools import *
connection = MySQLdb.connect(host='localhost', user=db_user, passwd=db_passwd, charset = 'utf8mb4')
cursor = connection.cursor()
cursor.execute("SET NAMES utf8")

def get_matches(region=None, db="soloq"):
    if region is not None:
        sql = "SELECT distinct match_id FROM %(db)s.games WHERE region = '%(region)s'"
        cursor.execute(sql % locals())
        connection.commit()
        return set([_i for (_i,) in cursor.fetchall()])
    else:
        sql = "SELECT distinct match_id FROM %(db)s.games"
        cursor.execute(sql % locals())
        connection.commit()
        return set([_i for (_i,) in cursor.fetchall()])

def get_last_game(player, db="soloq"):
    sql = """SELECT creation FROM %(db)s.lane_info join %(db)s.games using(match_id) WHERE player_name = '%(player)s' order by creation desc limit 3"""
    cursor.execute(sql % locals())
    res = [x for (x,) in cursor.fetchall()]
    if len(res) == 0: return 0
    return res[-1]

def load_game(match_id, version, result, creation, duration, region, db="soloq"):
    sql = """INSERT INTO %(db)s.games (match_id, version, result, creation, duration, region)
                 VALUES (%(match_id)s, '%(version)s', %(result)s, %(creation)s, %(duration)s, '%(region)s')
                 ON DUPLICATE KEY UPDATE
                 match_id = %(match_id)s;
          """
    #print(sql % locals())
    cursor.execute(sql % locals())
    connection.commit()

def load_bans(match_id, region, is_blue, ban1, ban2, ban3, ban4, ban5, db="soloq"):
    sql = """INSERT INTO %(db)s.bans (match_id, region, is_blue, ban1, ban2, ban3, ban4, ban5)
                 VALUES (%(match_id)s, '%(region)s', %(is_blue)s, "%(ban1)s", "%(ban2)s", "%(ban3)s", "%(ban4)s", "%(ban5)s")
                 ON DUPLICATE KEY UPDATE
                 match_id = %(match_id)s;
          """
    #print(sql % locals())
    cursor.execute(sql % locals())
    connection.commit()

def load_lane_info(match_id, region, role, is_blue, player_name, champ, result, db="soloq"):
    sql = """INSERT INTO %(db)s.lane_info (match_id, region, role, is_blue, player_name, champ, result)
                 VALUES (%(match_id)s, '%(region)s', '%(role)s', %(is_blue)s, '%(player_name)s', "%(champ)s", %(result)s)
                 ON DUPLICATE KEY UPDATE
                 match_id = %(match_id)s;
          """
    #print(sql % locals())
    cursor.execute(sql % locals())
    connection.commit()

def load_stats(match_id, region, role, is_blue, champ, result, kills, deaths, assists, cc_score, gold_spent, damage, heal, tank, cs10, cs20, g10, g20, xp10, xp20, db="soloq"):
    sql = """INSERT INTO %(db)s.stats (
                match_id,
                region,
                role,
                is_blue,
                champ,
                result,
                kills,
                deaths,
                assists,
                cc_score,
                gold_spent,
                damage,
                heal,
                tank,
                cs10,
                cs20,
                g10,
                g20,
                xp10,
                xp20)
                VALUES (
                 %(match_id)s,
                 '%(region)s',
                 '%(role)s',
                 %(is_blue)s,
                 "%(champ)s",
                 %(result)s,
                 %(kills)s,
                 %(deaths)s,
                 %(assists)s,
                 %(cc_score)s,
                 %(gold_spent)s,
                 %(damage)s,
                 %(heal)s,
                 %(tank)s,
                 %(cs10)s,
                 %(cs20)s,
                 %(g10)s,
                 %(g20)s,
                 %(xp10)s,
                 %(xp20)s)
                ON DUPLICATE KEY UPDATE
                match_id = %(match_id)s;
          """
    #print(sql % locals())
    cursor.execute(sql % locals())
    connection.commit()
