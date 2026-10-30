"""Experimental keeper affiliation from repeated nearby teammate evidence."""

from collections import Counter
from math import hypot


class KeeperTeamConsensus:
    def __init__(self, fps):
        self.required = max(3, round(fps * 0.5))
        self.history = {}
        self.last_index = None

    def update(self, detections, index, *, reset=False):
        if reset or self.last_index is None or index != self.last_index + 1:
            self.history.clear()
        self.last_index = index
        following = {}
        field_players = [
            d
            for d in detections
            if d.semantic_class == "player"
            and d.player_kind != "goalkeeper"
            and d.projection_status == "valid"
            and d.team_id in {"A", "B"}
            and d.field_position
        ]
        for keeper in detections:
            position = keeper.field_position
            if (
                keeper.semantic_class != "player"
                or keeper.player_kind != "goalkeeper"
                or keeper.projection_status != "valid"
                or keeper.track_id is None
                or not position
                or not (position[0] < 0.12 or position[0] > 0.88)
                or not 0.2 < position[1] < 0.8
            ):
                continue
            votes = Counter()
            for player in field_players:
                x, y = player.field_position
                same_end = x < 0.25 if position[0] < 0.12 else x > 0.75
                if same_end and hypot((x - position[0]) * 105, (y - position[1]) * 68) <= 25:
                    votes[player.team_id] += 1
            ordered = votes.most_common()
            if not ordered:
                continue
            team, count = ordered[0]
            other = ordered[1][1] if len(ordered) > 1 else 0
            if count < 3 or count - other < 2:
                continue
            previous_team, n = self.history.get(keeper.track_id, (None, 0))
            n = n + 1 if previous_team == team else 1
            following[keeper.track_id] = (team, n)
            if n >= self.required:
                keeper.team_id = team
                keeper.team_status = "assigned"
                keeper.team_source = "experimental_keeper_position_consensus"
        self.history = following
