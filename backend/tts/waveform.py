import numpy as np


class WaveformGenerator:
    """
    Generates waveform data for the UI.
    """

    def peaks(
        self,
        waveform,
        samples=1000,
    ):

        waveform = np.asarray(waveform)

        if len(waveform) <= samples:

            return waveform.tolist()

        step = len(waveform) // samples

        peaks = []

        for i in range(0, len(waveform), step):

            block = waveform[i:i + step]

            if len(block):

                peaks.append(

                    float(

                        np.max(

                            np.abs(block)

                        )

                    )

                )

        return peaks

    def rms(
        self,
        waveform,
        frame=1024,
    ):

        values = []

        for i in range(

            0,

            len(waveform),

            frame,

        ):

            block = waveform[i:i + frame]

            if len(block):

                values.append(

                    float(

                        np.sqrt(

                            np.mean(

                                block ** 2

                            )

                        )

                    )

                )

        return values

    def duration(
        self,
        waveform,
        sample_rate,
    ):

        return len(waveform) / sample_rate