"""
Module temporal - Génération automatique des marqueurs temporels.

Fournit la dataclass TemporalMarkers pour auto-générer ou stocker
les informations de contexte temporel (moment de la journée, jour de la semaine).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


# Types pour les marqueurs temporels
TimeOfDay = Literal["morning", "afternoon", "evening", "night"]
DayOfWeek = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]


@dataclass
class TemporalMarkers:
    """
    Marqueurs temporels auto-générés ou manuels.

    Utilisés pour situer un souvenir dans le temps et permettre
    des recherches contextuelles ("le bug du vendredi soir").
    """

    time_of_day: TimeOfDay
    day_of_week: DayOfWeek
    created_at: datetime

    @classmethod
    def from_datetime(cls, dt: Optional[datetime] = None) -> "TemporalMarkers":
        """
        Génère les marqueurs temporels à partir d'une datetime.

        Mapping des heures:
        - 05:00-11:59 → morning
        - 12:00-16:59 → afternoon
        - 17:00-20:59 → evening
        - 21:00-04:59 → night

        Args:
            dt: datetime à utiliser (défaut: maintenant)

        Returns:
            TemporalMarkers avec les valeurs calculées
        """
        dt = dt or datetime.now()
        hour = dt.hour

        # Détermine le moment de la journée
        if 5 <= hour < 12:
            time_of_day: TimeOfDay = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        # Jour de la semaine en anglais lowercase
        day_of_week: DayOfWeek = dt.strftime("%A").lower()  # type: ignore

        return cls(
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            created_at=dt,
        )

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour stockage."""
        return {
            "time_of_day": self.time_of_day,
            "day_of_week": self.day_of_week,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TemporalMarkers":
        """Reconstruit depuis un dictionnaire."""
        return cls(
            time_of_day=data["time_of_day"],
            day_of_week=data["day_of_week"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


def get_temporal_markers(
    time_of_day: Optional[str] = None,
    day_of_week: Optional[str] = None,
    dt: Optional[datetime] = None,
) -> TemporalMarkers:
    """
    Obtient les marqueurs temporels avec support d'override manuel.

    Si time_of_day ou day_of_week sont fournis, ils sont utilisés.
    Sinon, les valeurs sont auto-générées depuis la datetime.

    Args:
        time_of_day: Override manuel du moment de la journée
        day_of_week: Override manuel du jour de la semaine
        dt: datetime à utiliser pour l'auto-génération (défaut: maintenant)

    Returns:
        TemporalMarkers avec les valeurs finales
    """
    dt = dt or datetime.now()
    auto = TemporalMarkers.from_datetime(dt)

    # Applique les overrides si fournis
    final_time_of_day = time_of_day if time_of_day else auto.time_of_day
    final_day_of_week = day_of_week if day_of_week else auto.day_of_week

    return TemporalMarkers(
        time_of_day=final_time_of_day,  # type: ignore
        day_of_week=final_day_of_week,  # type: ignore
        created_at=dt,
    )
