import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('check_ui', ROOT / 'tools/check_ui.py')
UI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UI)


class UiSyntaxTests(unittest.TestCase):
    def test_complete_configuration(self):
        controls = UI.check()
        self.assertEqual(len(controls), 196)

    def test_missing_layout_separator_is_rejected(self):
        text = '界面:{日常功能:{水平布局:{文字框:{名称:"前"}},文字框:{名称:"后"}}}'
        UI.parse(text)
        with self.assertRaises(ValueError):
            UI.parse(text.replace('}},文字框', '}}文字框'))

    def test_unclosed_string_and_braces_are_rejected(self):
        for text in ['界面:{日常功能:{', '界面:{文字框:{名称:"未闭合}}']:
            with self.assertRaises((ValueError, IndexError)):
                UI.parse(text)

    def test_undefined_callback_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Undefined callback'):
            UI.inspect('界面:{多选框:{名称:"开关",选中:false,点击响应:"不存在"}}', '')


if __name__ == '__main__':
    unittest.main()
