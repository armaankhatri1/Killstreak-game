let sessionId = null;

async function startGame() {
  const playerId = document.getElementById("playerId").value;
  const res = await fetch("http://127.0.0.1:8000/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_id: playerId })
  });
  const data = await res.json();
  sessionId = data.session_id;
  document.getElementById("status").innerText = "Game Started! Session ID: " + sessionId;
}

async function shoot(hit) {
  if (!sessionId) return alert("Start the game first!");
  const reactionTime = Math.floor(Math.random() * 500) + 200; // fake timing for now
  const res = await fetch("http://127.0.0.1:8000/shot", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, hit, reaction_time: reactionTime })
  });
  const data = await res.json();
  document.getElementById("status").innerText = `Shot recorded! Score: ${data.score}`;
}

async function endGame() {
  if (!sessionId) return;
  const res = await fetch("http://127.0.0.1:8000/end", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId })
  });
  const data = await res.json();
  document.getElementById("status").innerText =
    `Game Over\nPlayer: ${data.player_id}\nScore: ${data.score}\nAvg Reaction Time: ${data.avg_reaction_time} ms`;
  sessionId = null;
}

async function fetchLeaderboard() {
  const res = await fetch('http://127.0.0.1:8000/leaderboard');
  const data = await res.json(); // { leaderboard: [...] }
  const tableBody = document.querySelector('#leaderboard-table tbody');
  tableBody.innerHTML = '';

  // Fix: use data.leaderboard
  data.leaderboard.sort((a, b) => b.score - a.score);

  data.leaderboard.forEach(player => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${player.player_id}</td>
      <td>${player.score}</td>
      <td>${player.avg_reaction_time}</td>
    `;
    tableBody.appendChild(row);
  });
}

