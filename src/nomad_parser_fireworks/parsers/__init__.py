from nomad.config.models.plugins import ParserEntryPoint
from pydantic import Field


class FireWorksParserEntryPoint(ParserEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        from nomad_parser_fireworks.parsers.parser import FireWorksParser

        return FireWorksParser(**self.dict())


nomad_parser_fireworks_parser = FireWorksParserEntryPoint(
    name='FireWorksParserEntryPoint',
    description='Entry point for the FireWorks parser.',
    mainfile_contents_dict={'__has_all_keys': ['fw_id', 'spec']},
    # large `level` because this is a workflow manager (but it should be handled by another key more explicit on this)
    # ! ask @ladinesa about this
    level=10,
)
