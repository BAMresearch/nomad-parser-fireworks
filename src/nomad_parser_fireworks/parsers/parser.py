import os
from typing import (
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

from nomad.config import config
from nomad.parsing.parser import MatchingParser

configuration = config.get_plugin_entry_point(
    'nomad_parser_fireworks.parsers:nomad_parser_fireworks_parser'
)


class FireWorksParser(MatchingParser):
    def parse(
        self, filepath: str, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        self.filepath = filepath
        self.archive = archive
        self.maindir = os.path.dirname(self.filepath)
        self.mainfile = os.path.basename(self.filepath)
