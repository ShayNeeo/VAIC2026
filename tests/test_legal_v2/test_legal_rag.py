"""Tests for Legal RAG."""

from app.legal.legal_rag import LegalRAGService

def test_legal_rag_search():
    rag = LegalRAGService()
    
    # Should find UBO related policy
    results = rag.search("ubo chủ sở hữu hưởng lợi", top_k=1)
    assert len(results) > 0
    assert "UBO" in results[0]["text"] or "hưởng lợi" in results[0]["text"]

def test_legal_rag_build_context():
    rag = LegalRAGService()
    
    context = rag.build_context(["báo cáo tài chính", "cấm vận pep"])
    assert context["grounded"] is True
    assert "context_text" in context
    assert "báo cáo tài chính" in context["context_text"].lower()
