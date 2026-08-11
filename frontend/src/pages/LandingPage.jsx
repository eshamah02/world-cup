import { useNavigate } from 'react-router-dom'

export default function LandingPage() {
    const navigate = useNavigate()
    return (
        <div className="min-h-screen flex flex-col items-center justify-center gap-6">
            <h1 className="text-4xl font-bold">World Cup Simulator</h1>
            <p className="text-gray-600 max-w-md text-center">
                Build two teams of three, then simulate the match.
            </p>
            <button
                onClick={() => navigate('/select')}
                className="px-6 py-3 rounded-xl bg-blue-600 text-white text-lg"
            >
                Let's Play
            </button>
        </div>
    )
}
