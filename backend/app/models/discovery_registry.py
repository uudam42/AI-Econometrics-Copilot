"""Backward-compatible re-exports from the persistent storage layer."""
from app.storage.repositories import DiscoveryRecord, discovery_repository as discovery_registry

__all__ = ["DiscoveryRecord", "discovery_registry"]
