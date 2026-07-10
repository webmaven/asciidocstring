from typing import List, Any, Dict
from dataclasses import dataclass
from asciidoctrine.nodes import NodeVisitor, Listing

@dataclass
class TestBlock:
    """Represents an executable code block extracted from a docstring."""
    content: str
    language: str
    line_number: int
    is_interactive: bool  # True if it contains ">>> " style prompts
    attributes: Dict[str, Any]

class TestBlockExtractorVisitor(NodeVisitor):
    """AST visitor to locate and extract Python test blocks from a docstring."""
    
    def __init__(self, target_language: str, requires_test_marker: bool):
        self.target_language = target_language.lower()
        self.requires_test_marker = requires_test_marker
        self.extracted_tests: List[TestBlock] = []

    def extract(self, node: Any) -> List[TestBlock]:
        """Reset state, traverse the node tree, and return extracted test blocks."""
        self.extracted_tests = []
        self.visit(node)
        return self.extracted_tests

    def visit_listing(self, node: Listing) -> None:
        """Process code listing blocks."""
        attrs = node.attributes or {}
        style = attrs.get("style", "")
        lang = attrs.get("language", "").lower()
        
        # A Listing node with style='source' represents a source code block
        is_source = (style == "source" or node.name == "listing")
        is_target_lang = (lang == self.target_language) or (not lang and self.target_language == "python")
        
        # Sgthand [.test] parsed as 'role': 'test'
        has_test_marker = ("test" in attrs or attrs.get("role") == "test")
        
        if is_source and is_target_lang:
            if self.requires_test_marker and not has_test_marker:
                return  # Skip since test marker is required but not present
                
            # Extract content from Text inline nodes
            content_parts = [inline.value for inline in node.inlines if hasattr(inline, "value")]
            content = "".join(content_parts)
            
            # Identify interactive session
            is_interactive = ">>> " in content
            
            # Fetch line numbers from node locations if available
            line_number = 1
            if hasattr(node, "location") and node.location:
                line_number = node.location[0].get("line", 1)
                
            self.extracted_tests.append(TestBlock(
                content=content,
                language=lang or self.target_language,
                line_number=line_number,
                is_interactive=is_interactive,
                attributes=attrs
            ))
