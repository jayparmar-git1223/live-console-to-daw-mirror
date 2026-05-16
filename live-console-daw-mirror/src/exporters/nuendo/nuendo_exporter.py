"""
nuendo_exporter.py — Nuendo Session Exporter

Nuendo uses the same project format as Cubase (.cpr / Track Archive XML),
so this exporter inherits from CubaseExporter with Nuendo-specific settings.

Nuendo is Steinberg's professional post-production DAW, sharing the
same core engine as Cubase but with additional post-production features.

For Version 1, this uses the same Track Archive XML approach as Cubase.
"""

import logging
from exporters.cubase.cubase_exporter import CubaseExporter

logger = logging.getLogger(__name__)


class NuendoExporter(CubaseExporter):
    """
    Nuendo Session Exporter.

    Inherits from CubaseExporter since Nuendo uses the same
    file format (.npr/.cpr are both compatible with Track Archive XML).

    The output is identical to CubaseExporter but labeled for Nuendo.
    """

    def __init__(self):
        # Call grandparent's __init__ with Nuendo settings
        super().__init__()
        self.daw_name = "Nuendo"

    def _build_guide(self, session) -> str:
        """Override guide header to say Nuendo instead of Cubase."""
        guide = super()._build_guide(session)
        guide = guide.replace("CUBASE SESSION GUIDE", "NUENDO SESSION GUIDE")
        guide = guide.replace(
            "3. File → Import → Track Archive",
            "3. File → Import → Track Archive  (same in Nuendo)",
        )
        return guide
