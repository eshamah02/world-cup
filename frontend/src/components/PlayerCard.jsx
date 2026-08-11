import { useDraggable } from "@dnd-kit/core";
import { CSS } from '@dnd-kit/utilities'
import PlayerImage from "./PlayerImage";

function PlayerCard({ player, countryImg, onOpenDetail }) {

    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `player-${player.player_id}`,
        data: { kind: 'player', player }
    })

    const style = {
        transform: CSS.Translate.toString(transform),
        opacity: isDragging ? 0.4 : 1
    }

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...attributes}
            {...listeners}
            onDoubleClick={() => onOpenDetail(player.player_id)}
            className="flex flex-col items-center gap-1 p-3 rounded-xl bg-white shadow cursor-grab select-none"
        >
            <PlayerImage player_src={player.image} country_src={countryImg} />
            <h3 className="font-semibold">{player.name}</h3>
            <span className="text-lg font-bold">{player.overall_rating}</span>
            <span className="text-sm text-gray-600">{player.positions.join(' / ')}</span>
            <span className="text-sm">{player.country_name}</span>
            <span className="text-sm text-gray-500">{player.club_name}</span>
        </div>

    )
}

export default PlayerCard;

