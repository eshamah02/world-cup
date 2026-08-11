import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import SelectPage from './pages/SelectPage'
import ResultsPage from './pages/ResultsPage'
import './App.css'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/select" element={<SelectPage />} />
      <Route path="/results" element={<ResultsPage />} />
    </Routes>
  )
}

export default App
