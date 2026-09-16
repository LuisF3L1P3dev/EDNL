import unittest


class UiImportTests(unittest.TestCase):
    def test_ui_module_imports_without_starting_mainloop(self) -> None:
        from labyrinth.ui import PathfindingApp

        self.assertTrue(callable(PathfindingApp))


if __name__ == "__main__":
    unittest.main()
