"""Utility functions for finding and categorizing experimental compilers."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ExperimentalCompiler:
    """Represents an experimental compiler with categorization."""

    id: str
    name: str
    category: str
    proposal_numbers: List[str]
    features: List[str]
    is_nightly: bool
    description: str
    version_info: Optional[Dict[str, Any]] = None
    modified: Optional[str] = None
    possible_overrides: Optional[Dict[str, Any]] = None
    possible_runtime_tools: Optional[Dict[str, Any]] = None
    tools: Optional[Dict[str, Any]] = None


class ExperimentalCompilerFinder:
    """Finds and categorizes experimental compilers from Compiler Explorer."""

    def __init__(self) -> None:
        # Patterns for detecting experimental features
        # Match both P-numbers (P1234) and N-numbers (N1234)
        self.proposal_pattern = re.compile(r"[pn](\d{4})", re.IGNORECASE)
        self.feature_keywords = {
            "reflection": ["reflection", "refl"],
            "concepts": ["concept", "concepts-ts"],
            "modules": ["module", "modules-ts"],
            "coroutines": ["coroutine", "coro"],
            "contracts": ["contract"],
            "ranges": ["range"],
            "networking": ["network", "net-ts"],
            "parallelism": ["parallel", "par-ts"],
            "lifetime": ["lifetime"],
            "metaprogramming": ["metaprog", "autonsdmi"],
        }

    def categorize_compilers(self, compilers: List[Dict[str, Any]]) -> Dict[str, List[ExperimentalCompiler]]:
        """
        Categorize compilers by experimental features and proposals.

        Args:
            compilers: List of compiler objects from CE API

        Returns:
            Dict mapping categories to lists of experimental compilers
        """
        categories: Dict[str, List[ExperimentalCompiler]] = {
            "proposals": [],
            "reflection": [],
            "concepts": [],
            "modules": [],
            "coroutines": [],
            "contracts": [],
            "lifetime_analysis": [],
            "metaprogramming": [],
            "trunk_nightly": [],
            "other_experimental": [],
        }

        for compiler in compilers:
            name = compiler.get("name", "")
            comp_id = compiler.get("id", "")
            name_lower = name.lower()
            id_lower = comp_id.lower()
            is_nightly = compiler.get("isNightly", False)

            # Skip if not experimental at all
            if not self._is_experimental(compiler):
                continue

            # Extract proposal numbers
            proposal_numbers = self._extract_proposal_numbers(name + " " + comp_id)

            # Determine primary category and features
            category, features = self._determine_category_and_features(name_lower, id_lower)

            # If compiler has proposal numbers, prioritize "proposals" as the category
            if proposal_numbers:
                primary_category = "proposals"
            else:
                primary_category = category

            experimental_comp = ExperimentalCompiler(
                id=comp_id,
                name=name,
                category=primary_category,
                proposal_numbers=proposal_numbers,
                features=features,
                is_nightly=is_nightly,
                description=self._generate_description(name, proposal_numbers, features),
                modified=None,  # Will be populated later if nightly
                possible_overrides=compiler.get("possibleOverrides"),
                possible_runtime_tools=compiler.get("possibleRuntimeTools"),
                tools=compiler.get("tools"),
            )

            # Add to appropriate category
            if proposal_numbers:
                categories["proposals"].append(experimental_comp)
                # Also add to the feature-based category if it's different from proposals
                if category != "proposals" and category in categories:
                    categories[category].append(experimental_comp)
            else:
                # No proposal numbers - add to feature-based category
                if category in categories:
                    categories[category].append(experimental_comp)
                else:
                    categories["other_experimental"].append(experimental_comp)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def find_by_proposal(self, compilers: List[Dict[str, Any]], proposal_number: str) -> List[ExperimentalCompiler]:
        """
        Find compilers supporting a specific proposal.

        Args:
            compilers: List of compiler objects from CE API
            proposal_number: Proposal number (e.g., 'P3385', 'N3089', '3385', 'p3385', 'n3089')

        Returns:
            List of compilers supporting the proposal
        """
        # Normalize proposal number - handle both P and N prefixes
        # Remove any existing prefix and extract the number
        number_match = re.search(r"([pn]?)?(\d{4})", proposal_number.lower())
        if not number_match:
            return []

        prefix, number = number_match.groups()

        # If no prefix specified, search for both P and N
        if not prefix:
            pattern = re.compile(rf"[pn]{number}\b", re.IGNORECASE)
        else:
            # Search for the specific prefix
            pattern = re.compile(rf"{prefix}{number}\b", re.IGNORECASE)

        matching_compilers = []
        for compiler in compilers:
            name = compiler.get("name", "")
            comp_id = compiler.get("id", "")

            if pattern.search(name + " " + comp_id):
                proposal_numbers = self._extract_proposal_numbers(name + " " + comp_id)
                features = self._extract_features(name.lower())

                matching_compilers.append(
                    ExperimentalCompiler(
                        id=comp_id,
                        name=name,
                        category="proposals",
                        proposal_numbers=proposal_numbers,
                        features=features,
                        is_nightly=compiler.get("isNightly", False),
                        description=self._generate_description(name, proposal_numbers, features),
                        modified=None,  # Will be populated later if nightly
                        possible_overrides=compiler.get("possibleOverrides"),
                        possible_runtime_tools=compiler.get("possibleRuntimeTools"),
                        tools=compiler.get("tools"),
                    )
                )

        return matching_compilers

    def find_by_feature(self, compilers: List[Dict[str, Any]], feature: str) -> List[ExperimentalCompiler]:
        """
        Find compilers supporting a specific experimental feature.

        Args:
            compilers: List of compiler objects from CE API
            feature: Feature name (e.g., 'reflection', 'concepts', 'modules')

        Returns:
            List of compilers supporting the feature
        """
        feature_lower = feature.lower()
        matching_compilers = []

        for compiler in compilers:
            name_lower = compiler.get("name", "").lower()

            # Check if this compiler supports the requested feature
            if any(keyword in name_lower for keyword in self.feature_keywords.get(feature_lower, [feature_lower])):
                proposal_numbers = self._extract_proposal_numbers(
                    compiler.get("name", "") + " " + compiler.get("id", "")
                )
                features = self._extract_features(name_lower)

                matching_compilers.append(
                    ExperimentalCompiler(
                        id=compiler.get("id", ""),
                        name=compiler.get("name", ""),
                        category=feature_lower,
                        proposal_numbers=proposal_numbers,
                        features=features,
                        is_nightly=compiler.get("isNightly", False),
                        description=self._generate_description(compiler.get("name", ""), proposal_numbers, features),
                        modified=None,  # Will be populated later if nightly
                        possible_overrides=compiler.get("possibleOverrides"),
                        possible_runtime_tools=compiler.get("possibleRuntimeTools"),
                        tools=compiler.get("tools"),
                    )
                )

        return matching_compilers

    def get_all_experimental_compilers(self, compilers: List[Dict[str, Any]]) -> List[ExperimentalCompiler]:
        """Get all experimental compilers with full details."""
        experimental = []

        for compiler in compilers:
            if self._is_experimental(compiler):
                name = compiler.get("name", "")
                comp_id = compiler.get("id", "")
                name_lower = name.lower()

                proposal_numbers = self._extract_proposal_numbers(name + " " + comp_id)
                category, features = self._determine_category_and_features(name_lower, comp_id.lower())

                # If compiler has proposal numbers, prioritize "proposals" as the category
                if proposal_numbers:
                    primary_category = "proposals"
                else:
                    primary_category = category

                experimental.append(
                    ExperimentalCompiler(
                        id=comp_id,
                        name=name,
                        category=primary_category,
                        proposal_numbers=proposal_numbers,
                        features=features,
                        is_nightly=compiler.get("isNightly", False),
                        description=self._generate_description(name, proposal_numbers, features),
                        modified=None,  # Will be populated later if nightly
                        possible_overrides=compiler.get("possibleOverrides"),
                        possible_runtime_tools=compiler.get("possibleRuntimeTools"),
                        tools=compiler.get("tools"),
                    )
                )

        return sorted(experimental, key=lambda x: (x.category, x.name))

    def _is_experimental(self, compiler: Dict[str, Any]) -> bool:
        """Check if a compiler is experimental."""
        name = compiler.get("name", "").lower()
        comp_id = compiler.get("id", "").lower()
        is_nightly = compiler.get("isNightly", False)

        experimental_indicators = [
            "experimental",
            "trunk" and is_nightly,
            self.proposal_pattern.search(name + " " + comp_id),
            any(keyword in name for keywords in self.feature_keywords.values() for keyword in keywords),
        ]

        return any(experimental_indicators)

    def _extract_proposal_numbers(self, text: str) -> List[str]:
        """Extract proposal numbers from text (both P and N numbers)."""
        # Find all matches with their prefixes
        full_matches = re.findall(r"([pn])(\d{4})", text, re.IGNORECASE)
        proposals = []
        for prefix, number in full_matches:
            # Normalize to uppercase
            proposals.append(f"{prefix.upper()}{number}")
        return proposals

    def _extract_features(self, name_lower: str) -> List[str]:
        """Extract experimental features from compiler name."""
        features = []
        for feature, keywords in self.feature_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                features.append(feature)
        return features

    def _determine_category_and_features(self, name_lower: str, id_lower: str) -> tuple[str, List[str]]:
        """Determine primary category and extract features."""
        features = self._extract_features(name_lower)

        # Determine primary category
        if "reflection" in name_lower:
            return "reflection", features
        elif any(word in name_lower for word in ["concept", "concepts-ts"]):
            return "concepts", features
        elif any(word in name_lower for word in ["module", "modules-ts"]):
            return "modules", features
        elif "coroutine" in name_lower:
            return "coroutines", features
        elif "contract" in name_lower:
            return "contracts", features
        elif "lifetime" in name_lower:
            return "lifetime_analysis", features
        elif any(word in name_lower for word in ["metaprog", "autonsdmi"]):
            return "metaprogramming", features
        elif "trunk" in name_lower:
            return "trunk_nightly", features
        else:
            return "other_experimental", features

    def _generate_description(self, name: str, proposal_numbers: List[str], features: List[str]) -> str:
        """Generate a user-friendly description."""
        desc_parts = [name]

        if proposal_numbers:
            desc_parts.append(f"Supports: {', '.join(proposal_numbers)}")

        if features:
            desc_parts.append(f"Features: {', '.join(features)}")

        return " | ".join(desc_parts)


def parse_version_info(raw_version_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse raw version info into a more structured format.

    Extracts:
    - Version number
    - Commit hash (if available)
    - Build date (if available)
    - Source URL (if available)
    - Modified datetime (if available)
    """
    if "error" in raw_version_info:
        return raw_version_info

    version_str = raw_version_info.get("version", "")
    parsed = {
        "raw_version": version_str,
        "full_version": raw_version_info.get("full_version", ""),
        "modified": raw_version_info.get("modified", ""),
    }

    # Extract version number (e.g., "21.0.0git" from "clang version 21.0.0git")
    import re

    version_match = re.search(r"version\s+([\d.]+\w*)", version_str)
    if version_match:
        parsed["version_number"] = version_match.group(1)

    # Extract commit hash from GitHub URLs
    commit_match = re.search(r"\b([a-f0-9]{40})\b", version_str)
    if not commit_match:
        # Try shorter hash
        commit_match = re.search(r"/([a-f0-9]{7,})\)", version_str)
    if commit_match:
        parsed["commit_hash"] = commit_match.group(1)

    # Extract build date (e.g., "20250724" from gcc version strings)
    date_match = re.search(r"\b(202\d{5})\b", version_str)
    if date_match:
        parsed["build_date"] = date_match.group(1)

    # Extract source URL
    url_match = re.search(r"(https?://[^\s)]+)", version_str)
    if url_match:
        parsed["source_url"] = url_match.group(1)

    # For GCC, extract the build hash
    gcc_build_match = re.search(r"gcc-([a-f0-9]{40})", version_str)
    if gcc_build_match:
        parsed["gcc_build_hash"] = gcc_build_match.group(1)

    return parsed


async def fetch_version_info_for_compilers(compilers: List[ExperimentalCompiler], client: Any) -> None:
    """
    Fetch version information for nightly compilers.

    Updates the version_info and modified fields for compilers where isNightly=True.
    """
    for compiler in compilers:
        if compiler.is_nightly:
            raw_version_info = await client.get_compiler_version(compiler.id)
            if "error" not in raw_version_info:
                parsed_info = parse_version_info(raw_version_info)
                compiler.version_info = parsed_info
                compiler.modified = parsed_info.get("modified", "")


async def search_experimental_compilers(
    language: str,
    client: Any,
    proposal: Optional[str] = None,
    feature: Optional[str] = None,
    category: Optional[str] = None,
    fetch_versions: bool = True,
) -> List[ExperimentalCompiler]:
    """
    Search for experimental compilers with various filters.

    Args:
        language: Programming language (e.g., 'c++')
        client: CompilerExplorerClient instance
        proposal: Proposal number to search for (e.g., 'P3385')
        feature: Feature to search for (e.g., 'reflection')
        category: Category to filter by (e.g., 'concepts')
        fetch_versions: Whether to fetch version info for nightly compilers

    Returns:
        List of matching experimental compilers with version info
    """
    compilers = await client.get_compilers(language, include_extended_info=True)
    finder = ExperimentalCompilerFinder()

    experimental_compilers: List[ExperimentalCompiler]
    if proposal:
        experimental_compilers = finder.find_by_proposal(compilers, proposal)
    elif feature:
        experimental_compilers = finder.find_by_feature(compilers, feature)
    elif category:
        all_experimental = finder.get_all_experimental_compilers(compilers)
        experimental_compilers = [comp for comp in all_experimental if comp.category == category]
    else:
        experimental_compilers = finder.get_all_experimental_compilers(compilers)

    # Fetch version info for nightly builds
    if fetch_versions:
        await fetch_version_info_for_compilers(experimental_compilers, client)

    # Sort by modified datetime (descending - most recent first)
    # Compilers without modified datetime go to the end
    def sort_key(compiler: ExperimentalCompiler) -> tuple[int, str]:
        if compiler.modified:
            # Higher sort value (1) for compilers with datetime - these come first with reverse=True
            # Use datetime string directly - reverse=True will sort most recent first
            return (1, compiler.modified)
        else:
            # Lower sort value (0) for compilers without datetime - these come last with reverse=True
            # Use negative name for reverse alphabetical (since we're using reverse=True)
            return (0, compiler.name)

    experimental_compilers.sort(key=sort_key, reverse=True)

    return experimental_compilers
