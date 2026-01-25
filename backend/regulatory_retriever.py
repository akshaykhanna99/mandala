"""Retrieve relevant regulatory snippets from FCA excerpts."""
import os
import re
from pathlib import Path
from typing import List, Tuple


class RegulatorySnippet:
    """A chunk of regulatory text with citation info."""
    def __init__(self, text: str, snippet_id: str, section: str):
        self.text = text
        self.snippet_id = snippet_id
        self.section = section


def _chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Split text into chunks, trying to break at paragraph boundaries."""
    if not text or not text.strip():
        return []
    
    # Split by double newlines (paragraphs)
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_size = len(para)
        if current_size + para_size > chunk_size and current_chunk:
            # Save current chunk
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        else:
            current_chunk.append(para)
            current_size += para_size + 2  # +2 for "\n\n"
    
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    
    return chunks


def _score_chunk(chunk: str, query_terms: List[str]) -> int:
    """Score a chunk based on keyword matches."""
    if not query_terms:
        return 1
    
    chunk_lower = chunk.lower()
    score = 0
    for term in query_terms:
        term_lower = term.lower()
        # Count occurrences
        score += chunk_lower.count(term_lower)
    
    return score


def retrieve_regulatory_snippets(
    query_terms: List[str],
    max_results: int = 3,
    base_path: Path | None = None,
) -> List[RegulatorySnippet]:
    """
    Retrieve top regulatory snippets relevant to the query.
    
    Args:
        query_terms: Keywords to search for (e.g., ["suitability", "risk", "documentation"])
        max_results: Maximum number of snippets to return
        base_path: Base path to docs/regulatory (defaults to project root)
    
    Returns:
        List of RegulatorySnippet objects
    """
    if base_path is None:
        # Assume we're in backend/, go up to project root
        base_path = Path(__file__).parent.parent
    
    excerpts_file = base_path / "docs" / "regulatory" / "FCA_EXCERPTS.md"
    
    if not excerpts_file.exists():
        return []
    
    try:
        content = excerpts_file.read_text(encoding="utf-8")
    except Exception:
        return []
    
    if not content.strip():
        return []
    
    # Extract sections (headings like ## COBS 9, ## SYSC 7)
    sections = {}
    current_section = "General"
    current_text = []
    
    for line in content.split("\n"):
        if line.startswith("## "):
            # Save previous section
            if current_text:
                sections[current_section] = "\n".join(current_text)
            # Start new section
            current_section = line[3:].strip()
            current_text = []
        else:
            current_text.append(line)
    
    # Save last section
    if current_text:
        sections[current_section] = "\n".join(current_text)
    
    # Chunk each section
    all_chunks: List[Tuple[str, str, str]] = []  # (text, section, chunk_id)
    
    for section_name, section_text in sections.items():
        chunks = _chunk_text(section_text, chunk_size=500)
        for i, chunk in enumerate(chunks):
            chunk_id = f"chunk_{section_name.lower().replace(' ', '_')}_{i+1:02d}"
            all_chunks.append((chunk, section_name, chunk_id))
    
    # Score and rank chunks
    scored_chunks = [
        (_score_chunk(chunk, query_terms), chunk, section, chunk_id)
        for chunk, section, chunk_id in all_chunks
    ]
    
    # Sort by score (descending) and take top N
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = scored_chunks[:max_results]
    
    # Convert to RegulatorySnippet objects
    snippets = [
        RegulatorySnippet(text=chunk, snippet_id=chunk_id, section=section)
        for _, chunk, section, chunk_id in top_chunks
        if chunk.strip()  # Only non-empty chunks
    ]
    
    return snippets


def get_snippet_texts(snippets: List[RegulatorySnippet]) -> List[str]:
    """Extract just the text from snippets."""
    return [s.text for s in snippets]
