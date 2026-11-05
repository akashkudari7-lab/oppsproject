
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

// =============================================
// 1. TEAM CLASS
// =============================================

class Team {

private:
  string teamId;
  string teamName;

public:
  Team(string id, string name) : teamId(id), teamName(name) {

    if (id.empty() || name.empty())
      throw invalid_argument("Invalid team details");
  }

  string getId() const { return teamId; }

  string getName() const { return teamName; }
};

// =============================================
// 2. PLAYER PERFORMANCE
// =============================================

struct PlayerPerformance {

  string playerId;
  string playerName;
  string teamName;

  int matches = 0;
  int runs = 0;
  int wickets = 0;

  int ballsFaced = 0;
  int ballsBowled = 0;

  int fours = 0;
  int sixes = 0;

  double getStrikeRate() const {

    if (ballsFaced == 0)
      return 0.0;

    return runs * 100.0 / ballsFaced;
  }

  double getEconomy() const {

    if (ballsBowled == 0)
      return 0.0;

    return runs / (ballsBowled / 6.0);
  }
};

// =============================================
// 3. PLAYER LEADERBOARD
// =============================================

class PlayerLeaderboard {

private:
  vector<PlayerPerformance> players;

  PlayerPerformance *findPlayer(const string &id) {

    for (auto &player : players) {

      if (player.playerId == id)
        return &player;
    }

    return nullptr;
  }

public:
  void registerPlayer(const string &id, const string &name,
                      const string &team) {

    if (id.empty() || name.empty() || team.empty())
      throw invalid_argument("Invalid player registration");

    if (findPlayer(id) != nullptr)
      throw invalid_argument("Duplicate player ID");

    PlayerPerformance p;

    p.playerId = id;
    p.playerName = name;
    p.teamName = team;

    players.push_back(p);
  }

  void recordPerformance(const string &id, int runs, int wickets,
                         int ballsFaced, int ballsBowled, int fours,
                         int sixes) {

    PlayerPerformance *player = findPlayer(id);

    if (player == nullptr)
      throw runtime_error("Player not found");

    if (runs < 0 || wickets < 0 || ballsFaced < 0 || ballsBowled < 0 ||
        fours < 0 || sixes < 0) {

      throw invalid_argument("Invalid performance data");
    }

    if (fours * 4 + sixes * 6 > runs)
      throw invalid_argument("Boundary runs exceed total runs");

    if (fours + sixes > ballsFaced)
      throw invalid_argument("Invalid boundary count");

    player->matches++;

    player->runs += runs;
    player->wickets += wickets;

    player->ballsFaced += ballsFaced;
    player->ballsBowled += ballsBowled;

    player->fours += fours;
    player->sixes += sixes;
  }

  void displayOrangeCap() const {

    vector<PlayerPerformance> ranking = players;

    sort(ranking.begin(), ranking.end(),
         [](const PlayerPerformance &a, const PlayerPerformance &b) {
           if (a.runs != b.runs)
             return a.runs > b.runs;

           if (a.getStrikeRate() != b.getStrikeRate())
             return a.getStrikeRate() > b.getStrikeRate();

           return a.playerName < b.playerName;
         });

    cout << "\n============== ORANGE CAP ==============\n";

    cout << left << setw(22) << "Player" << setw(18) << "Team" << setw(10)
         << "Matches" << setw(10) << "Runs" << setw(12) << "Strike Rate"
         << endl;

    for (const auto &p : ranking) {

      cout << left << setw(22) << p.playerName << setw(18) << p.teamName
           << setw(10) << p.matches << setw(10) << p.runs << fixed
           << setprecision(2) << p.getStrikeRate() << endl;
    }

    cout << "=========================================\n";
  }

  void displayPurpleCap() const {

    vector<PlayerPerformance> ranking = players;

    sort(ranking.begin(), ranking.end(),
         [](const PlayerPerformance &a, const PlayerPerformance &b) {
           if (a.wickets != b.wickets)
             return a.wickets > b.wickets;

           if (a.getEconomy() != b.getEconomy())
             return a.getEconomy() < b.getEconomy();

           return a.playerName < b.playerName;
         });

    cout << "\n============== PURPLE CAP ==============\n";

    cout << left << setw(22) << "Player" << setw(18) << "Team" << setw(10)
         << "Matches" << setw(10) << "Wickets" << setw(12) << "Economy" << endl;

    for (const auto &p : ranking) {

      cout << left << setw(22) << p.playerName << setw(18) << p.teamName
           << setw(10) << p.matches << setw(10) << p.wickets << fixed
           << setprecision(2) << p.getEconomy() << endl;
    }

    cout << "=========================================\n";
  }
};

// =============================================
// 4. LEAGUE TABLE ENTRY
// =============================================

struct LeagueEntry {

  string teamId;
  string teamName;

  int played = 0;
  int won = 0;
  int lost = 0;
  int tied = 0;

  int points = 0;

  double runsScored = 0;
  double ballsFaced = 0;

  double runsConceded = 0;
  double ballsBowled = 0;

  double nrr = 0;

  void calculateNRR() {

    if (ballsFaced == 0 || ballsBowled == 0) {
      nrr = 0;
      return;
    }

    nrr = (runsScored * 6.0 / ballsFaced) - (runsConceded * 6.0 / ballsBowled);
  }
};

// =============================================
// 5. LEAGUE TABLE
// =============================================

class LeagueTable {

private:
  vector<LeagueEntry> entries;

  LeagueEntry *findEntry(const string &id) {

    for (auto &entry : entries) {

      if (entry.teamId == id)
        return &entry;
    }

    return nullptr;
  }

public:
  void registerTeam(const Team &team) {

    if (findEntry(team.getId()))
      throw invalid_argument("Duplicate team");

    LeagueEntry entry;

    entry.teamId = team.getId();
    entry.teamName = team.getName();

    entries.push_back(entry);
  }

  void recordMatch(const string &team1, const string &team2, int runs1,
                   int balls1, bool allOut1, int runs2, int balls2,
                   bool allOut2) {

    LeagueEntry *a = findEntry(team1);
    LeagueEntry *b = findEntry(team2);

    if (!a || !b)
      throw runtime_error("Team not found");

    if (team1 == team2 || runs1 < 0 || runs2 < 0 || balls1 <= 0 ||
        balls2 <= 0) {

      throw invalid_argument("Invalid match data");
    }

    if (allOut1 && allOut2) {
      // All-out innings use the full 20-over quota
      // in this T20 demonstration.
      balls1 = 120;
      balls2 = 120;
    } else if (allOut1) {
      balls1 = 120;
    } else if (allOut2) {
      balls2 = 120;
    }

    a->played++;
    b->played++;

    a->runsScored += runs1;
    a->ballsFaced += balls1;

    a->runsConceded += runs2;
    a->ballsBowled += balls2;

    b->runsScored += runs2;
    b->ballsFaced += balls2;

    b->runsConceded += runs1;
    b->ballsBowled += balls1;

    if (runs1 > runs2) {

      a->won++;
      a->points += 2;

      b->lost++;
    } else if (runs2 > runs1) {

      b->won++;
      b->points += 2;

      a->lost++;
    } else {

      a->tied++;
      b->tied++;

      a->points++;
      b->points++;
    }

    a->calculateNRR();
    b->calculateNRR();
  }

  vector<LeagueEntry> getRankings() const {

    vector<LeagueEntry> ranking = entries;

    for (auto &entry : ranking)
      entry.calculateNRR();

    sort(ranking.begin(), ranking.end(),
         [](const LeagueEntry &a, const LeagueEntry &b) {
           if (a.points != b.points)
             return a.points > b.points;

           if (fabs(a.nrr - b.nrr) > 0.000001)
             return a.nrr > b.nrr;

           if (a.won != b.won)
             return a.won > b.won;

           return a.teamName < b.teamName;
         });

    return ranking;
  }

  void display() const {

    auto ranking = getRankings();

    cout << "\n=============== LEAGUE TABLE ===============\n";

    cout << left << setw(18) << "Team" << setw(6) << "P" << setw(6) << "W"
         << setw(6) << "L" << setw(8) << "Points"
         << "NRR" << endl;

    for (const auto &e : ranking) {

      cout << left << setw(18) << e.teamName << setw(6) << e.played << setw(6)
           << e.won << setw(6) << e.lost << setw(8) << e.points << fixed
           << setprecision(3) << e.nrr << endl;
    }

    cout << "=============================================\n";
  }
};

// =============================================
// 6. PLAYOFF STAGE
// =============================================

enum class PlayoffStage {

  QUALIFIER_1,
  ELIMINATOR,
  QUALIFIER_2,
  FINAL
};

string stageName(PlayoffStage stage) {

  switch (stage) {

  case PlayoffStage::QUALIFIER_1:
    return "QUALIFIER 1";

  case PlayoffStage::ELIMINATOR:
    return "ELIMINATOR";

  case PlayoffStage::QUALIFIER_2:
    return "QUALIFIER 2";

  case PlayoffStage::FINAL:
    return "GRAND FINAL";
  }

  return "UNKNOWN";
}

struct PlayoffMatch {

  PlayoffStage stage;

  string team1;
  string team2;

  string winner;

  bool completed = false;
};

// =============================================
// 7. PLAYOFF MANAGER
// =============================================

class PlayoffManager {

private:
  vector<PlayoffMatch> matches;

  string qualifier1Winner;
  string qualifier1Loser;

  string eliminatorWinner;

  string qualifier2Winner;

  string champion;

  PlayoffMatch *findStage(PlayoffStage stage) {

    for (auto &match : matches) {

      if (match.stage == stage)
        return &match;
    }

    return nullptr;
  }

  void addMatch(PlayoffStage stage, const string &team1, const string &team2) {

    if (team1.empty() || team2.empty() || team1 == team2) {

      throw invalid_argument("Invalid playoff matchup");
    }

    PlayoffMatch match;

    match.stage = stage;
    match.team1 = team1;
    match.team2 = team2;

    matches.push_back(match);
  }

public:
  void generatePlayoffs(const vector<LeagueEntry> &ranking) {

    if (!matches.empty())
      throw runtime_error("Playoffs already generated");

    if (ranking.size() < 4)
      throw runtime_error("At least four teams required");

    addMatch(PlayoffStage::QUALIFIER_1, ranking[0].teamId, ranking[1].teamId);

    addMatch(PlayoffStage::ELIMINATOR, ranking[2].teamId, ranking[3].teamId);

    cout << "\nTOP FOUR TEAMS QUALIFIED!\n";

    displayFixtures();
  }

  void recordWinner(PlayoffStage stage, const string &winner) {

    PlayoffMatch *match = findStage(stage);

    if (!match)
      throw runtime_error("Playoff match not found");

    if (match->completed)
      throw runtime_error("Match already completed");

    if (winner != match->team1 && winner != match->team2) {

      throw invalid_argument("Winner must be a participating team");
    }

    match->winner = winner;
    match->completed = true;

    if (stage == PlayoffStage::QUALIFIER_1) {

      qualifier1Winner = winner;

      qualifier1Loser = (winner == match->team1) ? match->team2 : match->team1;

      // Q2 waits for the eliminator winner.
    }

    else if (stage == PlayoffStage::ELIMINATOR) {

      eliminatorWinner = winner;

      if (!qualifier1Loser.empty()) {

        addMatch(PlayoffStage::QUALIFIER_2, qualifier1Loser, eliminatorWinner);
      }
    }

    else if (stage == PlayoffStage::QUALIFIER_2) {

      if (eliminatorWinner.empty() || qualifier1Loser.empty()) {

        throw runtime_error("Previous playoff stages incomplete");
      }

      qualifier2Winner = winner;

      addMatch(PlayoffStage::FINAL, qualifier1Winner, qualifier2Winner);
    }

    else if (stage == PlayoffStage::FINAL) {

      if (qualifier1Winner.empty() || qualifier2Winner.empty()) {

        throw runtime_error("Finalists not established");
      }

      champion = winner;
    }

    cout << "\n" << stageName(stage) << " winner: " << winner << endl;
  }

  void displayFixtures() const {

    cout << "\n============== PLAYOFF FIXTURES ==============\n";

    for (const auto &match : matches) {

      cout << "\n" << stageName(match.stage) << endl;

      cout << match.team1 << " VS " << match.team2 << endl;

      if (match.completed) {

        cout << "Winner: " << match.winner << endl;
      } else {

        cout << "Status: Upcoming" << endl;
      }
    }

    cout << "===============================================\n";
  }

  void displayChampion() const {

    if (champion.empty()) {

      cout << "\nTournament champion not decided yet.\n";
      return;
    }

    cout << "\n================================\n";
    cout << "       TOURNAMENT CHAMPION\n";
    cout << "             " << champion << endl;
    cout << "================================\n";
  }
};

// =============================================
// 8. MAIN FUNCTION
// =============================================

int main() {

  try {

    // Create teams

    Team india("T01", "India");
    Team australia("T02", "Australia");
    Team england("T03", "England");
    Team pakistan("T04", "Pakistan");
    Team southAfrica("T05", "South Africa");

    vector<Team> teams = {india, australia, england, pakistan, southAfrica};

    // Create league table

    LeagueTable league;

    for (const auto &team : teams)
      league.registerTeam(team);

    // Simulate league-stage matches.
    // These are sample results, not real fixtures.

    league.recordMatch("T01", "T02", 180, 120, false, 150, 120, false);

    league.recordMatch("T03", "T04", 170, 120, false, 160, 120, false);

    league.recordMatch("T05", "T01", 190, 120, false, 180, 120, false);

    league.recordMatch("T02", "T03", 175, 120, false, 165, 120, false);

    league.recordMatch("T04", "T05", 155, 120, false, 145, 120, false);

    league.recordMatch("T01", "T03", 200, 120, false, 160, 120, false);

    league.recordMatch("T02", "T04", 180, 120, false, 180, 120, false);

    league.recordMatch("T03", "T05", 170, 120, false, 150, 120, false);

    league.recordMatch("T01", "T04", 175, 120, false, 160, 120, false);

    league.recordMatch("T02", "T05", 165, 120, false, 150, 120, false);

    // Display league standings

    league.display();

    // Generate playoffs

    PlayoffManager playoffs;

    playoffs.generatePlayoffs(league.getRankings());

    // Simulate Qualifier 1

    auto rankings = league.getRankings();

    string first = rankings[0].teamId;
    string second = rankings[1].teamId;
    string third = rankings[2].teamId;
    string fourth = rankings[3].teamId;

    playoffs.recordWinner(PlayoffStage::QUALIFIER_1, first);

    // Simulate Eliminator

    playoffs.recordWinner(PlayoffStage::ELIMINATOR, third);

    // Simulate Qualifier 2

    playoffs.recordWinner(PlayoffStage::QUALIFIER_2, second);

    // Simulate Final

    playoffs.recordWinner(PlayoffStage::FINAL, first);

    playoffs.displayFixtures();

    playoffs.displayChampion();

    // -------------------------------------
    // PLAYER LEADERBOARDS
    // -------------------------------------

    PlayerLeaderboard leaderboard;

    leaderboard.registerPlayer("P01", "Virat Kohli", "India");

    leaderboard.registerPlayer("P02", "Rohit Sharma", "India");

    leaderboard.registerPlayer("P03", "Steve Smith", "Australia");

    leaderboard.registerPlayer("P04", "Pat Cummins", "Australia");

    leaderboard.registerPlayer("P05", "Joe Root", "England");

    leaderboard.registerPlayer("P06", "Babar Azam", "Pakistan");

    // Sample player performances

    leaderboard.recordPerformance("P01", 450, 2, 300, 24, 45, 15);

    leaderboard.recordPerformance("P02", 380, 1, 250, 12, 40, 18);

    leaderboard.recordPerformance("P03", 320, 3, 260, 60, 30, 8);

    leaderboard.recordPerformance("P04", 120, 15, 90, 120, 10, 5);

    leaderboard.recordPerformance("P05", 410, 5, 280, 96, 42, 9);

    leaderboard.recordPerformance("P06", 350, 4, 270, 48, 35, 12);

    // Display caps

    leaderboard.displayOrangeCap();

    leaderboard.displayPurpleCap();

  } catch (const exception &e) {

    cerr << "\nERROR: " << e.what() << endl;

    return 1;
  }

  return 0;
}
