"""API client for Compiler Explorer."""

import asyncio
import logging
import warnings
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientError, ClientTimeout

from .config import Config

logger = logging.getLogger(__name__)


class CompilerExplorerClient:
    """Client for interacting with Compiler Explorer API."""

    def __init__(self, config: Config):
        """Initialize the API client."""
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None
        self._closed = False

    async def __aenter__(self) -> "CompilerExplorerClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None:
            timeout = ClientTimeout(total=self.config.api.timeout)
            self.connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": self.config.api.user_agent,
                    "Accept": "application/json",
                },
                timeout=timeout,
                connector=self.connector,
            )
        return self.session

    async def close(self) -> None:
        """Close the session."""
        if self.session and not self._closed:
            await self.session.close()
            self.session = None

            # Close connector if it exists
            if self.connector:
                await self.connector.close()
                self.connector = None

            # Cancel any pending tasks and wait for cleanup
            pending_tasks = [task for task in asyncio.all_tasks() if not task.done()]
            if pending_tasks:
                await asyncio.sleep(0.2)  # Give more time for cleanup

            self._closed = True

    def __del__(self) -> None:
        """Cleanup on garbage collection."""
        if self.session and not self._closed:
            # Issue a warning instead of trying to close in __del__

            warnings.warn(
                "CompilerExplorerClient was not properly closed. " "Please call await client.close() in your code.",
                ResourceWarning,
                stacklevel=2,
            )

    async def compile(
        self,
        source: str,
        language: str,
        compiler: str,
        options: str = "",
        get_assembly: bool = False,
        filter_overrides: Optional[Dict[str, bool]] = None,
        libraries: List[Dict[str, str]] | None = None,
        tools: List[Dict[str, Any]] | None = None,
        produce_opt_info: bool = False,
    ) -> Dict[str, Any]:
        """Compile source code."""
        session = await self._get_session()

        payload = {
            "source": source,
            "compiler": compiler,
            "lang": language,
            "options": {
                "userArguments": options,
                "compilerOptions": {
                    "producePp": None,
                    "produceAst": None,
                    "produceGccDump": {},
                    "produceCfg": False,
                    "produceGnatDebugTree": None,
                    "produceGnatDebug": None,
                    "produceIr": None,
                    "produceOptInfo": produce_opt_info,
                    "produceStackUsageInfo": None,
                    "produceCppCheck": None,
                    "produceDevice": None,
                    "overrides": None,
                },
                "filters": {
                    "binary": (
                        filter_overrides.get("binary", self.config.filters.binary)
                        if filter_overrides
                        else self.config.filters.binary
                    ),
                    "binaryObject": (
                        filter_overrides.get("binaryObject", self.config.filters.binaryObject)
                        if filter_overrides
                        else self.config.filters.binaryObject
                    ),
                    "commentOnly": (
                        filter_overrides.get("commentOnly", self.config.filters.commentOnly)
                        if filter_overrides
                        else self.config.filters.commentOnly
                    ),
                    "demangle": (
                        filter_overrides.get("demangle", self.config.filters.demangle)
                        if filter_overrides
                        else self.config.filters.demangle
                    ),
                    "directives": (
                        filter_overrides.get("directives", self.config.filters.directives)
                        if filter_overrides
                        else self.config.filters.directives
                    ),
                    "execute": False,
                    "intel": (
                        filter_overrides.get("intel", self.config.filters.intel)
                        if filter_overrides
                        else self.config.filters.intel
                    ),
                    "labels": (
                        filter_overrides.get("labels", self.config.filters.labels)
                        if filter_overrides
                        else self.config.filters.labels
                    ),
                    "libraryCode": (
                        filter_overrides.get("libraryCode", self.config.filters.libraryCode)
                        if filter_overrides
                        else self.config.filters.libraryCode
                    ),
                    "trim": (
                        filter_overrides.get("trim", self.config.filters.trim)
                        if filter_overrides
                        else self.config.filters.trim
                    ),
                    "debugCalls": (
                        filter_overrides.get("debugCalls", self.config.filters.debugCalls)
                        if filter_overrides
                        else self.config.filters.debugCalls
                    ),
                },
                "tools": tools or [],
                "libraries": libraries or [],
            },
        }

        url = f"{self.config.api.endpoint}/compiler/{compiler}/compile"

        try:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                return await response.json()  # type: ignore[no-any-return]
        except ClientError as e:
            logger.error(f"API request failed: {e}")
            raise

    async def compile_and_execute(
        self,
        source: str,
        language: str,
        compiler: str,
        options: str = "",
        stdin: str = "",
        args: List[str] | None = None,
        timeout: int = 5000,
        libraries: List[Dict[str, str]] | None = None,
        tools: List[Dict[str, Any]] | None = None,
        filter_overrides: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Compile and execute source code."""
        session = await self._get_session()

        payload = {
            "source": source,
            "options": {
                "userArguments": options,
                "executeParameters": {
                    "args": args or [],
                    "stdin": stdin,
                },
                "compilerOptions": {
                    "executorRequest": True,
                    "skipAsm": True,
                },
                "filters": {
                    "execute": True,
                    "binary": (
                        filter_overrides.get("binary", self.config.filters.binary)
                        if filter_overrides
                        else self.config.filters.binary
                    ),
                    "binaryObject": (
                        filter_overrides.get("binaryObject", self.config.filters.binaryObject)
                        if filter_overrides
                        else self.config.filters.binaryObject
                    ),
                    "commentOnly": (
                        filter_overrides.get("commentOnly", self.config.filters.commentOnly)
                        if filter_overrides
                        else self.config.filters.commentOnly
                    ),
                    "demangle": (
                        filter_overrides.get("demangle", self.config.filters.demangle)
                        if filter_overrides
                        else self.config.filters.demangle
                    ),
                    "directives": (
                        filter_overrides.get("directives", self.config.filters.directives)
                        if filter_overrides
                        else self.config.filters.directives
                    ),
                    "intel": (
                        filter_overrides.get("intel", self.config.filters.intel)
                        if filter_overrides
                        else self.config.filters.intel
                    ),
                    "labels": (
                        filter_overrides.get("labels", self.config.filters.labels)
                        if filter_overrides
                        else self.config.filters.labels
                    ),
                    "libraryCode": (
                        filter_overrides.get("libraryCode", self.config.filters.libraryCode)
                        if filter_overrides
                        else self.config.filters.libraryCode
                    ),
                    "trim": (
                        filter_overrides.get("trim", self.config.filters.trim)
                        if filter_overrides
                        else self.config.filters.trim
                    ),
                    "debugCalls": (
                        filter_overrides.get("debugCalls", self.config.filters.debugCalls)
                        if filter_overrides
                        else self.config.filters.debugCalls
                    ),
                },
                "tools": tools or [],
                "libraries": libraries or [],
            },
        }

        url = f"{self.config.api.endpoint}/compiler/{compiler}/compile"

        try:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                return await response.json()  # type: ignore[no-any-return]
        except ClientError as e:
            logger.error(f"API request failed: {e}")
            raise

    async def create_short_link(
        self,
        source: str,
        language: str,
        compiler: str,
        options: str = "",
        layout: str = "simple",
        libraries: List[Dict[str, str]] | None = None,
        tools: List[Dict[str, Any]] | None = None,
        create_binary: bool = False,
        create_object_only: bool = False,
    ) -> str:
        """Create a short link for sharing."""
        session = await self._get_session()

        # Build the session configuration
        compiler_config: Dict[str, Any] = {
            "id": compiler,
            "options": options,
        }
        if libraries:
            compiler_config["libs"] = libraries
        if tools:
            compiler_config["tools"] = tools

        # Add binary/linking filters if specified
        if create_binary or create_object_only:
            filters = {}
            if create_binary:
                filters["binary"] = True
            if create_object_only:
                filters["binaryObject"] = True
            compiler_config["filters"] = filters

        session_config = {
            "sessions": [
                {
                    "id": 1,
                    "language": language,
                    "source": source,
                    "compilers": [compiler_config],
                }
            ],
        }

        url = f"{self.config.api.endpoint}/shortener"

        try:
            async with session.post(url, json=session_config) as response:
                response.raise_for_status()
                result = await response.json()
                return str(result.get("url", ""))
        except ClientError as e:
            logger.error(f"Failed to create short link: {e}")
            raise

    async def get_languages(self) -> List[Dict[str, Any]]:
        """Get list of supported languages."""
        session = await self._get_session()
        url = f"{self.config.api.endpoint}/languages"

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()  # type: ignore[no-any-return]
        except ClientError as e:
            logger.error(f"Failed to get languages: {e}")
            raise

    async def get_languages_list(self, search_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get simplified list of languages (id, name and extensions only) with optional search."""
        full_languages = await self.get_languages()

        # Filter to only include id, name, and extensions
        simplified_languages = [
            {"id": lang.get("id", ""), "name": lang.get("name", ""), "extensions": lang.get("extensions", [])}
            for lang in full_languages
        ]

        # Apply search filter if provided
        if search_text:
            search_lower = search_text.lower()
            simplified_languages = [
                lang
                for lang in simplified_languages
                if (search_lower in lang["id"].lower() or search_lower in lang["name"].lower())
            ]

        return simplified_languages

    async def get_compilers(self, language: str, include_extended_info: bool = False) -> List[Dict[str, Any]]:
        """Get list of compilers for a language."""
        session = await self._get_session()

        # Essential fields for compiler listing with library support info
        essential_fields = [
            "id",
            "name",
            "lang",
            "compilerType",
            "instructionSet",
            "semver",
            "group",
            "groupName",
            "hidden",
            "isNightly",
            "libsArr",
            "supportsLibraryCodeFilter",
            "supportsExecute",
            "supportsBinary",
            "supportsAsmDocs",
            "supportsOptOutput",
        ]

        # Extended fields for detailed compiler information
        extended_fields = essential_fields + [
            "tools",
            "possibleOverrides",
            "possibleRuntimeTools",
            "license",
            "notification",
            "options",
            "alias",
        ]

        fields = extended_fields if include_extended_info else essential_fields
        fields_param = ",".join(fields)

        url = f"{self.config.api.endpoint}/compilers/{language}?fields={fields_param}"

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()  # type: ignore[no-any-return]
        except ClientError as e:
            logger.error(f"Failed to get compilers: {e}")
            raise

    async def get_libraries(self, language: str) -> List[Dict[str, Any]]:
        """Get list of libraries for a language."""
        session = await self._get_session()
        url = f"{self.config.api.endpoint}/libraries/{language}"

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()  # type: ignore[no-any-return]
        except ClientError as e:
            logger.error(f"Failed to get libraries: {e}")
            raise

    async def get_libraries_list(self, language: str, search_text: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get simplified list of libraries (id and name only) with optional search."""
        full_libraries = await self.get_libraries(language)

        # Filter to only include id and name
        simplified_libraries = [{"id": lib.get("id", ""), "name": lib.get("name", "")} for lib in full_libraries]

        # Apply search filter if provided
        if search_text:
            search_lower = search_text.lower()
            simplified_libraries = [
                lib
                for lib in simplified_libraries
                if (search_lower in lib["id"].lower() or search_lower in lib["name"].lower())
            ]

        return simplified_libraries

    async def get_library_details(self, language: str, library_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific library."""
        full_libraries = await self.get_libraries(language)

        # Find the specific library
        target_library = None
        for lib in full_libraries:
            if lib.get("id") == library_id:
                target_library = lib
                break

        if not target_library:
            return None

        # Filter to only include relevant fields
        filtered_library = {
            "id": target_library.get("id", ""),
            "name": target_library.get("name", ""),
            "url": target_library.get("url", ""),
            "description": target_library.get("description", ""),
            "versions": [],
        }

        # Filter versions to only include version and id
        if "versions" in target_library:
            filtered_library["versions"] = [
                {"id": version.get("id", ""), "version": version.get("version", "")}
                for version in target_library["versions"]
                if isinstance(version, dict)
            ]

        return filtered_library

    async def get_shortlink_info(self, link_id: str) -> Dict[str, Any]:
        """Get shortlink information from Compiler Explorer."""
        session = await self._get_session()
        url = f"{self.config.api.endpoint}/shortlinkinfo/{link_id}"
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()  # type: ignore[no-any-return]
        except ClientError as e:
            logger.error(f"Failed to get shortlink info: {e}")
            raise

    async def get_compiler_version(self, compiler_id: str) -> Dict[str, Any]:
        """Get deployed version information for a compiler."""
        session = await self._get_session()
        url = f"https://api.compiler-explorer.com/get_deployed_exe_version?id={compiler_id}"

        try:
            async with session.get(url) as response:
                if response.status == 404:
                    return {"error": "Version info not available"}
                response.raise_for_status()
                result = await response.json()
                return result  # type: ignore[no-any-return]
        except ClientError as e:
            logger.debug(f"Failed to get version for {compiler_id}: {e}")
            return {"error": str(e)}

    async def get_instruction_docs(self, instruction_set: str, opcode: str) -> Dict[str, Any]:
        """Get documentation for assembly instruction/opcode."""
        session = await self._get_session()
        url = f"{self.config.api.endpoint}/asm/{instruction_set}/{opcode}"

        try:
            async with session.get(url) as response:
                if response.status == 404:
                    return {
                        "error": f"Instruction '{opcode}' not found for instruction set '{instruction_set}'",
                        "instruction_set": instruction_set,
                        "opcode": opcode,
                        "found": False,
                    }
                response.raise_for_status()
                result = await response.json()
                return {
                    "instruction_set": instruction_set,
                    "opcode": opcode,
                    "found": True,
                    "documentation": result,
                }  # type: ignore[no-any-return]
        except ClientError as e:
            logger.error(f"Failed to get instruction docs for {instruction_set}/{opcode}: {e}")
            return {
                "error": f"Failed to get instruction documentation: {str(e)}",
                "instruction_set": instruction_set,
                "opcode": opcode,
                "found": False,
            }
