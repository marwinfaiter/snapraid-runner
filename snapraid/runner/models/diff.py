from attrs import define

@define(frozen=True)
class Diff:
    equal: int
    added: int
    removed: int
    updated: int
    moved: int
    copied: int
    restored: int

    @property
    def changes(self) -> bool:
        return any([
            self.added,
            self.removed,
            self.updated,
            self.moved,
        ])
