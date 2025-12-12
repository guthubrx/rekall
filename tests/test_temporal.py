"""
Tests pour le module temporal.

Tests couvrant:
- TemporalMarkers.from_datetime() avec différentes heures
- Mapping correct time_of_day (morning/afternoon/evening/night)
- Mapping correct day_of_week
- get_temporal_markers() avec et sans overrides
- Sérialisation/désérialisation
"""

from datetime import datetime

import pytest

from rekall.temporal import (
    DayOfWeek,
    TemporalMarkers,
    TimeOfDay,
    get_temporal_markers,
)


# ============================================================
# Tests: TemporalMarkers.from_datetime()
# ============================================================


class TestFromDatetime:
    """Tests pour TemporalMarkers.from_datetime()."""

    def test_morning_5am(self) -> None:
        """05:00 est 'morning'."""
        dt = datetime(2025, 12, 10, 5, 0)  # 05:00
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "morning"

    def test_morning_11am(self) -> None:
        """11:59 est encore 'morning'."""
        dt = datetime(2025, 12, 10, 11, 59)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "morning"

    def test_afternoon_noon(self) -> None:
        """12:00 est 'afternoon'."""
        dt = datetime(2025, 12, 10, 12, 0)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "afternoon"

    def test_afternoon_4pm(self) -> None:
        """16:59 est encore 'afternoon'."""
        dt = datetime(2025, 12, 10, 16, 59)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "afternoon"

    def test_evening_5pm(self) -> None:
        """17:00 est 'evening'."""
        dt = datetime(2025, 12, 10, 17, 0)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "evening"

    def test_evening_8pm(self) -> None:
        """20:59 est encore 'evening'."""
        dt = datetime(2025, 12, 10, 20, 59)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "evening"

    def test_night_9pm(self) -> None:
        """21:00 est 'night'."""
        dt = datetime(2025, 12, 10, 21, 0)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "night"

    def test_night_midnight(self) -> None:
        """00:00 est 'night'."""
        dt = datetime(2025, 12, 10, 0, 0)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "night"

    def test_night_4am(self) -> None:
        """04:59 est encore 'night'."""
        dt = datetime(2025, 12, 10, 4, 59)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "night"

    def test_uses_now_by_default(self) -> None:
        """Utilise datetime.now() par défaut."""
        markers = TemporalMarkers.from_datetime()
        now = datetime.now()
        # Le jour devrait correspondre (permettre un décalage de 1 seconde)
        assert markers.day_of_week == now.strftime("%A").lower()

    def test_stores_created_at(self) -> None:
        """Stocke la datetime dans created_at."""
        dt = datetime(2025, 12, 10, 14, 30)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.created_at == dt


# ============================================================
# Tests: day_of_week mapping
# ============================================================


class TestDayOfWeek:
    """Tests pour le mapping des jours de la semaine."""

    def test_monday(self) -> None:
        """Lundi → 'monday'."""
        dt = datetime(2025, 12, 8, 12, 0)  # 8 Dec 2025 is Monday
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.day_of_week == "monday"

    def test_tuesday(self) -> None:
        """Mardi → 'tuesday'."""
        dt = datetime(2025, 12, 9, 12, 0)  # Tuesday
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.day_of_week == "tuesday"

    def test_wednesday(self) -> None:
        """Mercredi → 'wednesday'."""
        dt = datetime(2025, 12, 10, 12, 0)  # Wednesday
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.day_of_week == "wednesday"

    def test_thursday(self) -> None:
        """Jeudi → 'thursday'."""
        dt = datetime(2025, 12, 11, 12, 0)  # Thursday
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.day_of_week == "thursday"

    def test_friday(self) -> None:
        """Vendredi → 'friday'."""
        dt = datetime(2025, 12, 12, 12, 0)  # Friday
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.day_of_week == "friday"

    def test_saturday(self) -> None:
        """Samedi → 'saturday'."""
        dt = datetime(2025, 12, 13, 12, 0)  # Saturday
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.day_of_week == "saturday"

    def test_sunday(self) -> None:
        """Dimanche → 'sunday'."""
        dt = datetime(2025, 12, 14, 12, 0)  # Sunday
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.day_of_week == "sunday"


# ============================================================
# Tests: get_temporal_markers() with overrides
# ============================================================


class TestGetTemporalMarkers:
    """Tests pour get_temporal_markers avec overrides."""

    def test_auto_generates_without_overrides(self) -> None:
        """Auto-génère si aucun override fourni."""
        dt = datetime(2025, 12, 10, 14, 30)  # Wednesday afternoon
        markers = get_temporal_markers(dt=dt)
        assert markers.time_of_day == "afternoon"
        assert markers.day_of_week == "wednesday"

    def test_respects_time_of_day_override(self) -> None:
        """Respecte l'override de time_of_day."""
        dt = datetime(2025, 12, 10, 14, 30)  # Auto = afternoon
        markers = get_temporal_markers(time_of_day="morning", dt=dt)
        assert markers.time_of_day == "morning"  # Override
        assert markers.day_of_week == "wednesday"  # Auto

    def test_respects_day_of_week_override(self) -> None:
        """Respecte l'override de day_of_week."""
        dt = datetime(2025, 12, 10, 14, 30)  # Auto = wednesday
        markers = get_temporal_markers(day_of_week="friday", dt=dt)
        assert markers.time_of_day == "afternoon"  # Auto
        assert markers.day_of_week == "friday"  # Override

    def test_both_overrides(self) -> None:
        """Respecte les deux overrides."""
        dt = datetime(2025, 12, 10, 14, 30)  # Wednesday afternoon
        markers = get_temporal_markers(
            time_of_day="night",
            day_of_week="sunday",
            dt=dt,
        )
        assert markers.time_of_day == "night"
        assert markers.day_of_week == "sunday"

    def test_preserves_created_at_from_dt(self) -> None:
        """Préserve created_at depuis dt même avec overrides."""
        dt = datetime(2025, 12, 10, 14, 30)
        markers = get_temporal_markers(
            time_of_day="morning",
            day_of_week="monday",
            dt=dt,
        )
        assert markers.created_at == dt


# ============================================================
# Tests: Serialization
# ============================================================


class TestSerialization:
    """Tests pour la sérialisation/désérialisation."""

    def test_to_dict(self) -> None:
        """Convertit correctement en dictionnaire."""
        dt = datetime(2025, 12, 10, 14, 30)
        markers = TemporalMarkers(
            time_of_day="afternoon",
            day_of_week="wednesday",
            created_at=dt,
        )
        result = markers.to_dict()

        assert result["time_of_day"] == "afternoon"
        assert result["day_of_week"] == "wednesday"
        assert result["created_at"] == "2025-12-10T14:30:00"

    def test_from_dict(self) -> None:
        """Reconstruit correctement depuis un dictionnaire."""
        data = {
            "time_of_day": "evening",
            "day_of_week": "friday",
            "created_at": "2025-12-12T19:00:00",
        }
        markers = TemporalMarkers.from_dict(data)

        assert markers.time_of_day == "evening"
        assert markers.day_of_week == "friday"
        assert markers.created_at == datetime(2025, 12, 12, 19, 0)

    def test_roundtrip(self) -> None:
        """to_dict -> from_dict préserve les données."""
        original = TemporalMarkers(
            time_of_day="morning",
            day_of_week="monday",
            created_at=datetime(2025, 12, 8, 8, 30),
        )
        data = original.to_dict()
        restored = TemporalMarkers.from_dict(data)

        assert restored.time_of_day == original.time_of_day
        assert restored.day_of_week == original.day_of_week
        assert restored.created_at == original.created_at


# ============================================================
# Tests: Edge cases
# ============================================================


class TestEdgeCases:
    """Tests pour les cas limites."""

    def test_boundary_5am_morning_start(self) -> None:
        """Limite exacte du début de morning (5:00)."""
        dt = datetime(2025, 12, 10, 5, 0)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "morning"

    def test_boundary_12pm_afternoon_start(self) -> None:
        """Limite exacte du début de afternoon (12:00)."""
        dt = datetime(2025, 12, 10, 12, 0)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "afternoon"

    def test_boundary_5pm_evening_start(self) -> None:
        """Limite exacte du début de evening (17:00)."""
        dt = datetime(2025, 12, 10, 17, 0)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "evening"

    def test_boundary_9pm_night_start(self) -> None:
        """Limite exacte du début de night (21:00)."""
        dt = datetime(2025, 12, 10, 21, 0)
        markers = TemporalMarkers.from_datetime(dt)
        assert markers.time_of_day == "night"

    def test_empty_string_override_uses_auto(self) -> None:
        """String vide comme override utilise la valeur auto."""
        dt = datetime(2025, 12, 10, 14, 30)
        markers = get_temporal_markers(time_of_day="", dt=dt)
        # Empty string is falsy, so should use auto
        assert markers.time_of_day == "afternoon"

    def test_none_override_uses_auto(self) -> None:
        """None comme override utilise la valeur auto."""
        dt = datetime(2025, 12, 10, 14, 30)
        markers = get_temporal_markers(time_of_day=None, day_of_week=None, dt=dt)
        assert markers.time_of_day == "afternoon"
        assert markers.day_of_week == "wednesday"


# ============================================================
# Tests: Type hints validation
# ============================================================


class TestTypeHints:
    """Tests pour valider que les types sont corrects."""

    def test_time_of_day_is_valid_literal(self) -> None:
        """time_of_day est dans les valeurs Literal autorisées."""
        valid_times: list[TimeOfDay] = ["morning", "afternoon", "evening", "night"]
        for hour, expected in [(8, "morning"), (14, "afternoon"), (18, "evening"), (23, "night")]:
            dt = datetime(2025, 12, 10, hour, 0)
            markers = TemporalMarkers.from_datetime(dt)
            assert markers.time_of_day in valid_times

    def test_day_of_week_is_valid_literal(self) -> None:
        """day_of_week est dans les valeurs Literal autorisées."""
        valid_days: list[DayOfWeek] = [
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday"
        ]
        # Test each day (Dec 8-14, 2025 is Mon-Sun)
        for day in range(8, 15):
            dt = datetime(2025, 12, day, 12, 0)
            markers = TemporalMarkers.from_datetime(dt)
            assert markers.day_of_week in valid_days
