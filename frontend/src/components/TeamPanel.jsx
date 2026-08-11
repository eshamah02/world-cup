import PlayerSlot from './PlayerSlot'

function TeamPanel({ team, slots, playersById, onRemove }) {
    return (
        <div className="flex flex-col gap-2">
            <h2 className="font-bold">Team {team}</h2>
            <div className="flex gap-2">
                {slots.map((slot, index) => {
                    const player = slot && !slot.random ? playersById[slot.playerId] : null
                    return (
                        <PlayerSlot
                            key={index}
                            team={team}
                            index={index}
                            slot={slot}
                            player={player}
                            onRemove={onRemove}
                        />
                    )
                })}
            </div>
        </div>
    )
}

export default TeamPanel