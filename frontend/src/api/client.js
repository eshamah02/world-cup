const BASE = import.meta.env.VITE_API_BASE ?? '/api'

async function handle(res) {
    if (!res.ok) {
        let detail
        try {
            detail = (await res.json()).detail
        } catch {
            detail = res.statusText
        }
        throw new Error(detail || `Request failed: ${res.status}`)
    }
    return res.json()
}

export async function fetchPlayers(filters = {}) {
    const params = new URLSearchParams()
    for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && value !== '') {
            params.append(key, value)
        }
    }
    const res = await fetch(`${BASE}/players?${params.toString()}`)
    return handle(res)
}

export async function fetchPlayerDetail(playerId) {
    const res = await fetch(`${BASE}/players/${playerId}`)
    return handle(res)
}

export async function simulate({ teamA, teamB }) {
    const res = await fetch(`${BASE}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ team_a: teamA, team_b: teamB })
    })
    return handle(res)
}
