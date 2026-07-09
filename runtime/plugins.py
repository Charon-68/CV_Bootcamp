import os
import sys
import importlib.util
from dataclasses import dataclass
from typing import Dict, Any, List, Type, Optional
from runtime.logger import get_logger
from runtime.graph.context import PluginLoaded, PluginUnloaded

logger = get_logger("nexusguard.runtime.plugins")
@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    supported_inputs: List[str]
    supported_outputs: List[str]

class PluginRegistry:
    """Discovers, validates, registers, and hot-reloads plugins dynamically from directory paths."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.loaded_plugins: Dict[str, Dict[str, Any]] = {}
        # Callbacks for load/unload events
        self.event_handler: Optional[Any] = None

    def discover_and_load(self) -> None:
        """Scan plugins directory recursively and load python plugin files."""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            return

        # Scan for .py files
        for root, _, files in os.walk(self.plugins_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    filepath = os.path.join(root, file)
                    self.load_plugin(filepath)

    def load_plugin(self, filepath: str) -> bool:
        """Load a plugin from a file path dynamically."""
        plugin_name = os.path.splitext(os.path.basename(filepath))[0]
        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(plugin_name, filepath)
            if not spec or not spec.loader:
                return False
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)

            # Retrieve register hook or metadata if present
            metadata = getattr(module, "PLUGIN_METADATA", None)
            if metadata:
                self.loaded_plugins[plugin_name] = {
                    "module": module,
                    "metadata": metadata,
                    "filepath": filepath,
                }
                logger.info(f"Loaded plugin '{plugin_name}' version {metadata.get('version', '1.0.0')}")
                if self.event_handler:
                    self.event_handler(PluginLoaded(plugin_name=plugin_name, version=metadata.get("version", "1.0.0")))
                return True
        except Exception as e:
            logger.error(f"Failed to load plugin from '{filepath}': {e}", exc_info=True)
        return False

    def unload_plugin(self, plugin_name: str) -> None:
        """Unload a loaded plugin module."""
        if plugin_name in self.loaded_plugins:
            del self.loaded_plugins[plugin_name]
            if plugin_name in sys.modules:
                del sys.modules[plugin_name]
            logger.info(f"Unloaded plugin '{plugin_name}'")
            if self.event_handler:
                self.event_handler(PluginUnloaded(plugin_name=plugin_name))

    def reload_plugins(self) -> None:
        """Reload all discovered plugins from disk."""
        logger.info("Reloading all plugins...")
        for name in list(self.loaded_plugins.keys()):
            self.unload_plugin(name)
        self.discover_and_load()

    def query_plugins(self) -> List[Dict[str, Any]]:
        """Return metadata details for all loaded plugins."""
        return [
            {
                "name": name,
                "version": info["metadata"].get("version", "1.0.0"),
                "author": info["metadata"].get("author", "unknown"),
                "description": info["metadata"].get("description", ""),
                "supported_inputs": info["metadata"].get("supported_inputs", []),
                "supported_outputs": info["metadata"].get("supported_outputs", []),
            }
            for name, info in self.loaded_plugins.items()
        ]

# Global/Singleton plugin registry instance
plugin_registry = PluginRegistry()
