import PlayerImage from "./PlayerImage";

function PlayerCard({player_img, country_img, name, rating, positions, country_nane, club_name}) {

    return (
        <div className="flex flex-col">
            <PlayerImage player_src={player_img} country_src={country_img}></PlayerImage>
            <text>{name}</text>
            <text>{rating}</text>
            <text>{positions}</text>
            <text>{country_nane}</text>
            <text>{club_name}</text>            
        </div>
    )
}

export default PlayerCard;

