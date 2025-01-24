from nomad.config.models.plugins import SchemaPackageEntryPoint
from pydantic import Field


class FireWorksSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        from nomad_parser_fireworks.schema_packages.schema_package import m_package

        return m_package


nomad_parser_fireworks_schema = FireWorksSchemaPackageEntryPoint(
    name='FireWorksSchemaPackage',
    description='Entry point for the FireWorks code-specific schema.',
)
