"""Bundle a local vaxfont.dat for private builds when the font file is present."""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version, build_data):
        root = Path(self.root)
        candidates = (
            root / "src" / "strokefont" / "data" / "vaxfont.dat",
            root / "vaxfont.dat",
        )
        source = next((path for path in candidates if path.is_file()), None)
        if source is None:
            return

        if self.target_name == "sdist":
            target = "src/strokefont/data/vaxfont.dat"
        else:
            target = "strokefont/data/vaxfont.dat"
        build_data["force_include"][str(source)] = target
