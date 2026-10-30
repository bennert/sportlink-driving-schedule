import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from tempfile import TemporaryDirectory
import unittest

import yaml


ROOT = Path(__file__).parent
WORKFLOW = ROOT / '.github' / 'workflows' / 'driving_schedule.yml'
AUDIT = ROOT / '.github' / 'action-runtime-audit.json'


def load_workflow():
    return yaml.load(WORKFLOW.read_text(encoding='utf-8'), Loader=yaml.BaseLoader)


def workflow_steps():
    return {step['name']: step for step in load_workflow()['jobs']['generate-schedule']['steps']}


class WorkflowMigrationTests(unittest.TestCase):
    def test_direct_actions_match_reviewed_node24_commits(self):
        audit = json.loads(AUDIT.read_text(encoding='utf-8'))
        reviewed = {(action['repository'], action['ref']): action for action in audit['actions']}
        for repository in ('actions/checkout', 'actions/setup-python', 'actions/configure-pages',
                           'actions/deploy-pages', 'actions/upload-artifact'):
            matches = [step for step in workflow_steps().values()
                       if step.get('uses', '').startswith(repository + '@')]
            self.assertTrue(matches, repository)
            for step in matches:
                action = reviewed[(repository, step['uses'].split('@')[1])]
                self.assertEqual(action['using'], 'node24')
                self.assertRegex(action['ref'], r'^[0-9a-f]{40}$')
                self.assertEqual(step['uses'], f"{repository}@{action['ref']}")
                self.assertTrue(set(step.get('with', {})).issubset(action['inputs']))

    def test_existing_execution_and_notification_contract_is_unchanged(self):
        workflow = load_workflow()
        job = workflow['jobs']['generate-schedule']
        steps = workflow_steps()
        self.assertEqual(workflow['on'], {'push': {'branches': ['main']}, 'workflow_dispatch': '',
                                          'schedule': [{'cron': '0 6 * * 1'}]})
        self.assertEqual(job['runs-on'], 'ubuntu-latest')
        self.assertEqual(job['permissions'], {'contents': 'read', 'pages': 'write', 'id-token': 'write'})
        self.assertEqual(job['environment'], {'name': 'github-pages',
                         'url': '${{ steps.deployment.outputs.page_url }}'})
        self.assertEqual(steps['Set up Python']['with'], {'python-version': '3.11'})
        for name, identifier in (('Deploy to GitHub Pages', 'deployment'),
                                 ('Create driving schedule', 'create_schedule'),
                                 ('Check for changes', 'check_changes')):
            self.assertEqual(steps[name]['id'], identifier)
        self.assertEqual(steps['Send emails per team']['if'], "steps.check_changes.outputs.changes == 'true'")
        self.assertEqual(steps['Send weekly Telegram announcements']['if'],
                         "always() && github.event_name == 'schedule' && steps.create_schedule.outcome == 'success'")
        text = WORKFLOW.read_text(encoding='utf-8')
        for setting in ('FORCE_JAVASCRIPT_ACTIONS_TO_NODE24', 'ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION'):
            self.assertNotIn(setting, text)

    def test_ordinary_artifact_paths_and_retention_are_preserved(self):
        expected = {
            'driving-schedules-md': (['docs/*.md', 'docs/schedule_changes_*.json'], '30'),
            'google-maps-place-id-cache': (['docs/google_maps_place_ids.json'], '90'),
            'driving-schedules-pdf': (['docs/*.pdf'], '90'),
        }
        uploads = {step['with']['name']: step for step in workflow_steps().values()
                   if step.get('uses', '').startswith('actions/upload-artifact@')}
        for name, (paths, retention) in expected.items():
            self.assertEqual(uploads[name]['with']['path'].split(), paths)
            self.assertEqual(uploads[name]['with']['retention-days'], retention)
        self.assertEqual(uploads['google-maps-place-id-cache']['if'],
                         "steps.create_schedule.outcome == 'success'")

    def test_both_downloads_keep_previous_successful_run_and_missing_artifact_contracts(self):
        audit = json.loads(AUDIT.read_text(encoding='utf-8'))
        action = next(item for item in audit['actions']
                      if item['repository'] == 'dawidd6/action-download-artifact')
        self.assertEqual(action['using'], 'node24')
        self.assertRegex(action['ref'], r'^[0-9a-f]{40}$')
        downloads = [step for step in workflow_steps().values()
                     if step.get('uses', '').startswith('dawidd6/action-download-artifact@')]
        self.assertEqual(len(downloads), 2)
        self.assertEqual({step['with']['name'] for step in downloads},
                         {'driving-schedules-md', 'google-maps-place-id-cache'})
        for step in downloads:
            self.assertEqual(step['uses'], f"{action['repository']}@{action['ref']}")
            self.assertEqual(step['continue-on-error'], 'true')
            self.assertEqual(step['with'], {
                'name': step['with']['name'], 'path': 'docs/', 'workflow': 'driving_schedule.yml',
                'workflow_conclusion': 'success', 'if_no_artifact_found': 'ignore',
            })
            self.assertTrue(set(step['with']).issubset(action['inputs']))

    def test_pages_composite_uses_only_reviewed_node24_dependencies(self):
        audit = json.loads(AUDIT.read_text(encoding='utf-8'))
        reviewed = {f"{action['repository']}@{action['ref']}": action for action in audit['actions']}
        step = workflow_steps()['Upload GitHub Pages artifact']
        pages = reviewed[step['uses']]
        self.assertEqual(pages['using'], 'composite')
        self.assertEqual(step['with'], {'path': 'site', 'name': 'github-pages',
                                       'retention-days': '1', 'include-hidden-files': 'false'})
        self.assertEqual(len(pages['dependencies']), 1)
        for dependency in pages['dependencies']:
            self.assertEqual(reviewed[dependency]['using'], 'node24')

    def test_reviewed_pages_tar_contract_keeps_site_paths_and_excludes_secrets_and_links(self):
        audit = json.loads(AUDIT.read_text(encoding='utf-8'))
        pages = next(action for action in audit['actions'] if action['using'] == 'composite')
        git = shutil.which('git')
        git_tar = Path(git).parents[1] / 'usr' / 'bin' / 'tar.exe' if git else Path('/nonexistent')
        tar = str(git_tar) if git_tar.exists() else shutil.which('tar')
        self.assertIsNotNone(tar, 'tar is required to validate the Pages archive contract')
        with TemporaryDirectory() as directory:
            root = Path(directory)
            site = root / 'site'
            team = site / 'teams' / 'ehv-hs1'
            team.mkdir(parents=True)
            (site / 'index.html').write_text('Schedule links', encoding='utf-8')
            (team / 'latest.pdf').write_bytes(b'PDF fixture')
            os.link(team / 'latest.pdf', team / 'linked.pdf')
            (site / '.env').write_text('DO_NOT_PUBLISH', encoding='utf-8')
            for name in ('.git', '.github'):
                (site / name).mkdir()
                (site / name / 'secret').write_text('DO_NOT_PUBLISH', encoding='utf-8')
            (root / 'outside.txt').write_text('OUTSIDE_SITE', encoding='utf-8')
            archive = root / 'artifact.tar'
            arguments = [argument.format(site='site', archive='artifact.tar')
                         for argument in pages['linux_archive_arguments']]
            result = subprocess.run([tar, *arguments], cwd=root, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            with tarfile.open(archive) as packaged:
                members = packaged.getmembers()
                files = {member.name.removeprefix('./') for member in members if member.isfile()}
                self.assertEqual(files, {'index.html', 'teams/ehv-hs1/latest.pdf', 'teams/ehv-hs1/linked.pdf'})
                self.assertFalse(any(member.issym() or member.islnk() for member in members))
                self.assertEqual(packaged.extractfile('./teams/ehv-hs1/latest.pdf').read(), b'PDF fixture')


if __name__ == '__main__':
    unittest.main()