from __future__ import annotations


class LinkMapBuilder:
    def build(self, links: list[tuple[int, int]]) -> dict[int, set[int]]:
        link_map: dict[int, set[int]] = {}
        for question_id, template_id in links:
            link_map.setdefault(question_id, set()).add(template_id)
        return link_map
