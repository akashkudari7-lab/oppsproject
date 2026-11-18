#ifndef TOURNAMENT_CPP
#define TOURNAMENT_CPP

#include "Match.cpp"
#include <vector>
#include <map>
#include <algorithm>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <cmath>

/**
 * Converts cricket overs (e.g. 19.4) to decimal overs (e.g. 19 + 4/6 = 19.667)
 */
inline double toDecimalOvers(double overs) {
    int fullOvers = static_cast<int>(overs);
    double fraction = overs - fullOvers;
    int balls = static_cast<int>(fraction * 10.0 + 0.5);
    if (balls >= 6) {
        fullOvers += balls / 6;
        balls = balls % 6;
    }
    return fullOvers + (balls / 6.0);
}

/**
 * Structure representing a team's standing in the Points Table
 */
struct TeamStanding {
    int rank;
    int teamId;
    std::string teamName;
    int played;
    int won;
    int lost;
    int tied;
    int points;
    double nrr;
    int runsScored;
    double oversFaced;
    int runsConceded;
    double oversBowled;

    TeamStanding()
        : rank(0), teamId(0), teamName(""), played(0), won(0), lost(0), tied(0), points(0),
          nrr(0.0), runsScored(0), oversFaced(0.0), runsConceded(0), oversBowled(0.0) {}

    TeamStanding(int id, const std::string& name)
        : rank(0), teamId(id), teamName(name), played(0), won(0), lost(0), tied(0), points(0),
          nrr(0.0), runsScored(0), oversFaced(0.0), runsConceded(0), oversBowled(0.0) {}

    std::string toJson() const {
        std::ostringstream ss;
        ss << std::fixed << std::setprecision(3);
        ss << "{"
           << "\"rank\":" << rank << ","
           << "\"team_id\":" << teamId << ","
           << "\"team_name\":\"" << teamName << "\","
           << "\"played\":" << played << ","
           << "\"won\":" << won << ","
           << "\"lost\":" << lost << ","
           << "\"tied\":" << tied << ","
           << "\"points\":" << points << ","
           << "\"nrr\":" << nrr << ","
           << "\"runs_scored\":" << runsScored << ","
           << "\"overs_faced\":" << oversFaced << ","
           << "\"runs_conceded\":" << runsConceded << ","
           << "\"overs_bowled\":" << oversBowled
           << "}";
        return ss.str();
    }
};

/**
 * Strict Points Table Comparator:
 * 1. Highest points
 * 2. Highest number of wins
 * 3. Highest Net Run Rate (NRR)
 * 4. Team name alphabetically
 */
inline bool compareStandings(const TeamStanding& a, const TeamStanding& b) {
    if (a.points != b.points) {
        return a.points > b.points;
    }
    if (a.won != b.won) {
        return a.won > b.won;
    }
    if (std::abs(a.nrr - b.nrr) > 0.0001) {
        return a.nrr > b.nrr;
    }
    return a.teamName < b.teamName;
}

/**
 * Data structure representing a match result passed for points calculation
 */
struct MatchRecord {
    int teamAId;
    int teamBId;
    int scoreA;
    int scoreB;
    int wicketsA;
    int wicketsB;
    double oversA;
    double oversB;
    int winnerId;
    bool isTie;
    bool isCompleted;
    std::string stage;
    bool isPlayoff;

    MatchRecord()
        : teamAId(0), teamBId(0), scoreA(0), scoreB(0),
          wicketsA(0), wicketsB(0), oversA(0.0), oversB(0.0),
          winnerId(0), isTie(false), isCompleted(false),
          stage("Group"), isPlayoff(false) {}
};

/**
 * Data structure for Playoff / Qualifier Fixtures
 */
struct PlayoffFixture {
    int matchNumber;
    std::string stage; // "Qualifier 1", "Eliminator", "Qualifier 2", "Final"
    int teamAId;
    std::string teamAName;
    int teamBId;
    std::string teamBName;
    std::string teamASource; // e.g. "Rank 1"
    std::string teamBSource; // e.g. "Rank 2"
    std::string description;
};

/**
 * Tournament Class
 * Manages tournament metadata, participating teams, fixture generation,
 * and points table compilation according to ICC cricket tournament rules.
 */
class Tournament {
private:
    int id;
    std::string name;
    std::string format; // "T20", "ODI", "Test"
    std::vector<Team> teams;
    std::vector<Match*> matches;

    static std::string escapeJson(const std::string& input) {
        std::string out;
        for (char c : input) {
            if (c == '"') out += "\\\"";
            else if (c == '\\') out += "\\\\";
            else out += c;
        }
        return out;
    }

public:
    Tournament(int tId = 0, const std::string& tName = "", const std::string& tFormat = "T20")
        : id(tId), name(tName), format(tFormat) {}

    ~Tournament() {
        clearMatches();
    }

    void clearMatches() {
        for (Match* m : matches) {
            delete m;
        }
        matches.clear();
    }

    // Getters and Setters
    int getId() const { return id; }
    void setId(int tId) { id = tId; }

    std::string getName() const { return name; }
    void setName(const std::string& tName) { name = tName; }

    std::string getFormat() const { return format; }
    void setFormat(const std::string& tFormat) { format = tFormat; }

    const std::vector<Team>& getTeams() const { return teams; }
    const std::vector<Match*>& getMatches() const { return matches; }

    // Add team to tournament
    bool addTeam(const Team& team) {
        // Prevent duplicate team registration
        for (const auto& t : teams) {
            if (t.getId() == team.getId()) {
                return false;
            }
        }
        teams.push_back(team);
        return true;
    }

    // Automatic Round-Robin Fixture Generation
    // Rules:
    // 1. Every team plays against every other team exactly once.
    // 2. Prevent a team from playing against itself.
    // 3. Prevent creating fixtures with fewer than 2 teams.
    bool generateRoundRobinFixtures() {
        if (teams.size() < 2) {
            return false;
        }

        clearMatches();
        int matchNumber = 1;
        size_t n = teams.size();

        for (size_t i = 0; i < n; ++i) {
            for (size_t j = i + 1; j < n; ++j) {
                // Ensure no team plays against itself
                if (teams[i].getId() == teams[j].getId()) continue;

                // Create polymorphic Match based on tournament format
                Match* match = createMatch(format, matchNumber++, teams[i], teams[j]);
                matches.push_back(match);
            }
        }
        return true;
    }

    // Calculate Points Table
    // Rules:
    // Win = 2 points
    // Tie = 1 point for each team
    // Loss = 0 points
    // Net Run Rate = (Runs Scored / Overs Faced) - (Runs Conceded / Overs Bowled)
    // ICC Rule: If a team is bowled out, overs faced is considered full maximum overs.
    std::vector<TeamStanding> calculatePointsTable(const std::vector<MatchRecord>& matchRecords) const {
        std::map<int, TeamStanding> standingsMap;

        // Initialize standings for all participating teams
        for (const auto& team : teams) {
            standingsMap[team.getId()] = TeamStanding(team.getId(), team.getName());
        }

        double maxOvers = 20.0;
        if (format == "ODI" || format == "odi") maxOvers = 50.0;
        else if (format == "Test" || format == "test") maxOvers = 90.0;

        // Tally results for all completed matches (only Group stage counts towards table)
        for (const auto& match : matchRecords) {
            if (!match.isCompleted || match.isPlayoff) continue;

            auto itA = standingsMap.find(match.teamAId);
            auto itB = standingsMap.find(match.teamBId);

            if (itA != standingsMap.end() && itB != standingsMap.end()) {
                TeamStanding& teamA = itA->second;
                TeamStanding& teamB = itB->second;

                teamA.played++;
                teamB.played++;

                if (match.isTie) {
                    teamA.tied++;
                    teamA.points += 1;
                    teamB.tied++;
                    teamB.points += 1;
                } else if (match.winnerId == match.teamAId) {
                    teamA.won++;
                    teamA.points += 2;
                    teamB.lost++;
                } else if (match.winnerId == match.teamBId) {
                    teamB.won++;
                    teamB.points += 2;
                    teamA.lost++;
                }

                // Net Run Rate Calculation
                double effOversA = toDecimalOvers(match.oversA);
                if (match.wicketsA >= 10 && maxOvers > 0.0 && format != "Test" && format != "test") {
                    effOversA = maxOvers;
                }
                if (effOversA <= 0.0) effOversA = (match.oversA > 0.0 ? match.oversA : maxOvers);

                double effOversB = toDecimalOvers(match.oversB);
                if (match.wicketsB >= 10 && maxOvers > 0.0 && format != "Test" && format != "test") {
                    effOversB = maxOvers;
                }
                if (effOversB <= 0.0) effOversB = (match.oversB > 0.0 ? match.oversB : maxOvers);

                teamA.runsScored += match.scoreA;
                teamA.oversFaced += effOversA;
                teamA.runsConceded += match.scoreB;
                teamA.oversBowled += effOversB;

                teamB.runsScored += match.scoreB;
                teamB.oversFaced += effOversB;
                teamB.runsConceded += match.scoreA;
                teamB.oversBowled += effOversA;
            }
        }

        // Compute final NRR for each team
        for (auto& pair : standingsMap) {
            TeamStanding& s = pair.second;
            double runRateFor = (s.oversFaced > 0.0) ? (static_cast<double>(s.runsScored) / s.oversFaced) : 0.0;
            double runRateAgainst = (s.oversBowled > 0.0) ? (static_cast<double>(s.runsConceded) / s.oversBowled) : 0.0;
            s.nrr = runRateFor - runRateAgainst;
        }

        // Convert map to vector
        std::vector<TeamStanding> standingsList;
        for (const auto& pair : standingsMap) {
            standingsList.push_back(pair.second);
        }

        // Sort by:
        // 1. Highest points
        // 2. Highest number of wins
        // 3. Highest Net Run Rate (NRR)
        // 4. Team name alphabetically
        std::sort(standingsList.begin(), standingsList.end(), compareStandings);

        // Assign ordinal ranks
        for (size_t i = 0; i < standingsList.size(); ++i) {
            standingsList[i].rank = static_cast<int>(i + 1);
        }

        return standingsList;
    }

    // Generate Playoff / Qualifier Fixtures (IPL / ICC standard format)
    // Top 4 Teams:
    // Qualifier 1: Rank 1 vs Rank 2 (Winner to Final, Loser to Qualifier 2)
    // Eliminator:  Rank 3 vs Rank 4 (Winner to Qualifier 2, Loser eliminated)
    // Qualifier 2: Loser Q1 vs Winner Eliminator (Winner to Final)
    // Final:       Winner Q1 vs Winner Q2 (Winner is Champion)
    std::vector<PlayoffFixture> generatePlayoffs(const std::vector<TeamStanding>& standings, int startingMatchNum = 1) const {
        std::vector<PlayoffFixture> playoffs;
        if (standings.size() < 2) return playoffs;

        int mNum = startingMatchNum;

        if (standings.size() >= 4) {
            // 4-Team IPL-Style Playoffs
            // Match 1: Qualifier 1
            playoffs.push_back({
                mNum++,
                "Qualifier 1",
                standings[0].teamId, standings[0].teamName,
                standings[1].teamId, standings[1].teamName,
                "Rank 1", "Rank 2",
                "Winner advances directly to the Grand Final; Loser goes to Qualifier 2."
            });

            // Match 2: Eliminator
            playoffs.push_back({
                mNum++,
                "Eliminator",
                standings[2].teamId, standings[2].teamName,
                standings[3].teamId, standings[3].teamName,
                "Rank 3", "Rank 4",
                "Winner advances to Qualifier 2; Loser is eliminated."
            });

            // Match 3: Qualifier 2 (Initially pre-seeded with Rank 2 vs Rank 3 as placeholders until Q1/Elim finish)
            playoffs.push_back({
                mNum++,
                "Qualifier 2",
                standings[1].teamId, standings[1].teamName + " (Loser Q1)",
                standings[2].teamId, standings[2].teamName + " (Winner Elim)",
                "Loser Q1", "Winner Eliminator",
                "Winner advances to the Grand Final; Loser is eliminated."
            });

            // Match 4: Final (Initially pre-seeded with Rank 1 vs Winner Q2 as placeholder)
            playoffs.push_back({
                mNum++,
                "Final",
                standings[0].teamId, standings[0].teamName + " (Winner Q1)",
                standings[1].teamId, standings[1].teamName + " (Winner Q2)",
                "Winner Q1", "Winner Q2",
                "Grand Finale - Winner is crowned Tournament Champion!"
            });
        } else if (standings.size() == 3) {
            // 3-Team Format: Qualifier and Final
            playoffs.push_back({
                mNum++,
                "Qualifier",
                standings[1].teamId, standings[1].teamName,
                standings[2].teamId, standings[2].teamName,
                "Rank 2", "Rank 3",
                "Winner advances to the Grand Final to face Rank 1."
            });
            playoffs.push_back({
                mNum++,
                "Final",
                standings[0].teamId, standings[0].teamName,
                standings[1].teamId, standings[1].teamName + " (Winner Qualifier)",
                "Rank 1", "Winner Qualifier",
                "Grand Finale - Winner is crowned Tournament Champion!"
            });
        } else {
            // 2-Team Format: Direct Final
            playoffs.push_back({
                mNum++,
                "Final",
                standings[0].teamId, standings[0].teamName,
                standings[1].teamId, standings[1].teamName,
                "Rank 1", "Rank 2",
                "Grand Finale - Winner is crowned Tournament Champion!"
            });
        }

        return playoffs;
    }

    // Display Tournament Details
    void displayTournamentDetails() const {
        std::cout << "\n============================================================\n";
        std::cout << "TOURNAMENT: " << name << " (ID: " << id << ")\n";
        std::cout << "Format: " << format << " | Participating Teams: " << teams.size() << "\n";
        std::cout << "------------------------------------------------------------\n";
        std::cout << "Teams:\n";
        for (const auto& t : teams) {
            std::cout << "  - [ID: " << t.getId() << "] " << t.getName() 
                      << " (" << t.getPlayerCount() << " players)\n";
        }
        std::cout << "------------------------------------------------------------\n";
        std::cout << "Generated Fixtures (" << matches.size() << " total):\n";
        for (const auto* m : matches) {
            std::cout << "  Match #" << m->getMatchId() << ": "
                      << m->getTeamA().getName() << " vs " << m->getTeamB().getName()
                      << " [" << m->getFormat() << "]\n";
        }
        std::cout << "============================================================\n";
    }

    // JSON serialization of generated fixtures
    std::string fixturesToJson() const {
        std::ostringstream ss;
        ss << "{"
           << "\"status\":\"success\","
           << "\"tournament_id\":" << id << ","
           << "\"tournament_name\":\"" << escapeJson(name) << "\","
           << "\"format\":\"" << escapeJson(format) << "\","
           << "\"total_fixtures\":" << matches.size() << ","
           << "\"fixtures\":[";
        for (size_t i = 0; i < matches.size(); ++i) {
            if (i > 0) ss << ",";
            ss << "{"
               << "\"match_number\":" << matches[i]->getMatchId() << ","
               << "\"format\":\"" << escapeJson(matches[i]->getFormat()) << "\","
               << "\"team_a_id\":" << matches[i]->getTeamA().getId() << ","
               << "\"team_a_name\":\"" << escapeJson(matches[i]->getTeamA().getName()) << "\","
               << "\"team_b_id\":" << matches[i]->getTeamB().getId() << ","
               << "\"team_b_name\":\"" << escapeJson(matches[i]->getTeamB().getName()) << "\""
               << "}";
        }
        ss << "]}";
        return ss.str();
    }
};

#endif // TOURNAMENT_CPP
