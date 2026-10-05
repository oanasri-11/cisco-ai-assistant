"""
Diagram generator using Graphviz
Converts validated network topology to visual diagrams
"""

import os
import subprocess
import tempfile
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DiagramGenerator:
    def __init__(self, output_format: str = "png"):
        """
        Initialize diagram generator.

        Args:
            output_format: Output format ('png', 'svg', 'pdf', etc.)
        """
        self.output_format = output_format.lower()
        self.device_icons = {
            'router': 'router.svg',
            'switch': 'switch.svg',
            'pc': 'pc.svg',
            'server': 'server.svg',
            'cloud': 'cloud.svg',
            'firewall': 'router.svg',  # fallback
            'loadbalancer': 'server.svg'  # fallback
        }

    def generate_diagram(self, topology: Dict[str, Any],
                        output_dir: str = "outputs",
                        filename: str = "network_diagram") -> Tuple[bool, str, Optional[str]]:
        """
        Generate diagram from network topology.

        Args:
            topology: Dictionary containing devices and connections
            output_dir: Directory to save output files
            filename: Base filename for output (without extension)

        Returns:
            Tuple of (success, message, output_file_path)
        """
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Generate DOT language content
            dot_content = self._generate_dot(topology)

            # Save DOT file temporarily
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
                f.write(dot_content)
                dot_file = f.name

            # Output file path
            output_file = os.path.join(output_dir, f"{filename}.{self.output_format}")

            # Generate diagram using Graphviz
            success, message = self._render_dot_to_image(dot_file, output_file)

            # Clean up temporary DOT file
            try:
                os.unlink(dot_file)
            except OSError:
                pass

            if success:
                return True, f"Diagram generated successfully: {output_file}", output_file
            else:
                return False, f"Failed to generate diagram: {message}", None

        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            return False, f"Error generating diagram: {str(e)}", None

    def _generate_dot(self, topology: Dict[str, Any]) -> str:
        """
        Generate DOT language representation of the topology.

        Args:
            topology: Dictionary with devices and connections

        Returns:
            DOT language string
        """
        lines = [
            "digraph NetworkDiagram {",
            "    rankdir=LR;",  # Left to right layout
            "    node [shape=none];",  # We'll use images for nodes
            "    splines=ortho;",  # Orthogonal lines for connections
            ""
        ]

        # Add devices as nodes with images
        for device in topology.get('devices', []):
            device_id = device['id']
            device_type = device.get('type', 'router')
            label = device.get('label', device_id)

            # Get icon for device type
            icon_filename = self.device_icons.get(device_type, 'router.svg')
            icon_path = f"assets/{icon_filename}"

            # Create node with image and label
            lines.append(f'    {device_id} [')
            lines.append(f'        label=<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">')
            lines.append(f'            <TR><TD><IMG SRC="{icon_path}" SCALING="TRUE" WIDTH="32" HEIGHT="32"/></TD></TR>')
            lines.append(f'            <TR><TD>{label}</TD></TR>')
            lines.append(f'            <TR><TD FontSize="10">{device_type}</TD></TR>')
            lines.append(f'        </TABLE>>;')
            lines.append(f'        shape=none;')
            lines.append(f'    ];')
            lines.append("")

        # Add connections as edges
        for i, conn in enumerate(topology.get('connections', [])):
            source = conn['source']
            target = conn['target']
            label = conn.get('label', '')
            conn_type = conn.get('type', 'ethernet')

            # Style based on connection type
            style = self._get_connection_style(conn_type)

            edge_label = f' [label="{label}" {style}]' if label else f' [{style}]' if style else ''
            lines.append(f'    {source} -> {target}{edge_label};')

        lines.append("}")
        return "\n".join(lines)

    def _get_connection_style(self, conn_type: str) -> str:
        """
        Get styling for connection based on type.

        Args:
            conn_type: Connection type

        Returns:
            String of DOT attributes
        """
        styles = {
            'ethernet': 'color=blue',
            'serial': 'color=green, style=dashed',
            'wireless': 'color=orange, style=dotted',
            'vpn': 'color=purple, style=bold'
        }
        return styles.get(conn_type, 'color=black')

    def _render_dot_to_image(self, dot_file: str, output_file: str) -> Tuple[bool, str]:
        """
        Render DOT file to image using Graphviz.

        Args:
            dot_file: Path to input DOT file
            output_file: Path for output image file

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if dot command is available
            result = subprocess.run(['dot', '-V'], capture_output=True, text=True)
            if result.returncode != 0:
                return False, "Graphviz 'dot' command not found. Please install Graphviz."

            # Render the diagram
            cmd = [
                'dot',
                f'-T{self.output_format}',
                '-o', output_file,
                dot_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True, "Success"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return False, f"Graphviz error: {error_msg}"

        except FileNotFoundError:
            return False, "Graphviz 'dot' command not found. Please install Graphviz and ensure it's in PATH."
        except Exception as e:
            return False, f"Error running Graphviz: {str(e)}"

# Convenience function
def generate_network_diagram(topology: Dict[str, Any],
                           output_dir: str = "outputs",
                           filename: str = "network_diagram",
                           output_format: str = "png") -> Tuple[bool, str, Optional[str]]:
    """
    Convenience function to generate network diagram.

    Args:
        topology: Network topology dictionary
        output_dir: Output directory
        filename: Base filename
        output_format: Output format

    Returns:
        Tuple of (success, message, output_file_path)
    """
    generator = DiagramGenerator(output_format=output_format)
    return generator.generate_diagram(topology, output_dir, filename)

# For direct testing
if __name__ == "__main__":
    # Example topology
    sample_topology = {
        "devices": [
            {
                "id": "router1",
                "type": "router",
                "label": "Main Router",
                "properties": {
                    "ip": "192.168.1.1",
                    "hostname": "router1.example.com"
                }
            },
            {
                "id": "switch1",
                "type": "switch",
                "label": "Floor 1 Switch",
                "properties": {
                    "ip": "192.168.1.2",
                    "hostname": "switch1.example.com"
                }
            },
            {
                "id": "pc1",
                "type": "pc",
                "label": "Workstation 1",
                "properties": {
                    "ip": "192.168.1.10",
                    "hostname": "ws1.example.com"
                }
            }
        ],
        "connections": [
            {
                "source": "router1",
                "target": "switch1",
                "label": "Uplink",
                "type": "ethernet"
            },
            {
                "source": "switch1",
                "target": "pc1",
                "label": "Access Port",
                "type": "ethernet"
            }
        ]
    }

    success, message, output_file = generate_network_diagram(sample_topology)
    print(f"Success: {success}")
    print(f"Message: {message}")
    if output_file:
        print(f"Output file: {output_file}")