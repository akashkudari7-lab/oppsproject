
#include <algorithm>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

// =============================================
// 1. BATTING STATISTICS
// =============================================

struct BattingCard {
  int runs = 0;
  int balls = 0;
  int fours = 0;
  int sixes = 0;
  int dismissals = 0;

  double strikeRate() const { return balls == 0 ? 0.0 : runs * 100.0 / balls; }

  double average() const {
    return dismissals == 0 ? 0.0 : static_cast<double>(runs) / dismissals;
  }
};

// =============================================
// 2. BOWLING STATISTICS
// =============================================

struct BowlingCard {
  int legalBalls = 0;
  int runsConceded = 0;
  int wickets = 0;

  double economy() const {
    return legalBalls == 0 ? 0.0 : runsConceded * 6.0 / legalBalls;
  }

  double average() const {
    return wickets == 0 ? 0.0 : static_cast<double>(runsConceded) / wickets;
  }
};

// =============================================
// 3. PLAYER CLASS
// =============================================

class Player {

private:
  string playerId;
  string name;
  int age;

  int matchesPlayed = 0;

  BattingCard batting;
  BowlingCard bowling;

public:
  Player(string id, string n, int a) : playerId(id), name(n), age(a) {

    if (id.empty() || n.empty() || a <= 0)
      throw invalid_argument("Invalid player details");
  }

  string getId() const { return playerId; }

  string getName() const { return name; }

  int getMatches() const { return matchesPlayed; }

  const BattingCard &getBatting() const { return batting; }

  const BowlingCard &getBowling() const { return bowling; }

  void addBatting(const BattingCard &stats) {
    batting.runs += stats.runs;
    batting.balls += stats.balls;
    batting.fours += stats.fours;
    batting.sixes += stats.sixes;
    batting.dismissals += stats.dismissals;
  }

  void addBowling(const BowlingCard &stats) {
    bowling.legalBalls += stats.legalBalls;
    bowling.runsConceded += stats.runsConceded;
    bowling.wickets += stats.wickets;
  }

  void addMatch() { matchesPlayed++; }

  void display() const {

    cout << "\nPlayer: " << name << endl;

    cout << "Matches: " << matchesPlayed << endl;

    cout << "Runs: " << batting.runs << endl;

    cout << "Batting Average: " << fixed << setprecision(2) << batting.average()
         << endl;

    cout << "Strike Rate: " << batting.strikeRate() << endl;

    cout << "Wickets: " << bowling.wickets << endl;

    cout << "Bowling Average: " << bowling.average() << endl;

    cout << "Economy: " << bowling.economy() << endl;
  }
};

// =============================================
// 4. TEAM CLASS
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

  Player *findPlayer(const string &id) {

    for (auto &player : players) {

      if (player.getId() == id)
        return &player;
    }

    return nullptr;
  }

  const vector<Player> &getPlayers() const { return players; }

  void displayTeam() const {

    cout << "\nTeam: " << teamName << endl;

    for (const auto &player : players) {
      cout << player.getName() << endl;
    }
  }
};

// =============================================
// 5. BALL EVENT
// =============================================

enum class Dismissal {
  NONE,
  BOWLED,
  CAUGHT,
  LBW,
  STUMPED,
  HIT_WICKET,
  RUN_OUT
};

struct BallEvent {

  int batterRuns = 0;

  bool wide = false;
  bool noBall = false;

  int byes = 0;
  int legByes = 0;

  Dismissal dismissal = Dismissal::NONE;

  string dismissedPlayerId;
};

// =============================================
// 6. INNINGS CLASS
// =============================================

class Innings {

private:
  string battingTeamId;

  string striker;
  string nonStriker;

  int totalRuns = 0;
  int totalWickets = 0;
  int legalBalls = 0;

  int maxOvers;

  bool completed = false;

  unordered_map<string, BattingCard> batting;
  unordered_map<string, BowlingCard> bowling;

  bool isBowlerCredited(Dismissal d) const {

    return d == Dismissal::BOWLED || d == Dismissal::CAUGHT ||
           d == Dismissal::LBW || d == Dismissal::STUMPED ||
           d == Dismissal::HIT_WICKET;
  }

public:
  Innings(const string &teamId, const string &openingBatter,
          const string &openingNonStriker, int overs)
      : battingTeamId(teamId), striker(openingBatter),
        nonStriker(openingNonStriker), maxOvers(overs) {

    if (teamId.empty() || openingBatter.empty() || openingNonStriker.empty() ||
        openingBatter == openingNonStriker || overs <= 0) {

      throw invalid_argument("Invalid innings setup");
    }
  }

  void recordDelivery(const BallEvent &event, const string &bowlerId) {

    if (completed)
      throw runtime_error("Innings completed");

    if (bowlerId.empty())
      throw invalid_argument("Invalid bowler");

    if (event.batterRuns < 0 || event.byes < 0 || event.legByes < 0) {

      throw invalid_argument("Negative runs");
    }

    if (event.wide && event.noBall)
      throw invalid_argument("Wide and no-ball conflict");

    if (event.wide &&
        (event.batterRuns > 0 || event.byes > 0 || event.legByes > 0)) {

      throw invalid_argument("Invalid wide combination");
    }

    if (event.byes > 0 && event.legByes > 0)
      throw invalid_argument("Invalid extras");

    if ((event.byes > 0 || event.legByes > 0) && event.batterRuns > 0) {

      throw invalid_argument("Invalid extras combination");
    }

    if (event.dismissal != Dismissal::NONE) {

      if (event.dismissedPlayerId != striker &&
          event.dismissedPlayerId != nonStriker) {

        throw invalid_argument("Invalid dismissed player");
      }

      if (event.wide && event.dismissal != Dismissal::RUN_OUT &&
          event.dismissal != Dismissal::STUMPED) {

        throw invalid_argument("Invalid wide dismissal");
      }

      if (event.noBall && event.dismissal != Dismissal::RUN_OUT) {

        throw invalid_argument("Invalid no-ball dismissal");
      }
    }

    bool legal = !event.wide && !event.noBall;

    if (legal && legalBalls >= maxOvers * 6)
      throw runtime_error("Over limit reached");

    string facingBatter = striker;

    int extras = (event.wide ? 1 : 0) + (event.noBall ? 1 : 0) + event.byes +
                 event.legByes;

    totalRuns += event.batterRuns + extras;

    // Batting statistics

    BattingCard &bat = batting[facingBatter];

    bat.runs += event.batterRuns;

    if (!event.wide)
      bat.balls++;

    if (event.batterRuns == 4)
      bat.fours++;

    if (event.batterRuns == 6)
      bat.sixes++;

    // Bowling statistics

    BowlingCard &bowl = bowling[bowlerId];

    if (legal) {
      legalBalls++;
      bowl.legalBalls++;
    }

    bowl.runsConceded +=
        event.batterRuns + (event.wide ? 1 : 0) + (event.noBall ? 1 : 0);

    // Wicket statistics

    if (event.dismissal != Dismissal::NONE) {

      totalWickets++;

      batting[event.dismissedPlayerId].dismissals++;

      if (isBowlerCredited(event.dismissal))
        bowl.wickets++;
    }

    // Strike rotation

    int completedRuns = event.batterRuns + event.byes + event.legByes;

    if (completedRuns % 2 == 1)
      swap(striker, nonStriker);

    if (legal && legalBalls % 6 == 0)
      swap(striker, nonStriker);

    // Vacate dismissed player's position

    if (event.dismissal != Dismissal::NONE) {

      if (event.dismissedPlayerId == striker)
        striker.clear();

      else if (event.dismissedPlayerId == nonStriker)
        nonStriker.clear();
    }

    // Innings completion

    if (totalWickets >= 10 || legalBalls >= maxOvers * 6) {

      completed = true;
    }
  }

  void setNextBatter(const string &id) {

    if (completed || id.empty())
      throw runtime_error("Cannot add batter");

    if (id == striker || id == nonStriker)
      throw invalid_argument("Player already batting");

    if (striker.empty())
      striker = id;

    else if (nonStriker.empty())
      nonStriker = id;

    else
      throw runtime_error("No vacant position");
  }

  string getTeamId() const { return battingTeamId; }

  int getRuns() const { return totalRuns; }

  int getWickets() const { return totalWickets; }

  int getBalls() const { return legalBalls; }

  bool isCompleted() const { return completed; }

  const unordered_map<string, BattingCard> &getBattingStats() const {
    return batting;
  }

  const unordered_map<string, BowlingCard> &getBowlingStats() const {
    return bowling;
  }

  void displayScore() const {

    cout << "\nTeam: " << battingTeamId << endl;

    cout << "Score: " << totalRuns << "/" << totalWickets << endl;

    cout << "Overs: " << legalBalls / 6 << "." << legalBalls % 6 << endl;
  }
};

// =============================================
// 7. MATCH RESULT
// =============================================

struct MatchResult {

  string winner;
  string resultType;
  int margin = 0;

  bool tie = false;
};

// =============================================
// 8. MATCH CLASS
// =============================================

class Match {

private:
  string matchId;

  Team &team1;
  Team &team2;

  Innings *firstInnings = nullptr;
  Innings *secondInnings = nullptr;

  bool finalized = false;

  MatchResult result;

  void transferStatistics(const Innings &innings) {

    Team *team = nullptr;

    if (innings.getTeamId() == team1.getId())
      team = &team1;

    else if (innings.getTeamId() == team2.getId())
      team = &team2;

    if (team == nullptr)
      throw runtime_error("Unknown batting team");

    for (const auto &entry : innings.getBattingStats()) {

      Player *player = team->findPlayer(entry.first);

      if (player == nullptr)
        throw runtime_error("Batter not registered in team");

      player->addBatting(entry.second);
    }

    Team *bowlingTeam = (team == &team1) ? &team2 : &team1;

    for (const auto &entry : innings.getBowlingStats()) {

      Player *player = bowlingTeam->findPlayer(entry.first);

      if (player == nullptr)
        throw runtime_error("Bowler not registered in team");

      player->addBowling(entry.second);
    }
  }

public:
  Match(const string &id, Team &t1, Team &t2)
      : matchId(id), team1(t1), team2(t2) {

    if (id.empty() || t1.getId() == t2.getId())
      throw invalid_argument("Invalid match");
  }

  void setInnings(Innings &first, Innings &second) {

    if (finalized)
      throw runtime_error("Match already finalized");

    if (first.getTeamId() == second.getTeamId())
      throw invalid_argument("Both innings cannot belong to same team");

    bool validTeams = (first.getTeamId() == team1.getId() &&
                       second.getTeamId() == team2.getId()) ||
                      (first.getTeamId() == team2.getId() &&
                       second.getTeamId() == team1.getId());

    if (!validTeams)
      throw invalid_argument("Invalid teams in match");

    if (!first.isCompleted() || !second.isCompleted())
      throw runtime_error("Both innings must be completed");

    firstInnings = &first;
    secondInnings = &second;
  }

  MatchResult calculateResult() {

    if (finalized)
      throw runtime_error("Match already finalized");

    if (firstInnings == nullptr || secondInnings == nullptr)
      throw runtime_error("Match innings not assigned");

    // Transfer statistics to player profiles

    transferStatistics(*firstInnings);
    transferStatistics(*secondInnings);

    // Increment matches played

    for (const auto &p : team1.getPlayers()) {
      team1.findPlayer(p.getId())->addMatch();
    }

    for (const auto &p : team2.getPlayers()) {
      team2.findPlayer(p.getId())->addMatch();
    }

    int score1 = firstInnings->getRuns();
    int score2 = secondInnings->getRuns();

    int wicketsLost = secondInnings->getWickets();

    if (score1 == score2) {

      result.tie = true;
      result.resultType = "TIE";
      result.winner = "No winner";
      result.margin = 0;
    } else if (score2 > score1) {

      result.winner = secondInnings->getTeamId();

      result.resultType = "WICKETS";

      result.margin = 10 - wicketsLost;
    } else {

      result.winner = firstInnings->getTeamId();

      result.resultType = "RUNS";

      result.margin = score1 - score2;
    }

    finalized = true;

    return result;
  }

  void displayResult() const {

    if (!finalized)
      throw runtime_error("Calculate result first");

    cout << "\n========== MATCH RESULT ==========\n";

    cout << "Match ID: " << matchId << endl;

    firstInnings->displayScore();
    secondInnings->displayScore();

    if (result.tie) {

      cout << "\nMATCH TIED!" << endl;
    } else {

      cout << "\nWinner: " << result.winner << endl;

      cout << "Won by: " << result.margin << " " << result.resultType << endl;
    }

    cout << "==================================\n";
  }
};

// =============================================
// 9. PLAYER OF THE MATCH
// =============================================

Player *findPlayerOfMatch(Team &team1, Team &team2) {

  Player *bestPlayer = nullptr;

  double bestScore = -1;

  auto evaluate = [&](Team &team) {
    for (const auto &p : team.getPlayers()) {

      Player *player = team.findPlayer(p.getId());

      const auto &bat = player->getBatting();
      const auto &bowl = player->getBowling();

      // Simple illustrative performance formula.
      // This is not an official cricket rating.

      double score =
          bat.runs * 1.0 + bowl.wickets * 25.0 - bowl.runsConceded * 0.15;

      if (score > bestScore) {

        bestScore = score;
        bestPlayer = player;
      }
    }
  };

  evaluate(team1);
  evaluate(team2);

  return bestPlayer;
}

// =============================================
// 10. MAIN FUNCTION
// =============================================

int main() {

  try {

    // Create teams

    Team india("IND", "India");

    Team australia("AUS", "Australia");

    // Register Indian players

    india.addPlayer(Player("P01", "Virat Kohli", 37));
    india.addPlayer(Player("P02", "Rohit Sharma", 39));
    india.addPlayer(Player("P03", "Shubman Gill", 27));
    india.addPlayer(Player("P04", "Hardik Pandya", 33));

    // Register Australian players

    australia.addPlayer(Player("P05", "Steve Smith", 37));
    australia.addPlayer(Player("P06", "David Warner", 40));
    australia.addPlayer(Player("P07", "Pat Cummins", 33));
    australia.addPlayer(Player("P08", "Mitchell Starc", 36));

    // Create first innings

    Innings first("IND", "P01", "P02", 1);

    BallEvent ball;

    // Six legal deliveries.
    // India scores 12 runs.

    ball.batterRuns = 4;
    first.recordDelivery(ball, "P07");

    ball = BallEvent{};
    ball.batterRuns = 2;
    first.recordDelivery(ball, "P07");

    ball = BallEvent{};
    ball.batterRuns = 1;
    first.recordDelivery(ball, "P07");

    ball = BallEvent{};
    ball.batterRuns = 4;
    first.recordDelivery(ball, "P07");

    ball = BallEvent{};
    first.recordDelivery(ball, "P07");

    ball = BallEvent{};
    ball.batterRuns = 1;
    first.recordDelivery(ball, "P07");

    // Create second innings

    Innings second("AUS", "P05", "P06", 1);

    // Australia scores 9 runs.

    ball = BallEvent{};
    ball.batterRuns = 1;
    second.recordDelivery(ball, "P03");

    ball = BallEvent{};
    ball.batterRuns = 2;
    second.recordDelivery(ball, "P03");

    ball = BallEvent{};
    ball.batterRuns = 4;
    second.recordDelivery(ball, "P03");

    ball = BallEvent{};
    ball.batterRuns = 1;
    second.recordDelivery(ball, "P03");

    ball = BallEvent{};
    second.recordDelivery(ball, "P03");

    ball = BallEvent{};
    ball.batterRuns = 1;
    second.recordDelivery(ball, "P03");

    // Create match

    Match match("M001", india, australia);

    match.setInnings(first, second);

    MatchResult result = match.calculateResult();

    // Display match result

    match.displayResult();

    // Display player statistics

    cout << "\n========== PLAYER STATISTICS ==========\n";

    for (const auto &player : india.getPlayers())
      india.findPlayer(player.getId())->display();

    for (const auto &player : australia.getPlayers())
      australia.findPlayer(player.getId())->display();

    // Player of the Match

    Player *best = findPlayerOfMatch(india, australia);

    if (best != nullptr) {

      cout << "\nPLAYER OF THE MATCH: " << best->getName() << endl;
    }

  } catch (const exception &e) {

    cerr << "\nERROR: " << e.what() << endl;

    return 1;
  }

  return 0;
}
