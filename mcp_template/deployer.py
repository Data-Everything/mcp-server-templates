"""
Deployer
"""

import logging
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)


def list_missing_properties(
    template: Dict[str, Any], config: Dict[str, Any]
) -> List[str]:
    """Check for missing required properties in the configuration."""

    missing_properties = []
    required_properties = template.get("config_schema", {}).get("required", [])
    required_properties_env_vars = {
        prop: template["config_schema"]["properties"][prop].get("env_mapping")
        for prop in required_properties
        if prop in template.get("config_schema", {}).get("properties", {})
        and template["config_schema"]["properties"][prop].get("env_mapping")
    }
    for prop in required_properties:
        if prop not in config and required_properties_env_vars.get(prop) not in config:
            missing_properties.append(prop)
    return missing_properties


def append_volume_mounts_to_template(
    template: Dict[str, Any],
    data_dir: Optional[str] = None,
    config_dir: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Get volume mounts from the template and configuration."""

    template_copy = template.copy()
    if data_dir or config_dir:
        template_copy["volumes"] = template["volumes"].copy()

        if data_dir:
            for key in template_copy["volumes"]:
                if "/data" in template_copy["volumes"][key]:
                    template_copy["volumes"][key] = template_copy["volumes"][
                        key
                    ].replace("/data", data_dir)

        if config_dir:
            for key in template_copy["volumes"]:
                if "/config" in template_copy["volumes"][key]:
                    template_copy["volumes"][key] = template_copy["volumes"][
                        key
                    ].replace("/config", config_dir)

    return template_copy
