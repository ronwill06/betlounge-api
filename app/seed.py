from sqlalchemy.orm import Session
from .models import PropOffer, PropProjection

def seed(db: Session):
    db.query(PropOffer).delete()
    db.query(PropProjection).delete()
    db.commit()

    offers = [
        PropOffer(sport="NBA", market_group="PRA", player_name="LeBron James", book="DK", line=49.5),
        PropOffer(sport="NBA", market_group="PRA", player_name="LeBron James", book="FD", line=50.5),
        PropOffer(sport="NBA", market_group="PRA", player_name="Nikola Jokic", book="DK", line=48.5),
        PropOffer(sport="NBA", market_group="PRA", player_name="Jayson Tatum", book="DK", line=41.5),
        PropOffer(sport="NBA", market_group="Points", player_name="LeBron James", book="DK", line=26.5),
    ]

    projections = [
        PropProjection(sport="NBA", market_group="PRA", player_name="LeBron James", projection=53.2, confidence=78),
        PropProjection(sport="NBA", market_group="PRA", player_name="Nikola Jokic", projection=50.1, confidence=72),
        PropProjection(sport="NBA", market_group="PRA", player_name="Jayson Tatum", projection=40.9, confidence=64),  # near no-edge
        PropProjection(sport="NBA", market_group="Points", player_name="LeBron James", projection=28.1, confidence=70),
    ]

    db.add_all(offers)
    db.add_all(projections)
    db.commit()