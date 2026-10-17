import json
import unittest
from mq_subset import ROOT
from mq_symbols import symbol_conflicts


class MQSymbolTests(unittest.TestCase):
    def test_global_variable_and_function_differing_only_by_case_collide(self):
        problems = symbol_conflicts([('entry', 'Dim legendTerminal\n'), ('flow', 'Function LegendTerminal(reason)\nEnd Function\n')])
        self.assertEqual(len(problems), 1)
        self.assertIn('legendTerminal', problems[0])

    def test_duplicate_procedure_names_across_modules_collide(self):
        self.assertEqual(len(symbol_conflicts([('a', 'Sub Finish()\nEnd Sub'), ('b', 'Function FINISH()\nEnd Function')])), 1)

    def test_distinct_confirmation_function_and_terminal_variable_are_legal(self):
        self.assertEqual(symbol_conflicts([('a', 'Dim legendTerminal\nFunction ConfirmLegendTerminal(reason)\nDim result\nEnd Function\nSub Other()\nDim result\nEnd Sub')]), [])

    def test_current_project_has_no_global_case_insensitive_collisions(self):
        config = json.loads((ROOT/'project.json').read_text('utf-8-sig'))
        paths = [config['entry']] + config['modules']
        self.assertEqual(symbol_conflicts((p, (ROOT/p).read_text('utf-8-sig')) for p in paths), [])


if __name__ == '__main__':
    unittest.main()
