"""Tests for Document Classifier."""

from app.legal.document_classifier import DocumentClassifier

def test_classify_documents():
    classifier = DocumentClassifier()
    docs = [
        {"title": "Giấy phép kinh doanh", "content": "", "issue_date": "15/05/2020"},
        {"title": "CMND", "content": "123456789", "expiry_date": "2020-01-01"}, # Expired
        {"title": "Báo cáo tài chính năm 2025", "content": ""}
    ]
    
    classified = classifier.classify_documents(docs)
    
    assert len(classified) == 3
    assert classified[0]["document_type_id"] == "BUSINESS_REGISTRATION"
    assert classified[0]["is_expired"] is False
    
    assert classified[1]["document_type_id"] == "IDENTITY_DOCUMENT"
    assert classified[1]["is_expired"] is True
    
    assert classified[2]["document_type_id"] == "FINANCIAL_STATEMENT"
    assert classified[2]["is_expired"] is False
