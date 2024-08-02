"""Generate the docs."""

from pathlib import Path
import pdoc
import pdoc.render


here = Path(__file__).parent

pdoc.render.configure(
    docformat="google",
    footer_text="atlus",
    favicon="https://whubsch.github.io/atlus/atlus_fav.svg",
    logo="https://whubsch.github.io/atlus/logo_black.png",
)
pdoc.pdoc("src/atlus", output_directory=here.parent / "docs")
