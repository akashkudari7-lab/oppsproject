#ifndef PLAYER_CPP
#define PLAYER_CPP

#include <iostream>
#include <string>
#include <sstream>

/**
 * Player Class
 * Demonstrates Encapsulation with private data members,
 * parameterized and default constructors, getters, setters,
 * and display methods.
 */
class Player {
private:
    int id;
    std::string name;
    std::string role; // "Batter", "Bowler", "All-rounder", "Wicket-keeper"
    int teamId;

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
    Player() : id(0), name(""), role("Batter"), teamId(0) {}

    // Parameterized constructor
    Player(int pId, const std::string& pName, const std::string& pRole, int pTeamId = 0)
        : id(pId), name(pName), role(pRole), teamId(pTeamId) {}

    // Getter methods
    int getId() const { return id; }
    std::string getName() const { return name; }
    std::string getRole() const { return role; }
    int getTeamId() const { return teamId; }

    // Setter methods
    void setId(int pId) { id = pId; }
    void setName(const std::string& pName) { name = pName; }
    void setRole(const std::string& pRole) { role = pRole; }
    void setTeamId(int pTeamId) { teamId = pTeamId; }

    // Display player information
    void display() const {
        std::cout << "  - [ID: " << id << "] " << name 
                  << " | Role: " << role 
                  << " | Team ID: " << teamId << std::endl;
    }

    // JSON serialization for communication with Flask
    std::string toJson() const {
        std::ostringstream ss;
        ss << "{"
           << "\"id\":" << id << ","
           << "\"name\":\"" << escapeJson(name) << "\","
           << "\"role\":\"" << escapeJson(role) << "\","
           << "\"team_id\":" << teamId
           << "}";
        return ss.str();
    }
};

#endif // PLAYER_CPP
