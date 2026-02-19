"""
🔄 JARVIS OTA (Over-The-Air) Live Update Engine v1.0
═══════════════════════════════════════════════════════════════════
APK updates WITHOUT re-download or reinstall!

Features:
  - Hot code push via WebView bundle replacement
  - Version management with semantic versioning
  - Delta updates (only changed files sent)
  - Background silent updates
  - Rollback support if update fails
  - Update notification to users
  - Force update for critical patches
  - Admin control panel integration

Architecture:
  APK = Native Android Shell (Capacitor) + WebView (React bundle)
  OTA updates replace the WebView bundle ONLY — no APK reinstall needed!
  The native shell checks for updates on every app launch.

Author: JARVIS AI
"""

import os
import json
import hashlib
import logging
import time
import zipfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger("jarvis-ota")
IST = timezone(timedelta(hours=5, minutes=30))

# ═══════════════════════════════════════════════════════════
#  OTA CONFIG
# ═══════════════════════════════════════════════════════════

OTA_DIR = Path(os.environ.get("OTA_DIR", "/workspaces/codespaces-blank/ota_releases"))
OTA_DIR.mkdir(exist_ok=True)

BUNDLE_SOURCE = Path("/workspaces/codespaces-blank/telegram-mini-app/dist")
MANIFEST_FILE = OTA_DIR / "manifest.json"
HISTORY_FILE = OTA_DIR / "update_history.json"

# Version tracking
CURRENT_VERSION = "2.0.0"
MIN_NATIVE_VERSION = "1.0.0"  # Minimum APK shell version required

# ═══════════════════════════════════════════════════════════
#  MANIFEST MANAGEMENT
# ═══════════════════════════════════════════════════════════

def _load_manifest() -> Dict:
    """Load the OTA manifest."""
    if MANIFEST_FILE.exists():
        try:
            return json.loads(MANIFEST_FILE.read_text())
        except:
            pass
    return {
        "current_version": CURRENT_VERSION,
        "min_native_version": MIN_NATIVE_VERSION,
        "releases": [],
        "force_update": False,
        "update_message": "",
        "created_at": datetime.now(IST).isoformat(),
    }


def _save_manifest(manifest: Dict):
    """Save the OTA manifest."""
    manifest["updated_at"] = datetime.now(IST).isoformat()
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, default=str))


def _load_history() -> List[Dict]:
    """Load update history."""
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except:
            pass
    return []


def _save_history(history: List[Dict]):
    """Save update history."""
    HISTORY_FILE.write_text(json.dumps(history[-100:], indent=2, default=str))


# ═══════════════════════════════════════════════════════════
#  BUNDLE HASHING — For delta updates
# ═══════════════════════════════════════════════════════════

def _hash_file(filepath: Path) -> str:
    """SHA256 hash a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _hash_directory(dirpath: Path) -> Dict[str, str]:
    """Hash all files in a directory recursively."""
    hashes = {}
    if not dirpath.exists():
        return hashes
    for f in dirpath.rglob('*'):
        if f.is_file():
            rel = str(f.relative_to(dirpath))
            hashes[rel] = _hash_file(f)
    return hashes


# ═══════════════════════════════════════════════════════════
#  CREATE OTA BUNDLE
# ═══════════════════════════════════════════════════════════

def create_ota_bundle(
    version: str,
    release_notes: str = "",
    force_update: bool = False,
    is_critical: bool = False
) -> Dict[str, Any]:
    """
    Create a new OTA update bundle from the current build.
    
    1. Builds React app
    2. Creates ZIP bundle
    3. Generates file hashes for delta updates
    4. Updates manifest
    
    Returns: Release info dict
    """
    if not BUNDLE_SOURCE.exists():
        return {"error": "Build directory not found. Run 'npm run build' first."}

    # Create release directory
    release_dir = OTA_DIR / f"v{version}"
    release_dir.mkdir(exist_ok=True)

    # Hash all files for delta comparison
    file_hashes = _hash_directory(BUNDLE_SOURCE)
    if not file_hashes:
        return {"error": "No files found in build directory"}

    # Create full bundle ZIP
    bundle_path = release_dir / f"jarvis-v{version}.zip"
    with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in BUNDLE_SOURCE.rglob('*'):
            if f.is_file():
                zf.write(f, f.relative_to(BUNDLE_SOURCE))

    bundle_size = bundle_path.stat().st_size
    bundle_hash = _hash_file(bundle_path)

    # Create delta bundle (if previous release exists)
    manifest = _load_manifest()
    delta_info = None
    
    if manifest["releases"]:
        prev_release = manifest["releases"][-1]
        prev_hashes = prev_release.get("file_hashes", {})
        
        # Find changed files only
        changed_files = []
        new_files = []
        deleted_files = []
        
        for fp, fh in file_hashes.items():
            if fp not in prev_hashes:
                new_files.append(fp)
            elif prev_hashes[fp] != fh:
                changed_files.append(fp)
        
        for fp in prev_hashes:
            if fp not in file_hashes:
                deleted_files.append(fp)
        
        # Create delta ZIP with only changed/new files
        if changed_files or new_files:
            delta_path = release_dir / f"jarvis-v{version}-delta.zip"
            with zipfile.ZipFile(delta_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for fp in changed_files + new_files:
                    full_path = BUNDLE_SOURCE / fp
                    if full_path.exists():
                        zf.write(full_path, fp)
                # Include deletion manifest
                zf.writestr("__deleted__.json", json.dumps(deleted_files))
            
            delta_info = {
                "delta_bundle": str(delta_path),
                "delta_size": delta_path.stat().st_size,
                "delta_hash": _hash_file(delta_path),
                "changed_files": len(changed_files),
                "new_files": len(new_files),
                "deleted_files": len(deleted_files),
                "from_version": prev_release["version"],
            }

    # Build release record
    release = {
        "version": version,
        "bundle_path": str(bundle_path),
        "bundle_size": bundle_size,
        "bundle_hash": bundle_hash,
        "file_hashes": file_hashes,
        "total_files": len(file_hashes),
        "release_notes": release_notes,
        "force_update": force_update,
        "is_critical": is_critical,
        "delta": delta_info,
        "created_at": datetime.now(IST).isoformat(),
        "download_url": f"/api/ota/download/{version}",
        "delta_url": f"/api/ota/download/{version}/delta" if delta_info else None,
    }

    # Update manifest
    manifest["current_version"] = version
    manifest["releases"].append(release)
    manifest["force_update"] = force_update
    if release_notes:
        manifest["update_message"] = release_notes
    _save_manifest(manifest)

    # Log history
    history = _load_history()
    history.append({
        "action": "release",
        "version": version,
        "size": bundle_size,
        "files": len(file_hashes),
        "delta": bool(delta_info),
        "at": datetime.now(IST).isoformat(),
    })
    _save_history(history)

    logger.info(f"🔄 OTA Bundle v{version} created: {bundle_size} bytes, {len(file_hashes)} files")
    
    return {
        "success": True,
        "version": version,
        "bundle_size": bundle_size,
        "total_files": len(file_hashes),
        "delta": delta_info,
        "download_url": release["download_url"],
    }


# ═══════════════════════════════════════════════════════════
#  CHECK FOR UPDATES — Called by APK on launch
# ═══════════════════════════════════════════════════════════

def check_update(
    client_version: str,
    native_version: str = "1.0.0",
    client_file_hashes: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Check if an update is available.
    Called by the APK's native code on every app launch.
    
    Returns update info or "no update" response.
    """
    manifest = _load_manifest()
    
    if not manifest["releases"]:
        return {"update_available": False, "message": "No releases available"}

    latest = manifest["releases"][-1]
    latest_version = latest["version"]

    # Compare versions
    def _ver_tuple(v):
        try:
            return tuple(int(x) for x in v.split('.'))
        except:
            return (0, 0, 0)

    client_ver = _ver_tuple(client_version)
    latest_ver = _ver_tuple(latest_version)

    if client_ver >= latest_ver:
        return {"update_available": False, "current_version": client_version}

    # Check if native shell is compatible
    min_native = _ver_tuple(manifest.get("min_native_version", "1.0.0"))
    native_ver = _ver_tuple(native_version)

    if native_ver < min_native:
        return {
            "update_available": True,
            "requires_apk_update": True,
            "message": "Naya APK download karein — native shell update zaroori hai",
            "apk_download_url": "/download/apk",
        }

    # Determine if delta update is possible
    use_delta = False
    delta_info = latest.get("delta")
    
    if delta_info and delta_info.get("from_version") == client_version:
        use_delta = True

    response = {
        "update_available": True,
        "current_version": client_version,
        "latest_version": latest_version,
        "force_update": latest.get("force_update", False) or manifest.get("force_update", False),
        "release_notes": latest.get("release_notes", ""),
        "is_critical": latest.get("is_critical", False),
    }

    if use_delta:
        response["update_type"] = "delta"
        response["download_url"] = latest["delta_url"]
        response["bundle_size"] = delta_info["delta_size"]
        response["bundle_hash"] = delta_info["delta_hash"]
        response["changed_files"] = delta_info["changed_files"]
    else:
        response["update_type"] = "full"
        response["download_url"] = latest["download_url"]
        response["bundle_size"] = latest["bundle_size"]
        response["bundle_hash"] = latest["bundle_hash"]

    return response


# ═══════════════════════════════════════════════════════════
#  ROLLBACK — If update fails
# ═══════════════════════════════════════════════════════════

def rollback_to_version(target_version: str) -> Dict[str, Any]:
    """Rollback to a previous version."""
    manifest = _load_manifest()

    for release in manifest["releases"]:
        if release["version"] == target_version:
            manifest["current_version"] = target_version
            _save_manifest(manifest)
            
            history = _load_history()
            history.append({
                "action": "rollback",
                "to_version": target_version,
                "at": datetime.now(IST).isoformat(),
            })
            _save_history(history)

            logger.warning(f"⚠️ Rolled back to v{target_version}")
            return {"success": True, "version": target_version}

    return {"error": f"Version {target_version} not found"}


# ═══════════════════════════════════════════════════════════
#  GET RELEASE INFO
# ═══════════════════════════════════════════════════════════

def get_release_info() -> Dict[str, Any]:
    """Get current release information."""
    manifest = _load_manifest()
    history = _load_history()
    
    return {
        "current_version": manifest.get("current_version", CURRENT_VERSION),
        "min_native_version": manifest.get("min_native_version", MIN_NATIVE_VERSION),
        "total_releases": len(manifest.get("releases", [])),
        "force_update": manifest.get("force_update", False),
        "latest_release": manifest["releases"][-1] if manifest.get("releases") else None,
        "recent_history": history[-10:] if history else [],
    }


def get_all_versions() -> List[str]:
    """Get list of all release versions."""
    manifest = _load_manifest()
    return [r["version"] for r in manifest.get("releases", [])]


# ═══════════════════════════════════════════════════════════
#  FASTAPI ROUTES — Mount these on your server
# ═══════════════════════════════════════════════════════════

def register_ota_routes(app_or_router):
    """
    Register OTA API routes on a FastAPI app or router.
    
    Usage in server.py:
        from jarvis_ota_update import register_ota_routes
        register_ota_routes(app)
    """
    from fastapi import APIRouter, Query
    from fastapi.responses import FileResponse, JSONResponse

    ota_router = APIRouter(prefix="/api/ota", tags=["OTA Updates"])

    @ota_router.get("/check")
    async def api_check_update(
        version: str = Query("1.0.0"),
        native_version: str = Query("1.0.0")
    ):
        """APK calls this on launch to check for updates."""
        result = check_update(version, native_version)
        return JSONResponse(result)

    @ota_router.get("/download/{version}")
    async def api_download_bundle(version: str):
        """Download full OTA bundle."""
        bundle_path = OTA_DIR / f"v{version}" / f"jarvis-v{version}.zip"
        if bundle_path.exists():
            return FileResponse(
                bundle_path,
                media_type="application/zip",
                filename=f"jarvis-v{version}.zip"
            )
        return JSONResponse({"error": "Bundle not found"}, status_code=404)

    @ota_router.get("/download/{version}/delta")
    async def api_download_delta(version: str):
        """Download delta OTA bundle."""
        delta_path = OTA_DIR / f"v{version}" / f"jarvis-v{version}-delta.zip"
        if delta_path.exists():
            return FileResponse(
                delta_path,
                media_type="application/zip",
                filename=f"jarvis-v{version}-delta.zip"
            )
        return JSONResponse({"error": "Delta bundle not found"}, status_code=404)

    @ota_router.get("/manifest")
    async def api_manifest():
        """Get full OTA manifest."""
        return JSONResponse(_load_manifest())

    @ota_router.get("/info")
    async def api_release_info():
        """Get current release info."""
        return JSONResponse(get_release_info())

    @ota_router.post("/create")
    async def api_create_release(
        version: str = Query(...),
        notes: str = Query(""),
        force: bool = Query(False),
        critical: bool = Query(False)
    ):
        """Admin: Create new OTA release."""
        result = create_ota_bundle(version, notes, force, critical)
        return JSONResponse(result)

    @ota_router.post("/rollback")
    async def api_rollback(version: str = Query(...)):
        """Admin: Rollback to a previous version."""
        result = rollback_to_version(version)
        return JSONResponse(result)

    # Mount on the app/router
    if hasattr(app_or_router, 'include_router'):
        app_or_router.include_router(ota_router)
    else:
        # It's a regular FastAPI app
        app_or_router.include_router(ota_router)

    logger.info("🔄 OTA Update routes registered")


# ═══════════════════════════════════════════════════════════
#  EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'create_ota_bundle',
    'check_update',
    'rollback_to_version',
    'get_release_info',
    'get_all_versions',
    'register_ota_routes',
    'CURRENT_VERSION',
]
