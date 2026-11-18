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
let currentTournamentMatches = [];
let currentStageFilter = 'all';
let currentScorecardData = null;
let currentInningsView = 1;

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
    if (tabId === 'crex-stats') {
        loadTournaments();
        if (currentSelectedTourneyId) loadCrexStats(currentSelectedTourneyId);
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

    // Select Tournament for Crex Stats
    const selTourneyCrexStats = document.getElementById('selectTourneyForCrexStats');
    if (selTourneyCrexStats) {
        selTourneyCrexStats.addEventListener('change', (e) => {
            const tourneyId = e.target.value;
            currentSelectedTourneyId = tourneyId ? parseInt(tourneyId) : null;
            if (currentSelectedTourneyId) {
                loadCrexStats(currentSelectedTourneyId);
            } else {
                renderEmptyCrexStats();
            }
        });
    }

    // Generate Playoff / Qualifier Buttons
    const btnGenQual = document.getElementById('btnGenerateQualifiers');
    if (btnGenQual) {
        btnGenQual.addEventListener('click', () => {
            if (!currentSelectedTourneyId) {
                showToast('Please select a tournament first.', 'error');
                return;
            }
            triggerGenerateQualifiers(currentSelectedTourneyId);
        });
    }

    const btnGenQualStandings = document.getElementById('btnGenerateQualifiersFromStandings');
    if (btnGenQualStandings) {
        btnGenQualStandings.addEventListener('click', () => {
            if (!currentSelectedTourneyId) {
                showToast('Please select a tournament first.', 'error');
                return;
            }
            triggerGenerateQualifiers(currentSelectedTourneyId);
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

    const selCrex = document.getElementById('selectTourneyForCrexStats');
    if (selCrex) {
        const prev = selCrex.value;
        selCrex.innerHTML = options;
        if (prev) selCrex.value = prev;
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

    container.innerHTML = `<div class="text-center" style="padding: 2rem;">⏳ Loading fixtures & qualifiers...</div>`;

    try {
        const res = await fetch(`/api/tournaments/${tourneyId}/matches`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            currentTournamentMatches = data.data || [];
            updateStageCounts(currentTournamentMatches);
            renderFixtures(currentTournamentMatches);
        } else {
            container.innerHTML = `<div class="empty-state"><h3>Error loading fixtures</h3><p>${data.message}</p></div>`;
        }
    } catch (err) {
        container.innerHTML = `<div class="empty-state"><h3>Network Error</h3><p>${err.message}</p></div>`;
    }
}

function updateStageCounts(matches) {
    const countAll = document.getElementById('countAllMatches');
    const countGroup = document.getElementById('countGroupMatches');
    const countPlayoff = document.getElementById('countPlayoffMatches');

    if (countAll) countAll.innerText = matches.length;
    if (countGroup) countGroup.innerText = matches.filter(m => !m.is_playoff).length;
    if (countPlayoff) countPlayoff.innerText = matches.filter(m => m.is_playoff).length;
}

function filterFixturesByStage(stage) {
    currentStageFilter = stage;
    document.querySelectorAll('.filter-pill').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === stage);
    });
    renderFixtures(currentTournamentMatches);
}

function renderFixtures(allMatches) {
    const container = document.getElementById('fixturesContainer');
    if (!container) return;

    // Filter matches
    let matches = allMatches;
    if (currentStageFilter === 'group') {
        matches = allMatches.filter(m => !m.is_playoff);
    } else if (currentStageFilter === 'playoff') {
        matches = allMatches.filter(m => m.is_playoff);
    }

    // Check for Grand Final Winner Champion Banner
    const finalMatch = allMatches.find(m => (m.stage === 'Final' || m.stage === 'Grand Final') && m.status === 'Completed');
    const champContainer = document.getElementById('championBannerContainer');
    if (champContainer) {
        if (finalMatch && finalMatch.winner_name && finalMatch.winner_name !== 'Tie') {
            champContainer.innerHTML = `
                <div class="champion-banner">
                    <div class="champion-trophy">🏆</div>
                    <h2>TOURNAMENT CHAMPION</h2>
                    <h1 style="font-size:2.25rem; font-family:var(--font-heading); color:#fef08a; margin: 0.35rem 0;">${escapeHtml(finalMatch.winner_name)}</h1>
                    <p>${escapeHtml(finalMatch.result_description || 'Crowned Champion of the Tournament!')}</p>
                </div>
            `;
        } else {
            champContainer.innerHTML = '';
        }
    }

    if (matches.length === 0) {
        const msg = currentStageFilter === 'playoff'
            ? 'No playoff matches generated yet. Click "⚡ Generate Playoff Matches" once group stage finishes!'
            : 'No fixtures found for this tournament.';
        container.innerHTML = `
            <div class="empty-state">
                <span class="empty-state-icon">⚔️</span>
                <h3>No Matches Available</h3>
                <p>${msg}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="fixtures-grid">
            ${matches.map(m => {
                const isCompleted = (m.status === 'Completed');
                const isPlayoff = Boolean(m.is_playoff);
                let cardClass = isCompleted ? 'match-card completed' : 'match-card';
                if (isPlayoff) cardClass += ' playoff';

                // Stage Badge
                let stageBadgeHtml = '';
                if (m.stage === 'Qualifier 1') {
                    stageBadgeHtml = `<span class="badge badge-qualifier-1">⚡ QUALIFIER 1</span>`;
                } else if (m.stage === 'Eliminator') {
                    stageBadgeHtml = `<span class="badge badge-eliminator">🔥 ELIMINATOR</span>`;
                } else if (m.stage === 'Qualifier 2') {
                    stageBadgeHtml = `<span class="badge badge-qualifier-2">⚡ QUALIFIER 2</span>`;
                } else if (m.stage === 'Final') {
                    stageBadgeHtml = `<span class="badge badge-final">🏆 GRAND FINAL</span>`;
                } else if (isPlayoff) {
                    stageBadgeHtml = `<span class="badge badge-gold">⚡ ${escapeHtml(m.stage)}</span>`;
                }

                // Run rate calculation for completed matches
                let rrA = '';
                let rrB = '';
                if (isCompleted) {
                    if (m.overs_a && m.overs_a > 0) {
                        const decA = Math.floor(m.overs_a) + ((m.overs_a % 1) * 10) / 6.0;
                        rrA = ` <span style="font-size:0.75rem; color:#64748b;">(RR: ${(m.score_a / decA).toFixed(2)})</span>`;
                    }
                    if (m.overs_b && m.overs_b > 0) {
                        const decB = Math.floor(m.overs_b) + ((m.overs_b % 1) * 10) / 6.0;
                        rrB = ` <span style="font-size:0.75rem; color:#64748b;">(RR: ${(m.score_b / decB).toFixed(2)})</span>`;
                    }
                }

                return `
                    <div class="${cardClass}">
                        <div class="match-header">
                            <div>
                                <span class="match-num">Match #${m.match_number}</span>
                                ${stageBadgeHtml}
                            </div>
                            <span class="badge ${isCompleted ? 'badge-primary' : 'badge-muted'}">
                                ${isCompleted ? 'Completed' : 'Scheduled'}
                            </span>
                        </div>
                        <div class="match-body">
                            <div class="match-team-row">
                                <span class="team-name ${m.winner_id === m.team_a_id ? 'text-primary font-bold' : ''}">
                                    ${escapeHtml(m.team_a_name || 'TBD')} ${m.winner_id === m.team_a_id ? '🏆' : ''}
                                    ${m.team_a_source ? `<small class="text-muted" style="display:block; font-size:0.72rem;">${escapeHtml(m.team_a_source)}</small>` : ''}
                                </span>
                                <span class="team-score">
                                    ${isCompleted ? `${m.score_a}/${m.wickets_a} <small style="font-size:0.75rem; color:#64748b">(${m.overs_a} ov)</small>${rrA}` : '-'}
                                </span>
                            </div>
                            <div class="match-vs">VS</div>
                            <div class="match-team-row">
                                <span class="team-name ${m.winner_id === m.team_b_id ? 'text-primary font-bold' : ''}">
                                    ${escapeHtml(m.team_b_name || 'TBD')} ${m.winner_id === m.team_b_id ? '🏆' : ''}
                                    ${m.team_b_source ? `<small class="text-muted" style="display:block; font-size:0.72rem;">${escapeHtml(m.team_b_source)}</small>` : ''}
                                </span>
                                <span class="team-score">
                                    ${isCompleted ? `${m.score_b}/${m.wickets_b} <small style="font-size:0.75rem; color:#64748b">(${m.overs_b} ov)</small>${rrB}` : '-'}
                                </span>
                            </div>

                            ${isCompleted ? `
                                <div class="match-result-banner ${m.is_tie ? 'tie' : ''}">
                                    ${escapeHtml(m.result_description || 'Match completed')}
                                </div>
                                ${m.man_of_match ? `
                                    <div style="font-size: 0.78rem; color:#78350f; background:#fef3c7; border-radius:4px; padding:0.25rem 0.5rem; margin-top:0.35rem; display:flex; align-items:center; gap:0.35rem;">
                                        <span>⭐</span> <strong>Player of Match:</strong> ${escapeHtml(m.man_of_match)} <span class="text-muted">(${escapeHtml(m.man_of_match_performance || '')})</span>
                                    </div>
                                ` : ''}
                            ` : ''}
                        </div>
                        <div class="match-footer" style="display:flex; justify-content:space-between; gap:0.4rem;">
                            ${isCompleted ? `
                                <button class="btn btn-secondary btn-sm" onclick="openCrexScorecard(${m.id})">
                                    📊 Crex Scorecard
                                </button>
                                <button class="btn btn-secondary btn-sm" onclick="openScoreModal(${JSON.stringify(m).replace(/"/g, '&quot;')})">
                                    ✏️ Edit
                                </button>
                            ` : `
                                <button class="btn btn-primary btn-sm" style="width:100%;" onclick="openScoreModal(${JSON.stringify(m).replace(/"/g, '&quot;')})">
                                    🎯 Enter Score
                                </button>
                            `}
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

async function triggerGenerateQualifiers(tourneyId) {
    if (!confirm('Generate Qualifier & Playoff matches (Qualifier 1, Eliminator, Qualifier 2, Final) based on the current points table ranking?')) {
        return;
    }

    try {
        const res = await fetch(`/api/tournaments/${tourneyId}/qualifiers/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            showToast(data.message || 'Qualifier matches generated!', 'success');
            loadFixtures(tourneyId);
            loadDashboard();
            switchTab('fixtures');
            filterFixturesByStage('playoff');
        } else {
            showToast(data.message || 'Failed to generate qualifiers.', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
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
    const stagePrefix = match.stage ? `[${match.stage}] ` : '';
    document.getElementById('modalMatchTitle').innerText = `${stagePrefix}Match #${match.match_number} [${match.format} Format]`;
    document.getElementById('modalTeamAName').innerText = match.team_a_name || 'Team A';
    document.getElementById('modalTeamBName').innerText = match.team_b_name || 'Team B';
    document.getElementById('modalInnings1Label').innerText = match.team_a_name || 'Team A';
    document.getElementById('modalInnings2Label').innerText = match.team_b_name || 'Team B';

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
// POINTS TABLE LOADER & NET RUN RATE (NRR)
// ============================================================================

async function loadStandings(tourneyId) {
    const tbody = document.querySelector('#tableStandings tbody');
    const headerDiv = document.getElementById('standingsTourneyHeader');
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="8" class="text-center">⏳ Calculating Net Run Rate and standings...</td></tr>`;

    try {
        const res = await fetch(`/api/tournaments/${tourneyId}/standings`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            const standings = data.data.standings;
            const tourney = data.data.tournament;

            if (headerDiv) {
                headerDiv.innerHTML = `
                    <h3>${escapeHtml(tourney.name)} - Standings</h3>
                    <small class="text-muted">Format: ${tourney.format} • Net Run Rate (NRR) Calculated</small>
                `;
            }

            renderStandingsTable(standings);
        } else {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">${data.message}</td></tr>`;
        }
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Error: ${err.message}</td></tr>`;
    }
}

function renderStandingsTable(standings) {
    const tbody = document.querySelector('#tableStandings tbody');
    if (!tbody) return;

    if (standings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No teams in this tournament.</td></tr>`;
        return;
    }

    tbody.innerHTML = standings.map((row, idx) => {
        let rankClass = 'rank-badge';
        if (row.rank === 1) rankClass += ' rank-1';
        else if (row.rank === 2) rankClass += ' rank-2';
        else if (row.rank === 3) rankClass += ' rank-3';

        const nrrVal = (typeof row.nrr === 'number') ? row.nrr : 0.0;
        let nrrStr = (nrrVal > 0 ? '+' : '') + nrrVal.toFixed(3);
        let nrrClass = 'nrr-zero';
        if (nrrVal > 0) nrrClass = 'nrr-pos';
        else if (nrrVal < 0) nrrClass = 'nrr-neg';

        const isQualified = row.rank <= 4;
        const qualChip = isQualified
            ? `<span class="chip" style="font-size:0.68rem; margin-left:6px; background:#fef3c7; color:#b45309; font-weight:700;">Q</span>`
            : '';

        return `
            <tr>
                <td><span class="${rankClass}">${row.rank}</span></td>
                <td><strong>${escapeHtml(row.team_name)}</strong> ${row.rank === 1 ? '🥇' : ''} ${qualChip}</td>
                <td class="text-center">${row.played}</td>
                <td class="text-center"><span style="color:#16a34a; font-weight:700">${row.won}</span></td>
                <td class="text-center"><span style="color:#dc2626">${row.lost}</span></td>
                <td class="text-center"><span style="color:#d97706">${row.tied}</span></td>
                <td class="text-center"><span class="${nrrClass}">${nrrStr}</span></td>
                <td class="text-center"><span style="font-size:1.1rem; color:var(--primary-dark); font-weight:800">${row.points}</span></td>
            </tr>
        `;
    }).join('');
}

function renderEmptyStandings() {
    const tbody = document.querySelector('#tableStandings tbody');
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Select a tournament above to view its points table.</td></tr>`;
}

// ============================================================================
// CREX LIVE SCORECARD MODAL & EDITOR
// ============================================================================

async function openCrexScorecard(matchId) {
    try {
        const res = await fetch(`/api/matches/${matchId}/scorecard`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            currentScorecardData = data.data;
            const m = currentScorecardData.match;

            // Modal Title & Badges
            document.getElementById('crexModalTitle').innerText = `Match #${m.match_number}: ${m.team_a_name} vs ${m.team_b_name}`;
            document.getElementById('crexMatchStageBadge').innerText = m.stage || (m.is_playoff ? 'Playoff' : 'Group Match');
            document.getElementById('crexMatchFormatBadge').innerText = `${m.format} Format`;

            // Team Scores Banner
            document.getElementById('crexTeamAName').innerText = m.team_a_name;
            document.getElementById('crexTeamAScore').innerText = `${m.score_a || 0}/${m.wickets_a || 0}`;
            const rrA = m.overs_a ? (m.score_a / (Math.floor(m.overs_a) + (m.overs_a % 1 * 10) / 6.0)).toFixed(2) : '0.00';
            document.getElementById('crexTeamARR').innerText = `(${m.overs_a || 0.0} ov) RR: ${rrA}`;

            document.getElementById('crexTeamBName').innerText = m.team_b_name;
            document.getElementById('crexTeamBScore').innerText = `${m.score_b || 0}/${m.wickets_b || 0}`;
            const rrB = m.overs_b ? (m.score_b / (Math.floor(m.overs_b) + (m.overs_b % 1 * 10) / 6.0)).toFixed(2) : '0.00';
            document.getElementById('crexTeamBRR').innerText = `(${m.overs_b || 0.0} ov) RR: ${rrB}`;

            document.getElementById('crexResultDesc').innerText = m.result_description || 'Match Completed';

            // Player of the Match Banner
            const momBanner = document.getElementById('crexMomBanner');
            if (m.man_of_match) {
                document.getElementById('crexMomName').innerText = m.man_of_match;
                document.getElementById('crexMomPerf').innerText = m.man_of_match_performance || 'Match-winning performance';
                momBanner.style.display = 'flex';
            } else {
                momBanner.style.display = 'none';
            }

            // Innings Tabs Labels
            document.getElementById('labelInnings1Tab').innerText = `${m.team_a_name} - ${m.score_a || 0}/${m.wickets_a || 0}`;
            document.getElementById('labelInnings2Tab').innerText = `${m.team_b_name} - ${m.score_b || 0}/${m.wickets_b || 0}`;

            // Render Innings 1 by default
            currentInningsView = 1;
            renderCrexInnings(1);
            toggleCrexEditor(false);

            const modal = document.getElementById('crexScorecardModal');
            if (modal) modal.classList.add('show');
        } else {
            showToast(data.message || 'Failed to load scorecard.', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

function closeCrexModal() {
    const modal = document.getElementById('crexScorecardModal');
    if (modal) modal.classList.remove('show');
    toggleCrexEditor(false);
}

function switchCrexInnings(innNum) {
    currentInningsView = innNum;
    document.getElementById('btnInnings1Tab').classList.toggle('active', innNum === 1);
    document.getElementById('btnInnings2Tab').classList.toggle('active', innNum === 2);
    renderCrexInnings(innNum);
}

function renderCrexInnings(innNum) {
    if (!currentScorecardData) return;
    const inn = (innNum === 1) ? currentScorecardData.innings1 : currentScorecardData.innings2;
    if (!inn) return;

    // Batting Table
    const batTbody = document.querySelector('#tableCrexBatting tbody');
    if (batTbody) {
        if (!inn.batting || inn.batting.length === 0) {
            batTbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No batting data recorded.</td></tr>`;
        } else {
            batTbody.innerHTML = inn.batting.map(b => `
                <tr>
                    <td><strong>${escapeHtml(b.player_name)}</strong></td>
                    <td style="color:#64748b; font-size:0.82rem; font-style:italic;">${escapeHtml(b.dismissal)}</td>
                    <td class="text-right"><strong>${b.runs}</strong></td>
                    <td class="text-right" style="color:#64748b;">${b.balls}</td>
                    <td class="text-right">${b.fours}</td>
                    <td class="text-right">${b.sixes}</td>
                    <td class="text-right" style="font-weight:600; color:#0f766e;">${b.strike_rate}</td>
                </tr>
            `).join('');
        }
    }

    // Extras & Totals
    document.getElementById('crexExtras').innerText = inn.extras || 0;
    document.getElementById('crexTotalScore').innerText = `${inn.score || 0}/${inn.wickets || 0}`;
    document.getElementById('crexTotalOvers').innerText = `(${inn.overs || 0.0} Ov, RR: ${inn.run_rate || 0.0})`;

    // Did Not Bat
    const dnbRow = document.getElementById('crexYetToBatRow');
    const dnbSpan = document.getElementById('crexYetToBat');
    if (inn.did_not_bat && inn.did_not_bat.length > 0) {
        dnbSpan.innerText = inn.did_not_bat.join(', ');
        dnbRow.style.display = 'block';
    } else {
        dnbRow.style.display = 'none';
    }

    // Bowling Table
    const bowlTbody = document.querySelector('#tableCrexBowling tbody');
    if (bowlTbody) {
        if (!inn.bowling || inn.bowling.length === 0) {
            bowlTbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No bowling figures recorded.</td></tr>`;
        } else {
            bowlTbody.innerHTML = inn.bowling.map(b => `
                <tr>
                    <td><strong>${escapeHtml(b.player_name)}</strong></td>
                    <td class="text-right">${b.overs_bowled}</td>
                    <td class="text-right">${b.maidens}</td>
                    <td class="text-right">${b.runs_conceded}</td>
                    <td class="text-right"><strong style="color:#7c3aed; font-size:1.05rem;">${b.wickets}</strong></td>
                    <td class="text-right" style="font-weight:600; color:#0f766e;">${b.economy}</td>
                    <td class="text-right" style="color:#64748b;">${b.dot_balls}</td>
                </tr>
            `).join('');
        }
    }
}

function toggleCrexEditor(forceState) {
    const editor = document.getElementById('crexEditorSection');
    const innContent = document.getElementById('crexInningsContent');
    const btn = document.getElementById('btnToggleEditCrex');
    if (!editor || !currentScorecardData) return;

    const show = (forceState !== undefined) ? forceState : (editor.style.display === 'none');
    editor.style.display = show ? 'block' : 'none';
    innContent.style.display = show ? 'none' : 'block';
    if (btn) btn.innerText = show ? '👁️ View Scorecard' : '✏️ Edit Player Scores';

    if (show) {
        renderCrexEditorTables();
    }
}

function renderCrexEditorTables() {
    const container = document.getElementById('crexEditorTablesContainer');
    if (!container || !currentScorecardData) return;

    const inn1 = currentScorecardData.innings1;
    const inn2 = currentScorecardData.innings2;

    container.innerHTML = `
        <h5 style="margin-bottom:0.5rem; color:var(--primary-dark);">Innings 1 (${inn1.team_name}) - Batting & Bowling</h5>
        <div style="overflow-x:auto;">
            <table class="data-table crex-editor-table">
                <thead>
                    <tr><th>Player</th><th>Runs</th><th>Balls</th><th>4s</th><th>6s</th><th>Dismissal</th><th>Overs</th><th>Maidens</th><th>R Conceded</th><th>Wkts</th></tr>
                </thead>
                <tbody>
                    ${inn1.batting.map((b, i) => `
                        <tr data-inn="1" data-player-id="${b.player_id}" data-team-id="${inn1.team_id}" data-name="${escapeHtml(b.player_name)}">
                            <td>${escapeHtml(b.player_name)}</td>
                            <td><input type="number" class="inp-runs" value="${b.runs}"></td>
                            <td><input type="number" class="inp-balls" value="${b.balls}"></td>
                            <td><input type="number" class="inp-fours" value="${b.fours}"></td>
                            <td><input type="number" class="inp-sixes" value="${b.sixes}"></td>
                            <td><input type="text" class="inp-dismissal" value="${escapeHtml(b.dismissal)}"></td>
                            <td><input type="number" step="0.1" class="inp-overs" value="0.0"></td>
                            <td><input type="number" class="inp-maidens" value="0"></td>
                            <td><input type="number" class="inp-rc" value="0"></td>
                            <td><input type="number" class="inp-wkts" value="0"></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>

        <h5 style="margin-top:1.25rem; margin-bottom:0.5rem; color:var(--primary-dark);">Innings 2 (${inn2.team_name}) - Batting & Bowling</h5>
        <div style="overflow-x:auto;">
            <table class="data-table crex-editor-table">
                <thead>
                    <tr><th>Player</th><th>Runs</th><th>Balls</th><th>4s</th><th>6s</th><th>Dismissal</th><th>Overs</th><th>Maidens</th><th>R Conceded</th><th>Wkts</th></tr>
                </thead>
                <tbody>
                    ${inn2.batting.map((b, i) => `
                        <tr data-inn="2" data-player-id="${b.player_id}" data-team-id="${inn2.team_id}" data-name="${escapeHtml(b.player_name)}">
                            <td>${escapeHtml(b.player_name)}</td>
                            <td><input type="number" class="inp-runs" value="${b.runs}"></td>
                            <td><input type="number" class="inp-balls" value="${b.balls}"></td>
                            <td><input type="number" class="inp-fours" value="${b.fours}"></td>
                            <td><input type="number" class="inp-sixes" value="${b.sixes}"></td>
                            <td><input type="text" class="inp-dismissal" value="${escapeHtml(b.dismissal)}"></td>
                            <td><input type="number" step="0.1" class="inp-overs" value="0.0"></td>
                            <td><input type="number" class="inp-maidens" value="0"></td>
                            <td><input type="number" class="inp-rc" value="0"></td>
                            <td><input type="number" class="inp-wkts" value="0"></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function saveCrexEditorScores() {
    if (!currentScorecardData) return;
    const matchId = currentScorecardData.match.id;

    const rows = document.querySelectorAll('#crexEditorTablesContainer tr[data-player-id]');
    const performances = [];

    rows.forEach(r => {
        performances.push({
            team_id: parseInt(r.dataset.teamId),
            player_id: parseInt(r.dataset.playerId),
            player_name: r.dataset.name,
            innings: parseInt(r.dataset.inn),
            runs: parseInt(r.querySelector('.inp-runs')?.value || 0),
            balls: parseInt(r.querySelector('.inp-balls')?.value || 0),
            fours: parseInt(r.querySelector('.inp-fours')?.value || 0),
            sixes: parseInt(r.querySelector('.inp-sixes')?.value || 0),
            dismissal: r.querySelector('.inp-dismissal')?.value || 'not out',
            is_out: (r.querySelector('.inp-dismissal')?.value || 'not out').toLowerCase() !== 'not out' ? 1 : 0,
            overs_bowled: parseFloat(r.querySelector('.inp-overs')?.value || 0.0),
            maidens: parseInt(r.querySelector('.inp-maidens')?.value || 0),
            runs_conceded: parseInt(r.querySelector('.inp-rc')?.value || 0),
            wickets: parseInt(r.querySelector('.inp-wkts')?.value || 0)
        });
    });

    try {
        const res = await fetch(`/api/matches/${matchId}/scorecard`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ performances })
        });
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            showToast('Player scorecard updated successfully!', 'success');
            currentScorecardData = data.data;
            toggleCrexEditor(false);
            renderCrexInnings(currentInningsView);
        } else {
            showToast(data.message || 'Failed to update scorecard.', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// ============================================================================
// CREX STATS HUB (ORANGE & PURPLE CAP)
// ============================================================================

async function loadCrexStats(tourneyId) {
    const tableOrange = document.querySelector('#tableOrangeCap tbody');
    const tablePurple = document.querySelector('#tablePurpleCap tbody');

    if (tableOrange) tableOrange.innerHTML = `<tr><td colspan="8" class="text-center">⏳ Loading stats...</td></tr>`;
    if (tablePurple) tablePurple.innerHTML = `<tr><td colspan="8" class="text-center">⏳ Loading stats...</td></tr>`;

    try {
        const res = await fetch(`/api/tournaments/${tourneyId}/crex-stats`);
        const data = await res.json();
        if (res.ok && data.status === 'success') {
            renderCrexStats(data.data);
        } else {
            renderEmptyCrexStats(data.message);
        }
    } catch (err) {
        renderEmptyCrexStats(err.message);
    }
}

function renderCrexStats(stats) {
    const tableOrange = document.querySelector('#tableOrangeCap tbody');
    const tablePurple = document.querySelector('#tablePurpleCap tbody');

    const orangeList = stats.orange_cap || [];
    const purpleList = stats.purple_cap || [];

    if (tableOrange) {
        if (orangeList.length === 0) {
            tableOrange.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No batting statistics available yet. Complete matches to see leaders.</td></tr>`;
        } else {
            tableOrange.innerHTML = orangeList.map((p, idx) => `
                <tr>
                    <td><span class="rank-badge ${idx === 0 ? 'rank-1' : ''}">${p.rank}</span></td>
                    <td><strong>${escapeHtml(p.player_name)}</strong> ${idx === 0 ? '🧡' : ''}</td>
                    <td><span class="badge badge-primary">${escapeHtml(p.team_name)}</span></td>
                    <td class="text-right"><strong style="color:#c2410c; font-size:1.1rem;">${p.runs}</strong></td>
                    <td class="text-right" style="color:#64748b;">${p.balls}</td>
                    <td class="text-right">${p.fours}</td>
                    <td class="text-right">${p.sixes}</td>
                    <td class="text-right" style="color:#0f766e; font-weight:700;">${p.strike_rate}</td>
                </tr>
            `).join('');
        }
    }

    if (tablePurple) {
        if (purpleList.length === 0) {
            tablePurple.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No bowling statistics available yet. Complete matches to see leaders.</td></tr>`;
        } else {
            tablePurple.innerHTML = purpleList.map((p, idx) => `
                <tr>
                    <td><span class="rank-badge ${idx === 0 ? 'rank-1' : ''}">${p.rank}</span></td>
                    <td><strong>${escapeHtml(p.player_name)}</strong> ${idx === 0 ? '💜' : ''}</td>
                    <td><span class="badge badge-primary">${escapeHtml(p.team_name)}</span></td>
                    <td class="text-right"><strong style="color:#6d28d9; font-size:1.1rem;">${p.wickets}</strong></td>
                    <td class="text-right">${p.overs}</td>
                    <td class="text-right">${p.maidens}</td>
                    <td class="text-right" style="color:#64748b;">${p.runs_conceded}</td>
                    <td class="text-right" style="color:#0f766e; font-weight:700;">${p.economy}</td>
                </tr>
            `).join('');
        }
    }
}

function renderEmptyCrexStats(msg = 'Select a tournament above to view player leaderboards.') {
    const tableOrange = document.querySelector('#tableOrangeCap tbody');
    const tablePurple = document.querySelector('#tablePurpleCap tbody');
    if (tableOrange) tableOrange.innerHTML = `<tr><td colspan="8" class="text-center text-muted">${escapeHtml(msg)}</td></tr>`;
    if (tablePurple) tablePurple.innerHTML = `<tr><td colspan="8" class="text-center text-muted">${escapeHtml(msg)}</td></tr>`;
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
