import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DndContext, DragOverlay } from '@dnd-kit/core'
import { fetchPlayers, simulate } from '../api/client'
import { applyDrop, buildSimulateBody, isSubmitEnabled, emptyTeam } from '../helpers/SelectHelper'
import PlayerCard from '../components/PlayerCard'
import SearchBar from '../components/SearchBar'
import FilterPanel from '../components/FilterPanel'
import TeamPanel from '../components/TeamPanel'
import RandomCard from '../components/RandomCard'
import PlayerDetailModal from '../components/PlayerDetailModal'

const PAGE_SIZE = 20

export default function SelectPage() {
    const navigate = useNavigate()

    const [teams, setTeams] = useState({ teamA: emptyTeam(), teamB: emptyTeam() })
    const [placedPlayers, setPlacedPlayers] = useState({})

    const [players, setPlayers] = useState([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [query, setQuery] = useState('')
    const [filters, setFilters] = useState({})
    const [error, setError] = useState('')

    const [activeDrag, setActiveDrag] = useState(null)
    const [openId, setOpenId] = useState(null)
    const [submitError, setSubmitError] = useState('')

    useEffect(() => {
        let ignore = false
        setError('')
        fetchPlayers({ page, page_size: PAGE_SIZE, query, ...filters })
            .then((data) => {
                if (ignore) return
                setPlayers(data.items)
                setTotal(data.total)
            })
            .catch((err) => {
                if (ignore) return
                setError(err.message)
            })
        return () => { ignore = true }
    }, [page, query, filters])

    const handleDragStart = (event) => setActiveDrag(event.active.data.current)

    const handleDragEnd = (event) => {
        const { active, over } = event
        setActiveDrag(null)
        if (!over) return

        const data = active.data.current
        let dragged
        if (data.kind === 'random') {
            dragged = { kind: 'random' }
        } else {
            dragged = { kind: 'player', playerId: data.player.player_id }
            setPlacedPlayers((prev) => ({ ...prev, [data.player.player_id]: data.player }))
        }
        const target = over.data.current
        setTeams((prev) => applyDrop(prev, dragged, target))
    }

    const handleRemove = (team, index) => {
        setTeams((prev) => applyDrop(prev, { kind: 'remove' }, { team, index }))
    }

    const handleSubmit = async () => {
        setSubmitError('')
        try {
            const result = await simulate(buildSimulateBody(teams.teamA, teams.teamB))
            navigate('/results', { state: { result } })
        } catch (err) {
            setSubmitError(err.message)
        }
    }

    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
    const canSubmit = isSubmitEnabled(teams.teamA, teams.teamB)

    return (
        <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
            <div className="p-4 flex flex-col gap-4">
                <SearchBar onSearch={(q) => { setQuery(q); setPage(1) }} />
                <FilterPanel onFiltersChange={(f) => { setFilters(f); setPage(1) }} />

                <div className="flex gap-6">
                    <div className="flex-1">
                        {error ? (
                            <p className="text-red-600">{error}</p>
                        ) : (
                            <div className="grid grid-cols-3 gap-3">
                                {players.map((p) => (
                                    <PlayerCard key={p.player_id} player={p} onOpenDetail={setOpenId} />
                                ))}
                            </div>
                        )}

                        <div className="flex items-center gap-3 mt-4">
                            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</button>
                            <span>Page {page} of {totalPages}</span>
                            <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
                        </div>
                    </div>

                    <div className="flex flex-col gap-4">
                        <TeamPanel team="A" slots={teams.teamA} playersById={placedPlayers} onRemove={handleRemove} />
                        <TeamPanel team="B" slots={teams.teamB} playersById={placedPlayers} onRemove={handleRemove} />
                        <RandomCard />
                        <button
                            disabled={!canSubmit}
                            onClick={handleSubmit}
                            className="px-4 py-2 rounded bg-green-600 text-white disabled:opacity-40"
                        >
                            Simulate
                        </button>
                        {submitError && <p className="text-red-600">{submitError}</p>}
                    </div>
                </div>
            </div>

            <DragOverlay>
                {activeDrag ? (
                    <div className="p-3 rounded-xl bg-white shadow">
                        {activeDrag.kind === 'random' ? 'Random' : activeDrag.player.name}
                    </div>
                ) : null}
            </DragOverlay>

            {openId != null && (
                <PlayerDetailModal playerId={openId} onClose={() => setOpenId(null)} />
            )}
        </DndContext>
    )




}