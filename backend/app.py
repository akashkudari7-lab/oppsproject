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
        format_ = payload.get("format", "T20").upper()
        max_overs = 20.0
        if format_ == "ODI":
            max_overs = 50.0
        elif format_ == "TEST":
            max_overs = 90.0

        standings = {}
        for t in teams:
            standings[t["id"]] = {
                "team_id": t["id"],
                "team_name": t["name"],
                "played": 0,
                "won": 0,
                "lost": 0,
                "tied": 0,
                "points": 0,
                "nrr": 0.0,
                "runs_scored": 0,
                "overs_faced": 0.0,
                "runs_conceded": 0,
                "overs_bowled": 0.0
            }

        def to_decimal_overs(overs_val: float) -> float:
            full_overs = int(overs_val)
            fraction = overs_val - full_overs
            balls = round(fraction * 10.0)
            if balls >= 6:
                full_overs += balls // 6
                balls = balls % 6
            return full_overs + (balls / 6.0)

        for m in matches:
            if not m.get("is_completed", True) or m.get("is_playoff", False):
                continue
            ta_id = m.get("team_a_id")
            tb_id = m.get("team_b_id")
            if ta_id in standings and tb_id in standings:
                team_a = standings[ta_id]
                team_b = standings[tb_id]
                team_a["played"] += 1
                team_b["played"] += 1
                if m.get("is_tie", False):
                    team_a["tied"] += 1
                    team_a["points"] += 1
                    team_b["tied"] += 1
                    team_b["points"] += 1
                elif m.get("winner_id") == ta_id:
                    team_a["won"] += 1
                    team_a["points"] += 2
                    team_b["lost"] += 1
                elif m.get("winner_id") == tb_id:
                    team_b["won"] += 1
                    team_b["points"] += 2
                    team_a["lost"] += 1

                # Net Run Rate calculation
                score_a = int(m.get("score_a", 0) or 0)
                wickets_a = int(m.get("wickets_a", 0) or 0)
                raw_ov_a = float(m.get("overs_a", 0.0) or 0.0)
                eff_ov_a = to_decimal_overs(raw_ov_a)
                if wickets_a >= 10 and max_overs > 0.0 and format_ != "TEST":
                    eff_ov_a = max_overs
                if eff_ov_a <= 0.0:
                    eff_ov_a = raw_ov_a if raw_ov_a > 0.0 else max_overs

                score_b = int(m.get("score_b", 0) or 0)
                wickets_b = int(m.get("wickets_b", 0) or 0)
                raw_ov_b = float(m.get("overs_b", 0.0) or 0.0)
                eff_ov_b = to_decimal_overs(raw_ov_b)
                if wickets_b >= 10 and max_overs > 0.0 and format_ != "TEST":
                    eff_ov_b = max_overs
                if eff_ov_b <= 0.0:
                    eff_ov_b = raw_ov_b if raw_ov_b > 0.0 else max_overs

                team_a["runs_scored"] += score_a
                team_a["overs_faced"] += eff_ov_a
                team_a["runs_conceded"] += score_b
                team_a["overs_bowled"] += eff_ov_b

                team_b["runs_scored"] += score_b
                team_b["overs_faced"] += eff_ov_b
                team_b["runs_conceded"] += score_a
                team_b["overs_bowled"] += eff_ov_a

        # Compute NRR for each team
        for s in standings.values():
            rf = (s["runs_scored"] / s["overs_faced"]) if s["overs_faced"] > 0 else 0.0
            ra = (s["runs_conceded"] / s["overs_bowled"]) if s["overs_bowled"] > 0 else 0.0
            s["nrr"] = round(rf - ra, 3)

        # Sort criteria: 1. Points desc, 2. Wins desc, 3. NRR desc, 4. Team name asc
        table = list(standings.values())
        table.sort(key=lambda x: (-x["points"], -x["won"], -x["nrr"], x["team_name"].lower()))

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

    elif command in ("--qualifiers", "-q"):
        standings = payload.get("standings", [])
        starting_match_number = int(payload.get("starting_match_number", 1))
        qualifiers = []
        m_num = starting_match_number

        if len(standings) >= 4:
            qualifiers.append({
                "match_number": m_num,
                "stage": "Qualifier 1",
                "team_a_id": standings[0]["team_id"],
                "team_a_name": standings[0]["team_name"],
                "team_b_id": standings[1]["team_id"],
                "team_b_name": standings[1]["team_name"],
                "team_a_source": "Rank 1",
                "team_b_source": "Rank 2",
                "description": "Winner advances to Grand Final; Loser to Qualifier 2."
            })
            m_num += 1
            qualifiers.append({
                "match_number": m_num,
                "stage": "Eliminator",
                "team_a_id": standings[2]["team_id"],
                "team_a_name": standings[2]["team_name"],
                "team_b_id": standings[3]["team_id"],
                "team_b_name": standings[3]["team_name"],
                "team_a_source": "Rank 3",
                "team_b_source": "Rank 4",
                "description": "Winner advances to Qualifier 2; Loser is eliminated."
            })
            m_num += 1
            qualifiers.append({
                "match_number": m_num,
                "stage": "Qualifier 2",
                "team_a_id": standings[1]["team_id"],
                "team_a_name": f"{standings[1]['team_name']} (Loser Q1)",
                "team_b_id": standings[2]["team_id"],
                "team_b_name": f"{standings[2]['team_name']} (Winner Elim)",
                "team_a_source": "Loser Q1",
                "team_b_source": "Winner Eliminator",
                "description": "Winner advances to Grand Final; Loser is eliminated."
            })
            m_num += 1
            qualifiers.append({
                "match_number": m_num,
                "stage": "Final",
                "team_a_id": standings[0]["team_id"],
                "team_a_name": f"{standings[0]['team_name']} (Winner Q1)",
                "team_b_id": standings[1]["team_id"],
                "team_b_name": f"{standings[1]['team_name']} (Winner Q2)",
                "team_a_source": "Winner Q1",
                "team_b_source": "Winner Q2",
                "description": "Grand Finale - Winner is crowned Tournament Champion!"
            })
        elif len(standings) == 3:
            qualifiers.append({
                "match_number": m_num,
                "stage": "Qualifier",
                "team_a_id": standings[1]["team_id"],
                "team_a_name": standings[1]["team_name"],
                "team_b_id": standings[2]["team_id"],
                "team_b_name": standings[2]["team_name"],
                "team_a_source": "Rank 2",
                "team_b_source": "Rank 3",
                "description": "Winner advances to Grand Final."
            })
            m_num += 1
            qualifiers.append({
                "match_number": m_num,
                "stage": "Final",
                "team_a_id": standings[0]["team_id"],
                "team_a_name": standings[0]["team_name"],
                "team_b_id": standings[1]["team_id"],
                "team_b_name": f"{standings[1]['team_name']} (Winner Qualifier)",
                "team_a_source": "Rank 1",
                "team_b_source": "Winner Qualifier",
                "description": "Grand Finale - Winner is crowned Tournament Champion!"
            })
        elif len(standings) == 2:
            qualifiers.append({
                "match_number": m_num,
                "stage": "Final",
                "team_a_id": standings[0]["team_id"],
                "team_a_name": standings[0]["team_name"],
                "team_b_id": standings[1]["team_id"],
                "team_b_name": standings[1]["team_name"],
                "team_a_source": "Rank 1",
                "team_b_source": "Rank 2",
                "description": "Grand Finale - Winner is crowned Tournament Champion!"
            })

        return {
            "status": "success",
            "tournament_id": payload.get("tournament_id", 1),
            "qualifiers": qualifiers,
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

@app.route("/api/matches/<int:match_id>", methods=["DELETE"])
def delete_match(match_id):
    try:
        deleted = database.delete_match(match_id)
        if deleted:
            return jsonify({"status": "success", "message": "Match deleted successfully."})
        return jsonify({"status": "error", "message": "Match not found."}), 404
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

        # Build payload for C++ Engine with full overs and wickets for Net Run Rate (NRR)
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
                    "wickets_a": m.get("wickets_a", 0) or 0,
                    "wickets_b": m.get("wickets_b", 0) or 0,
                    "overs_a": m.get("overs_a", 0.0) or 0.0,
                    "overs_b": m.get("overs_b", 0.0) or 0.0,
                    "stage": m.get("stage", "Group"),
                    "is_playoff": bool(m.get("is_playoff", False)),
                    "winner_id": m["winner_id"] or 0,
                    "is_tie": bool(m["is_tie"]),
                    "is_completed": (m["status"] == "Completed")
                }
                for m in matches
            ]
        }

        # Invoke C++ OOP Engine to calculate points table with ICC ranking rules & NRR
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
# PLAYOFFS & QUALIFIER MATCHES API
# ============================================================================

@app.route("/api/tournaments/<int:tournament_id>/qualifiers/generate", methods=["POST"])
def generate_tournament_qualifiers(tournament_id):
    """
    Generates IPL / ICC style Qualifier & Playoff fixtures based on the top 4 teams
    from the tournament points table (Qualifier 1, Eliminator, Qualifier 2, Final).
    """
    try:
        tourney = database.get_tournament_by_id(tournament_id)
        if not tourney:
            return jsonify({"status": "error", "message": "Tournament not found."}), 404

        matches = database.get_tournament_matches(tournament_id)

        # 1. Fetch current standings from C++ engine to get accurate top teams
        standings_payload = {
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
                    "wickets_a": m.get("wickets_a", 0) or 0,
                    "wickets_b": m.get("wickets_b", 0) or 0,
                    "overs_a": m.get("overs_a", 0.0) or 0.0,
                    "overs_b": m.get("overs_b", 0.0) or 0.0,
                    "stage": m.get("stage", "Group"),
                    "is_playoff": bool(m.get("is_playoff", False)),
                    "winner_id": m["winner_id"] or 0,
                    "is_tie": bool(m["is_tie"]),
                    "is_completed": (m["status"] == "Completed")
                }
                for m in matches
            ]
        }
        standings_response = run_cpp_engine("--points-table", standings_payload)
        standings = standings_response.get("points_table", [])

        if len(standings) < 2:
            return jsonify({"status": "error", "message": "At least two teams are required to generate qualifier fixtures."}), 400

        # Number qualifier matches after group matches
        group_matches = [m for m in matches if not m.get("is_playoff", False)]
        max_num = max([m["match_number"] for m in group_matches], default=0)

        qualifier_payload = {
            "tournament_id": tourney["id"],
            "tournament_name": tourney["name"],
            "format": tourney["format"],
            "starting_match_number": max_num + 1,
            "standings": standings
        }

        engine_response = run_cpp_engine("--qualifiers", qualifier_payload)
        if engine_response.get("status") == "success":
            qualifiers = engine_response.get("qualifiers", [])
            database.save_qualifier_fixtures(tourney["id"], tourney["format"], qualifiers)
            return jsonify({
                "status": "success",
                "message": f"Successfully generated {len(qualifiers)} Playoff / Qualifier matches!",
                "data": qualifiers,
                "engine_source": engine_response.get("engine_source")
            }), 201
        else:
            return jsonify({"status": "error", "message": "Failed to generate qualifier fixtures."}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/tournaments/<int:tournament_id>/qualifiers", methods=["GET"])
def get_tournament_qualifiers(tournament_id):
    try:
        all_matches = database.get_tournament_matches(tournament_id)
        playoffs = [m for m in all_matches if m.get("is_playoff", False)]
        return jsonify({"status": "success", "data": playoffs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================================
# CREX SCORECARD & INDIVIDUAL PLAYER SCORES API
# ============================================================================

@app.route("/api/matches/<int:match_id>/scorecard", methods=["GET"])
def get_match_scorecard(match_id):
    """Retrieves full CREX-style individual player scorecard (Batting & Bowling)."""
    try:
        scorecard = database.get_match_scorecard(match_id)
        return jsonify({"status": "success", "data": scorecard})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/matches/<int:match_id>/scorecard", methods=["POST"])
def update_match_scorecard(match_id):
    """Allows users to customize and persist individual player scores."""
    try:
        data = request.get_json() or {}
        database.save_match_scorecard(match_id, data)
        scorecard = database.get_match_scorecard(match_id)
        return jsonify({"status": "success", "data": scorecard})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/tournaments/<int:tournament_id>/crex-stats", methods=["GET"])
def get_tournament_crex_stats(tournament_id):
    """Returns CREX app leaderboards: Orange Cap (Most Runs) and Purple Cap (Most Wickets)."""
    try:
        stats = database.get_tournament_player_stats(tournament_id)
        return jsonify({"status": "success", "data": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ============================================================================
# DEMO SEED DATA (HELPFUL FOR COLLEGE PRESENTATION & EVALUATION)
# ============================================================================

@app.route("/api/demo/seed", methods=["POST"])
def seed_demo_data():
    """Populates standard international cricket teams, players, and sample matches for quick demonstration."""
    try:
        sample_teams = [
            {
                "name": "India",
                "players": [
                    ("Rohit Sharma", "Batter"),
                    ("Virat Kohli", "Batter"),
                    ("Suryakumar Yadav", "Batter"),
                    ("Rishabh Pant", "Wicket-keeper"),
                    ("Hardik Pandya", "All-rounder"),
                    ("Ravindra Jadeja", "All-rounder"),
                    ("Jasprit Bumrah", "Bowler"),
                    ("Mohammed Siraj", "Bowler")
                ]
            },
            {
                "name": "Australia",
                "players": [
                    ("Travis Head", "Batter"),
                    ("David Warner", "Batter"),
                    ("Glenn Maxwell", "All-rounder"),
                    ("Marcus Stoinis", "All-rounder"),
                    ("Josh Inglis", "Wicket-keeper"),
                    ("Pat Cummins", "Bowler"),
                    ("Mitchell Starc", "Bowler"),
                    ("Adam Zampa", "Bowler")
                ]
            },
            {
                "name": "England",
                "players": [
                    ("Jos Buttler", "Wicket-keeper"),
                    ("Phil Salt", "Batter"),
                    ("Harry Brook", "Batter"),
                    ("Liam Livingstone", "Batter"),
                    ("Ben Stokes", "All-rounder"),
                    ("Sam Curran", "All-rounder"),
                    ("Jofra Archer", "Bowler"),
                    ("Adil Rashid", "Bowler")
                ]
            },
            {
                "name": "South Africa",
                "players": [
                    ("Quinton de Kock", "Wicket-keeper"),
                    ("Aiden Markram", "Batter"),
                    ("Heinrich Klaasen", "Batter"),
                    ("David Miller", "Batter"),
                    ("Marco Jansen", "All-rounder"),
                    ("Keshav Maharaj", "Bowler"),
                    ("Kagiso Rabada", "Bowler"),
                    ("Anrich Nortje", "Bowler")
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
                    t_id = existing[0]["id"]
                    created_team_ids.append(t_id)
                    # Add any missing players
                    curr_players = [p["name"].lower() for p in database.get_all_players(t_id)]
                    for p_name, p_role in t_info["players"]:
                        if p_name.lower() not in curr_players:
                            try:
                                database.add_player(p_name, p_role, t_id)
                            except Exception:
                                pass

        # Auto-create sample tournament if none exists
        tourneys = database.get_all_tournaments()
        if not tourneys and len(created_team_ids) >= 4:
            tourney = database.create_tournament("ICC T20 Super Cup 2026", "T20", created_team_ids[:4])
            engine_payload = {
                "tournament_id": tourney["id"],
                "tournament_name": tourney["name"],
                "format": "T20",
                "teams": tourney["teams"]
            }
            engine_response = run_cpp_engine("--fixtures", engine_payload)
            if engine_response.get("status") == "success":
                database.save_tournament_fixtures(tourney["id"], "T20", engine_response["fixtures"])

                # Seed sample match scores for the first 4 matches for instant live demo
                fixtures = database.get_tournament_matches(tourney["id"])
                simulated_scores = [
                    {"score_a": 192, "wickets_a": 5, "overs_a": 20.0, "score_b": 186, "wickets_b": 8, "overs_b": 20.0},
                    {"score_a": 174, "wickets_a": 7, "overs_a": 20.0, "score_b": 175, "wickets_b": 4, "overs_b": 19.1},
                    {"score_a": 185, "wickets_a": 4, "overs_a": 20.0, "score_b": 142, "wickets_b": 10, "overs_b": 17.4},
                    {"score_a": 204, "wickets_a": 3, "overs_a": 20.0, "score_b": 168, "wickets_b": 9, "overs_b": 20.0}
                ]
                for idx, s in enumerate(simulated_scores):
                    if idx < len(fixtures):
                        m = fixtures[idx]
                        score_a = s["score_a"]
                        score_b = s["score_b"]
                        winner_id = m["team_a_id"] if score_a > score_b else (m["team_b_id"] if score_b > score_a else None)
                        w_name = m["team_a_name"] if winner_id == m["team_a_id"] else m["team_b_name"]
                        margin = abs(score_a - score_b)
                        desc = f"{w_name} won by {margin} runs (T20)" if winner_id == m["team_a_id"] else f"{w_name} won by {10 - s['wickets_b']} wickets (T20)"
                        database.update_match_result(
                            match_id=m["id"],
                            score_a=score_a,
                            wickets_a=s["wickets_a"],
                            overs_a=s["overs_a"],
                            score_b=score_b,
                            wickets_b=s["wickets_b"],
                            overs_b=s["overs_b"],
                            winner_id=winner_id,
                            is_tie=False,
                            result_description=desc
                        )

        return jsonify({"status": "success", "message": "Demo sample teams, players, fixtures & Crex scorecards initialized!"})
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
