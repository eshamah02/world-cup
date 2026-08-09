
function PlayerImage({player_src, country_src = null}) {
    return (
        <div className="relative inline-block">
            <img 
                src={player_src}
                alt={'Image'}
                loading="lazy"
                referrerPolicy="no-referrer"
                className="w-64 h-64 rounded-full object-cover"
            />
            {country_src && (
                <img
                    src={country_src}
                    alt={'Country'}
                    loading="lazy"
                    referrerPolicy="no-referrer"
                    className="absolute top-1 right-1 w-12 h-10 rounded-xl object-cover"
                />
            )}
        </div>
    )
}

export default PlayerImage;

