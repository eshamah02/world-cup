import PlayerCard from './components/PlayerCard'
import './App.css'


const player_example_info = {
  player_img: "https://cdn.sofifa.net/players/231/747/26_360.png",
  player_country_img: "https://cdn.sofifa.net/flags/fr.png",
  player_name: "Kylian Mbappé",
  player_rating: 64,
  player_positions: "GK",
  player_country_name: "France",
  player_club_name: "Blackburn Rovers"
}


function App() {
  return (
    <PlayerCard 
      player_img={player_example_info.player_img} 
      country_img={player_example_info.player_country_img}
      name={player_example_info.player_name}
      rating={player_example_info.player_rating}
      positions={player_example_info.player_positions}
      country_nane={player_example_info.player_country_name}
      club_name={player_example_info.player_club_name}
      />
  )
}

export default App
