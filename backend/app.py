import os
import sys
import json
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from typing import Dict, Any, List

# Ensure current backend directory is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
CPP_ENGINE_DIR = os.path.join(BASE_DIR, "cpp_engine")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import database

# Initialize Flask App
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

# Locate compiled C++ engine executable
ENGINE_EXE_NAME = "engine.exe" if os.name == "nt" else "engine"
ENGINE_PATH = os.path.join(CPP_ENGINE_DIR, ENGINE_EXE_NAME)

# ============================================================================
# C++ ENGINE INTEGRATION VIA SUBPROCESS
# ============================================================================

def run_cpp_engine(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the compiled C++ OOP engine via Python subprocess,
    passing structured JSON data and receiving JSON results.
    If execution is blocked by OS environment policies (e.g. Windows Device Guard),
    it falls back to mirror C++ OOP logic seamlessly.
    """
    json_input = json.dumps(payload)

    if os.path.exists(ENGINE_PATH):
        try:
            # Invoke C++ executable
            result = subprocess.run(
                [ENGINE_PATH, command, json_input],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout.strip())
                    data["engine_source"] = "C++ OOP Engine (Compiled Binary)"
                    return data
                except json.JSONDecodeError:
                    pass
            else:
                print(f"[C++ Subprocess Notice] Return code: {result.returncode}, Stderr: {result.stderr.strip()}")
        except Exception as e:
            print(f"[C++ Subprocess Notice] Execution policy / error: {e}")

    # Fallback to Mirrored C++ Logic if binary execution is restricted by OS Device Guard
    return mirrored_cpp_engine_logic(command, payload)

def mirrored_cpp_engine_logic(command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Faithful Python mirror of the C++ OOP engine classes (Player, Team, Match, Tournament)
    ensuring 100% functionality even when OS policy blocks unsigned binaries.
    """
    if command in ("--fixtures", "-f"):
        teams = payload.get("teams", [])
        if len(teams) < 2:
            return {"status": "error", "message": "At least two teams are required to create a tournament."}
        
        fixtures = []
        match_number = 1
        n = len(teams)
        format_ = payload.get("format", "T20")
        
        # Round Robin algorithm: each pair plays once
        for i in range(n):
            for j in range(i + 1, n):
                fixtures.append({
                    "match_number": match_number,
                    "format": format_,
                    "team_a_id": teams[i]["id"],
                    "team_a_name": teams[i]["name"],
                    "team_b_id": teams[j]["id"],
                    "team_b_name": teams[j]["name"]
                })
                match_number += 1
                
        return {
            "status": "success",
            "tournament_id": payload.get("tournament_id", 1),
            "tournament_name": payload.get("tournament_name", "Tournament"),
            "format": format_,
            "total_fixtures": len(fixtures),
            "fixtures": fixtures,
            "engine_source": "C++ OOP Engine (Mirrored Fallback)"
        }

    elif command in ("--calculate-result", "--result", "-r"):
        format_ = payload.get("format", "T20")
        score_a = int(payload.get("score_a", 0))
        wickets_a = int(payload.get("wickets_a", 0))
        overs_a = float(payload.get("overs_a", 0.0))
        score_b = int(payload.get("score_b", 0))
        wickets_b = int(payload.get("wickets_b", 0))
        overs_b = float(payload.get("overs_b", 0.0))
        team_a_name = payload.get("team_a_name", "Team A")
        team_b_name = payload.get("team_b_name", "Team B")
        team_a_id = payload.get("team_a_id", 1)
        team_b_id = payload.get("team_b_id", 2)

        if score_a > score_b:
            winner_id = team_a_id
            winner_name = team_a_name
            loser_id = team_b_id
            loser_name = team_b_name
            is_tie = False
            margin = score_a - score_b
            result_description = f"{winner_name} won by {margin} runs ({format_})"
        elif score_b > score_a:
            winner_id = team_b_id
            winner_name = team_b_name
            loser_id = team_a_id
            loser_name = team_a_name
            is_tie = False
            wickets_left = max(1, 10 - wickets_b)
            result_description = f"{winner_name} won by {wickets_left} wickets ({format_})"
        else:
            winner_id = 0
            winner_name = "Tie"
            loser_id = 0
            loser_name = ""
            is_tie = True
            result_description = f"Match ended in a Tie! Both teams scored {score_a} runs ({format_})"

        return {
            "status": "success",
            "match": {
                "match_id": payload.get("match_id", 1),
                "format": format_,
                "team_a_id": team_a_id,
                "team_a_name": team_a_name,
                "team_b_id": team_b_id,
                "team_b_name": team_b_name,
                "score_a": score_a,
                "wickets_a": wickets_a,
                "overs_a": overs_a,
                "score_b": score_b,
                "wickets_b": wickets_b,
                "overs_b": overs_b,
                "is_completed": True,
                "is_tie": is_tie,
                "winner_id": winner_id,
                "winner_name": winner_name,
                "loser_id": loser_id,
                "loser_name": loser_name,
                "result_description": result_description
            },
            "engine_source": "C++ OOP Engine (Mirrored Fallback)"
        }

    elif command in ("--points-table", "--standings", "-p"):
        teams = payload.get("teams", [])
        matches = payload.get("matches", [])

        standings = {}
        for t in teams:
            standings[t["id"]] = {
                "team_id": t["id"],
                "team_name": t["name"],
                "played": 0,
                "won": 0,
                "lost": 0,
                "tied": 0,
                "points": 0
            }

        for m in matches:
            if not m.get("is_completed", True):
                continue
            ta_id = m.get("team_a_id")
            tb_id = m.get("team_b_id")
            if ta_id in standings and tb_id in standings:
                standings[ta_id]["played"] += 1
                standings[tb_id]["played"] += 1
                if m.get("is_tie", False):
                    standings[ta_id]["tied"] += 1
                    standings[ta_id]["points"] += 1
                    standings[tb_id]["tied"] += 1
                    standings[tb_id]["points"] += 1
                elif m.get("winner_id") == ta_id:
                    standings[ta_id]["won"] += 1
                    standings[ta_id]["points"] += 2
                    standings[tb_id]["lost"] += 1
                elif m.get("winner_id") == tb_id:
                    standings[tb_id]["won"] += 1
                    standings[tb_id]["points"] += 2
                    standings[ta_id]["lost"] += 1

        # Sort criteria: 1. Points desc, 2. Wins desc, 3. Team name asc
        table = list(standings.values())
        table.sort(key=lambda x: (-x["points"], -x["won"], x["team_name"].lower()))

        for rank, row in enumerate(table, start=1):
            row["rank"] = rank

        return {
            "status": "success",
            "tournament_id": payload.get("tournament_id", 1),
            "tournament_name": payload.get("tournament_name", "Tournament"),
            "format": payload.get("format", "T20"),
            "points_table": table,
            "engine_source": "C++ OOP Engine (Mirrored Fallback)"
        }

    return {"status": "error", "message": f"Unknown command {command}"}

# ============================================================================
# STATIC / FRONTEND ROUTES
# ============================================================================

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# ============================================================================
# DASHBOARD API
# ============================================================================

@app.route("/api/dashboard/stats", methods=["GET"])
def get_stats():
    try:
        stats = database.get_dashboard_summary()
        stats["engine_binary_exists"] = os.path.exists(ENGINE_PATH)
        return jsonify({"status": "success", "data": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================================
# TEAMS API
# ============================================================================

@app.route("/api/teams", methods=["GET"])
def list_teams():
    try:
        teams = database.get_all_teams()
        return jsonify({"status": "success", "data": teams})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/teams", methods=["POST"])
def create_team():
    try:
        data = request.get_json() or {}
        name = data.get("name")
        if not name or not name.strip():
            return jsonify({"status": "error", "message": "Team name is required."}), 400
        team = database.add_team(name)
        return jsonify({"status": "success", "data": team}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return jsonify({"status": "error", "message": "A team with this name already exists."}), 400
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/teams/<int:team_id>", methods=["DELETE"])
def remove_team(team_id):
    try:
        deleted = database.delete_team(team_id)
        if deleted:
            return jsonify({"status": "success", "message": "Team deleted successfully."})
        return jsonify({"status": "error", "message": "Team not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================================
# PLAYERS API
# ============================================================================

@app.route("/api/players", methods=["GET"])
def list_players():
    try:
        team_id = request.args.get("team_id", type=int)
        players = database.get_all_players(team_id)
        return jsonify({"status": "success", "data": players})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/players", methods=["POST"])
def create_player():
    try:
        data = request.get_json() or {}
        name = data.get("name")
        role = data.get("role")
        team_id = data.get("team_id")

        if not name or not role or not team_id:
            return jsonify({"status": "error", "message": "Player name, role, and team_id are required."}), 400

        player = database.add_player(name, role, int(team_id))
        return jsonify({"status": "success", "data": player}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/players/<int:player_id>", methods=["DELETE"])
def remove_player(player_id):
    try:
        deleted = database.delete_player(player_id)
        if deleted:
            return jsonify({"status": "success", "message": "Player deleted successfully."})
        return jsonify({"status": "error", "message": "Player not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================================
# TOURNAMENTS & AUTOMATIC FIXTURE GENERATION
# ============================================================================

@app.route("/api/tournaments", methods=["GET"])
def list_tournaments():
    try:
        tournaments = database.get_all_tournaments()
        return jsonify({"status": "success", "data": tournaments})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/tournaments/<int:tournament_id>", methods=["GET"])
def get_tournament_details(tournament_id):
    try:
        tournament = database.get_tournament_by_id(tournament_id)
        if not tournament:
            return jsonify({"status": "error", "message": "Tournament not found."}), 404
        return jsonify({"status": "success", "data": tournament})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/tournaments", methods=["POST"])
def create_tournament():
    try:
        data = request.get_json() or {}
        name = data.get("name")
        format_ = data.get("format", "T20")
        team_ids = data.get("team_ids", [])

        if not name or not name.strip():
            return jsonify({"status": "error", "message": "Tournament name is required."}), 400

        if len(team_ids) < 2:
            return jsonify({"status": "error", "message": "Cannot create tournament with fewer than two teams."}), 400

        # Step 1: Save Tournament in SQLite
        tournament = database.create_tournament(name, format_, team_ids)

        # Step 2: Invoke C++ OOP Engine to automatically generate Round-Robin Fixtures
        engine_payload = {
            "tournament_id": tournament["id"],
            "tournament_name": tournament["name"],
            "format": tournament["format"],
            "teams": tournament["teams"]
        }
        engine_response = run_cpp_engine("--fixtures", engine_payload)

        if engine_response.get("status") == "success":
            fixtures = engine_response.get("fixtures", [])
            # Step 3: Persist generated fixtures to SQLite matches table
            database.save_tournament_fixtures(tournament["id"], format_, fixtures)
            tournament["fixtures"] = fixtures
            tournament["engine_source"] = engine_response.get("engine_source")
            return jsonify({"status": "success", "data": tournament}), 201
        else:
            return jsonify({"status": "error", "message": engine_response.get("message", "Fixture generation failed.")}), 500

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/tournaments/<int:tournament_id>", methods=["DELETE"])
def remove_tournament(tournament_id):
    try:
        deleted = database.delete_tournament(tournament_id)
        if deleted:
            return jsonify({"status": "success", "message": "Tournament deleted successfully."})
        return jsonify({"status": "error", "message": "Tournament not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================================
# MATCHES & SCORE CALCULATION VIA C++ ENGINE
# ============================================================================

@app.route("/api/tournaments/<int:tournament_id>/matches", methods=["GET"])
def list_tournament_matches(tournament_id):
    try:
        matches = database.get_tournament_matches(tournament_id)
        return jsonify({"status": "success", "data": matches})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/matches/<int:match_id>/score", methods=["POST"])
def submit_match_score(match_id):
    try:
        match_record = database.get_match_by_id(match_id)
        if not match_record:
            return jsonify({"status": "error", "message": "Match not found."}), 404

        data = request.get_json() or {}
        score_a = int(data.get("score_a", 0))
        wickets_a = int(data.get("wickets_a", 0))
        overs_a = float(data.get("overs_a", 20.0))

        score_b = int(data.get("score_b", 0))
        wickets_b = int(data.get("wickets_b", 0))
        overs_b = float(data.get("overs_b", 20.0))

        # Pass scores to C++ OOP Engine to calculate winner and result
        engine_payload = {
            "match_id": match_id,
            "format": match_record["format"],
            "team_a_id": match_record["team_a_id"],
            "team_a_name": match_record["team_a_name"],
            "team_b_id": match_record["team_b_id"],
            "team_b_name": match_record["team_b_name"],
            "score_a": score_a,
            "wickets_a": wickets_a,
            "overs_a": overs_a,
            "score_b": score_b,
            "wickets_b": wickets_b,
            "overs_b": overs_b
        }

        engine_response = run_cpp_engine("--calculate-result", engine_payload)
        if engine_response.get("status") == "success":
            calc_match = engine_response.get("match", {})
            winner_id = calc_match.get("winner_id")
            if winner_id == 0:
                winner_id = None
            is_tie = calc_match.get("is_tie", False)
            result_desc = calc_match.get("result_description", "")

            # Save in SQLite
            database.update_match_result(
                match_id=match_id,
                score_a=score_a,
                wickets_a=wickets_a,
                overs_a=overs_a,
                score_b=score_b,
                wickets_b=wickets_b,
                overs_b=overs_b,
                winner_id=winner_id,
                is_tie=is_tie,
                result_description=result_desc
            )

            return jsonify({
                "status": "success",
                "data": calc_match,
                "engine_source": engine_response.get("engine_source")
            })
        else:
            return jsonify({"status": "error", "message": "Failed to calculate match result."}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================================
# POINTS TABLE API VIA C++ ENGINE
# ============================================================================

@app.route("/api/tournaments/<int:tournament_id>/standings", methods=["GET"])
def get_tournament_standings(tournament_id):
    try:
        tourney = database.get_tournament_by_id(tournament_id)
        if not tourney:
            return jsonify({"status": "error", "message": "Tournament not found."}), 404

        matches = database.get_tournament_matches(tournament_id)

        # Build payload for C++ Engine
        engine_payload = {
            "tournament_id": tourney["id"],
            "tournament_name": tourney["name"],
            "format": tourney["format"],
            "teams": tourney["teams"],
            "matches": [
                {
                    "team_a_id": m["team_a_id"],
                    "team_b_id": m["team_b_id"],
                    "score_a": m["score_a"] or 0,
                    "score_b": m["score_b"] or 0,
                    "winner_id": m["winner_id"] or 0,
                    "is_tie": bool(m["is_tie"]),
                    "is_completed": (m["status"] == "Completed")
                }
                for m in matches
            ]
        }

        # Invoke C++ OOP Engine to calculate points table with strict ranking rules
        engine_response = run_cpp_engine("--points-table", engine_payload)

        if engine_response.get("status") == "success":
            return jsonify({
                "status": "success",
                "data": {
                    "tournament": tourney,
                    "standings": engine_response.get("points_table", []),
                    "engine_source": engine_response.get("engine_source")
                }
            })
        else:
            return jsonify({"status": "error", "message": "Failed to calculate points table."}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================================
# DEMO SEED DATA (HELPFUL FOR COLLEGE PRESENTATION & EVALUATION)
# ============================================================================

@app.route("/api/demo/seed", methods=["POST"])
def seed_demo_data():
    """Populates standard international cricket teams and players for quick demonstration."""
    try:
        sample_teams = [
            {
                "name": "India",
                "players": [
                    ("Rohit Sharma", "Batter"),
                    ("Virat Kohli", "Batter"),
                    ("Hardik Pandya", "All-rounder"),
                    ("Jasprit Bumrah", "Bowler"),
                    ("Rishabh Pant", "Wicket-keeper")
                ]
            },
            {
                "name": "Australia",
                "players": [
                    ("Pat Cummins", "Bowler"),
                    ("Travis Head", "Batter"),
                    ("Glenn Maxwell", "All-rounder"),
                    ("Mitchell Starc", "Bowler"),
                    ("Josh Inglis", "Wicket-keeper")
                ]
            },
            {
                "name": "England",
                "players": [
                    ("Jos Buttler", "Wicket-keeper"),
                    ("Harry Brook", "Batter"),
                    ("Ben Stokes", "All-rounder"),
                    ("Jofra Archer", "Bowler"),
                    ("Adil Rashid", "Bowler")
                ]
            },
            {
                "name": "South Africa",
                "players": [
                    ("Aiden Markram", "Batter"),
                    ("Heinrich Klaasen", "Wicket-keeper"),
                    ("Marco Jansen", "All-rounder"),
                    ("Kagiso Rabada", "Bowler"),
                    ("David Miller", "Batter")
                ]
            }
        ]

        created_team_ids = []
        for t_info in sample_teams:
            try:
                t = database.add_team(t_info["name"])
                created_team_ids.append(t["id"])
                for p_name, p_role in t_info["players"]:
                    database.add_player(p_name, p_role, t["id"])
            except Exception:
                # Team may already exist
                existing = [x for x in database.get_all_teams() if x["name"].lower() == t_info["name"].lower()]
                if existing:
                    created_team_ids.append(existing[0]["id"])

        # Auto-create sample tournament if none exists
        tourneys = database.get_all_tournaments()
        if not tourneys and len(created_team_ids) >= 4:
            tourney = database.create_tournament("ICC Super 4 Champions Cup", "T20", created_team_ids[:4])
            engine_payload = {
                "tournament_id": tourney["id"],
                "tournament_name": tourney["name"],
                "format": "T20",
                "teams": tourney["teams"]
            }
            engine_response = run_cpp_engine("--fixtures", engine_payload)
            if engine_response.get("status") == "success":
                database.save_tournament_fixtures(tourney["id"], "T20", engine_response["fixtures"])

        return jsonify({"status": "success", "message": "Demo sample teams, players, and fixtures initialized!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================================
# APP ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    database.init_db()
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print("CRICKET TOURNAMENT MANAGEMENT SYSTEM - BACKEND READY")
    print(f"Server running at: http://127.0.0.1:{port}")
    print(f"C++ Engine Binary: {ENGINE_PATH} (Exists: {os.path.exists(ENGINE_PATH)})")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=True)
