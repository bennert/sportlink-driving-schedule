"""Audit GitHub Actions references against the reviewed runtime inventory."""

import hashlib
import json
from pathlib import Path
import re
import shlex

import requests
import yaml


ROOT = Path(__file__).parent
WORKFLOW = ROOT / '.github' / 'workflows' / 'driving_schedule.yml'
INVENTORY = ROOT / '.github' / 'action-runtime-audit.json'


def fetch_action_metadata(reference):
    """Fetch metadata for a pinned GitHub Action reference."""
    match = re.fullmatch(r'([\w.-]+/[\w.-]+)@([0-9a-f]{40})', reference)
    if not match:
        raise ValueError(f'Action must use a reviewed immutable commit: {reference}')
    repository, revision = match.groups()
    response = requests.get(
        f'https://raw.githubusercontent.com/{repository}/{revision}/action.yml', timeout=30)
    response.raise_for_status()
    return response.text


def _check_archive_contract(action, metadata):
    """Check that an action's archive command matches its reviewed contract."""
    linux = next(step for step in metadata['runs']['steps']
                 if step.get('if') == "runner.os == 'Linux'")
    expression = "${{ inputs.include-hidden-files != 'true' && '--exclude=.[^/]*' || '' }}"
    script = linux['run'].replace(expression, '--exclude=.[^/]*').replace('\\\n', ' ')
    command = next(line.strip() for line in script.splitlines() if line.strip().startswith('tar '))
    arguments = [argument.replace('$INPUT_PATH', '{site}').replace('$RUNNER_TEMP/artifact.tar', '{archive}')
                 for argument in shlex.split(command)[1:]]
    if arguments != action['linux_archive_arguments']:
        raise ValueError('Pages archive command differs from the tested contract')


def audit_workflow(workflow_path=WORKFLOW, inventory_path=INVENTORY, fetch_metadata=None):
    """Validate workflow action references against the runtime inventory."""
    fetch_metadata = fetch_metadata or fetch_action_metadata
    workflow = yaml.load(Path(workflow_path).read_text(encoding='utf-8'), Loader=yaml.BaseLoader)
    inventory = json.loads(Path(inventory_path).read_text(encoding='utf-8'))
    reviewed = {f"{action['repository']}@{action['ref']}": action for action in inventory['actions']}
    if len(reviewed) != len(inventory['actions']):
        raise ValueError('Duplicate reviewed action references')
    pending = [step for job in workflow['jobs'].values() for step in job['steps'] if 'uses' in step]
    checked, results = {}, []
    while pending:
        step = pending.pop(0)
        reference = step['uses']
        if reference not in reviewed or not re.fullmatch(r'[\w.-]+/[\w.-]+@[0-9a-f]{40}', reference):
            raise ValueError(f'Unreviewed action reference: {reference}')
        action = reviewed[reference]
        if reference not in checked:
            source = fetch_metadata(reference)
            metadata = yaml.load(source, Loader=yaml.BaseLoader)
            runtime = metadata['runs']['using']
            if runtime not in ('node24', 'composite') or runtime != action['using']:
                raise ValueError(f'Unsupported runtime for {reference}: {runtime}')
            inputs = metadata.get('inputs', {})
            if not set(action['inputs']).issubset(inputs):
                raise ValueError(f'Reviewed inputs no longer available: {reference}')
            if not set(action['outputs']).issubset(metadata.get('outputs', {})):
                raise ValueError(f'Reviewed outputs no longer available: {reference}')
            for name, value in action.get('defaults', {}).items():
                if inputs.get(name, {}).get('default') != value:
                    raise ValueError(f'Changed default for {reference}: {name}')
            children = [child for child in metadata['runs'].get('steps', []) if 'uses' in child]
            if {child['uses'] for child in children} != set(action.get('dependencies', [])):
                raise ValueError(f'Unreviewed nested dependency: {reference}')
            if 'linux_archive_arguments' in action:
                _check_archive_contract(action, metadata)
            pending.extend(children)
            checked[reference] = metadata
            results.append({'reference': reference, 'using': runtime,
                            'metadata_sha256': hashlib.sha256(source.encode('utf-8')).hexdigest()})
        inputs = checked[reference].get('inputs', {})
        if not set(step.get('with', {})).issubset(inputs):
            raise ValueError(f'Unknown workflow input: {reference}')
        for name, definition in inputs.items():
            if definition.get('required') == 'true' and 'default' not in definition and name not in step.get('with', {}):
                raise ValueError(f'Required action input missing for {reference}: {name}')
    if set(checked) != set(reviewed):
        raise ValueError('Inventory contains unused action references')
    return results


def main():
    """Run the workflow runtime audit and report its result."""
    try:
        results = audit_workflow()
    except (ValueError, KeyError, TypeError, StopIteration, OSError, requests.RequestException) as error:
        print(f'Action runtime audit failed: {error}')
        return 1
    print(json.dumps(results, indent=2))
    print('PASS: all referenced JavaScript actions declare node24; no workflow was executed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())