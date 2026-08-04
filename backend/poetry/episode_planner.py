from backend.poetry.metadata import Episode
from backend.poetry.duration_estimator import DurationEstimator


class EpisodePlanner:

    TARGET_DURATION = 15 * 60

    def create(self, poems):

        estimator = DurationEstimator()

        episodes = []

        current = Episode(
            number=1,
            title="Episode 1",
            duration_seconds=0,
        )

        for poem in poems:

            text = ""

            for stanza in poem.stanzas:

                for verse in stanza.verses:

                    text += verse.text + "\n"

            duration = estimator.estimate_seconds(text)

            if (
                current.duration_seconds + duration
                > self.TARGET_DURATION
                and current.poem_ids
            ):

                episodes.append(current)

                current = Episode(
                    number=len(episodes) + 1,
                    title=f"Episode {len(episodes)+1}",
                    duration_seconds=0,
                )

            current.poem_ids.append(poem.id)

            current.duration_seconds += duration

        if current.poem_ids:

            episodes.append(current)

        return episodes