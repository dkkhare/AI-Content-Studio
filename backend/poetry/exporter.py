import json


class PoetryExporter:

    def export(self, poems, filename):

        data = []

        for poem in poems:

            item = {
                "title": poem.title,
                "language": poem.language,
                "stanzas": []
            }

            for stanza in poem.stanzas:

                item["stanzas"].append(
                    [v.text for v in stanza.verses]
                )

            data.append(item)

        with open(filename, "w", encoding="utf8") as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )