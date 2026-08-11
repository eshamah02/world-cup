import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'

function RandomCard() {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: 'random-token',
        data: { kind: 'random' },
    })

    const style = { transform: CSS.Translate.toString(transform) }

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...attributes}
            {...listeners}
            className="group flex items-center justify-center w-16 hover:w-64 h-64 rounded-xl bg-purple-200 cursor-grab select-none overflow-hidden transition-all duration-300"
        >
            <span className="opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                pick random player
            </span>
        </div>
    )
}

export default RandomCard