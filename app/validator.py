"""
Network topology validator
Performs logical checks on network diagrams
"""

from typing import List, Dict, Any, Tuple, Optional
from .schemas import NetworkTopology, Device, Connection
import ipaddress
import logging

logger = logging.getLogger(__name__)

class NetworkValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate(self, topology: NetworkTopology) -> Tuple[bool, List[str], List[str]]:
        """
        Validate network topology for logical consistency.

        Args:
            topology: NetworkTopology object to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        # Convert to dictionaries for easier lookup
        devices_by_id = {device.id: device for device in topology.devices}
        device_ids = set(devices_by_id.keys())

        # Check 1: Duplicate device IDs
        self._check_duplicate_device_ids(topology.devices)

        # Check 2: Orphaned devices (no connections)
        self._check_orphaned_devices(topology.devices, topology.connections)

        # Check 3: Duplicate IPs
        self._check_duplicate_ips(topology.devices)

        # Check 4: Invalid IP addresses
        self._check_invalid_ips(topology.devices)

        # Check 5: Self-connections
        self._check_self_connections(topology.connections)

        # Check 6: Duplicate connections
        self._check_duplicate_connections(topology.connections)

        # Check 7: Connection references to non-existent devices
        self._check_invalid_connections(topology.connections, device_ids)

        # Check 8: Loop detection (basic)
        self._check_basic_loops(topology.connections)

        return len(self.errors) == 0, self.errors, self.warnings

    def _check_duplicate_device_ids(self, devices: List[Device]):
        """Check for duplicate device IDs."""
        ids = [device.id for device in devices]
        seen = set()
        duplicates = set()
        for device_id in ids:
            if device_id in seen:
                duplicates.add(device_id)
            else:
                seen.add(device_id)

        for device_id in duplicates:
            self.errors.append(f"Duplicate device ID: {device_id}")

    def _check_orphaned_devices(self, devices: List[Device], connections: List[Connection]):
        """Check for devices with no connections."""
        if not devices or not connections:
            return

        connected_devices = set()
        for conn in connections:
            connected_devices.add(conn.source)
            connected_devices.add(conn.target)

        for device in devices:
            if device.id not in connected_devices:
                self.warnings.append(f"Device '{device.id}' ({device.type}) has no connections")

    def _check_duplicate_ips(self, devices: List[Device]):
        """Check for duplicate IP addresses among devices."""
        ip_map = {}  # IP -> list of device IDs

        for device in devices:
            if device.properties and device.properties.ip:
                ip = device.properties.ip
                try:
                    # Validate IP format
                    ipaddress.ip_address(ip)
                    if ip not in ip_map:
                        ip_map[ip] = []
                    ip_map[ip].append(device.id)
                except ValueError:
                    # Invalid IP will be caught by _check_invalid_ips
                    pass

        for ip, device_ids in ip_map.items():
            if len(device_ids) > 1:
                self.errors.append(f"Duplicate IP address {ip} used by devices: {', '.join(device_ids)}")

    def _check_invalid_ips(self, devices: List[Device]):
        """Check for invalid IP address formats."""
        for device in devices:
            if device.properties and device.properties.ip:
                ip = device.properties.ip
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    self.errors.append(f"Invalid IP address '{ip}' for device '{device.id}'")

    def _check_self_connections(self, connections: List[Connection]):
        """Check for connections from a device to itself."""
        for conn in connections:
            if conn.source == conn.target:
                self.errors.append(f"Self-connection detected: {conn.source} -> {conn.target}")

    def _check_duplicate_connections(self, connections: List[Connection]):
        """Check for duplicate connections (same source-target pairs, treating as undirected)."""
        connection_map = {}  # (min(source,target), max(source,target)) -> count

        for conn in connections:
            # Normalize the connection so that (A,B) and (B,A) are the same key
            key = tuple(sorted([conn.source, conn.target]))
            connection_map[key] = connection_map.get(key, 0) + 1

        for (device1, device2), count in connection_map.items():
            if count > 1:
                self.errors.append(f"Duplicate connection between {device1} and {device2}")

    def _check_invalid_connections(self, connections: List[Connection], device_ids: set):
        """Check for connections referencing non-existent devices."""
        for conn in connections:
            if conn.source not in device_ids:
                self.errors.append(f"Connection source device '{conn.source}' not found")
            if conn.target not in device_ids:
                self.errors.append(f"Connection target device '{conn.target}' not found")

    def _check_basic_loops(self, connections: List[Connection]):
        """Basic loop detection - check for immediate loops like A->B, B->A."""
        # Build adjacency list
        adj = {}
        for conn in connections:
            if conn.source not in adj:
                adj[conn.source] = set()
            if conn.target not in adj:
                adj[conn.target] = set()
            adj[conn.source].add(conn.target)
            adj[conn.target].add(conn.source)  # Treat as undirected for loop detection

        # Check for triangles (A-B, B-C, C-A) - simple case
        visited = set()
        for device in adj:
            if device not in visited:
                # Simple DFS to detect cycles
                if self._has_cycle_dfs(adj, device, set(), None):
                    self.warnings.append(f"Potential network loop detected involving device {device}")
                    break  # Just report one warning for now

    def _has_cycle_dfs(self, adj: dict, node: str, visited: set, parent: Optional[str]) -> bool:
        """DFS helper to detect cycles in undirected graph."""
        visited.add(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                if self._has_cycle_dfs(adj, neighbor, visited, node):
                    return True
            elif parent is not None and neighbor != parent:
                return True
        return False

def validate_network_topology(topology_dict: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate network topology from dictionary.

    Args:
        topology_dict: Dictionary representation of network topology

    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    try:
        # Convert dictionary to NetworkTopology object
        topology = NetworkTopology(**topology_dict)
        validator = NetworkValidator()
        return validator.validate(topology)
    except Exception as e:
        logger.error(f"Error validating topology: {e}")
        return False, [f"Validation error: {str(e)}"], []

# For direct testing
if __name__ == "__main__":
    # Example usage
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
            }
        ],
        "connections": [
            {
                "source": "router1",
                "target": "switch1",
                "label": "Uplink",
                "type": "ethernet"
            }
        ]
    }

    is_valid, errors, warnings = validate_network_topology(sample_topology)
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")