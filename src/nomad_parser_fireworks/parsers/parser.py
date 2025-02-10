import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

from nomad.config import config
from nomad.parsing.parser import MatchingParser

from nomad_parser_fireworks.parsers.utils import get_files
from nomad_parser_fireworks.schema_packages.schema_package import (
    FireWorks,
    FireWorksTask,
)

configuration = config.get_plugin_entry_point(
    'nomad_parser_fireworks.parsers:nomad_parser_fireworks_parser'
)


class FireWorksParser(MatchingParser):
    def parse_task(self, fw_task_dict: dict) -> FireWorksTask:
        """
        Parse the FireWorks task from the JSON file data in `fw_task_dict`.

        Args:
            fw_task_dict (dict): The dictionary containing the FireWorks task data.

        Returns:
            FireWorksTask: The parsed FireWorks task.
        """
        files = []
        fw_name = ''
        task_name = ''
        general_metadata: dict = {}
        for key, val in fw_task_dict.items():
            if key in [
                'additional_files',
                'poscar_path',
                'incar_path',
                'potcar_path',
                'files',
            ]:
                # flattening the list
                if isinstance(val, list):
                    for v in val:
                        files.append(v)
                else:
                    files.append(val)
            elif key == '_fw_name':
                fw_name = val
                try:
                    task_name = fw_name.replace('}}', '').split('.')[-1]
                except Exception:
                    continue
            else:
                # flattening the dictionary
                if isinstance(val, dict):
                    for k, v in val.items():
                        general_metadata[f'{key}.{k}'] = v
                else:
                    general_metadata[key] = val

        return FireWorksTask(
            fw_name=fw_name,
            name=task_name,
            files=files,
            general_metadata=general_metadata,
        )

    def parse_atomate_vasp_lobster(self, metadata: list, upload_id: str):
        """
        Parses the specific FireWorks workflow for DFT VASP + LOBSTER and tries to connect them with the
        FireWorks tasks in the upload.

        Args:
            metadata (list): The list of metadata containing the entry_id and mainfile of the entries in the upload.
            upload_id (str): The upload_id of the current upload.
        """
        # Store the nearest VASP and LOBSTER mainfiles in the upload and try to connect them with the FireWorks tasks
        vasp_files = get_files('vapsrun.xml', self.filepath, self.mainfile, deep=False)
        vasp_file = vasp_files[-1].split('raw/')[-1]
        lobster_files = get_files(
            r'.*lobsterout.*', self.filepath, self.mainfile, deep=False
        )
        lobster_file = lobster_files[-1].split('raw/')[-1]

        # FireWorks filepath stripped from the raw/ part
        filepath_stripped = self.filepath.split('raw/')[-1]

        for entry_id, mainfile in metadata:
            if mainfile == filepath_stripped:
                continue
            entry_archive = self.archive.m_context.load_archive(
                entry_id, upload_id, None
            )

            for task in self.archive.workfow2.tasks:
                if task.name == 'CopyVaspOutputs' and mainfile == vasp_file:
                    task_ref = entry_archive.worflow2
                    task.task = task_ref
                    task.inputs = [task_ref.inputs[0]]
                    task.outputs = [task_ref.outputs[-1]]
                    # add the input of the DFT VASP run as an input of this specific FireWorks workflow
                    self.archive.workflow2.inputs = [task_ref.inputs[0]]
                elif task.name == 'RunLobster' and mainfile == lobster_file:
                    task_ref = entry_archive.worflow2
                    task.task = task_ref
                    task.inputs = [task_ref.inputs[0]]
                    task.outputs = [task_ref.outputs[-1]]
                    # add the output of the LOBSTER run as an output of this specific FireWorks workflow
                    self.archive.workflow2.outputs = [task_ref.outputs[-1]]

    def parse(
        self, filepath: str, archive: 'EntryArchive', logger: 'BoundLogger'
    ) -> None:
        self.filepath = filepath
        self.archive = archive
        self.maindir = os.path.dirname(self.filepath)
        self.mainfile = os.path.basename(self.filepath)

        # Read the file data
        with open(filepath) as f:
            data = json.load(f)

        # Create the `workflow` section and append it to the `archive`
        workflow = FireWorks(
            fw_id=data.get('fw_id'),
            name=data.get('name'),
            created_on=data.get('created_on'),
            updated_on=data.get('updated_on'),
        )
        self.archive.workflow2 = workflow

        # Parse each of the tasks specified in the `json_data["spec"]["_tasks"]`
        fw_tasks = data.get('spec', {}).get('_tasks', [])
        for fw_task in fw_tasks:
            task = self.parse_task(fw_task)
            workflow.tasks.append(task)

        # Try to connect the tasks with actual entries in the archive
        # ! This only works when the `archive` has the context of being an upload in NOMAD (need to be tested in the GUI!)
        upload_id = ''
        try:
            from nomad.app.v1.models import MetadataRequired
            from nomad.search import search

            # Searches in the same upload as the FireWorks JSON file
            upload_id = self.archive.metadata.upload_id
            search_ids = search(
                owner='visible',
                user_id=self.archive.metadata.main_author.user_id,
                query={'upload_id': upload_id},
                required=MetadataRequired(include=['entry_id', 'mainfile']),
            ).data
            # `metadata` stores a list of entry_id and mainfiles present in the upload
            metadata = [[sid['entry_id'], sid['mainfile']] for sid in search_ids]
            if len(metadata) <= 1:
                logger.info('No other mainfiles found in the upload.')
                return
        except Exception:
            logger.warning(
                'Could not connect any of the FireWorks tasks with actual entries in the upload.'
            )

        # If `metadata` has more than one entry, try to connect the tasks with the entries
        try:
            self.parse_atomate_vasp_lobster(metadata, upload_id)
        except Exception:
            return
