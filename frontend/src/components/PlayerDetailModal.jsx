import { useEffect, useState } from 'react'
import { fetchPlayerDetail } from '../api/client'

const GROUPS = ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']

function PlayerDetailModal({ playerId, onClose }) {
    const [status, setStatus] = useState('loading')
    const [detail, setDetail] = useState(null)
    const [error, setError] = useState('')

    useEffect(() => {
        if (playerId == null) return
        let ignore = false
        setStatus('loading')
        fetchPlayerDetail(playerId)
            .then((data) => {
                if (ignore) return
                setDetail(data)
                setStatus('loaded')
            })
            .catch((err) => {
                if (ignore) return
                setError(err.message)
                setStatus('error')
            })
        return () => { ignore = true }
    }, [playerId])

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center" onClick={onClose}>
            <div className="bg-white rounded-xl p-6 max-w-lg w-full max-h-[80vh] overflow-auto"
                onClick={(e) => e.stopPropagation()}>
                <button onClick={onClose} aria-label="Close" className="float-right text-xl">×</button>

                {status === 'loading' && <p>Loading...</p>}
                {status === 'error' && <p className="text-red-600">{error}</p>}
                {status === 'loaded' && detail && (
                    <div>
                        <h2 className="text-xl font-bold">{detail.full_name}</h2>
                        <p className="mb-2">Overall {detail.overall_rating}</p>
                        {GROUPS.map((group) => (
                            <div key={group} className="mb-2">
                                <h3 className="font-semibold capitalize">{group}</h3>
                                <ul className="text-sm">
                                    {Object.entries(detail[group]).map(([stat, val]) => (
                                        <li key={stat}>{stat}: {val}</li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

export default PlayerDetailModal
