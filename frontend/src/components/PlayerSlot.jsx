import { useDroppable } from '@dnd-kit/core'
import PlayerImage from './PlayerImage'

function RemoveButton({ onClick }) {
    return (
        <button onClick={onClick} aria-label="Remove" className="absolute top-1 right-1 w-6 h-6 rounded-full bg-red-500 text-white">
            ×
        </button>
    )
}

function PlayerSlot({ team, index, slot, player, onRemove }) {
    const { isOver, setNodeRef } = useDroppable({
        id: `slot-${team}-${index}`,
        data: { team, index }
    })

    return (
        <div
            ref={setNodeRef}
            className={`relative w-40 h-56 rounded-xl border-2 border-dashed flex items-center justify-center
                ${isOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
        >
            {slot === null && <span className="text-gray-400">Empty</span>}

            {slot?.random && (
                <>
                    <span className="font-semibold">Random</span>
                    <RemoveButton onClick={() => onRemove(team, index)} />
                </>
            )}

            {slot && !slot.random && player && (
                <>
                    <div className="flex flex-col items-center">
                        <PlayerImage player_src={player.image} />
                        <span className="text-sm">{player.name}</span>
                    </div>
                    <RemoveButton onClick={() => onRemove(team, index)} />
                </>
            )}
        </div>

    )
}

export default PlayerSlot