"""
Pydantic schemas for network topology validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import re

class DeviceProperties(BaseModel):
    ip: Optional[str] = Field(None, description="IP address of the device")
    hostname: Optional[str] = Field(None, description="Hostname of the device")
    model: Optional[str] = Field(None, description="Device model")
    os: Optional[str] = Field(None, description="Operating system")
    # Allow additional properties
    class Config:
        extra = "allow"

class Device(BaseModel):
    id: str = Field(..., description="Unique device identifier")
    type: str = Field(..., description="Device type")
    label: Optional[str] = Field(None, description="Human readable label")
    position: Optional[Dict[str, int]] = Field(None, description="Position for layout")
    properties: Optional[DeviceProperties] = Field(None, description="Device properties")

    @validator('type')
    def validate_device_type(cls, v):
        allowed_types = ['router', 'switch', 'pc', 'server', 'cloud', 'firewall', 'loadbalancer']
        if v not in allowed_types:
            raise ValueError(f'Device type must be one of {allowed_types}')
        return v

class ConnectionProperties(BaseModel):
    bandwidth: Optional[str] = Field(None, description="Link bandwidth")
    latency: Optional[str] = Field(None, description="Link latency")
    # Allow additional properties
    class Config:
        extra = "allow"

class Connection(BaseModel):
    source: str = Field(..., description="Source device ID")
    target: str = Field(..., description="Target device ID")
    label: Optional[str] = Field(None, description="Connection label")
    type: Optional[str] = Field(None, description="Connection type")
    properties: Optional[ConnectionProperties] = Field(None, description="Connection properties")

    @validator('type')
    def validate_connection_type(cls, v):
        if v is None:
            return v
        allowed_types = ['ethernet', 'serial', 'wireless', 'vpn']
        if v not in allowed_types:
            raise ValueError(f'Connection type must be one of {allowed_types}')
        return v

class NetworkTopology(BaseModel):
    devices: List[Device] = Field(default_factory=list, description="List of network devices")
    connections: List[Connection] = Field(default_factory=list, description="List of network connections")

    @validator('devices')
    def validate_unique_device_ids(cls, v):
        ids = [device.id for device in v]
        if len(ids) != len(set(ids)):
            raise ValueError('Device IDs must be unique')
        return v

    @validator('connections')
    def validate_connection_references(cls, v, values):
        if 'devices' in values:
            device_ids = {device.id for device in values['devices']}
            for conn in v:
                if conn.source not in device_ids:
                    raise ValueError(f'Source device {conn.source} not found in devices')
                if conn.target not in device_ids:
                    raise ValueError(f'Target device {conn.target} not found in devices')
        return v

# Schema for LLM output (less strict)
class LLMSchema(BaseModel):
    devices: List[Dict[str, Any]] = Field(default_factory=list)
    connections: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None

    class Config:
        extra = "allow"