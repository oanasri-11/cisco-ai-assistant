"""
Diagram generator using Graphviz.

Converts validated network topology to visual diagrams
using Cisco device icons.
"""

import os
import subprocess
import tempfile
from typing import Dict, Any, Tuple, Optional
import logging

import cairosvg

logger = logging.getLogger(__name__)


class DiagramGenerator:
    """Generate network diagrams using Graphviz and Cisco icons."""

    def __init__(self, output_format: str = "png"):
        """
        Initialize diagram generator.

        Args:
            output_format: Output format ('png', 'svg', 'pdf', etc.)
        """

        self.output_format = output_format.lower()

        # Project root directory
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        # Cisco SVG icons
        self.device_icons = {
            "router": "router.svg",
            "switch": "switch.svg",
            "pc": "pc.svg",
        }

    def _get_icon_path(self, device_type: str) -> Optional[str]:
        """
        Get a PNG icon path for a device type.

        Graphviz can be unreliable with SVG images,
        so SVG icons are converted to PNG automatically.
        """

        svg_filename = self.device_icons.get(device_type)

        if not svg_filename:
            return None

        assets_dir = os.path.join(
            self.base_dir,
            "assets",
        )

        svg_path = os.path.join(
            assets_dir,
            svg_filename,
        )

        if not os.path.exists(svg_path):
            logger.warning(
                f"Icon not found: {svg_path}"
            )
            return None

        # PNG version
        png_filename = os.path.splitext(
            svg_filename
        )[0] + ".png"

        png_path = os.path.join(
            assets_dir,
            png_filename,
        )

        # Convert SVG → PNG if PNG does not exist
        if not os.path.exists(png_path):

            try:
                cairosvg.svg2png(
                    url=svg_path,
                    write_to=png_path,
                    output_width=64,
                    output_height=64,
                )

                logger.info(
                    f"Converted {svg_filename} to {png_filename}"
                )

            except Exception as e:

                logger.error(
                    f"Failed to convert {svg_filename}: {e}"
                )

                return None

        return png_path

    def generate_diagram(
        self,
        topology: Dict[str, Any],
        output_dir: str = "outputs",
        filename: str = "network_diagram",
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Generate diagram from network topology.

        Args:
            topology: Dictionary containing devices and connections.
            output_dir: Directory to save output files.
            filename: Base filename for output.

        Returns:
            Tuple of:
            (success, message, output_file_path)
        """

        try:

            # Make output directory absolute
            if not os.path.isabs(output_dir):
                output_dir = os.path.join(
                    self.base_dir,
                    output_dir,
                )

            os.makedirs(
                output_dir,
                exist_ok=True,
            )

            # Generate DOT content
            dot_content = self._generate_dot(
                topology
            )

            # Temporary DOT file
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".dot",
                delete=False,
                encoding="utf-8",
            ) as f:

                f.write(dot_content)
                dot_file = f.name

            # Output file
            output_file = os.path.join(
                output_dir,
                f"{filename}.{self.output_format}",
            )

            # Render with Graphviz
            success, message = (
                self._render_dot_to_image(
                    dot_file,
                    output_file,
                )
            )

            # Delete temporary DOT file
            try:
                os.unlink(dot_file)
            except OSError:
                pass

            if success:

                return (
                    True,
                    f"Diagram generated successfully: {output_file}",
                    output_file,
                )

            return (
                False,
                f"Failed to generate diagram: {message}",
                None,
            )

        except Exception as e:

            logger.error(
                f"Error generating diagram: {e}"
            )

            return (
                False,
                f"Error generating diagram: {str(e)}",
                None,
            )

    def _generate_dot(
        self,
        topology: Dict[str, Any],
    ) -> str:
        """
        Generate Graphviz DOT representation
        using Cisco icons.
        """

        lines = [
            "digraph NetworkDiagram {",
            "    rankdir=LR;",
            '    graph [bgcolor="white"];',
            '    node [fontname="Arial"];',
            '    edge [fontname="Arial"];',
            "    splines=ortho;",
            "",
        ]

        # --------------------------------------------------
        # DEVICES
        # --------------------------------------------------

        for device in topology.get(
            "devices",
            [],
        ):

            device_id = device["id"]

            device_type = device.get(
                "type",
                "router",
            ).lower()

            label = device.get(
                "label",
                device_id,
            )

            icon_path = self._get_icon_path(
                device_type
            )

            safe_label = str(label).replace(
                '"',
                '\\"',
            )

            # If Cisco icon exists
            if icon_path:

                # Graphviz expects a path with forward slashes
                graphviz_icon_path = icon_path.replace(
                    "\\",
                    "/",
                )

                lines.append(
                    f'    "{device_id}" ['
                )

                lines.append(
                    '        shape=none,'
                )

                lines.append(
                    '        label=<'
                )

                lines.append(
                    '            <TABLE '
                    'BORDER="0" '
                    'CELLBORDER="0" '
                    'CELLSPACING="0">'
                )

                lines.append(
                    f'                <TR>'
                    f'<TD>'
                    f'<IMG SRC="{graphviz_icon_path}" '
                    f'WIDTH="64" '
                    f'HEIGHT="64"/>'
                    f'</TD>'
                    f'</TR>'
                )

                lines.append(
                    f'                <TR>'
                    f'<TD>'
                    f'{safe_label}'
                    f'</TD>'
                    f'</TR>'
                )

                lines.append(
                    '            </TABLE>'
                )

                lines.append(
                    '        >;'
                )

                lines.append(
                    '    ];'
                )

            else:

                # Fallback if icon is missing
                lines.append(
                    f'    "{device_id}" '
                    f'[label="{safe_label}", '
                    f'shape=box];'
                )

            lines.append("")

        # --------------------------------------------------
        # CONNECTIONS
        # --------------------------------------------------

        for conn in topology.get(
            "connections",
            [],
        ):

            source = conn["source"]
            target = conn["target"]

            label = conn.get(
                "label",
                "",
            )

            conn_type = conn.get(
                "type",
                "ethernet",
            )

            style = self._get_connection_style(
                conn_type
            )

            if label:

                safe_label = str(label).replace(
                    '"',
                    '\\"',
                )

                lines.append(
                    f'    "{source}" -> "{target}" '
                    f'[label="{safe_label}" {style}];'
                )

            else:

                lines.append(
                    f'    "{source}" -> "{target}" '
                    f'[{style}];'
                )

        lines.append("}")

        return "\n".join(lines)

    def _get_connection_style(
        self,
        conn_type: str,
    ) -> str:
        """Get styling for connection type."""

        styles = {
            "ethernet": "color=blue",
            "serial": "color=green, style=dashed",
            "wireless": "color=orange, style=dotted",
            "vpn": "color=purple, style=bold",
        }

        return styles.get(
            conn_type,
            "color=black",
        )

    def _render_dot_to_image(
        self,
        dot_file: str,
        output_file: str,
    ) -> Tuple[bool, str]:
        """
        Render DOT file using Graphviz.
        """

        try:

            # Check Graphviz
            result = subprocess.run(
                ["dot", "-V"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:

                return (
                    False,
                    "Graphviz 'dot' command not found. "
                    "Make sure Graphviz is installed and in PATH.",
                )

            # Render diagram
            command = [
                "dot",
                f"-T{self.output_format}",
                "-o",
                output_file,
                dot_file,
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:

                return (
                    True,
                    "Success",
                )

            error_msg = (
                result.stderr.strip()
                if result.stderr
                else "Unknown Graphviz error"
            )

            return (
                False,
                f"Graphviz error: {error_msg}",
            )

        except FileNotFoundError:

            return (
                False,
                "Graphviz 'dot' command not found. "
                "Install Graphviz and add it to PATH.",
            )

        except Exception as e:

            return (
                False,
                f"Error running Graphviz: {str(e)}",
            )


# ------------------------------------------------------
# Convenience function
# ------------------------------------------------------

def generate_network_diagram(
    topology: Dict[str, Any],
    output_dir: str = "outputs",
    filename: str = "network_diagram",
    output_format: str = "png",
) -> Tuple[bool, str, Optional[str]]:

    generator = DiagramGenerator(
        output_format=output_format
    )

    return generator.generate_diagram(
        topology,
        output_dir,
        filename,
    )


# ------------------------------------------------------
# Direct testing
# ------------------------------------------------------

if __name__ == "__main__":

    sample_topology = {
        "devices": [
            {
                "id": "router1",
                "type": "router",
                "label": "Router",
            },
            {
                "id": "switch1",
                "type": "switch",
                "label": "Switch",
            },
            {
                "id": "pc1",
                "type": "pc",
                "label": "PC 1",
            },
        ],
        "connections": [
            {
                "source": "router1",
                "target": "switch1",
                "type": "ethernet",
            },
            {
                "source": "switch1",
                "target": "pc1",
                "type": "ethernet",
            },
        ],
    }

    success, message, output_file = (
        generate_network_diagram(
            sample_topology
        )
    )

    print(f"Success: {success}")
    print(f"Message: {message}")

    if output_file:
        print(f"Output file: {output_file}")