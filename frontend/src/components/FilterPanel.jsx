import { useState } from 'react'

function FilterPanel({ onFiltersChange }) {
    const [position, setPosition] = useState('')
    const [country, setCountry] = useState('')
    const [club, setClub] = useState('')
    const [minRating, setMinRating] = useState('')
    const [maxRating, setMaxRating] = useState('')

    const emit = (next) => {
        onFiltersChange({
            position, country, club,
            min_rating: minRating, max_rating: maxRating,
            ...next,
        })
    }

    return (
        <div className="flex flex-col gap-2">
            <input value={position} placeholder="Position"
                onChange={(e) => { setPosition(e.target.value); emit({ position: e.target.value }) }} />
            <input value={country} placeholder="Country"
                onChange={(e) => { setCountry(e.target.value); emit({ country: e.target.value }) }} />
            <input value={club} placeholder="Club"
                onChange={(e) => { setClub(e.target.value); emit({ club: e.target.value }) }} />
            <div className="flex gap-2">
                <input type="number" value={minRating} placeholder="Min rating"
                    onChange={(e) => { setMinRating(e.target.value); emit({ min_rating: e.target.value }) }} />
                <input type="number" value={maxRating} placeholder="Max rating"
                    onChange={(e) => { setMaxRating(e.target.value); emit({ max_rating: e.target.value }) }} />
            </div>
        </div>
    )

}

export default FilterPanel