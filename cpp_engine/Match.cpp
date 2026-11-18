#ifndef MATCH_CPP
#define MATCH_CPP

#include "Team.cpp"
#include <iostream>
#include <string>
#include <sstream>
#include <iomanip>

/**
 * Base Abstract Class: Match
 * Demonstrates Abstraction and Encapsulation.
 * Defines standard attributes and polymorphic interface for all cricket match formats.
 */
class Match {
protected:
    int matchId;
    Team teamA;
    Team teamB;
    int scoreA;
    int scoreB;
    int wicketsA;
    int wicketsB;
    double oversA;
    double oversB;

    int winnerId;
    std::string winnerName;
    int loserId;
    std::string loserName;
    bool isTie;
    std::string resultDescription;
    bool isCompleted;
    std::string stage;
    bool isPlayoff;
    std::string manOfMatch;
    std::string manOfMatchPerformance;

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
    Match(int id, const Team& a, const Team& b)
        : matchId(id), teamA(a), teamB(b),
          scoreA(0), scoreB(0), wicketsA(0), wicketsB(0),
          oversA(0.0), oversB(0.0),
          winnerId(0), winnerName(""), loserId(0), loserName(""),
          isTie(false), resultDescription("Match Scheduled"), isCompleted(false),
          stage("Group"), isPlayoff(false), manOfMatch(""), manOfMatchPerformance("") {}

    virtual ~Match() {}

    // Pure Virtual Functions (Abstraction & Runtime Polymorphism Interface)
    virtual std::string getFormat() const = 0;
    virtual int getMaxOvers() const = 0;
    virtual std::string getFormatDescription() const = 0;

    // Getters
    int getMatchId() const { return matchId; }
    const Team& getTeamA() const { return teamA; }
    const Team& getTeamB() const { return teamB; }
    int getScoreA() const { return scoreA; }
    int getScoreB() const { return scoreB; }
    int getWicketsA() const { return wicketsA; }
    int getWicketsB() const { return wicketsB; }
    double getOversA() const { return oversA; }
    double getOversB() const { return oversB; }
    int getWinnerId() const { return winnerId; }
    std::string getWinnerName() const { return winnerName; }
    int getLoserId() const { return loserId; }
    std::string getLoserName() const { return loserName; }
    bool getIsTie() const { return isTie; }
    std::string getResultDescription() const { return resultDescription; }
    bool getIsCompleted() const { return isCompleted; }
    std::string getStage() const { return stage; }
    bool getIsPlayoff() const { return isPlayoff; }
    std::string getManOfMatch() const { return manOfMatch; }
    std::string getManOfMatchPerformance() const { return manOfMatchPerformance; }

    void setStage(const std::string& st, bool playoff = false) {
        stage = st;
        isPlayoff = playoff;
    }

    void setManOfMatch(const std::string& name, const std::string& perf) {
        manOfMatch = name;
        manOfMatchPerformance = perf;
    }

    // Setter for Scores
    void setScores(int sA, int wA, double oA, int sB, int wB, double oB) {
        scoreA = sA;
        wicketsA = wA;
        oversA = oA;
        scoreB = sB;
        wicketsB = wB;
        oversB = oB;
        isCompleted = true;
    }

    // Virtual function for Winner Calculation
    virtual void calculateWinner() {
        isCompleted = true;
        if (scoreA > scoreB) {
            winnerId = teamA.getId();
            winnerName = teamA.getName();
            loserId = teamB.getId();
            loserName = teamB.getName();
            isTie = false;
            int marginRuns = scoreA - scoreB;
            resultDescription = winnerName + " won by " + std::to_string(marginRuns) + " runs (" + getFormat() + ")";
        } else if (scoreB > scoreA) {
            winnerId = teamB.getId();
            winnerName = teamB.getName();
            loserId = teamA.getId();
            loserName = teamA.getName();
            isTie = false;
            int wicketsRemaining = 10 - wicketsB;
            if (wicketsRemaining <= 0) wicketsRemaining = 1;
            resultDescription = winnerName + " won by " + std::to_string(wicketsRemaining) + " wickets (" + getFormat() + ")";
        } else {
            // Scores are equal -> Match is a Tie
            winnerId = 0;
            winnerName = "Tie";
            loserId = 0;
            loserName = "";
            isTie = true;
            resultDescription = "Match ended in a Tie! Both teams scored " + std::to_string(scoreA) + " runs (" + getFormat() + ")";
        }
    }

    // Display match details & result
    virtual void displayResult() const {
        std::cout << "\n----------------------------------------------------\n";
        std::cout << "Match #" << matchId << " [" << getFormat() << " Format | Max " << getMaxOvers() << " Overs]\n";
        std::cout << "Rules: " << getFormatDescription() << "\n";
        std::cout << teamA.getName() << " vs " << teamB.getName() << "\n";
        if (isCompleted) {
            std::cout << "Innings 1: " << teamA.getName() << " -> " 
                      << scoreA << "/" << wicketsA << " (" << oversA << " ov)\n";
            std::cout << "Innings 2: " << teamB.getName() << " -> " 
                      << scoreB << "/" << wicketsB << " (" << oversB << " ov)\n";
            std::cout << "Result: " << resultDescription << "\n";
        } else {
            std::cout << "Status: Scheduled / Pending Result\n";
        }
        std::cout << "----------------------------------------------------\n";
    }

    // JSON serialization
    std::string toJson() const {
        std::ostringstream ss;
        ss << "{"
           << "\"match_id\":" << matchId << ","
           << "\"format\":\"" << escapeJson(getFormat()) << "\","
           << "\"max_overs\":" << getMaxOvers() << ","
           << "\"format_description\":\"" << escapeJson(getFormatDescription()) << "\","
           << "\"team_a_id\":" << teamA.getId() << ","
           << "\"team_a_name\":\"" << escapeJson(teamA.getName()) << "\","
           << "\"team_b_id\":" << teamB.getId() << ","
           << "\"team_b_name\":\"" << escapeJson(teamB.getName()) << "\","
           << "\"score_a\":" << scoreA << ","
           << "\"wickets_a\":" << wicketsA << ","
           << "\"overs_a\":" << oversA << ","
           << "\"score_b\":" << scoreB << ","
           << "\"wickets_b\":" << wicketsB << ","
           << "\"overs_b\":" << oversB << ","
           << "\"is_completed\":" << (isCompleted ? "true" : "false") << ","
           << "\"is_tie\":" << (isTie ? "true" : "false") << ","
           << "\"winner_id\":" << winnerId << ","
           << "\"winner_name\":\"" << escapeJson(winnerName) << "\","
           << "\"loser_id\":" << loserId << ","
           << "\"loser_name\":\"" << escapeJson(loserName) << "\","
           << "\"result_description\":\"" << escapeJson(resultDescription) << "\","
           << "\"stage\":\"" << escapeJson(stage) << "\","
           << "\"is_playoff\":" << (isPlayoff ? "true" : "false") << ","
           << "\"man_of_match\":\"" << escapeJson(manOfMatch) << "\","
           << "\"man_of_match_performance\":\"" << escapeJson(manOfMatchPerformance) << "\""
           << "}";
        return ss.str();
    }
};

/**
 * Derived Class: T20Match
 * Demonstrates Inheritance and Runtime Polymorphism.
 */
class T20Match : public Match {
public:
    T20Match(int id, const Team& a, const Team& b) : Match(id, a, b) {}

    std::string getFormat() const override {
        return "T20";
    }

    int getMaxOvers() const override {
        return 20;
    }

    std::string getFormatDescription() const override {
        return "Twenty20: 20 overs per innings, explosive batting and tight fielding.";
    }

    void calculateWinner() override {
        Match::calculateWinner();
    }
};

/**
 * Derived Class: ODIMatch
 * Demonstrates Inheritance and Runtime Polymorphism.
 */
class ODIMatch : public Match {
public:
    ODIMatch(int id, const Team& a, const Team& b) : Match(id, a, b) {}

    std::string getFormat() const override {
        return "ODI";
    }

    int getMaxOvers() const override {
        return 50;
    }

    std::string getFormatDescription() const override {
        return "One Day International: 50 overs per innings, strategic middle overs.";
    }

    void calculateWinner() override {
        Match::calculateWinner();
    }
};

/**
 * Derived Class: TestMatch
 * Demonstrates Inheritance and Runtime Polymorphism.
 */
class TestMatch : public Match {
public:
    TestMatch(int id, const Team& a, const Team& b) : Match(id, a, b) {}

    std::string getFormat() const override {
        return "Test";
    }

    int getMaxOvers() const override {
        return 90; // Standard 90 overs per day
    }

    std::string getFormatDescription() const override {
        return "Test Match: Traditional multi-day format testing resilience, technique, and stamina.";
    }

    void calculateWinner() override {
        isCompleted = true;
        if (scoreA > scoreB) {
            winnerId = teamA.getId();
            winnerName = teamA.getName();
            loserId = teamB.getId();
            loserName = teamB.getName();
            isTie = false;
            int margin = scoreA - scoreB;
            resultDescription = winnerName + " won by " + std::to_string(margin) + " runs (Test Match)";
        } else if (scoreB > scoreA) {
            winnerId = teamB.getId();
            winnerName = teamB.getName();
            loserId = teamA.getId();
            loserName = teamA.getName();
            isTie = false;
            int wicketsRemaining = 10 - wicketsB;
            if (wicketsRemaining <= 0) wicketsRemaining = 1;
            resultDescription = winnerName + " won by " + std::to_string(wicketsRemaining) + " wickets (Test Match)";
        } else {
            winnerId = 0;
            winnerName = "Tie";
            loserId = 0;
            loserName = "";
            isTie = true;
            resultDescription = "Historic Test Match finished in a dead heat Tie!";
        }
    }
};

/**
 * Factory Function for Match Creation
 * Returns a pointer to the abstract base class Match,
 * demonstrating dynamic binding / runtime polymorphism.
 */
inline Match* createMatch(const std::string& format, int id, const Team& a, const Team& b) {
    if (format == "ODI" || format == "odi") {
        return new ODIMatch(id, a, b);
    } else if (format == "Test" || format == "test") {
        return new TestMatch(id, a, b);
    } else {
        return new T20Match(id, a, b);
    }
}

#endif // MATCH_CPP
