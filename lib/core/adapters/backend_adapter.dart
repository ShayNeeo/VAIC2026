library backend_adapter;

import '../models/case_models.dart';

/// Maps backend `SharedCaseState` (from /api/v1/cases) into the UI models.
///
/// The backend returns raw orchestration state; the frontend consumes a
/// brief-shaped contract (CaseQueueItem / CaseDetail). This adapter is the
/// single place that bridges the two. If the backend later exposes dedicated
/// DTOs, swap the parser here only.

OpportunityStatus _statusFromBackend(Map<String, dynamic> state) {
  final risk = (state['risk_level'] as String? ?? 'low').toLowerCase();
  final finalStatus = (state['final_status'] as String? ?? 'new').toLowerCase();
  if (finalStatus == 'pending_information') return OpportunityStatus.needInfo;
  if (finalStatus == 'failed') return OpportunityStatus.blocked;
  if (risk == 'high') return OpportunityStatus.reviewRequired;
  return OpportunityStatus.ready;
}

List<CaseQueueItem> mapQueue(List<dynamic> raw) {
  return raw.map((e) => mapQueueItem(e as Map<String, dynamic>)).toList();
}

CaseQueueItem mapQueueItem(Map<String, dynamic> s) {
  final profile = (s['company_profile'] as Map?)?.cast<String, dynamic>() ?? {};
  final products = _backendProducts(s);
  final status = _statusFromBackend(s);
  return CaseQueueItem(
    caseId: s['case_id'] as String? ?? '',
    caseNumber: s['case_id'] as String? ?? '',
    title: _requestText(s),
    status: (s['final_status'] as String? ?? 'new'),
    companyName: profile['name'] as String? ?? 'Khách hàng doanh nghiệp',
    companyId: s['customer_id'] as String? ?? '',
    opportunityCount: products.length,
    branchStatusCounts: {
      'ready': status == OpportunityStatus.ready ? products.length : 0,
      'need_info': status == OpportunityStatus.needInfo ? products.length : 0,
      'review_required': status == OpportunityStatus.reviewRequired ? products.length : 0,
      'blocked': status == OpportunityStatus.blocked ? products.length : 0,
    },
    nextAction: _nextAction(s),
    sla: _sla(s),
    updatedAt: DateTime.tryParse(s['updated_at'] as String? ?? '') ?? DateTime.now(),
  );
}

CaseDetail mapDetail(Map<String, dynamic> s) {
  final profile = (s['company_profile'] as Map?)?.cast<String, dynamic>() ?? {};
  final products = _backendProducts(s);
  final evidence = (s['evidences'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  final missing = (s['missing_information'] as List?)?.cast<String>() ?? [];
  final plan = (s['execution_plan'] as List?)?.cast<Map<String, dynamic>>() ?? [];

  return CaseDetail(
    caseId: s['case_id'] as String? ?? '',
    caseNumber: s['case_id'] as String? ?? '',
    title: _requestText(s),
    description: _requestText(s),
    companyName: profile['name'] as String? ?? 'Khách hàng doanh nghiệp',
    companyId: s['customer_id'] as String? ?? '',
    segment: (profile['segment'] as String?) ?? (profile['industry'] as String?) ?? '',
    industry: (profile['industry'] as String?) ?? '',
    rmId: s['rm_id'] as String? ?? '',
    rmName: s['rm_id'] as String? ?? '',
    updatedAt: DateTime.tryParse(s['updated_at'] as String? ?? '') ?? DateTime.now(),
    needFacts: profile.entries
        .map((e) => NeedFact(
              field: e.key,
              value: e.value?.toString() ?? '',
              source: 'CRM',
              confidence: 0.9,
              confirmed: true,
              freshness: DateTime.now(),
            ))
        .toList(),
    opportunities: products
        .map((p) => OpportunityCard(
              opportunityId: p['product_id'] as String? ?? '',
              product: p['name'] as String? ?? '',
              productId: p['product_id'] as String? ?? '',
              customer: profile['name'] as String? ?? '',
              caseId: s['case_id'] as String? ?? '',
              status: _statusFromBackend(s),
              businessNeed: _requestText(s),
              signals: [
                Signal(
                  fact: p['matching_reason'] as String? ?? '',
                  source: 'Product Agent',
                  strength: ((p['match_score'] as num?)?.toDouble() ?? 0.7),
                )
              ],
              productFit: [p['matching_reason'] as String? ?? ''],
              evidence: evidence
                  .map((ev) => EvidenceRef(
                        id: ev['agent'] as String? ?? '',
                        document: ev['source_doc'] as String? ?? '',
                        section: ev['page_or_section'] as String? ?? '',
                        effectiveDate: '',
                        owner: ev['agent'] as String? ?? '',
                        tier: ev['is_valid'] == true ? 'Xác minh' : 'Chờ xác minh',
                      ))
                  .toList(),
              missingInfo: missing,
              risk: [(s['risk_level'] as String? ?? 'low')],
              nextBestAction: _nextAction(s),
              owner: 'RM',
              sla: _sla(s),
              expectedOutcome: p['name'] as String? ?? '',
            ))
        .toList(),
    missingDocuments: missing
        .map((m) => MissingDocument(
              documentType: m,
              description: m,
              reason: 'Thiếu từ RM / khách hàng',
              responsibleParty: 'RM',
            ))
        .toList(),
    evidence: evidence
        .map((ev) => EvidenceRef(
              id: ev['agent'] as String? ?? '',
              document: ev['source_doc'] as String? ?? '',
              section: ev['page_or_section'] as String? ?? '',
              effectiveDate: '',
              owner: ev['agent'] as String? ?? '',
              tier: ev['is_valid'] == true ? 'Xác minh' : 'Chờ xác minh',
            ))
        .toList(),
    emailDraft: (s['operations_result'] as Map?)?.cast<String, dynamic>()['email_draft'] as String? ?? '',
    checklist: plan
        .map((t) => ChecklistItem(
              id: t['task_id'] as String? ?? '',
              text: t['description'] as String? ?? '',
              owner: t['owner'] as String? ?? '',
              sla: '7 ngày',
              completed: (t['status'] as String? ?? 'pending') == 'completed',
            ))
        .toList(),
  );
}

List<Map<String, dynamic>> _backendProducts(Map<String, dynamic> s) {
  final result = (s['product_result'] as Map?)?.cast<String, dynamic>() ?? {};
  final bundle = (result['recommended_bundle'] as Map?)?.cast<String, dynamic>() ?? {};
  final products = (bundle['products'] as List?)?.cast<Map<String, dynamic>>() ?? [];
  return products;
}

String _requestText(Map<String, dynamic> s) {
  final req = s['customer_request'];
  if (req is Map) return (req['text'] as String?) ?? req.toString();
  return req?.toString() ?? 'Yêu cầu mới';
}

String _nextAction(Map<String, dynamic> s) {
  final finalStatus = (s['final_status'] as String? ?? 'new').toLowerCase();
  if (finalStatus == 'pending_information') return 'Bổ sung tài liệu thiếu';
  if (finalStatus == 'pending_approval') return 'Chờ RM phê duyệt';
  if (finalStatus == 'completed') return 'Hoàn thành';
  return 'Xem xét decision brief';
}

String _sla(Map<String, dynamic> s) {
  final risk = (s['risk_level'] as String? ?? 'low').toLowerCase();
  if (risk == 'high') return 'Ưu tiên cao';
  if (risk == 'medium') return '7 ngày';
  return '14 ngày';
}
