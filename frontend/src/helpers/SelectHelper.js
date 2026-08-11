
export const emptyTeam = () => [null, null, null]

export function applyDrop(state, dragged, target) {
    const { team, index } = target

    let teamA = [...state.teamA]
    let teamB = [...state.teamB]
    if (dragged.kind === 'player') {
        const clear = (slots) =>
            slots.map((s) => (s && s.playerId === dragged.playerId ? null : s))
        teamA = clear(teamA)
        teamB = clear(teamB)
    }

    let value
    if (dragged.kind === 'player') {
        value = { playerId: dragged.playerId }
    } else if (dragged.kind === 'random') {
        value = { random: true }
    } else {
        value = null
    }

    const targetSlots = team === 'A' ? teamA : teamB
    targetSlots[index] = value

    return { teamA, teamB }
}

export function buildSimulateBody(teamA, teamB) {
    const toEntry = (slot) => (slot?.random ? 'random' : slot.playerId)
    return { teamA: teamA.map(toEntry), teamB: teamB.map(toEntry) }
}

export function isSubmitEnabled(teamA, teamB) {
    return [...teamA, ...teamB].every((slot) => slot !== null)
}

