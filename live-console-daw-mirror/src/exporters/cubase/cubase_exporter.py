"""
cubase_exporter.py — Cubase/Nuendo Template Injector

VERSION 1 APPROACH: Template Injection

Rather than attempting to generate a full Cubase .cpr binary file
(which uses a complex proprietary binary format), this exporter:

1. Loads a pre-made Cubase template .cpr file (user-provided)
2. Writes a companion "track setup" XML file that describes
   all tracks, names, groups, and colors
3. Writes a human-readable track list guide for manual or
   scripted import

Future versions will support full .cpr binary generation via
reverse-engineering the CPR format.

The companion XML can be used with future automation or with
the Cubase Track Archive import feature.

Usage:
    from exporters.cubase.cubase_exporter import CubaseExporter

    exporter = CubaseExporter()
    path = exporter.export(session, "output/arena_show_cubase")
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

from models.session import Session
from exporters.base_exporter import BaseExporter, ExporterError

logger = logging.getLogger(__name__)


class CubaseExporter(BaseExporter):
    """
    Cubase/Nuendo Session Exporter.

    VERSION 1: Generates a Track Archive XML + track guide.

    The Track Archive XML format is a subset of Cubase's XML import format.
    This is the recommended approach until full .cpr binary generation
    is implemented.

    What is generated:
    - {session_name}_tracks.xml  → Cubase Track Archive (import via
                                   File → Import → Track Archive)
    - {session_name}_guide.txt   → Human-readable track setup guide

    Note on CPR binary format:
        The .cpr format is a proprietary binary format used by Steinberg.
        Full generation requires reverse-engineering the format, which is
        planned for a future version.
    """

    def __init__(self):
        super().__init__(daw_name="Cubase", file_extension=".xml")

    def export(self, session: Session, output_path: str) -> str:
        """
        Export session data for Cubase import.

        Parameters
        ----------
        session : Session
            The session to export.
        output_path : str
            Base path for output files (extension is managed internally).

        Returns
        -------
        str
            Path to the generated XML file.
        """
        if not session.tracks:
            raise ExporterError("CubaseExporter: Session has no tracks to export.")

        self.logger.info(
            f"[INFO] CubaseExporter: Exporting '{session.session_name}' "
            f"({len(session.tracks)} tracks) → Cubase"
        )

        base = Path(output_path).with_suffix("")

        # Generate Track Archive XML
        xml_path = base.with_suffix(".xml")
        xml_path.parent.mkdir(parents=True, exist_ok=True)
        xml_content = self._build_track_archive_xml(session)
        xml_path.write_text(xml_content, encoding="utf-8")

        # Generate human-readable guide
        guide_path = base.with_name(base.name + "_guide.txt")
        guide_content = self._build_guide(session)
        guide_path.write_text(guide_content, encoding="utf-8")

        self.logger.info(
            f"[SUCCESS] CubaseExporter: "
            f"XML → '{xml_path}', Guide → '{guide_path}'"
        )

        return str(xml_path)

    def _build_track_archive_xml(self, session: Session) -> str:
        """
        Build a Cubase Track Archive XML document.

        Track Archive is a standard Cubase format for importing
        track configurations. It can be imported via:
        File → Import → Track Archive
        """
        root = ET.Element("tracklist")
        root.set("version", "8.0")

        for track in session.tracks:
            track_elem = ET.SubElement(root, "track")
            track_elem.set("type", "AudioTrack")

            name_elem = ET.SubElement(track_elem, "name")
            name_elem.text = track.name

            ch_elem = ET.SubElement(track_elem, "channel")
            ch_elem.text = str(track.channel)

            group_elem = ET.SubElement(track_elem, "group")
            group_elem.text = track.group

            type_elem = ET.SubElement(track_elem, "trackType")
            type_elem.text = track.track_type

            color_elem = ET.SubElement(track_elem, "color")
            color_elem.text = track.color

            output_elem = ET.SubElement(track_elem, "output")
            output_elem.text = track.output

            if track.stereo_pair:
                stereo_elem = ET.SubElement(track_elem, "stereoPair")
                stereo_elem.text = str(track.stereo_pair)

        # Pretty-print the XML
        raw = ET.tostring(root, encoding="unicode")
        try:
            reparsed = minidom.parseString(raw)
            return reparsed.toprettyxml(indent="  ", encoding=None)
        except Exception:
            return raw

    def _build_guide(self, session: Session) -> str:
        """
        Build a human-readable track setup guide.

        This guide can be used to manually set up a Cubase session
        if the XML import doesn't work as expected.
        """
        lines = [
            "=" * 60,
            f"CUBASE SESSION GUIDE",
            f"Generated by: Live Console DAW Mirror",
            "=" * 60,
            f"",
            f"Session Name : {session.session_name}",
            f"Console      : {session.console}",
            f"Sample Rate  : {session.sample_rate} Hz",
            f"Bit Depth    : {session.bit_depth}-bit",
            f"Track Count  : {session.get_track_count()}",
            f"Source File  : {session.source_file}",
            f"",
            "─" * 60,
            f"TRACK LIST (in order)",
            "─" * 60,
            "",
        ]

        groups_done = set()
        for track in session.tracks:
            if track.group not in groups_done:
                lines.append(f"  ── {track.group} ──")
                groups_done.add(track.group)

            stereo_note = ""
            if track.stereo_pair:
                stereo_note = f"  ↔ ch{track.stereo_pair}"

            lines.append(
                f"  CH {track.channel:>3}  │  {track.name:<30} │ {track.track_type}{stereo_note}"
            )

        lines += [
            "",
            "─" * 60,
            "GROUPS / FOLDER TRACKS",
            "─" * 60,
            "",
        ]

        for group in session.get_unique_groups():
            group_tracks = session.get_tracks_in_group(group)
            ch_list = ", ".join(str(t.channel) for t in group_tracks)
            lines.append(f"  {group:<15} → CH: {ch_list}")

        lines += [
            "",
            "─" * 60,
            "BUSES",
            "─" * 60,
            "",
        ]

        for bus in session.buses:
            ch_list = ", ".join(str(c) for c in bus.channels)
            lines.append(f"  {bus.name:<20} ({bus.bus_type}) → CH: {ch_list}")

        lines += [
            "",
            "─" * 60,
            "IMPORT INSTRUCTIONS",
            "─" * 60,
            "",
            "1. Open Cubase / Nuendo",
            "2. Create a new empty project",
            "3. File → Import → Track Archive",
            "4. Select the .xml file alongside this guide",
            "5. Tracks will be created in the correct order",
            "6. Set input routing manually or use Dante/patch sheet",
            "",
            "=" * 60,
            "Live Console DAW Mirror — liveconsole.io",
            "=" * 60,
        ]

        return "\n".join(lines)
