class VoiceValidator:

    MIN_DURATION = 10

    MAX_DURATION = 300

    def validate(self, metrics):

        errors = []

        if metrics.duration < self.MIN_DURATION:

            errors.append(
                "Reference audio is too short."
            )

        if metrics.duration > self.MAX_DURATION:

            errors.append(
                "Reference audio is too long."
            )

        return errors