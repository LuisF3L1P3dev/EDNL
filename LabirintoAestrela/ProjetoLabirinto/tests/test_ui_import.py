import unittest
from unittest.mock import Mock


class UiImportTests(unittest.TestCase):
    def test_ui_module_imports_without_starting_mainloop(self) -> None:
        from labyrinth.ui import PathfindingApp

        self.assertTrue(callable(PathfindingApp))

    def test_available_grid_sizes_create_clean_valid_grids(self) -> None:
        from labyrinth.ui import GRID_SIZES, _create_grid_for_size

        expected_sizes = {
            "Pequeno (11 × 17)": (11, 17),
            "Médio (21 × 31)": (21, 31),
            "Grande (31 × 45)": (31, 45),
        }
        self.assertEqual(GRID_SIZES, expected_sizes)

        for size_name, dimensions in expected_sizes.items():
            with self.subTest(size=size_name):
                grid = _create_grid_for_size(size_name)
                self.assertEqual((grid.rows, grid.columns), dimensions)
                self.assertTrue(grid.in_bounds(grid.start))
                self.assertTrue(grid.in_bounds(grid.goal))
                self.assertNotEqual(grid.start, grid.goal)
                self.assertEqual(grid.walls, set())

    def test_unknown_grid_size_is_rejected(self) -> None:
        from labyrinth.ui import _create_grid_for_size

        with self.assertRaisesRegex(ValueError, "Tamanho de grade desconhecido"):
            _create_grid_for_size("Gigante")

    def test_grid_size_change_cancels_execution_and_rebuilds_panels(self) -> None:
        from labyrinth.model import Grid
        from labyrinth.ui import PathfindingApp

        app = object.__new__(PathfindingApp)
        app.grid_model = Grid()
        app.grid_model.set_wall((0, 0))
        app.grid_size_var = Mock()
        app.grid_size_var.get.return_value = "Pequeno (11 × 17)"
        app.status_var = Mock()
        app._cancel_execution = Mock()
        app._rebuild_panels = Mock()

        PathfindingApp._on_grid_size_changed(app, None)

        app._cancel_execution.assert_called_once_with()
        app._rebuild_panels.assert_called_once_with()
        self.assertEqual((app.grid_model.rows, app.grid_model.columns), (11, 17))
        self.assertEqual(app.grid_model.walls, set())
        app.status_var.set.assert_called_with("Grade alterada para 11 × 17.")


if __name__ == "__main__":
    unittest.main()
