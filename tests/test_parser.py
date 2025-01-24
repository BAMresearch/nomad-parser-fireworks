import logging

from nomad.datamodel import EntryArchive

from nomad_parser_fireworks.parsers.parser import FireWorksParser


def test_parse_file():
    parser = FireWorksParser()
    archive = EntryArchive()
    parser.parse('tests/data/FW.json', archive, logging.getLogger())

    assert True
