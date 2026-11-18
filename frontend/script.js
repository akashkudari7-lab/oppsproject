/**
 * Cricket Tournament Management System - Client Controller
 * Pure Vanilla JavaScript communicating with Tournament REST API
 */

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initEventListeners();
    loadDashboard();
    loadTeams();
    loadPlayers();
    loadTournaments();
});

// State
let allTeamsCache = [];
let allTournamentsCache = [];
let currentSelectedTourneyId = null;

// ============================================================================
// TAB NAVIGATION
// ============================================================================

function initTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            switchTab(tabId);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll('.nav-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.tab === tabId);
    });

    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `tab-${tabId}`);
    });

    // Refresh tab-specific data
    if (tabId === 'dashboard') loadDashboard();
    if (tabId === 'teams') loadTeams();
    if (tabId === 'players') loadPlayers();
    if (tabId === 'tournaments') {
        loadTeams();
        loadTournaments();
    }
    if (tabId === 'fixtures') {
        loadTournaments();
        if (currentSelectedTourneyId) loadFixtures(currentSelectedTourneyId);
    }
    if (tabId === 'standings') {
        loadTournaments();
        if (currentSelectedTourneyId) loadStandings(currentSelectedTourneyId);
    }
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function initEventListeners() {
    // 1. Add Team Form
    const formAddTeam = document.getElementById('formAddTeam');
    if (formAddTeam) {
        formAddTeam.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nameInput = document.getElementById('teamName');
            const name = nameInput.value.trim();
            if (!name) return;

            try {
                const res = await fetch('/api/teams', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name })
                });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    showToast(`Team '${data.data.name}' registered successfully!`, 'success');
                    nameInput.value = '';
                    loadTeams();
                    loadDashboard();
                } else {
                    showToast(data.message || 'Failed to add team.', 'error');
                }
            } catch (err) {
                showToast(`Error: ${err.message}`, 'error');
            }
        });
    }

    // Refresh Teams Button
    const btnRefreshTeams = document.getElementById('btnRefreshTeams');
    if (btnRefreshTeams) {
        btnRefreshTeams.addEventListener('click', loadTeams);
    }

    // 2. Add Player Form
    const formAddPlayer = document.getElementById('formAddPlayer');
    if (formAddPlayer) {
        formAddPlayer.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('playerName').value.trim();
            const role = document.getElementById('playerRole').value;
            const teamId = document.getElementById('playerTeamSelect').value;

            if (!name || !role || !teamId) {
                showToast('Please fill all player fields.', 'error');
                return;
            }

            try {
                const res = await fetch('/api/players', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, role, team_id: parseInt(teamId) })
                });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    showToast(`Player '${data.data.name}' assigned to team!`, 'success');
                    document.getElementById('playerName').value = '';
                    loadPlayers();
                    loadTeams();
                    loadDashboard();
                } else {
                    showToast(data.message || 'Failed to register player.', 'error');
                }
            } catch (err) {
                showToast(`Error: ${err.message}`, 'error');
            }
        });
    }

    // Filter Players by Team
    const filterPlayerTeam = document.getElementById('filterPlayerTeam');
    if (filterPlayerTeam) {
        filterPlayerTeam.addEventListener('change', (e) => {
            loadPlayers(e.target.value);
        });
    }

    // 3. Create Tournament Form
    const formCreateTourney = document.getElementById('formCreateTournament');
    if (formCreateTourney) {
        formCreateTourney.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('tourneyName').value.trim();
            const format = document.getElementById('tourneyFormat').value;

            const selectedCheckboxes = document.querySelectorAll('input[name="tourneyTeam"]:checked');
            const teamIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));

            if (!name) {
                showToast('Please enter a tournament name.', 'error');
                return;
            }

            if (teamIds.length < 2) {
                showToast('Please select at least 2 teams to generate fixtures.', 'error');
                return;
            }

            try {
                const res = await fetch('/api/tournaments', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, format, team_ids: teamIds })
                });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    const tourney = data.data;
                    showToast(`Tournament '${tourney.name}' created with ${tourney.fixtures.length} fixtures!`, 'success');
                    document.getElementById('tourneyName').value = '';
                    // Reset checkboxes
                    document.querySelectorAll('input[name="tourneyTeam"]').forEach(cb => cb.checked = false);
                    
                    loadTournaments();
                    loadDashboard();

                    // Switch to fixtures view
                    currentSelectedTourneyId = tourney.id;
                    switchTab('fixtures');
                    const sel = document.getElementById('selectTourneyForFixtures');
                    if (sel) sel.value = tourney.id;
                    loadFixtures(tourney.id);
                } else {
                    showToast(data.message || 'Failed to create tournament.', 'error');
                }
            } catch (err) {
                showToast(`Error: ${err.message}`, 'error');
            }
        });
    }

    // Refresh Tournaments Button
    const btnRefreshTourneys = document.getElementById('btnRefreshTourneys');
    if (btnRefreshTourneys) {
        btnRefreshTourneys.addEventListener('click', loadTournaments);
    }

    // Select Tournament for Fixtures
    const selTourneyFix = document.getElementById('selectTourneyForFixtures');
    if (selTourneyFix) {
        selTourneyFix.addEventListener('change', (e) => {
            const tourneyId = e.target.value;
            currentSelectedTourneyId = tourneyId ? parseInt(tourneyId) : null;
            if (currentSelectedTourneyId) {
                loadFixtures(currentSelectedTourneyId);
            } else {
                renderEmptyFixtures();
            }
        });
    }

    // Select Tournament for Standings
    const selTourneyStandings = document.getElementById('selectTourneyForStandings');
    if (selTourneyStandings) {
        selTourneyStandings.addEventListener('change', (e) => {
            const tourneyId = e.target.value;
            currentSelectedTourneyId = tourneyId ? parseInt(tourneyId) : null;
            if (currentSelectedTourneyId) {
                loadStandings(currentSelectedTourneyId);
            } else {
                renderEmptyStandings();
            }
        });
    }

    // 4. Score Entry Modal Form
    const formScoreEntry = document.getElementById('formScoreEntry');
    if (formScoreEntry) {
        formScoreEntry.addEventListener('submit', async (e) => {
            e.preventDefault();
            const matchId = document.getElementById('modalMatchId').value;
            const scoreA = parseInt(document.getElementById('scoreA').value);
            const wicketsA = parseInt(document.getElementById('wicketsA').value);
            const oversA = parseFloat(document.getElementById('oversA').value);

            const scoreB = parseInt(document.getElementById('scoreB').value);
            const wicketsB = parseInt(document.getElementById('wicketsB').value);
            const oversB = parseFloat(document.getElementById('oversB').value);

            try {
                const res = await fetch(`/api/matches/${matchId}/score`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        score_a: scoreA,
                        wickets_a: wicketsA,
                        overs_a: oversA,
                        score_b: scoreB,
                        wickets_b: wicketsB,
                        overs_b: oversB
                    })
                });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    showToast(`Result Calculated: ${data.data.result_description}`, 'success');
                    closeScoreModal();
                    if (currentSelectedTourneyId) {
                        loadFixtures(currentSelectedTourneyId);
                    }
                    loadDashboard();
                } else {
                    showToast(data.message || 'Failed to submit match score.', 'error');
                }
            } catch (err) {
                showToast(`Error: ${err.message}`, 'error');
            }
        });
    }

    // 5. Quick Demo Data Button
    const btnSeedDemo = document.getElementById('btnSeedDemo');
    if (btnSeedDemo) {
        btnSeedDemo.addEventListener('click', async () => {
            btnSeedDemo.disabled = true;
            btnSeedDemo.innerText = '⏳ Initializing...';
            try {
                const res = await fetch('/api/demo/seed', { method: 'POST' });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    showToast('Sample cricket teams, players & tournament seeded successfully!', 'success');
                    loadDashboard();
                    loadTeams();
                    loadPlayers();
                    loadTournaments();
                } else {
                    showToast(data.message || 'Failed to seed sample data.', 'error');
                }
            } catch (err) {
                showToast(`Error: ${err.message}`, 'error');
            } finally {
                btnSeedDemo.disabled = false;
                btnSeedDemo.innerText = '⚡ Quick Demo Data';
            }
        });
    }
}

// ============================================================================
// DASHBOARD LOADER
// ============================================================================

async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard/stats');
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            const stats = data.data;
            document.getElementById('statTeams').innerText = stats.total_teams || 0;
            document.getElementById('statPlayers').innerText = stats.total_players || 0;
            document.getElementById('statTournaments').innerText = stats.total_tournaments || 0;
            document.getElementById('statMatches').innerText = stats.total_completed_matches || 0;
        }
    } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
    }
}

// ============================================================================
// TEAMS LOADER & ACTIONS
// ============================================================================

async function loadTeams() {
    try {
        const res = await fetch('/api/teams');
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            allTeamsCache = data.data;
            renderTeamsTable(allTeamsCache);
            populateTeamDropdowns(allTeamsCache);
            populateTourneyTeamCheckboxes(allTeamsCache);
        }
    } catch (err) {
        console.error('Failed to load teams:', err);
    }
}

function renderTeamsTable(teams) {
    const tbody = document.querySelector('#tableTeams tbody');
    const teamCountSpan = document.getElementById('teamCount');
    if (teamCountSpan) teamCountSpan.innerText = teams.length;

    if (!tbody) return;
    if (teams.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No teams registered yet. Use the form to add one.</td></tr>`;
        return;
    }

    tbody.innerHTML = teams.map(team => `
        <tr>
            <td><strong>#${team.id}</strong></td>
            <td><strong>${escapeHtml(team.name)}</strong></td>
            <td><span class="badge badge-primary">${team.player_count} players</span></td>
            <td>
                <button class="btn btn-danger btn-xs" onclick="deleteTeam(${team.id}, '${escapeHtml(team.name)}')">
                    🗑️ Delete
                </button>
            </td>
        </tr>
    `).join('');
}

async function deleteTeam(teamId, teamName) {
    if (!confirm(`Are you sure you want to delete team '${teamName}'? This will also remove its players and tournament entries.`)) {
        return;
    }

    try {
        const res = await fetch(`/api/teams/${teamId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            showToast(`Team '${teamName}' deleted successfully.`, 'success');
            loadTeams();
            loadPlayers();
            loadTournaments();
            loadDashboard();
        } else {
            showToast(data.message || 'Failed to delete team.', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

function populateTeamDropdowns(teams) {
    const playerTeamSelect = document.getElementById('playerTeamSelect');
    const filterPlayerTeam = document.getElementById('filterPlayerTeam');

    if (playerTeamSelect) {
        const prevVal = playerTeamSelect.value;
        playerTeamSelect.innerHTML = `<option value="" disabled selected>Select Team...</option>` +
            teams.map(t => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join('');
        if (prevVal) playerTeamSelect.value = prevVal;
    }

    if (filterPlayerTeam) {
        const prevVal = filterPlayerTeam.value;
        filterPlayerTeam.innerHTML = `<option value="">All Teams (Show All)</option>` +
            teams.map(t => `<option value="${t.id}">${escapeHtml(t.name)}</option>`).join('');
        if (prevVal) filterPlayerTeam.value = prevVal;
    }
}

function populateTourneyTeamCheckboxes(teams) {
    const container = document.getElementById('tourneyTeamCheckboxes');
    if (!container) return;

    if (teams.length === 0) {
        container.innerHTML = `<span class="text-muted">No teams registered yet. Please add at least 2 teams first.</span>`;
        return;
    }

    container.innerHTML = teams.map(team => `
        <label class="checkbox-item">
            <input type="checkbox" name="tourneyTeam" value="${team.id}">
            <span>${escapeHtml(team.name)} (${team.player_count} players)</span>
        </label>
    `).join('');
}

// ============================================================================
// PLAYERS LOADER & ACTIONS
// ============================================================================

async function loadPlayers(teamIdFilter = '') {
    try {
        const url = teamIdFilter ? `/api/players?team_id=${teamIdFilter}` : '/api/players';
        const res = await fetch(url);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            renderPlayersTable(data.data);
        }
    } catch (err) {
        console.error('Failed to load players:', err);
    }
}

function renderPlayersTable(players) {
    const tbody = document.querySelector('#tablePlayers tbody');
    const countSpan = document.getElementById('playerCount');
    if (countSpan) countSpan.innerText = players.length;

    if (!tbody) return;
    if (players.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No players found.</td></tr>`;
        return;
    }

    tbody.innerHTML = players.map(p => {
        const roleClass = `role-${p.role.toLowerCase().replace(/[^a-z0-9]/g, '-')}`;
        return `
            <tr>
                <td>#${p.id}</td>
                <td><strong>${escapeHtml(p.name)}</strong></td>
                <td><span class="badge ${roleClass}">${p.role}</span></td>
                <td>${escapeHtml(p.team_name)}</td>
                <td>
                    <button class="btn btn-danger btn-xs" onclick="deletePlayer(${p.id}, '${escapeHtml(p.name)}')">
                        🗑️ Delete
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

async function deletePlayer(playerId, playerName) {
    if (!confirm(`Delete player '${playerName}'?`)) return;

    try {
        const res = await fetch(`/api/players/${playerId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            showToast(`Player '${playerName}' deleted.`, 'success');
            loadPlayers(document.getElementById('filterPlayerTeam')?.value || '');
            loadTeams();
            loadDashboard();
        } else {
            showToast(data.message || 'Failed to delete player.', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// ============================================================================
// TOURNAMENTS LOADER & ACTIONS
// ============================================================================

async function loadTournaments() {
    try {
        const res = await fetch('/api/tournaments');
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            allTournamentsCache = data.data;
            renderTournamentsList(allTournamentsCache);
            populateTourneyDropdowns(allTournamentsCache);
        }
    } catch (err) {
        console.error('Failed to load tournaments:', err);
    }
}

function renderTournamentsList(tourneys) {
    const container = document.getElementById('tournamentsList');
    if (!container) return;

    if (tourneys.length === 0) {
        container.innerHTML = `<p class="text-center text-muted">No tournaments created yet.</p>`;
        return;
    }

    container.innerHTML = tourneys.map(t => {
        let statusBadge = 'badge-muted';
        if (t.status === 'Completed') statusBadge = 'badge-primary';
        if (t.status === 'In Progress') statusBadge = 'badge-gold';

        return `
            <div class="card" style="margin-bottom: 0.85rem; padding: 1rem;">
                <div class="flex-between">
                    <div>
                        <h4 style="font-family: var(--font-heading); font-size: 1.05rem;">${escapeHtml(t.name)}</h4>
                        <div style="display:flex; gap: 0.4rem; margin-top: 0.3rem;">
                            <span class="badge badge-blue">${t.format} Format</span>
                            <span class="badge ${statusBadge}">${t.status}</span>
                            <span class="chip">${t.team_count} Teams</span>
                            <span class="chip">${t.completed_match_count || 0}/${t.match_count || 0} Matches</span>
                        </div>
                    </div>
                    <div style="display:flex; gap: 0.4rem;">
                        <button class="btn btn-secondary btn-xs" onclick="viewTournamentFixtures(${t.id})">
                            ⚔️ Fixtures
                        </button>
                        <button class="btn btn-primary btn-xs" onclick="viewTournamentStandings(${t.id})">
                            📋 Points
                        </button>
                        <button class="btn btn-danger btn-xs" onclick="deleteTournament(${t.id}, '${escapeHtml(t.name)}')">
                            🗑️
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function deleteTournament(tourneyId, tourneyName) {
    if (!confirm(`Delete tournament '${tourneyName}' and all its matches?`)) return;

    try {
        const res = await fetch(`/api/tournaments/${tourneyId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            showToast(`Tournament deleted.`, 'success');
            loadTournaments();
            loadDashboard();
            if (currentSelectedTourneyId === tourneyId) {
                currentSelectedTourneyId = null;
                renderEmptyFixtures();
                renderEmptyStandings();
            }
        } else {
            showToast(data.message || 'Failed to delete tournament.', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

function populateTourneyDropdowns(tourneys) {
    const selFix = document.getElementById('selectTourneyForFixtures');
    const selStan = document.getElementById('selectTourneyForStandings');

    const options = `<option value="">-- Choose a tournament --</option>` +
        tourneys.map(t => `<option value="${t.id}">${escapeHtml(t.name)} (${t.format})</option>`).join('');

    if (selFix) {
        const prev = selFix.value;
        selFix.innerHTML = options;
        if (prev) selFix.value = prev;
    }

    if (selStan) {
        const prev = selStan.value;
        selStan.innerHTML = options;
        if (prev) selStan.value = prev;
    }
}

function viewTournamentFixtures(tourneyId) {
    currentSelectedTourneyId = tourneyId;
    switchTab('fixtures');
    const sel = document.getElementById('selectTourneyForFixtures');
    if (sel) sel.value = tourneyId;
    loadFixtures(tourneyId);
}

function viewTournamentStandings(tourneyId) {
    currentSelectedTourneyId = tourneyId;
    switchTab('standings');
    const sel = document.getElementById('selectTourneyForStandings');
    if (sel) sel.value = tourneyId;
    loadStandings(tourneyId);
}

// ============================================================================
// FIXTURES & MATCH RESULTS
// ============================================================================

async function loadFixtures(tourneyId) {
    const container = document.getElementById('fixturesContainer');
    if (!container) return;

    container.innerHTML = `<div class="text-center" style="padding: 2rem;">⏳ Loading fixtures...</div>`;

    try {
        const res = await fetch(`/api/tournaments/${tourneyId}/matches`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            renderFixtures(data.data);
        } else {
            container.innerHTML = `<div class="empty-state"><h3>Error loading fixtures</h3><p>${data.message}</p></div>`;
        }
    } catch (err) {
        container.innerHTML = `<div class="empty-state"><h3>Network Error</h3><p>${err.message}</p></div>`;
    }
}

function renderFixtures(matches) {
    const container = document.getElementById('fixturesContainer');
    if (!container) return;

    if (matches.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="empty-state-icon">⚔️</span>
                <h3>No Fixtures Generated</h3>
                <p>No fixtures found for this tournament.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="fixtures-grid">
            ${matches.map(m => {
                const isCompleted = (m.status === 'Completed');
                const cardClass = isCompleted ? 'match-card completed' : 'match-card';

                return `
                    <div class="${cardClass}">
                        <div class="match-header">
                            <span class="match-num">Match #${m.match_number}</span>
                            <span class="badge ${isCompleted ? 'badge-primary' : 'badge-muted'}">
                                ${isCompleted ? 'Completed' : 'Scheduled'}
                            </span>
                        </div>
                        <div class="match-body">
                            <div class="match-team-row">
                                <span class="team-name ${m.winner_id === m.team_a_id ? 'text-primary' : ''}">
                                    ${escapeHtml(m.team_a_name)} ${m.winner_id === m.team_a_id ? '🏆' : ''}
                                </span>
                                <span class="team-score">
                                    ${isCompleted ? `${m.score_a}/${m.wickets_a} <small style="font-size:0.75rem; color:#64748b">(${m.overs_a} ov)</small>` : '-'}
                                </span>
                            </div>
                            <div class="match-vs">VS</div>
                            <div class="match-team-row">
                                <span class="team-name ${m.winner_id === m.team_b_id ? 'text-primary' : ''}">
                                    ${escapeHtml(m.team_b_name)} ${m.winner_id === m.team_b_id ? '🏆' : ''}
                                </span>
                                <span class="team-score">
                                    ${isCompleted ? `${m.score_b}/${m.wickets_b} <small style="font-size:0.75rem; color:#64748b">(${m.overs_b} ov)</small>` : '-'}
                                </span>
                            </div>

                            ${isCompleted ? `
                                <div class="match-result-banner ${m.is_tie ? 'tie' : ''}">
                                    ${escapeHtml(m.result_description || 'Match completed')}
                                </div>
                            ` : ''}
                        </div>
                        <div class="match-footer">
                            <button class="btn ${isCompleted ? 'btn-secondary' : 'btn-primary'} btn-sm" onclick="openScoreModal(${JSON.stringify(m).replace(/"/g, '&quot;')})">
                                ${isCompleted ? '✏️ Edit Score' : '🎯 Enter Score'}
                            </button>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderEmptyFixtures() {
    const container = document.getElementById('fixturesContainer');
    if (!container) return;
    container.innerHTML = `
        <div class="empty-state">
            <span class="empty-state-icon">⚔️</span>
            <h3>No Tournament Selected</h3>
            <p>Select a tournament from the dropdown above to view generated fixtures and enter match results.</p>
        </div>
    `;
}

// ============================================================================
// SCORE ENTRY MODAL
// ============================================================================

function openScoreModal(match) {
    document.getElementById('modalMatchId').value = match.id;
    document.getElementById('modalMatchTitle').innerText = `Match #${match.match_number} [${match.format} Format]`;
    document.getElementById('modalTeamAName').innerText = match.team_a_name;
    document.getElementById('modalTeamBName').innerText = match.team_b_name;
    document.getElementById('modalInnings1Label').innerText = match.team_a_name;
    document.getElementById('modalInnings2Label').innerText = match.team_b_name;

    // Prefill scores if editing
    document.getElementById('scoreA').value = match.score_a !== null ? match.score_a : '';
    document.getElementById('wicketsA').value = match.wickets_a !== null ? match.wickets_a : 4;
    document.getElementById('oversA').value = match.overs_a !== null ? match.overs_a : (match.format === 'ODI' ? 50 : 20);

    document.getElementById('scoreB').value = match.score_b !== null ? match.score_b : '';
    document.getElementById('wicketsB').value = match.wickets_b !== null ? match.wickets_b : 6;
    document.getElementById('oversB').value = match.overs_b !== null ? match.overs_b : (match.format === 'ODI' ? 50 : 20);

    const modal = document.getElementById('scoreModal');
    if (modal) modal.classList.add('show');
}

function closeScoreModal() {
    const modal = document.getElementById('scoreModal');
    if (modal) modal.classList.remove('show');
}

// ============================================================================
// POINTS TABLE LOADER
// ============================================================================

async function loadStandings(tourneyId) {
    const tbody = document.querySelector('#tableStandings tbody');
    const headerDiv = document.getElementById('standingsTourneyHeader');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" class="text-center">⏳ Calculating standings...</td></tr>`;

    try {
        const res = await fetch(`/api/tournaments/${tourneyId}/standings`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            const standings = data.data.standings;
            const tourney = data.data.tournament;

            if (headerDiv) {
                headerDiv.innerHTML = `
                    <h3>${escapeHtml(tourney.name)} - Standings</h3>
                    <small class="text-muted">Format: ${tourney.format}</small>
                `;
            }

            renderStandingsTable(standings);
        } else {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">${data.message}</td></tr>`;
        }
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Error: ${err.message}</td></tr>`;
    }
}

function renderStandingsTable(standings) {
    const tbody = document.querySelector('#tableStandings tbody');
    if (!tbody) return;

    if (standings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No teams in this tournament.</td></tr>`;
        return;
    }

    tbody.innerHTML = standings.map((row, idx) => {
        let rankClass = 'rank-badge';
        if (row.rank === 1) rankClass += ' rank-1';
        else if (row.rank === 2) rankClass += ' rank-2';
        else if (row.rank === 3) rankClass += ' rank-3';

        return `
            <tr>
                <td><span class="${rankClass}">${row.rank}</span></td>
                <td><strong>${escapeHtml(row.team_name)}</strong> ${row.rank === 1 ? '🥇' : ''}</td>
                <td>${row.played}</td>
                <td><span style="color:#16a34a; font-weight:700">${row.won}</span></td>
                <td><span style="color:#dc2626">${row.lost}</span></td>
                <td><span style="color:#d97706">${row.tied}</span></td>
                <td><span style="font-size:1.1rem; color:var(--primary-dark); font-weight:800">${row.points}</span></td>
            </tr>
        `;
    }).join('');
}

function renderEmptyStandings() {
    const tbody = document.querySelector('#tableStandings tbody');
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Select a tournament above to view its points table.</td></tr>`;
}

// ============================================================================
// TOAST NOTIFICATIONS & UTILITIES
// ============================================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'success' ? '✅' : (type === 'error' ? '❌' : 'ℹ️');
    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
