import json
from pathlib import Path
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
        reviewed = {action['repository']: action for action in audit['actions']}
        for repository in ('actions/checkout', 'actions/setup-python', 'actions/configure-pages',
                           'actions/deploy-pages', 'actions/upload-artifact'):
            action = reviewed[repository]
            self.assertEqual(action['using'], 'node24')
            self.assertRegex(action['ref'], r'^[0-9a-f]{40}$')
            matches = [step for step in workflow_steps().values()
                       if step.get('uses', '').startswith(repository + '@')]
            self.assertTrue(matches, repository)
            for step in matches:
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


if __name__ == '__main__':
    unittest.main()