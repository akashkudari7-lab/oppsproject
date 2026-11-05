
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

// =============================================
// 1. CRICKET FORMAT
// =============================================

enum class CricketFormat { T20, ODI, TEST };

string formatName(CricketFormat format) {

  switch (format) {

  case CricketFormat::T20:
    return "T20";

  case CricketFormat::ODI:
    return "ODI";

  case CricketFormat::TEST:
    return "TEST";
  }

  return "UNKNOWN";
}

int getMaximumOvers(CricketFormat format) {

  switch (format) {

  case CricketFormat::T20:
    return 20;

  case CricketFormat::ODI:
    return 50;

  case CricketFormat::TEST:
    return -1;
  }

  return -1;
}

// =============================================
// 2. PLAYER CLASS
// =============================================

class Player {

private:
  string playerId;
  string name;
  int age;

public:
  Player(string id, string n, int a) : playerId(id), name(n), age(a) {

    if (id.empty() || n.empty() || a <= 0)
      throw invalid_argument("Invalid player details");
  }

  string getId() const { return playerId; }

  string getName() const { return name; }

  int getAge() const { return age; }

  void display() const {

    cout << left << setw(12) << playerId << setw(22) << name << age << endl;
  }
};

// =============================================
// 3. TEAM CLASS
// =============================================

class Team {

private:
  string teamId;
  string teamName;

  vector<Player> players;

public:
  Team(string id, string name) : teamId(id), teamName(name) {

    if (id.empty() || name.empty())
      throw invalid_argument("Invalid team details");
  }

  void addPlayer(const Player &player) {

    for (const auto &p : players) {

      if (p.getId() == player.getId())
        throw invalid_argument("Duplicate player ID");
    }

    players.push_back(player);
  }

  string getId() const { return teamId; }

  string getName() const { return teamName; }

  int getPlayerCount() const { return static_cast<int>(players.size()); }

  const vector<Player> &getPlayers() const { return players; }

  void displayTeam() const {

    cout << "\nTeam: " << teamName << endl;

    cout << left << setw(12) << "Player ID" << setw(22) << "Player Name"
         << "Age" << endl;

    for (const auto &player : players)
      player.display();
  }
};

// =============================================
// 4. MATCH FIXTURE
// =============================================

struct MatchFixture {

  string matchId;

  string team1Id;
  string team2Id;

  int roundNumber;

  bool completed = false;

  string result;
};

// =============================================
// 5. INNINGS RESULT
// =============================================

struct InningsResult {

  int runs = 0;

  int wickets = 0;

  // Store legal balls rather than decimal overs.
  // Example: 9.3 overs = 57 legal balls.

  int legalBalls = 0;

  bool allOut = false;
};

// =============================================
// 6. POINTS TABLE ENTRY
// =============================================

struct PointsEntry {

  string teamId;
  string teamName;

  int played = 0;
  int won = 0;
  int lost = 0;
  int tied = 0;
  int noResult = 0;

  int points = 0;

  double runsScored = 0;
  double ballsFaced = 0;

  double runsConceded = 0;
  double ballsBowled = 0;

  double nrr = 0.0;

  void calculateNRR() {

    if (ballsFaced == 0 || ballsBowled == 0) {
      nrr = 0.0;
      return;
    }

    double runRateFor = runsScored * 6.0 / ballsFaced;

    double runRateAgainst = runsConceded * 6.0 / ballsBowled;

    nrr = runRateFor - runRateAgainst;
  }
};

// =============================================
// 7. POINTS TABLE CLASS
// =============================================

class PointsTable {

private:
  vector<PointsEntry> entries;

  PointsEntry *findEntry(const string &teamId) {

    for (auto &entry : entries) {

      if (entry.teamId == teamId)
        return &entry;
    }

    return nullptr;
  }

  const PointsEntry *findEntry(const string &teamId) const {

    for (const auto &entry : entries) {

      if (entry.teamId == teamId)
        return &entry;
    }

    return nullptr;
  }

public:
  void registerTeam(const Team &team) {

    if (findEntry(team.getId()) != nullptr)
      throw invalid_argument("Team already registered");

    PointsEntry entry;

    entry.teamId = team.getId();
    entry.teamName = team.getName();

    entries.push_back(entry);
  }

  // Record one completed limited-overs innings
  // for net run rate calculations.

  void addInningsData(const string &teamId, const InningsResult &own,
                      const InningsResult &opponent, int maximumOvers) {

    PointsEntry *entry = findEntry(teamId);

    if (entry == nullptr)
      throw runtime_error("Team not found");

    double ownBalls = own.legalBalls;
    double opponentBalls = opponent.legalBalls;

    // Under standard limited-overs NRR rules,
    // a team dismissed before its quota is treated
    // as having used its full quota.

    if (own.allOut)
      ownBalls = maximumOvers * 6;

    if (opponent.allOut)
      opponentBalls = maximumOvers * 6;

    entry->runsScored += own.runs;
    entry->ballsFaced += ownBalls;

    entry->runsConceded += opponent.runs;
    entry->ballsBowled += opponentBalls;

    entry->calculateNRR();
  }

  void recordWin(const string &teamId) {

    PointsEntry *entry = findEntry(teamId);

    if (entry == nullptr)
      throw runtime_error("Team not found");

    entry->played++;
    entry->won++;
    entry->points += 2;
  }

  void recordLoss(const string &teamId) {

    PointsEntry *entry = findEntry(teamId);

    if (entry == nullptr)
      throw runtime_error("Team not found");

    entry->played++;
    entry->lost++;
  }

  void recordTie(const string &team1, const string &team2) {

    PointsEntry *first = findEntry(team1);
    PointsEntry *second = findEntry(team2);

    if (!first || !second)
      throw runtime_error("Team not found");

    first->played++;
    second->played++;

    first->tied++;
    second->tied++;

    first->points++;
    second->points++;
  }

  void recordNoResult(const string &team1, const string &team2) {

    PointsEntry *first = findEntry(team1);
    PointsEntry *second = findEntry(team2);

    if (!first || !second)
      throw runtime_error("Team not found");

    first->played++;
    second->played++;

    first->noResult++;
    second->noResult++;

    first->points++;
    second->points++;
  }

  void display() {

    // Update NRR before sorting.

    for (auto &entry : entries)
      entry.calculateNRR();

    sort(entries.begin(), entries.end(),
         [](const PointsEntry &a, const PointsEntry &b) {
           if (a.points != b.points)
             return a.points > b.points;

           if (fabs(a.nrr - b.nrr) > 0.000001)
             return a.nrr > b.nrr;

           if (a.won != b.won)
             return a.won > b.won;

           return a.teamName < b.teamName;
         });

    cout << "\n================ POINTS TABLE ================\n";

    cout << left << setw(18) << "Team" << setw(5) << "P" << setw(5) << "W"
         << setw(5) << "L" << setw(5) << "T" << setw(5) << "NR" << setw(7)
         << "Points"
         << "NRR" << endl;

    cout << string(75, '-') << endl;

    for (const auto &entry : entries) {

      cout << left << setw(18) << entry.teamName << setw(5) << entry.played
           << setw(5) << entry.won << setw(5) << entry.lost << setw(5)
           << entry.tied << setw(5) << entry.noResult << setw(7) << entry.points
           << fixed << setprecision(3) << entry.nrr << endl;
    }

    cout << "===============================================\n";
  }
};

// =============================================
// 8. FIXTURE GENERATOR
// =============================================

class FixtureGenerator {

public:
  static vector<MatchFixture> generate(const vector<Team> &teams,
                                       bool doubleRoundRobin = false) {

    if (teams.size() < 2)
      throw invalid_argument("At least two teams are required");

    vector<string> ids;

    for (const auto &team : teams)
      ids.push_back(team.getId());

    // Add BYE when team count is odd.

    if (ids.size() % 2 != 0)
      ids.push_back("BYE");

    int n = static_cast<int>(ids.size());

    int totalRounds = n - 1;

    int matchesPerRound = n / 2;

    vector<MatchFixture> fixtures;

    string matchPrefix = "M";

    int matchNumber = 1;

    vector<string> rotation = ids;

    for (int round = 1; round <= totalRounds; round++) {

      for (int i = 0; i < matchesPerRound; i++) {

        string teamA = rotation[i];

        string teamB = rotation[n - 1 - i];

        // Skip BYE matches.

        if (teamA == "BYE" || teamB == "BYE")
          continue;

        MatchFixture fixture;

        fixture.matchId = matchPrefix + to_string(matchNumber++);

        fixture.team1Id = teamA;
        fixture.team2Id = teamB;

        fixture.roundNumber = round;

        fixtures.push_back(fixture);
      }

      // Circle method:
      // Keep first team fixed and rotate others.

      string last = rotation.back();

      for (int i = n - 1; i > 1; i--)
        rotation[i] = rotation[i - 1];

      rotation[1] = last;
    }

    if (doubleRoundRobin) {

      int originalSize = static_cast<int>(fixtures.size());

      for (int i = 0; i < originalSize; i++) {

        MatchFixture reverseFixture;

        reverseFixture.matchId = matchPrefix + to_string(matchNumber++);

        reverseFixture.team1Id = fixtures[i].team2Id;

        reverseFixture.team2Id = fixtures[i].team1Id;

        reverseFixture.roundNumber = fixtures[i].roundNumber + totalRounds;

        fixtures.push_back(reverseFixture);
      }
    }

    return fixtures;
  }
};

// =============================================
// 9. TOURNAMENT CLASS
// =============================================

class Tournament {

private:
  string tournamentId;
  string tournamentName;

  CricketFormat format;

  vector<Team> teams;

  vector<MatchFixture> fixtures;

  PointsTable pointsTable;

  bool fixturesGenerated = false;

  int getTeamIndex(const string &id) const {

    for (int i = 0; i < static_cast<int>(teams.size()); i++) {

      if (teams[i].getId() == id)
        return i;
    }

    return -1;
  }

  MatchFixture *findFixture(const string &matchId) {

    for (auto &fixture : fixtures) {

      if (fixture.matchId == matchId)
        return &fixture;
    }

    return nullptr;
  }

  void validateInnings(const InningsResult &innings) const {

    if (innings.runs < 0 || innings.wickets < 0 || innings.wickets > 10 ||
        innings.legalBalls < 0) {

      throw invalid_argument("Invalid innings result");
    }

    if (format != CricketFormat::TEST) {

      int maximumBalls = getMaximumOvers(format) * 6;

      if (innings.legalBalls > maximumBalls)
        throw invalid_argument("Over limit exceeded");
    }

    if (innings.allOut && innings.wickets != 10)
      throw invalid_argument("All-out status requires 10 wickets");
  }

public:
  Tournament(string id, string name, CricketFormat f)
      : tournamentId(id), tournamentName(name), format(f) {

    if (id.empty() || name.empty())
      throw invalid_argument("Invalid tournament details");
  }

  void registerTeam(const Team &team) {

    if (fixturesGenerated)
      throw runtime_error("Cannot add teams after fixtures are generated");

    if (getTeamIndex(team.getId()) != -1)
      throw invalid_argument("Duplicate team");

    teams.push_back(team);

    pointsTable.registerTeam(team);
  }

  Team *getTeam(const string &id) {

    int index = getTeamIndex(id);

    if (index == -1)
      return nullptr;

    return &teams[index];
  }

  void generateFixtures(bool doubleRoundRobin = false) {

    if (fixturesGenerated)
      throw runtime_error("Fixtures already generated");

    fixtures = FixtureGenerator::generate(teams, doubleRoundRobin);

    fixturesGenerated = true;
  }

  void displayFixtures() const {

    cout << "\n============== TOURNAMENT FIXTURES ==============\n";

    cout << "Tournament: " << tournamentName << endl;

    cout << "Format: " << formatName(format) << endl;

    for (const auto &fixture : fixtures) {

      int a = getTeamIndex(fixture.team1Id);
      int b = getTeamIndex(fixture.team2Id);

      cout << "\nRound " << fixture.roundNumber << " | Match "
           << fixture.matchId << endl;

      cout << teams[a].getName() << " VS " << teams[b].getName() << endl;

      cout << "Status: " << (fixture.completed ? "Completed" : "Upcoming")
           << endl;
    }

    cout << "=================================================\n";
  }

  void recordMatchResult(const string &matchId, const InningsResult &first,
                         const InningsResult &second, bool noResult = false) {

    MatchFixture *fixture = findFixture(matchId);

    if (fixture == nullptr)
      throw runtime_error("Match not found");

    if (fixture->completed)
      throw runtime_error("Match result already recorded");

    if (!noResult) {

      validateInnings(first);
      validateInnings(second);
    }

    if (noResult) {

      pointsTable.recordNoResult(fixture->team1Id, fixture->team2Id);

      fixture->result = "NO RESULT";
    } else {

      // Add NRR data for limited-overs matches.

      if (format != CricketFormat::TEST) {

        pointsTable.addInningsData(fixture->team1Id, first, second,
                                   getMaximumOvers(format));

        pointsTable.addInningsData(fixture->team2Id, second, first,
                                   getMaximumOvers(format));
      }

      if (first.runs == second.runs) {

        pointsTable.recordTie(fixture->team1Id, fixture->team2Id);

        fixture->result = "TIE";
      } else if (first.runs > second.runs) {

        pointsTable.recordWin(fixture->team1Id);

        pointsTable.recordLoss(fixture->team2Id);

        fixture->result = fixture->team1Id + " WON";
      } else {

        pointsTable.recordWin(fixture->team2Id);

        pointsTable.recordLoss(fixture->team1Id);

        fixture->result = fixture->team2Id + " WON";
      }
    }

    fixture->completed = true;

    cout << "\nResult recorded for " << matchId << ": " << fixture->result
         << endl;
  }

  void displayPointsTable() { pointsTable.display(); }

  void displayTeams() const {

    cout << "\n========== REGISTERED TEAMS ==========\n";

    for (const auto &team : teams) {

      cout << team.getId() << " - " << team.getName()
           << " | Players: " << team.getPlayerCount() << endl;
    }
  }

  void displayTournamentInfo() const {

    cout << "\n========== TOURNAMENT INFORMATION ==========\n";

    cout << "Tournament ID: " << tournamentId << endl;

    cout << "Tournament Name: " << tournamentName << endl;

    cout << "Format: " << formatName(format) << endl;

    cout << "Teams: " << teams.size() << endl;

    cout << "Matches: " << fixtures.size() << endl;

    cout << "Fixtures Generated: " << (fixturesGenerated ? "Yes" : "No")
         << endl;
  }
};

// =============================================
// 10. MAIN FUNCTION
// =============================================

int main() {

  try {

    // Create tournament

    Tournament tournament("TR001", "College Cricket Championship",
                          CricketFormat::T20);

    // Create teams

    Team india("T01", "India");
    Team australia("T02", "Australia");
    Team england("T03", "England");
    Team pakistan("T04", "Pakistan");

    // Add players

    india.addPlayer(Player("P01", "Virat Kohli", 37));

    india.addPlayer(Player("P02", "Rohit Sharma", 39));

    australia.addPlayer(Player("P03", "Steve Smith", 37));

    australia.addPlayer(Player("P04", "Pat Cummins", 33));

    england.addPlayer(Player("P05", "Joe Root", 35));

    pakistan.addPlayer(Player("P06", "Babar Azam", 32));

    // Register teams

    tournament.registerTeam(india);
    tournament.registerTeam(australia);
    tournament.registerTeam(england);
    tournament.registerTeam(pakistan);

    tournament.displayTournamentInfo();

    tournament.displayTeams();

    // Generate fixtures

    tournament.generateFixtures();

    tournament.displayFixtures();

    // -------------------------------------
    // Record sample match results
    // -------------------------------------

    // Match 1: India vs Pakistan
    // India 180, Pakistan 150

    InningsResult indiaScore;

    indiaScore.runs = 180;
    indiaScore.wickets = 6;
    indiaScore.legalBalls = 120;

    InningsResult pakistanScore;

    pakistanScore.runs = 150;
    pakistanScore.wickets = 8;
    pakistanScore.legalBalls = 120;

    tournament.recordMatchResult("M1", indiaScore, pakistanScore);

    // Match 2: Australia vs England
    // Australia 160, England 160

    InningsResult australiaScore;

    australiaScore.runs = 160;
    australiaScore.wickets = 7;
    australiaScore.legalBalls = 120;

    InningsResult englandScore;

    englandScore.runs = 160;
    englandScore.wickets = 9;
    englandScore.legalBalls = 120;

    tournament.recordMatchResult("M2", australiaScore, englandScore);

    // Match 3: India vs England
    // England wins

    InningsResult indiaScore2;

    indiaScore2.runs = 140;
    indiaScore2.wickets = 8;
    indiaScore2.legalBalls = 120;

    InningsResult englandScore2;

    englandScore2.runs = 142;
    englandScore2.wickets = 4;
    englandScore2.legalBalls = 110;

    tournament.recordMatchResult("M3", indiaScore2, englandScore2);

    tournament.displayPointsTable();

  } catch (const exception &e) {

    cerr << "\nERROR: " << e.what() << endl;

    return 1;
  }

  return 0;
}
