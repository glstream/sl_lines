from airflow.decorators import task
import json, requests, re
from psycopg2.extras import execute_batch
from bs4 import BeautifulSoup
from datetime import datetime
from airflow.providers.postgres.hooks.postgres import PostgresHook


@task()
def ktc_web_scraper():
    page = "0"
    league_format = {"single_qb": "1", "sf": "2"}

    # Dynasty rankings URL
    dynasty_url = f"https://keeptradecut.com/dynasty-rankings?page={page}&filters=QB|WR|RB|TE|RDP&format={league_format['sf']}"
    dynasty_res = requests.get(dynasty_url)

    # Redraft rankings URL
    redraft_url = "https://keeptradecut.com/fantasy-rankings"
    redraft_res = requests.get(redraft_url)

    # Function to parse the script containing player data
    def parse_players_script(response, rank_type):
        soup = BeautifulSoup(response.text, "html.parser")
        scripts = soup.find_all("script")
        script_var_array = scripts[16]  # Assuming the target script is at index 16
        players_script = script_var_array.contents[0]
        START_REGEX = "var playersArray ="
        start_substr_num = players_script.find(START_REGEX) + len(START_REGEX) + 1
        end_regex = ";"
        second_semicolin_num = [m.start() for m in re.finditer(r";", players_script)][1]
        players_array = players_script[start_substr_num:second_semicolin_num]
        players_json = json.loads(players_array)

        # Add rank_type to each player record
        for player in players_json:
            player['rank_type'] = rank_type

        return players_json

    # Parse both dynasty and redraft rankings
    dynasty_players = parse_players_script(dynasty_res, 'dynasty')
    redraft_players = parse_players_script(redraft_res, 'redraft')

    # Combine both rankings into one JSON object
    ktc_players_json = dynasty_players + redraft_players

    return ktc_players_json


@task()
def data_validation(ktc_players_json: dict):
    return ktc_players_json if len(ktc_players_json) > 0 else False


@task()
def ktc_player_load(ktc_players_json):

    pg_hook = PostgresHook(postgres_conn_id="postgres_akv")
    conn = pg_hook.get_conn()

    cursor = conn.cursor()
    print("Connection established")

    enrty_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f%z")

    ktc_players = []

    for ktc_player in ktc_players_json:
        ktc_players.append(
            [
                ktc_player["playerName"].split(" ")[0],
                ktc_player["playerName"].replace(' III', "").replace(' Jr.', "").split(" ")[-1],
                ktc_player["playerName"],
                ktc_player["playerID"],
                ktc_player["slug"],
                ktc_player["position"],
                ktc_player["positionID"],
                ktc_player["team"],
                ktc_player["rookie"],
                ktc_player.get("college"),
            ktc_player["age"],
            ktc_player["heightFeet"],
            ktc_player["heightInches"],
            ktc_player["weight"],
            ktc_player["seasonsExperience"],
            ktc_player["pickRound"],
            ktc_player["pickNum"],
            ktc_player["oneQBValues"]["value"],
            ktc_player["oneQBValues"]["startSitValue"],
            ktc_player["oneQBValues"]["rank"],
            ktc_player["oneQBValues"]["overallTrend"],
            ktc_player["oneQBValues"].get("positionalTrend"),
            ktc_player["oneQBValues"].get("positionalRank"),
            ktc_player["oneQBValues"].get("rookieRank"),
            ktc_player["oneQBValues"].get("rookiePositionalRank"),
            ktc_player["oneQBValues"]["kept"],
            ktc_player["oneQBValues"]["traded"],
            ktc_player["oneQBValues"]["cut"],
            ktc_player["oneQBValues"]["overallTier"],
            ktc_player["oneQBValues"].get("positionalTier"),
            ktc_player["oneQBValues"].get("rookieTier"),
            ktc_player["oneQBValues"].get('rookiePositionalTier'),
            ktc_player["oneQBValues"].get('startSitOverallRank'),
            ktc_player["oneQBValues"].get('startSitPositionalRank'),
            ktc_player["oneQBValues"].get('startSitOverallTier'),
            ktc_player["oneQBValues"].get('startSitPositionalTier'),
            ktc_player["oneQBValues"].get('startSitOneQBFlexTier'),
            ktc_player["oneQBValues"].get('startSitSuperflexFlexTier'),
            ktc_player["superflexValues"]["value"],
            ktc_player["superflexValues"]["startSitValue"],
            ktc_player["superflexValues"]["rank"],
            ktc_player["superflexValues"]["overallTrend"],
            ktc_player["superflexValues"].get('positionalTrend'),
            ktc_player["superflexValues"].get('positionalRank'),
            ktc_player["superflexValues"].get('rookieRank'),
            ktc_player["superflexValues"].get("rookiePositionalRank"),
            ktc_player["superflexValues"]["kept"],
            ktc_player["superflexValues"]["traded"],
            ktc_player["superflexValues"]["cut"],
            ktc_player["superflexValues"]["overallTier"],
            ktc_player["superflexValues"].get('positionalTier'),
            ktc_player["superflexValues"].get("rookieTier"),
            ktc_player["superflexValues"].get("rookiePositionalTier"),
            ktc_player["superflexValues"].get("startSitOverallRank"),
            ktc_player["superflexValues"].get("startSitPositionalRank"),
            ktc_player["superflexValues"].get("startSitOverallTier"),
            ktc_player["superflexValues"].get("startSitPositionalTier"),
            enrty_time,
            ktc_player["rank_type"]
            ]
        )

    execute_batch(
        cursor,
        """
            INSERT INTO dynastr.ktc_player_ranks (
                player_first_name,
                player_last_name,
                player_full_name,
                ktc_player_id,
                slug,
                position,
                position_id,
                team,
                rookie,
                college,
                age,
                height_feet,
                height_inches,
                weight,
                season_experience,
                pick_round,
                pink_num,
                one_qb_value,
                start_sit_value,
                rank,
                overall_trend,
                positional_trend,
                positional_rank,
                rookie_rank,
                rookie_positional_rank,
                kept,
                traded,
                cut,
                overall_tier,
                positional_tier,
                rookie_tier,
                rookie_positional_tier,
                start_sit_overall_rank,
                start_sit_positional_rank,
                start_sit_overall_tier,
                start_sit_positional_tier,
                start_sit_oneQB_flex_tier,
                start_sit_superflex_flex_tier,
                sf_value,
                sf_start_sit_value,
                sf_rank,
                sf_overall_trend,
                sf_positional_trend,
                sf_positional_rank,
                sf_rookie_rank,
                sf_rookie_positional_rank,
                sf_kept,
                sf_traded,
                sf_cut,
                sf_overall_tier,
                sf_positional_tier,
                sf_rookie_tier,
                sf_rookie_positional_tier,
                sf_start_sit_overall_rank,
                sf_start_sit_positional_rank,
                sf_start_sit_overall_tier,
                sf_start_sit_positional_tier,
                insert_date, 
                rank_type
        )        
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (ktc_player_id, rank_type)
        DO UPDATE SET sf_rank = EXCLUDED.sf_rank
            , sf_positional_rank = EXCLUDED.sf_positional_rank
            , rank = EXCLUDED.rank
            , positional_rank = EXCLUDED.positional_rank
            , one_qb_value = EXCLUDED.one_qb_value
            , sf_value = EXCLUDED.sf_value
            , rookie = EXCLUDED.rookie
            , insert_date = EXCLUDED.insert_date;
        """,
        tuple(ktc_players),
        page_size=1000,
    )

    print(f"{len(ktc_players)} ktc players to inserted or updated.")
    conn.commit()
    cursor.close()
    return "dynastr.ktc_player_ranks"


@task()
def surrogate_key_formatting(table_name: str):
    pg_hook = PostgresHook(postgres_conn_id="postgres_akv")
    conn = pg_hook.get_conn()
    cursor = conn.cursor()
    print("Connection established")
    cursor.execute(
        f"""UPDATE {table_name} 
                        SET player_first_name = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(player_first_name,'.',''), ' Jr', ''), ' III',''),'Jeffery','Jeff'), 'Joshua','Josh'),'William','Will'), ' II', ''),'''',''),'Kenneth','Ken'),'Mitchell','Mitch'),'DWayne','Dee')
                        """
    )
    conn.commit()
    cursor.close()
    return
