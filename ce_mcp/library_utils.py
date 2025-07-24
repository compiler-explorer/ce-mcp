"""Utility functions for library management and resolution."""

from typing import Dict, List, Any
from packaging import version


class LibraryError(Exception):
    """Base class for library-related errors."""

    pass


class LibraryNotFoundError(LibraryError):
    """Library not found."""

    pass


class LibraryVersionError(LibraryError):
    """Library version not found."""

    pass


class CompilerLibraryError(LibraryError):
    """Compiler doesn't support library."""

    pass


def resolve_library_version(
    library_versions: List[Dict[str, Any]], requested_version: str
) -> str | None:
    """
    Resolve version request to specific version ID.

    Args:
        library_versions: List of version objects from CE API
        requested_version: Version string, version ID, alias, or "latest"

    Returns:
        Version ID if found, None if not found
    """
    if not library_versions:
        return None

    # Handle "latest" - find the most recent version
    if requested_version == "latest":
        return get_latest_version_id(library_versions)

    # Check if it's a direct version ID match
    for ver in library_versions:
        if ver["id"] == requested_version:
            return requested_version

    # Check if it's a version string match
    for ver in library_versions:
        if ver["version"] == requested_version:
            return str(ver["id"])

    # Check if it's an alias match
    for ver in library_versions:
        if requested_version in ver.get("alias", []):
            return str(ver["id"])

    return None


def get_latest_version_id(library_versions: List[Dict[str, Any]]) -> str:
    """
    Get the latest stable version ID from a list of library versions.
    Excludes development versions like 'trunk', 'master', 'main', 'dev', etc.

    Args:
        library_versions: List of version objects from CE API

    Returns:
        Version ID of the latest stable version
    """
    if not library_versions:
        raise ValueError("No library versions available")

    # Filter out development/unstable versions
    stable_versions = []
    dev_keywords = {"trunk", "master", "main", "dev", "nightly", "snapshot", "head"}

    for ver in library_versions:
        version_str = ver.get("version", "").lower()
        version_id = ver.get("id", "").lower()

        # Skip if version contains development keywords
        is_dev_version = any(
            keyword in version_str or keyword in version_id for keyword in dev_keywords
        )

        if not is_dev_version:
            stable_versions.append(ver)

    # If no stable versions found, fall back to all versions
    # (better to return something than nothing)
    versions_to_use = stable_versions if stable_versions else library_versions

    # Sort by $order field if available (CE uses this for ordering)
    if all("$order" in ver for ver in versions_to_use):
        sorted_versions = sorted(
            versions_to_use, key=lambda x: x["$order"], reverse=True
        )
        return str(sorted_versions[0]["id"])  # Higher $order = newer

    # Fallback: try to parse semantic versions
    try:

        def version_key(ver_obj: Dict[str, Any]) -> Any:
            ver_str = ver_obj["version"]
            # Extract semantic version from strings like "20250127.0"
            # Try to parse as semantic version
            try:
                return version.parse(ver_str)
            except Exception:
                # If parsing fails, use string comparison
                return ver_str

        sorted_versions = sorted(versions_to_use, key=version_key, reverse=True)
        return str(sorted_versions[0]["id"])
    except Exception:
        # Final fallback: return first version from filtered list
        return str(versions_to_use[0]["id"])


def validate_library_requests(
    library_requests: List[Dict[str, Any]], available_libraries: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Validate and resolve library requests against available libraries.

    Args:
        library_requests: List of {"id": lib_id, "version": version_spec}
        available_libraries: List of library objects from CE API

    Returns:
        List of resolved library specs with actual version IDs

    Raises:
        ValueError: If library not found or version not available
    """
    # Create lookup dict for libraries
    lib_lookup = {lib["id"]: lib for lib in available_libraries}

    resolved = []
    for req in library_requests:
        lib_id = req["id"]
        requested_version = req.get("version", "latest")

        # Check if library exists
        if lib_id not in lib_lookup:
            available_ids = list(lib_lookup.keys())
            raise ValueError(
                f"Library '{lib_id}' not found. Available libraries: {available_ids[:10]}..."
            )

        library = lib_lookup[lib_id]

        # Resolve version
        version_id = resolve_library_version(library["versions"], requested_version)
        if version_id is None:
            available_versions = [v["version"] for v in library["versions"]]
            raise ValueError(
                f"Version '{requested_version}' not found for library '{lib_id}'. "
                f"Available versions: {available_versions[:5]}..."
            )

        resolved.append({"id": lib_id, "version": version_id, "name": library["name"]})

    return resolved


def extract_library_info(library_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant information from a CE library object.

    Args:
        library_obj: Library object from CE API

    Returns:
        Simplified library info dict
    """
    versions = []
    for ver in library_obj.get("versions", []):
        versions.append(
            {
                "id": ver["id"],
                "version": ver["version"],
                "aliases": ver.get("alias", []),
            }
        )

    # Determine latest version
    latest_version_id = get_latest_version_id(library_obj.get("versions", []))

    return {
        "id": library_obj["id"],
        "name": library_obj["name"],
        "url": library_obj.get("url", ""),
        "versions": versions,
        "latest_version": latest_version_id,
        "version_count": len(versions),
    }


def group_compilers_by_buildenv(
    compilers: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """
    Group compilers by their build environment setup.

    Args:
        compilers: List of compiler objects from CE API

    Returns:
        Dict mapping build env ID to list of compiler IDs
    """
    groups: Dict[str, List[str]] = {}

    for compiler in compilers:
        buildenv_id = compiler.get("buildenvsetup", {}).get("id", "default")
        if buildenv_id not in groups:
            groups[buildenv_id] = []
        groups[buildenv_id].append(compiler["id"])

    return groups


def get_compiler_library_support(
    compiler: Dict[str, Any], all_libraries: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Determine library support for a compiler based on libsArr field.

    Key insight: If libsArr is empty, compiler supports ALL libraries for the language.
    If libsArr has entries, only those libraries are supported.

    Args:
        compiler: Compiler object from CE API with libsArr field
        all_libraries: All available libraries for the language

    Returns:
        Dict with library support information
    """
    libs_arr = compiler.get("libsArr", [])
    supports_library_filter = compiler.get("supportsLibraryCodeFilter", True)

    if not libs_arr:
        # Empty libsArr means ALL libraries are supported
        return {
            "supports_all_libraries": True,
            "supported_libraries": [lib["id"] for lib in all_libraries],
            "library_count": len(all_libraries),
            "supports_library_filtering": supports_library_filter,
            "restriction_type": "none",
        }
    else:
        # Non-empty libsArr means only specific libraries are supported
        return {
            "supports_all_libraries": False,
            "supported_libraries": libs_arr,
            "library_count": len(libs_arr),
            "supports_library_filtering": supports_library_filter,
            "restriction_type": "limited",
        }


def filter_compilers_by_library_support(
    compilers: List[Dict[str, Any]], required_library: str
) -> List[Dict[str, Any]]:
    """
    Filter compilers that support a specific library.

    Args:
        compilers: List of compiler objects with libsArr field
        required_library: Library ID that must be supported

    Returns:
        List of compilers that support the library
    """
    supporting_compilers = []

    for compiler in compilers:
        libs_arr = compiler.get("libsArr", [])

        # Empty libsArr means all libraries supported
        if not libs_arr or required_library in libs_arr:
            supporting_compilers.append(compiler)

    return supporting_compilers


def filter_libraries_by_search(
    libraries: List[Dict[str, Any]], search_term: str
) -> List[Dict[str, Any]]:
    """
    Filter libraries by search term in name or ID with fuzzy matching.

    Args:
        libraries: List of library info objects
        search_term: Search term to match against

    Returns:
        Filtered list of libraries sorted by relevance
    """
    if not search_term:
        return libraries

    search_lower = search_term.lower()
    scored_results = []

    for lib in libraries:
        lib_id = lib["id"].lower()
        lib_name = lib["name"].lower()

        # Exact matches get highest score
        if search_lower == lib_id or search_lower == lib_name:
            scored_results.append((lib, 100))
        # Exact substring matches
        elif search_lower in lib_id or search_lower in lib_name:
            scored_results.append((lib, 80))
        # Starts with search term
        elif lib_id.startswith(search_lower) or lib_name.startswith(search_lower):
            scored_results.append((lib, 70))
        # Simple fuzzy matching - count common characters
        else:
            # Check for fuzzy matches (useful for typos)
            id_score = _fuzzy_match_score(search_lower, lib_id)
            name_score = _fuzzy_match_score(search_lower, lib_name)
            max_score = max(id_score, name_score)

            # Only include if we have decent similarity
            if max_score > 0.6:
                scored_results.append((lib, int(max_score * 60)))

    # Sort by score descending
    scored_results.sort(key=lambda x: x[1], reverse=True)

    return [lib for lib, score in scored_results]


def _fuzzy_match_score(search_term: str, target: str) -> float:
    """
    Calculate fuzzy match score between two strings.

    Simple algorithm based on:
    - Common character ratio
    - Character order preservation
    - Length similarity
    """
    if not search_term or not target:
        return 0.0

    # Count common characters
    search_chars = set(search_term)
    target_chars = set(target)
    common_chars = len(search_chars & target_chars)

    # Character ratio score
    char_ratio = common_chars / max(len(search_chars), len(target_chars))

    # Length similarity score
    len_diff = abs(len(search_term) - len(target))
    max_len = max(len(search_term), len(target))
    len_score = 1.0 - (len_diff / max_len) if max_len > 0 else 0.0

    # Check for character order preservation (basic)
    order_score = 0.0
    if len(search_term) <= len(target):
        # See how many characters appear in order
        search_idx = 0
        for char in target:
            if search_idx < len(search_term) and char == search_term[search_idx]:
                search_idx += 1
        order_score = search_idx / len(search_term)

    # Combine scores with weights
    final_score = char_ratio * 0.4 + len_score * 0.3 + order_score * 0.3
    return final_score


async def resolve_libraries_for_compilation(
    libraries: List[Dict[str, str]], language: str, compiler_id: str, client: Any
) -> List[Dict[str, str]]:
    """
    Resolve library specifications to concrete library configs for compilation.

    Args:
        libraries: List of {"id": lib_id, "version": version_spec}
        language: Programming language (e.g., "c++")
        compiler_id: Compiler identifier (e.g., "g132")
        client: CompilerExplorerClient instance

    Returns:
        List of resolved library specs ready for CE API

    Raises:
        LibraryNotFoundError: If library doesn't exist
        LibraryVersionError: If version doesn't exist
        CompilerLibraryError: If compiler doesn't support library
    """
    if not libraries:
        return []

    # Fetch available libraries for the language
    try:
        all_libraries = await client.get_libraries(language)
    except Exception as e:
        raise LibraryError(f"Failed to fetch libraries for {language}: {e}")

    # Fetch compiler info to check library support
    try:
        compilers = await client.get_compilers(language, include_extended_info=False)
        compiler_info = next((c for c in compilers if c["id"] == compiler_id), None)
        if not compiler_info:
            raise CompilerLibraryError(
                f"Compiler '{compiler_id}' not found for {language}"
            )
    except Exception as e:
        raise LibraryError(f"Failed to fetch compiler info: {e}")

    # Check compiler library support
    unsupported = check_compiler_library_compatibility(
        compiler_info, [lib["id"] for lib in libraries], all_libraries
    )
    if unsupported:
        raise CompilerLibraryError(
            f"Compiler '{compiler_id}' does not support libraries: {', '.join(unsupported)}"
        )

    # Validate and resolve each library
    resolved_libraries = []
    lib_lookup = {lib["id"]: lib for lib in all_libraries}

    for lib_request in libraries:
        lib_id = lib_request["id"]
        requested_version = lib_request.get("version", "latest")

        # Check if library exists
        if lib_id not in lib_lookup:
            raise LibraryNotFoundError(f"Library '{lib_id}' not found for {language}")

        library = lib_lookup[lib_id]

        # Resolve version (including "latest")
        version_id: str
        if requested_version == "latest":
            version_id = get_latest_version_id(library["versions"])
        else:
            resolved_version = resolve_library_version(library["versions"], requested_version)
            if resolved_version is None:
                available_versions = [v["version"] for v in library["versions"]]
                raise LibraryVersionError(
                    f"Version '{requested_version}' not found for library '{lib_id}'. "
                    f"Available versions: {available_versions[:5]}..."
                )
            version_id = resolved_version

        # At this point version_id should never be None
        assert version_id is not None
        if False:  # This check is now redundant but kept for structure
            available_versions = [v["version"] for v in library["versions"]]
            raise LibraryVersionError(
                f"Version '{requested_version}' not found for library '{lib_id}'. "
                f"Available versions: {available_versions[:5]}..."
            )

        resolved_libraries.append({"id": lib_id, "version": version_id})

    return resolved_libraries


async def search_libraries(
    search_term: str, language: str, client: Any, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search libraries by name/ID and return suggestions.

    Args:
        search_term: Term to search for
        language: Programming language
        client: CompilerExplorerClient instance
        limit: Maximum number of results

    Returns:
        List of matching library info dicts
    """
    try:
        all_libraries = await client.get_libraries(language)
    except Exception:
        return []

    # Extract simplified library info
    library_info = [extract_library_info(lib) for lib in all_libraries]

    # Filter by search term
    filtered = filter_libraries_by_search(library_info, search_term)

    # Return limited results
    return filtered[:limit]


def check_compiler_library_compatibility(
    compiler_info: Dict[str, Any],
    requested_libraries: List[str],
    all_libraries: List[Dict[str, Any]],
) -> List[str]:
    """
    Check if compiler supports all requested libraries.

    Args:
        compiler_info: Compiler object with libsArr field
        requested_libraries: List of library IDs to check
        all_libraries: All available libraries for the language

    Returns:
        List of unsupported library IDs (empty if all supported)
    """
    if not requested_libraries:
        return []

    libs_arr = compiler_info.get("libsArr", [])

    # If libsArr is empty, all libraries are supported
    if not libs_arr:
        return []

    # If libsArr has entries, only those libraries are supported
    unsupported = []
    for lib_id in requested_libraries:
        if lib_id not in libs_arr:
            unsupported.append(lib_id)

    return unsupported


async def validate_and_resolve_libraries(
    libraries: List[Dict[str, str]] | None, language: str, compiler_id: str, client: Any
) -> List[Dict[str, str]]:
    """
    Complete validation and resolution pipeline.

    Args:
        libraries: Optional list of library specs
        language: Programming language
        compiler_id: Compiler identifier
        client: CompilerExplorerClient instance

    Returns:
        List of resolved library specs for CE API

    Raises:
        LibraryError subclasses for various error conditions
    """
    if not libraries:
        return []

    return await resolve_libraries_for_compilation(
        libraries, language, compiler_id, client
    )


def format_library_error_with_suggestions(
    error: LibraryError,
    search_term: str,
    language: str,
    suggestions: List[Dict[str, Any]],
) -> str:
    """
    Format library errors with helpful suggestions.

    Args:
        error: The library error that occurred
        search_term: The original search term
        language: Programming language
        suggestions: List of suggested libraries

    Returns:
        Formatted error message with suggestions
    """
    base_msg = str(error)

    if not suggestions:
        return f"{base_msg}\n\nNo similar libraries found for {language}."

    suggestion_lines = []
    for lib in suggestions[:5]:  # Limit to top 5 suggestions
        versions = lib.get("versions", [])
        version_info = f"versions: {', '.join([v.get('version', 'unknown') for v in versions[:3]])}"
        if len(versions) > 3:
            version_info += f", +{len(versions) - 3} more"

        suggestion_lines.append(f"  - {lib['id']} ({lib['name']}) - {version_info}")

    suggestions_text = "\n".join(suggestion_lines)

    return f"""{base_msg}

Did you mean:
{suggestions_text}

Example usage: [{{"id": "{suggestions[0]['id']}", "version": "latest"}}]"""
