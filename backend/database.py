import os
import sqlite3
from typing import List, Dict, Any, Optional

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))
DB_PATH = os.path.join(DB_DIR, "cricket.db")

def get_connection() -> sqlite3.Connection:
    """Creates a connection to SQLite database with foreign keys enabled."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database schema according to specifications."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Teams Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Players Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Batter', 'Bowler', 'All-rounder', 'Wicket-keeper')),
                team_id INTEGER NOT NULL,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );
        """)

        # 3. Tournaments Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                format TEXT NOT NULL DEFAULT 'T20' CHECK(format IN ('T20', 'ODI', 'Test')),
                status TEXT NOT NULL DEFAULT 'Upcoming' CHECK(status IN ('Upcoming', 'In Progress', 'Completed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Tournament Teams (Associative table for Many-to-Many relation)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tournament_teams (
                tournament_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                PRIMARY KEY (tournament_id, team_id),
                FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );
        """)

        # 5. Matches Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL,
                match_number INTEGER NOT NULL,
                format TEXT NOT NULL DEFAULT 'T20',
                stage TEXT NOT NULL DEFAULT 'Group',
                is_playoff INTEGER NOT NULL DEFAULT 0,
                team_a_id INTEGER NOT NULL,
                team_b_id INTEGER NOT NULL,
                team_a_source TEXT DEFAULT NULL,
                team_b_source TEXT DEFAULT NULL,
                score_a INTEGER DEFAULT NULL,
                wickets_a INTEGER DEFAULT NULL,
                overs_a REAL DEFAULT NULL,
                score_b INTEGER DEFAULT NULL,
                wickets_b INTEGER DEFAULT NULL,
                overs_b REAL DEFAULT NULL,
                winner_id INTEGER DEFAULT NULL,
                is_tie INTEGER NOT NULL DEFAULT 0,
                result_description TEXT DEFAULT 'Scheduled',
                man_of_match TEXT DEFAULT NULL,
                man_of_match_performance TEXT DEFAULT NULL,
                status TEXT NOT NULL DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Completed')),
                FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
                FOREIGN KEY (team_a_id) REFERENCES teams(id) ON DELETE CASCADE,
                FOREIGN KEY (team_b_id) REFERENCES teams(id) ON DELETE CASCADE
            );
        """)

        # 6. Crex Individual Player Match Performance Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_player_performances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                team_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                innings INTEGER NOT NULL, -- 1 = First Innings, 2 = Second Innings
                batting_order INTEGER DEFAULT 0,
                runs INTEGER DEFAULT 0,
                balls INTEGER DEFAULT 0,
                fours INTEGER DEFAULT 0,
                sixes INTEGER DEFAULT 0,
                dismissal TEXT DEFAULT 'not out',
                is_out INTEGER DEFAULT 0,
                overs_bowled REAL DEFAULT 0.0,
                maidens INTEGER DEFAULT 0,
                runs_conceded INTEGER DEFAULT 0,
                wickets INTEGER DEFAULT 0,
                dot_balls INTEGER DEFAULT 0,
                FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
                FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
            );
        """)

        # Ensure schema migrations for existing databases
        cursor.execute("PRAGMA table_info(matches);")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        if "stage" not in existing_cols:
            cursor.execute("ALTER TABLE matches ADD COLUMN stage TEXT NOT NULL DEFAULT 'Group';")
        if "is_playoff" not in existing_cols:
            cursor.execute("ALTER TABLE matches ADD COLUMN is_playoff INTEGER NOT NULL DEFAULT 0;")
        if "team_a_source" not in existing_cols:
            cursor.execute("ALTER TABLE matches ADD COLUMN team_a_source TEXT DEFAULT NULL;")
        if "team_b_source" not in existing_cols:
            cursor.execute("ALTER TABLE matches ADD COLUMN team_b_source TEXT DEFAULT NULL;")
        if "man_of_match" not in existing_cols:
            cursor.execute("ALTER TABLE matches ADD COLUMN man_of_match TEXT DEFAULT NULL;")
        if "man_of_match_performance" not in existing_cols:
            cursor.execute("ALTER TABLE matches ADD COLUMN man_of_match_performance TEXT DEFAULT NULL;")

        conn.commit()

# ============================================================================
# TEAM CRUD OPERATIONS
# ============================================================================

def add_team(name: str) -> Dict[str, Any]:
    name = name.strip()
    if not name:
        raise ValueError("Team name cannot be empty.")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO teams (name) VALUES (?)", (name,))
        conn.commit()
        team_id = cursor.lastrowid
        return {"id": team_id, "name": name}

def get_all_teams() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.name, t.created_at, COUNT(p.id) AS player_count
            FROM teams t
            LEFT JOIN players p ON t.id = p.team_id
            GROUP BY t.id, t.name, t.created_at
            ORDER BY t.name ASC;
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_team_by_id(team_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, created_at FROM teams WHERE id = ?", (team_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_team(team_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        conn.commit()
        return cursor.rowcount > 0

# ============================================================================
# PLAYER CRUD OPERATIONS
# ============================================================================

def add_player(name: str, role: str, team_id: int) -> Dict[str, Any]:
    name = name.strip()
    role = role.strip()
    valid_roles = ('Batter', 'Bowler', 'All-rounder', 'Wicket-keeper')
    if not name:
        raise ValueError("Player name cannot be empty.")
    if role not in valid_roles:
        raise ValueError(f"Invalid role '{role}'. Must be one of {valid_roles}")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        # Verify team exists
        cursor.execute("SELECT id, name FROM teams WHERE id = ?", (team_id,))
        team = cursor.fetchone()
        if not team:
            raise ValueError(f"Team with ID {team_id} does not exist.")
        
        cursor.execute(
            "INSERT INTO players (name, role, team_id) VALUES (?, ?, ?)",
            (name, role, team_id)
        )
        conn.commit()
        player_id = cursor.lastrowid
        return {
            "id": player_id,
            "name": name,
            "role": role,
            "team_id": team_id,
            "team_name": team["name"]
        }

def get_all_players(team_id: Optional[int] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if team_id:
            cursor.execute("""
                SELECT p.id, p.name, p.role, p.team_id, t.name as team_name
                FROM players p
                JOIN teams t ON p.team_id = t.id
                WHERE p.team_id = ?
                ORDER BY p.name ASC;
            """, (team_id,))
        else:
            cursor.execute("""
                SELECT p.id, p.name, p.role, p.team_id, t.name as team_name
                FROM players p
                JOIN teams t ON p.team_id = t.id
                ORDER BY t.name ASC, p.name ASC;
            """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def delete_player(player_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM players WHERE id = ?", (player_id,))
        conn.commit()
        return cursor.rowcount > 0

# ============================================================================
# TOURNAMENT OPERATIONS
# ============================================================================

def create_tournament(name: str, format_: str, team_ids: List[int]) -> Dict[str, Any]:
    name = name.strip()
    format_ = format_.strip()
    if not name:
        raise ValueError("Tournament name cannot be empty.")
    if len(team_ids) < 2:
        raise ValueError("A tournament must have at least two participating teams.")
    if format_ not in ('T20', 'ODI', 'Test'):
        format_ = 'T20'

    with get_connection() as conn:
        cursor = conn.cursor()
        # Verify all teams exist
        placeholders = ",".join("?" for _ in team_ids)
        cursor.execute(f"SELECT id, name FROM teams WHERE id IN ({placeholders})", team_ids)
        teams = cursor.fetchall()
        if len(teams) < len(team_ids):
            raise ValueError("One or more selected teams do not exist.")

        cursor.execute(
            "INSERT INTO tournaments (name, format, status) VALUES (?, ?, 'Upcoming')",
            (name, format_)
        )
        tournament_id = cursor.lastrowid

        for t in teams:
            cursor.execute(
                "INSERT INTO tournament_teams (tournament_id, team_id) VALUES (?, ?)",
                (tournament_id, t["id"])
            )
        conn.commit()

        return {
            "id": tournament_id,
            "name": name,
            "format": format_,
            "status": "Upcoming",
            "teams": [{"id": t["id"], "name": t["name"]} for t in teams]
        }

def save_tournament_fixtures(tournament_id: int, format_: str, fixtures: List[Dict[str, Any]]) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        for fix in fixtures:
            cursor.execute("""
                INSERT INTO matches (
                    tournament_id, match_number, format, stage, is_playoff, team_a_id, team_b_id, status
                ) VALUES (?, ?, ?, 'Group', 0, ?, ?, 'Scheduled')
            """, (
                tournament_id,
                fix.get("match_number", 1),
                format_,
                fix["team_a_id"],
                fix["team_b_id"]
            ))
        conn.commit()

def save_qualifier_fixtures(tournament_id: int, format_: str, qualifiers: List[Dict[str, Any]]) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        # Remove any existing scheduled playoff matches to allow regenerating if needed
        cursor.execute("DELETE FROM matches WHERE tournament_id = ? AND is_playoff = 1 AND status = 'Scheduled'", (tournament_id,))
        for q in qualifiers:
            cursor.execute("""
                INSERT INTO matches (
                    tournament_id, match_number, format, stage, is_playoff,
                    team_a_id, team_b_id, team_a_source, team_b_source, status
                ) VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, 'Scheduled')
            """, (
                tournament_id,
                q.get("match_number", 1),
                format_,
                q.get("stage", "Qualifier 1"),
                q.get("team_a_id", 0),
                q.get("team_b_id", 0),
                q.get("team_a_source", ""),
                q.get("team_b_source", "")
            ))
        conn.commit()

def get_all_tournaments() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.id, t.name, t.format, t.status, t.created_at,
                COUNT(DISTINCT tt.team_id) AS team_count,
                COUNT(DISTINCT m.id) AS match_count,
                SUM(CASE WHEN m.status = 'Completed' THEN 1 ELSE 0 END) AS completed_match_count
            FROM tournaments t
            LEFT JOIN tournament_teams tt ON t.id = tt.tournament_id
            LEFT JOIN matches m ON t.id = m.tournament_id
            GROUP BY t.id, t.name, t.format, t.status, t.created_at
            ORDER BY t.id DESC;
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_tournament_by_id(tournament_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, format, status, created_at FROM tournaments WHERE id = ?", (tournament_id,))
        row = cursor.fetchone()
        if not row:
            return None
        tourney = dict(row)

        cursor.execute("""
            SELECT t.id, t.name
            FROM teams t
            JOIN tournament_teams tt ON t.id = tt.team_id
            WHERE tt.tournament_id = ?
            ORDER BY t.name ASC;
        """, (tournament_id,))
        tourney["teams"] = [dict(t) for t in cursor.fetchall()]
        return tourney

def delete_tournament(tournament_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
        conn.commit()
        return cursor.rowcount > 0

def delete_match(match_id: int) -> bool:
    """Delete a single match and its associated player performances."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM match_player_performances WHERE match_id = ?", (match_id,))
        cursor.execute("DELETE FROM matches WHERE id = ?", (match_id,))
        conn.commit()
        return cursor.rowcount > 0

# ============================================================================
# MATCH OPERATIONS
# ============================================================================

def get_tournament_matches(tournament_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                m.id, m.tournament_id, m.match_number, m.format,
                m.stage, m.is_playoff, m.team_a_source, m.team_b_source,
                m.team_a_id, COALESCE(ta.name, 'TBD') as team_a_name,
                m.team_b_id, COALESCE(tb.name, 'TBD') as team_b_name,
                m.score_a, m.wickets_a, m.overs_a,
                m.score_b, m.wickets_b, m.overs_b,
                m.winner_id,
                CASE 
                    WHEN m.is_tie = 1 THEN 'Tie'
                    WHEN m.winner_id = m.team_a_id THEN ta.name
                    WHEN m.winner_id = m.team_b_id THEN tb.name
                    ELSE NULL
                END as winner_name,
                m.is_tie, m.result_description, m.man_of_match, m.man_of_match_performance, m.status
            FROM matches m
            LEFT JOIN teams ta ON m.team_a_id = ta.id
            LEFT JOIN teams tb ON m.team_b_id = tb.id
            WHERE m.tournament_id = ?
            ORDER BY m.is_playoff ASC, m.match_number ASC;
        """, (tournament_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_match_by_id(match_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                m.*,
                COALESCE(ta.name, 'TBD') as team_a_name,
                COALESCE(tb.name, 'TBD') as team_b_name
            FROM matches m
            LEFT JOIN teams ta ON m.team_a_id = ta.id
            LEFT JOIN teams tb ON m.team_b_id = tb.id
            WHERE m.id = ?;
        """, (match_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_match_result(
    match_id: int,
    score_a: int,
    wickets_a: int,
    overs_a: float,
    score_b: int,
    wickets_b: int,
    overs_b: float,
    winner_id: Optional[int],
    is_tie: bool,
    result_description: str,
    man_of_match: Optional[str] = None,
    man_of_match_performance: Optional[str] = None
) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE matches
            SET score_a = ?,
                wickets_a = ?,
                overs_a = ?,
                score_b = ?,
                wickets_b = ?,
                overs_b = ?,
                winner_id = ?,
                is_tie = ?,
                result_description = ?,
                man_of_match = COALESCE(?, man_of_match),
                man_of_match_performance = COALESCE(?, man_of_match_performance),
                status = 'Completed'
            WHERE id = ?;
        """, (
            score_a, wickets_a, overs_a,
            score_b, wickets_b, overs_b,
            winner_id,
            1 if is_tie else 0,
            result_description,
            man_of_match,
            man_of_match_performance,
            match_id
        ))

        # Update qualifier/playoff progression if this is a playoff match
        update_qualifier_progression(match_id, conn)

        # Check if all matches in this tournament are completed, update tournament status
        cursor.execute("SELECT tournament_id FROM matches WHERE id = ?", (match_id,))
        t_row = cursor.fetchone()
        if t_row:
            tourney_id = t_row["tournament_id"]
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
                FROM matches WHERE tournament_id = ?
            """, (tourney_id,))
            counts = cursor.fetchone()
            if counts and counts["total"] > 0:
                if counts["completed"] == counts["total"]:
                    new_status = "Completed"
                elif counts["completed"] > 0:
                    new_status = "In Progress"
                else:
                    new_status = "Upcoming"
                cursor.execute("UPDATE tournaments SET status = ? WHERE id = ?", (new_status, tourney_id))

        conn.commit()

    # Automatically generate Crex-style individual player scores if not already existing
    auto_generate_crex_scorecard(match_id)

    return True

def update_qualifier_progression(match_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    """Updates team participants in future playoff stages (Qualifier 2, Final) when playoff matches finish."""
    own_conn = False
    if conn is None:
        conn = get_connection()
        own_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
        match = cursor.fetchone()
        if not match or not match["is_playoff"] or match["status"] != "Completed":
            return

        tourney_id = match["tournament_id"]
        stage = match["stage"]
        winner_id = match["winner_id"]
        if not winner_id:
            return

        team_a_id = match["team_a_id"]
        team_b_id = match["team_b_id"]
        loser_id = team_b_id if winner_id == team_a_id else team_a_id

        if stage == "Qualifier 1":
            # Loser goes to Qualifier 2 as Team A
            cursor.execute("""
                UPDATE matches SET team_a_id = ?
                WHERE tournament_id = ? AND stage = 'Qualifier 2'
            """, (loser_id, tourney_id))
            # Winner goes to Final as Team A
            cursor.execute("""
                UPDATE matches SET team_a_id = ?
                WHERE tournament_id = ? AND stage = 'Final'
            """, (winner_id, tourney_id))

        elif stage == "Eliminator":
            # Winner goes to Qualifier 2 as Team B
            cursor.execute("""
                UPDATE matches SET team_b_id = ?
                WHERE tournament_id = ? AND stage = 'Qualifier 2'
            """, (winner_id, tourney_id))

        elif stage == "Qualifier 2":
            # Winner goes to Final as Team B
            cursor.execute("""
                UPDATE matches SET team_b_id = ?
                WHERE tournament_id = ? AND stage = 'Final'
            """, (winner_id, tourney_id))

        elif stage == "Qualifier":
            # For 3-team tournament: Winner goes to Final as Team B
            cursor.execute("""
                UPDATE matches SET team_b_id = ?
                WHERE tournament_id = ? AND stage = 'Final'
            """, (winner_id, tourney_id))

        if own_conn:
            conn.commit()
    finally:
        if own_conn:
            conn.close()

# ============================================================================
# CREX SCORECARD OPERATIONS (INDIVIDUAL PLAYER SCORES)
# ============================================================================

def auto_generate_crex_scorecard(match_id: int) -> None:
    """
    Intelligently generates realistic, mathematically consistent individual scores
    matching the team's total runs, wickets, and overs in authentic Crex app style.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if already generated
        cursor.execute("SELECT COUNT(*) FROM match_player_performances WHERE match_id = ?", (match_id,))
        if cursor.fetchone()[0] > 0:
            return

        cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
        match = cursor.fetchone()
        if not match or match["status"] != "Completed":
            return

        team_a_id = match["team_a_id"]
        team_b_id = match["team_b_id"]
        score_a = match["score_a"] or 0
        wickets_a = match["wickets_a"] or 0
        overs_a = match["overs_a"] or 20.0

        score_b = match["score_b"] or 0
        wickets_b = match["wickets_b"] or 0
        overs_b = match["overs_b"] or 20.0

        cursor.execute("SELECT * FROM players WHERE team_id = ? ORDER BY id ASC", (team_a_id,))
        team_a_players = [dict(p) for p in cursor.fetchall()]

        cursor.execute("SELECT * FROM players WHERE team_id = ? ORDER BY id ASC", (team_b_id,))
        team_b_players = [dict(p) for p in cursor.fetchall()]

        # Helper to synthesize players if team has fewer than 11
        def ensure_squad(players_list, team_id, default_prefix):
            result = list(players_list)
            needed = 11 - len(result)
            for i in range(1, needed + 1):
                result.append({
                    "id": 900000 + team_id * 100 + i,
                    "name": f"{default_prefix} Player {len(result) + 1}",
                    "role": "Batter" if i <= 4 else ("All-rounder" if i <= 6 else "Bowler"),
                    "team_id": team_id
                })
            return result

        team_a_squad = ensure_squad(team_a_players, team_a_id, "Team A")
        team_b_squad = ensure_squad(team_b_players, team_b_id, "Team B")

        # --- Generate Innings 1: Team A Bats, Team B Bowls ---
        inn1_batting, inn1_bowling = _synthesize_innings(
            batting_squad=team_a_squad,
            bowling_squad=team_b_squad,
            total_runs=score_a,
            wickets_lost=wickets_a,
            overs_faced=overs_a,
            match_id=match_id,
            innings_num=1
        )

        # --- Generate Innings 2: Team B Bats, Team A Bowls ---
        inn2_batting, inn2_bowling = _synthesize_innings(
            batting_squad=team_b_squad,
            bowling_squad=team_a_squad,
            total_runs=score_b,
            wickets_lost=wickets_b,
            overs_faced=overs_b,
            match_id=match_id,
            innings_num=2
        )

        # Insert all performances
        for p in inn1_batting + inn1_bowling + inn2_batting + inn2_bowling:
            cursor.execute("""
                INSERT INTO match_player_performances (
                    match_id, team_id, player_id, player_name, innings,
                    batting_order, runs, balls, fours, sixes, dismissal, is_out,
                    overs_bowled, maidens, runs_conceded, wickets, dot_balls
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["match_id"], p["team_id"], p["player_id"], p["player_name"], p["innings"],
                p.get("batting_order", 0), p.get("runs", 0), p.get("balls", 0),
                p.get("fours", 0), p.get("sixes", 0), p.get("dismissal", "not out"),
                p.get("is_out", 0), p.get("overs_bowled", 0.0), p.get("maidens", 0),
                p.get("runs_conceded", 0), p.get("wickets", 0), p.get("dot_balls", 0)
            ))

        # Determine Player of the Match
        winner_team_id = match["winner_id"] or team_a_id
        all_players = inn1_batting + inn1_bowling + inn2_batting + inn2_bowling
        winner_perfs = [p for p in all_players if p["team_id"] == winner_team_id]
        if not winner_perfs:
            winner_perfs = all_players

        def calc_impact(p):
            runs = p.get("runs", 0)
            wickets = p.get("wickets", 0)
            fours = p.get("fours", 0)
            sixes = p.get("sixes", 0)
            maidens = p.get("maidens", 0)
            return (runs * 1.0) + (fours * 0.5) + (sixes * 1.5) + (wickets * 28.0) + (maidens * 8.0)

        best_player = max(winner_perfs, key=calc_impact)
        mom_name = best_player["player_name"]
        runs = best_player.get("runs", 0)
        balls = best_player.get("balls", 0)
        wickets = best_player.get("wickets", 0)
        overs = best_player.get("overs_bowled", 0.0)
        runs_c = best_player.get("runs_conceded", 0)

        perf_parts = []
        if runs > 0:
            not_out = "*" if best_player.get("is_out", 0) == 0 else ""
            perf_parts.append(f"{runs}{not_out} ({balls}b)")
        if wickets > 0:
            perf_parts.append(f"{wickets}/{runs_c} ({overs} ov)")

        mom_perf = " & ".join(perf_parts) if perf_parts else "All-round contribution"

        cursor.execute("""
            UPDATE matches
            SET man_of_match = ?, man_of_match_performance = ?
            WHERE id = ?
        """, (mom_name, mom_perf, match_id))

        conn.commit()

def _synthesize_innings(batting_squad, bowling_squad, total_runs, wickets_lost, overs_faced, match_id, innings_num):
    """Internal helper to calculate balanced batting and bowling stats for an innings."""
    batting_team_id = batting_squad[0]["team_id"]
    bowling_team_id = bowling_squad[0]["team_id"]

    # Calculate extras (approx 4-8% of total runs)
    extras = max(4, min(16, int(total_runs * 0.06)))
    runs_from_bat = max(0, total_runs - extras)

    total_balls = int(overs_faced) * 6 + round((overs_faced - int(overs_faced)) * 10)
    if total_balls <= 0:
        total_balls = 120

    # Batters: determine how many batted
    num_batters = min(len(batting_squad), max(wickets_lost + 2, min(len(batting_squad), 4)))
    batters_playing = batting_squad[:num_batters]

    # Select bowlers from bowling team (typically bowlers and all-rounders)
    bowlers = [p for p in bowling_squad if p.get("role") in ("Bowler", "All-rounder")]
    if len(bowlers) < 4:
        bowlers = bowling_squad[max(0, len(bowling_squad)-5):]
    bowlers = bowlers[:5]

    # Distribute wickets among bowlers
    w_remaining = wickets_lost
    bowler_wickets = [0] * len(bowlers)
    for i in range(len(bowlers)):
        if w_remaining <= 0:
            break
        give = min(w_remaining, 2 if i < 2 else 1)
        bowler_wickets[i] = give
        w_remaining -= give
    if w_remaining > 0 and len(bowlers) > 0:
        bowler_wickets[0] += w_remaining

    # Generate dismissals for out batters
    out_dismissals = []
    bowler_idx = 0
    for i in range(wickets_lost):
        b_name = bowlers[bowler_idx % len(bowlers)]["name"]
        f_name = bowling_squad[(i + 1) % len(bowling_squad)]["name"]
        modes = [
            f"c {f_name} b {b_name}",
            f"b {b_name}",
            f"lbw b {b_name}",
            f"c & b {b_name}",
            f"run out ({f_name})"
        ]
        out_dismissals.append(modes[i % len(modes)])
        bowler_idx += 1

    # Distribute runs from bat among batters
    # Realistic weights: top-order scores more
    weights = [28, 26, 20, 14, 8, 4, 2, 1, 1, 1, 1][:num_batters]
    sum_w = sum(weights) or 1
    batter_runs = [int(runs_from_bat * (w / sum_w)) for w in weights]
    diff = runs_from_bat - sum(batter_runs)
    if diff != 0 and len(batter_runs) > 0:
        batter_runs[0] += diff

    # Distribute balls faced proportionally
    sum_r = sum(batter_runs) or 1
    batter_balls = [max(1, int(total_balls * (r / sum_r))) for r in batter_runs]
    balls_diff = total_balls - sum(batter_balls)
    if balls_diff != 0 and len(batter_balls) > 0:
        batter_balls[0] += balls_diff

    batting_records = []
    for idx, p in enumerate(batters_playing):
        r = max(0, batter_runs[idx])
        b = max(1, batter_balls[idx])
        is_out = 1 if idx < wickets_lost else 0
        dis = out_dismissals[idx] if is_out else "not out"
        # 4s and 6s
        sixes = min(r // 6, max(0, (r // 15)))
        rem_r = r - (sixes * 6)
        fours = min(rem_r // 4, max(0, (rem_r // 6)))

        batting_records.append({
            "match_id": match_id,
            "team_id": batting_team_id,
            "player_id": p["id"],
            "player_name": p["name"],
            "innings": innings_num,
            "batting_order": idx + 1,
            "runs": r,
            "balls": b,
            "fours": fours,
            "sixes": sixes,
            "dismissal": dis,
            "is_out": is_out
        })

    # Bowler records: distribute total runs conceded
    runs_to_concede = runs_from_bat
    runs_per_bowler = [runs_to_concede // len(bowlers)] * len(bowlers)
    r_rem = runs_to_concede - sum(runs_per_bowler)
    if r_rem != 0 and len(runs_per_bowler) > 0:
        runs_per_bowler[0] += r_rem

    overs_each = round(overs_faced / max(1, len(bowlers)), 1)
    bowling_records = []
    for idx, b in enumerate(bowlers):
        b_w = bowler_wickets[idx] if idx < len(bowler_wickets) else 0
        b_rc = runs_per_bowler[idx] if idx < len(runs_per_bowler) else 0
        maidens = 1 if (b_rc < 20 and b_w > 0 and idx == 0) else 0
        dots = max(4, int(overs_each * 3))

        bowling_records.append({
            "match_id": match_id,
            "team_id": bowling_team_id,
            "player_id": b["id"],
            "player_name": b["name"],
            "innings": innings_num,
            "overs_bowled": overs_each,
            "maidens": maidens,
            "runs_conceded": b_rc,
            "wickets": b_w,
            "dot_balls": dots
        })

    return batting_records, bowling_records

def get_match_scorecard(match_id: int) -> Dict[str, Any]:
    """Returns complete CREX-style individual player scorecard for a match."""
    match = get_match_by_id(match_id)
    if not match:
        raise ValueError("Match not found.")

    # Auto-generate if completed and performances are empty
    if match["status"] == "Completed":
        auto_generate_crex_scorecard(match_id)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM match_player_performances
            WHERE match_id = ?
            ORDER BY innings ASC, batting_order ASC, wickets DESC, runs_conceded ASC;
        """, (match_id,))
        rows = [dict(r) for r in cursor.fetchall()]

        # Squad players to compute 'Yet to Bat'
        cursor.execute("SELECT id, name FROM players WHERE team_id = ? ORDER BY id ASC", (match["team_a_id"],))
        squad_a = [dict(p) for p in cursor.fetchall()]
        cursor.execute("SELECT id, name FROM players WHERE team_id = ? ORDER BY id ASC", (match["team_b_id"],))
        squad_b = [dict(p) for p in cursor.fetchall()]

    # Ensure Player of the Match is populated
    if not match.get("man_of_match") and rows:
        winner_team_id = match.get("winner_id") or match["team_a_id"]
        winner_perfs = [p for p in rows if p["team_id"] == winner_team_id] or rows
        def calc_impact(p):
            return (p.get("runs", 0) * 1.0) + (p.get("fours", 0) * 0.5) + (p.get("sixes", 0) * 1.5) + (p.get("wickets", 0) * 28.0) + (p.get("maidens", 0) * 8.0)
        best = max(winner_perfs, key=calc_impact)
        match["man_of_match"] = best["player_name"]
        perf_parts = []
        if best.get("runs", 0) > 0:
            not_out = "*" if best.get("is_out", 0) == 0 else ""
            perf_parts.append(f"{best['runs']}{not_out} ({best['balls']}b)")
        if best.get("wickets", 0) > 0:
            perf_parts.append(f"{best['wickets']}/{best['runs_conceded']} ({best['overs_bowled']} ov)")
        match["man_of_match_performance"] = " & ".join(perf_parts) if perf_parts else "Match Impact"

    def format_innings(inn_num, team_id, team_name, score, wickets, overs, squad):
        batted_rows = [r for r in rows if r["innings"] == inn_num and r["team_id"] == team_id and (r["batting_order"] > 0 or r["balls"] > 0 or r["runs"] > 0)]
        bowled_rows = [r for r in rows if r["innings"] == inn_num and r["team_id"] != team_id and (r["overs_bowled"] > 0 or r["runs_conceded"] > 0 or r["wickets"] > 0)]

        batting = []
        batted_player_ids = set()
        for r in batted_rows:
            batted_player_ids.add(r["player_id"])
            sr = round((r["runs"] / r["balls"] * 100.0), 2) if r["balls"] > 0 else 0.0
            batting.append({
                "player_id": r["player_id"],
                "player_name": r["player_name"],
                "batting_order": r["batting_order"],
                "runs": r["runs"],
                "balls": r["balls"],
                "fours": r["fours"],
                "sixes": r["sixes"],
                "dismissal": r["dismissal"],
                "is_out": bool(r["is_out"]),
                "strike_rate": sr
            })

        bowling = []
        for r in bowled_rows:
            ov = r["overs_bowled"]
            dec_ov = int(ov) + round((ov - int(ov)) * 10) / 6.0
            econ = round((r["runs_conceded"] / dec_ov), 2) if dec_ov > 0 else 0.0
            bowling.append({
                "player_id": r["player_id"],
                "player_name": r["player_name"],
                "overs_bowled": r["overs_bowled"],
                "maidens": r["maidens"],
                "runs_conceded": r["runs_conceded"],
                "wickets": r["wickets"],
                "economy": econ,
                "dot_balls": r["dot_balls"]
            })

        did_not_bat = [p["name"] for p in squad if p["id"] not in batted_player_ids]
        dec_total_ov = int(overs or 20) + round(((overs or 20) - int(overs or 20)) * 10) / 6.0
        run_rate = round(((score or 0) / dec_total_ov), 2) if dec_total_ov > 0 else 0.0
        extras = max(4, (score or 0) - sum(b["runs"] for b in batting))

        return {
            "team_id": team_id,
            "team_name": team_name,
            "score": score or 0,
            "wickets": wickets or 0,
            "overs": overs or 0.0,
            "run_rate": run_rate,
            "extras": max(0, extras),
            "batting": batting,
            "bowling": bowling,
            "did_not_bat": did_not_bat
        }

    return {
        "match": match,
        "innings1": format_innings(1, match["team_a_id"], match["team_a_name"], match["score_a"], match["wickets_a"], match["overs_a"], squad_a),
        "innings2": format_innings(2, match["team_b_id"], match["team_b_name"], match["score_b"], match["wickets_b"], match["overs_b"], squad_b)
    }

def save_match_scorecard(match_id: int, payload: Dict[str, Any]) -> None:
    """Updates custom individual player scorecard entries."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM match_player_performances WHERE match_id = ?", (match_id,))

        players = payload.get("performances", [])
        for p in players:
            cursor.execute("""
                INSERT INTO match_player_performances (
                    match_id, team_id, player_id, player_name, innings,
                    batting_order, runs, balls, fours, sixes, dismissal, is_out,
                    overs_bowled, maidens, runs_conceded, wickets, dot_balls
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_id, p["team_id"], p["player_id"], p["player_name"], p["innings"],
                p.get("batting_order", 0), p.get("runs", 0), p.get("balls", 0),
                p.get("fours", 0), p.get("sixes", 0), p.get("dismissal", "not out"),
                p.get("is_out", 0), p.get("overs_bowled", 0.0), p.get("maidens", 0),
                p.get("runs_conceded", 0), p.get("wickets", 0), p.get("dot_balls", 0)
            ))
        conn.commit()

def get_tournament_player_stats(tournament_id: int) -> Dict[str, Any]:
    """Computes CREX Leaderboards: Orange Cap (Most Runs) and Purple Cap (Most Wickets)."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Orange Cap: Top Run Scorers
        cursor.execute("""
            SELECT 
                p.player_id, p.player_name, t.name as team_name,
                COUNT(DISTINCT p.match_id) as matches,
                SUM(CASE WHEN p.balls > 0 OR p.runs > 0 THEN 1 ELSE 0 END) as innings,
                SUM(p.runs) as total_runs,
                SUM(p.balls) as total_balls,
                SUM(p.fours) as total_fours,
                SUM(p.sixes) as total_sixes,
                MAX(p.runs) as highest_score,
                SUM(p.is_out) as dismissals
            FROM match_player_performances p
            JOIN matches m ON p.match_id = m.id
            JOIN teams t ON p.team_id = t.id
            WHERE m.tournament_id = ?
            GROUP BY p.player_id, p.player_name, t.name
            HAVING total_runs > 0
            ORDER BY total_runs DESC, total_sixes DESC
            LIMIT 10;
        """, (tournament_id,))
        bat_rows = cursor.fetchall()
        orange_cap = []
        for rank, r in enumerate(bat_rows, 1):
            runs = r["total_runs"]
            balls = r["total_balls"]
            dismissals = r["dismissals"]
            sr = round((runs / balls * 100.0), 2) if balls > 0 else 0.0
            avg = round((runs / dismissals), 2) if dismissals > 0 else float(runs)
            orange_cap.append({
                "rank": rank,
                "player_id": r["player_id"],
                "player_name": r["player_name"],
                "team_name": r["team_name"],
                "matches": r["matches"],
                "innings": r["innings"],
                "runs": runs,
                "balls": balls,
                "fours": r["total_fours"],
                "sixes": r["total_sixes"],
                "highest_score": r["highest_score"],
                "strike_rate": sr,
                "average": avg
            })

        # Purple Cap: Top Wicket Takers
        cursor.execute("""
            SELECT 
                p.player_id, p.player_name, t.name as team_name,
                COUNT(DISTINCT p.match_id) as matches,
                SUM(p.wickets) as total_wickets,
                SUM(p.overs_bowled) as total_overs,
                SUM(p.maidens) as total_maidens,
                SUM(p.runs_conceded) as total_runs_conceded,
                MAX(p.wickets) as best_wickets
            FROM match_player_performances p
            JOIN matches m ON p.match_id = m.id
            JOIN teams t ON p.team_id = t.id
            WHERE m.tournament_id = ?
            GROUP BY p.player_id, p.player_name, t.name
            HAVING total_wickets > 0
            ORDER BY total_wickets DESC, total_runs_conceded ASC
            LIMIT 10;
        """, (tournament_id,))
        bowl_rows = cursor.fetchall()
        purple_cap = []
        for rank, r in enumerate(bowl_rows, 1):
            w = r["total_wickets"]
            ov = r["total_overs"]
            rc = r["total_runs_conceded"]
            dec_ov = int(ov) + round((ov - int(ov)) * 10) / 6.0
            econ = round((rc / dec_ov), 2) if dec_ov > 0 else 0.0
            purple_cap.append({
                "rank": rank,
                "player_id": r["player_id"],
                "player_name": r["player_name"],
                "team_name": r["team_name"],
                "matches": r["matches"],
                "wickets": w,
                "overs": ov,
                "maidens": r["total_maidens"],
                "runs_conceded": rc,
                "economy": econ,
                "best_wickets": r["best_wickets"]
            })

        return {
            "orange_cap": orange_cap,
            "purple_cap": purple_cap
        }

# ============================================================================
# STATS OPERATIONS
# ============================================================================

def get_dashboard_summary() -> Dict[str, int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM teams")
        total_teams = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM players")
        total_players = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tournaments")
        total_tournaments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM matches WHERE status = 'Completed'")
        total_completed_matches = cursor.fetchone()[0]

        return {
            "total_teams": total_teams,
            "total_players": total_players,
            "total_tournaments": total_tournaments,
            "total_completed_matches": total_completed_matches
        }
