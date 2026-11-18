#ifndef TEAM_CPP
#define TEAM_CPP

#include "Player.cpp"
#include <vector>
#include <algorithm>
#include <iostream>
#include <sstream>

/**
 * Team Class
 * Encapsulates team identification, team name, and a dynamic collection
 * of Player objects. Provides methods to add/remove players and display details.
 */
class Team {
private:
    int id;
    std::string name;
    std::vector<Player> players;

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
    // Default constructor
    Team() : id(0), name("") {}

    // Parameterized constructor
    Team(int tId, const std::string& tName) : id(tId), name(tName) {}

    // Getters and Setters
    int getId() const { return id; }
    void setId(int tId) { id = tId; }

    std::string getName() const { return name; }
    void setName(const std::string& tName) { name = tName; }

    const std::vector<Player>& getPlayers() const { return players; }
    int getPlayerCount() const { return static_cast<int>(players.size()); }

    // Add Player to Team
    void addPlayer(const Player& player) {
        players.push_back(player);
    }

    // Remove Player by ID
    bool removePlayer(int playerId) {
        for (auto it = players.begin(); it != players.end(); ++it) {
            if (it->getId() == playerId) {
                players.erase(it);
                return true;
            }
        }
        return false;
    }

    // Find Player by ID
    const Player* findPlayer(int playerId) const {
        for (const auto& p : players) {
            if (p.getId() == playerId) return &p;
        }
        return nullptr;
    }

    // Display Team and Squad details
    void display() const {
        std::cout << "====================================================\n";
        std::cout << "Team ID: " << id << " | Team Name: " << name << "\n";
        std::cout << "Squad (" << players.size() << " players registered):\n";
        if (players.empty()) {
            std::cout << "  (No players currently assigned to this team)\n";
        } else {
            for (const auto& player : players) {
                player.display();
            }
        }
        std::cout << "====================================================\n";
    }

    // JSON serialization
    std::string toJson() const {
        std::ostringstream ss;
        ss << "{"
           << "\"id\":" << id << ","
           << "\"name\":\"" << escapeJson(name) << "\","
           << "\"player_count\":" << players.size() << ","
           << "\"players\":[";
        for (size_t i = 0; i < players.size(); ++i) {
            if (i > 0) ss << ",";
            ss << players[i].toJson();
        }
        ss << "]}";
        return ss.str();
    }
};

#endif // TEAM_CPP
