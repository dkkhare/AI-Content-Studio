import json
from dataclasses import asdict


class MetadataExporter:

    def export(
        self,
        metadata,
        filename,
    ):

        with open(
            filename,
            "w",
            encoding="utf8",
        ) as file:

            json.dump(
                asdict(metadata),
                file,
                indent=4,
                ensure_ascii=False,
            )