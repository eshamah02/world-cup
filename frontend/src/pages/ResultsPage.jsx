import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

export default function ResultsPage() {
    const location = useLocation()
    const navigate = useNavigate()
    const result = location.state?.result

    useEffect(() => {
        if (!result) navigate('/select', { replace: true })
    }, [result, navigate])

    if (!result) return null // redirecting

    return (
        <div className="p-6 flex flex-col gap-4">
            <h1 className="text-2xl font-bold">
                {result.team_a_names.join(', ')} vs {result.team_b_names.join(', ')}
            </h1>
            <p className="text-xl">Final score: {result.final_score[0]} – {result.final_score[1]}</p>
            <p>Winner: {result.winner ?? 'Draw'}</p>
            <p>MVP: {result.mvp}</p>

            <div>
                <h2 className="font-semibold">Match events</h2>
                <ol className="list-decimal list-inside">
                    {result.events.map((e, i) => (
                        <li key={i}>{e.text}</li>
                    ))}
                </ol>
            </div>

            <button onClick={() => navigate('/select')} className="px-4 py-2 rounded bg-blue-600 text-white w-fit">
                Play again
            </button>
        </div>
    )
}