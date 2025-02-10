from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

from nomad.config import config
from nomad.datamodel.metainfo.workflow import Task, TaskReference, Workflow
from nomad.metainfo import JSON, Quantity, SchemaPackage, SubSection

configuration = config.get_plugin_entry_point(
    'nomad_parser_fireworks.schema_packages:nomad_parser_fireworks_schema'
)

m_package = SchemaPackage()


class FireWorksTask(TaskReference):
    """
    Each of the FireWorks tasks defined in the JSON `json_data["spec"]["_tasks"]`.
    """

    fw_name = Quantity(
        type=str,
        description="""
        The name of the FireWorks task.
        """,
    )

    name = Quantity(
        type=str,
        description="""
        The final string name of the FireWorks task extracted from `fw_name`. Useful when identifying
        the action performed by the task. E.g., if `"atomate.vasp.firetasks.glue_tasks.CopyVaspOutputs"`, then
        `name` is `"CopyVaspOutputs"`.
        """,
    )

    files = Quantity(
        type=str,
        shape=['*'],
        description="""
        The list of files associated with the FireWorks task.
        """,
    )

    general_metadata = Quantity(
        type=JSON,
        description="""
        The general metadata associated with the FireWorks task and which is specific of each of the
        tasks performed in the workflow run.
        """,
    )

    task = Quantity(
        type=Task,
        description="""
        Reference to another entry workflow task composing the FireWorks workflow.
        """,
    )


class FireWorks(Workflow):
    """
    The FireWorks workflow run schema. This is used to define the `Task` and the `Link` between them from the
    main JSON file output by FireWorks.
    """

    fw_id = Quantity(
        type=np.int32,
        description="""
        The ID of the FireWorks workflow run.
        """,
    )

    name = Quantity(
        type=str,
        description="""
        The name of the FireWorks workflow run.
        """,
    )

    created_on = Quantity(
        type=str,
        description="""
        The time at which the FireWorks workflow run started.
        """,
    )

    updated_on = Quantity(
        type=str,
        description="""
        The time at which the FireWorks workflow run ended.
        """,
    )

    tasks = SubSection(
        sub_section=FireWorksTask,
        repeats=True,
        description="""
        The FireWorks tasks of this workflow as a repeating sub section.
        """,
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)


m_package.__init_metainfo__()
