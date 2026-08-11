import { useState } from 'react'

function SearchBar({ onSearch }) {
    const [value, setValue] = useState('')
    const handleSubmit = (e) => {
        e.preventDefault()
        onSearch(value.trim())
    }

    return (
        <form onSubmit={handleSubmit} className="flex gap-2">
            <input
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="Search players..."
                className="border rounded px-3 py-2 flex-1"
            />
            <button type="submit" className='px-4 py-2 rounded bg-blue-600 text-white'>
                Search
            </button>
        </form>
    )
}

export default SearchBar