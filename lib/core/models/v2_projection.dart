/// Projection of live backend v2 `SharedCaseState` onto the demo-shaped
/// Flutter models (`CaseQueueItem`, `CaseDetail`). The backend contract is the
/// source of truth; demo fields are derived best-effort so the existing UI
/// (S1/S2/S3) renders the same way for both mock and live data.
library;

import 'case_models.dart';

const String kDemoEmployeeId = 'EMP-RM-001';
const String kDemoSessionId = 'SES-DEMO-001';
const String kDemoRmName = 'Nguyễn An';

Map<String, int> _branchStatusCounts(String status) {
  // Map backend CaseStatus -> demo branch buckets (ready/need_info/review/blocked)
  return switch (status) {
    'pending_information' => {'ready': 0, 'need_info': 1, 'review_required': 0, 'blocked': 0},
    'pending_review' => {'ready': 0, 'need_info': 0, 'review_required': 1, 'blocked': 0},
    'blocked' => {'ready': 0, 'need_info': 0, 'review_required': 0, 'blocked': 1},
    'failed' => {'ready': 0, 'need_info': 0, 'review_required': 0, 'blocked': 1},
    'completed' => {'ready': 1, 'need_info': 0, 'review_required': 0, 'blocked': 0},
    'rejected' => {'ready': 1, 'need_info': 0, 'review_required': 0, 'blocked': 0},
    _ => {'ready': 1, 'need_info': 0, 'review_required': 0, 'blocked': 0},
  };
}

String _customerName(Map<String, dynamic> customer) {
  final attrs = customer['attributes'] as Map<String, dynamic>? ?? {};
  return (attrs['name'] ?? attrs['company_name'] ?? attrs['legal_name'] ?? customer['customer_id'] ?? 'Khách hàng').toString();
}

CaseQueueItem projectQueueItem(Map<String, dynamic> raw) {
  final status = (raw['status'] ?? 'new').toString();
  final ctx = raw['context'] as Map<String, dynamic>? ?? {};
  final customer = ctx['customer'] as Map<String, dynamic>? ?? {};
  final name = _customerName(customer);
  final request = raw['request'] as Map<String, dynamic>? ?? {};
  final workflow = raw['workflow'] as Map<String, dynamic>? ?? {};
  final tasks = (workflow['tasks'] as List? ?? []);
  return CaseQueueItem(
    caseId: raw['case_id'] ?? '',
    caseNumber: raw['case_id'] ?? '',
    title: (request['text'] ?? 'Cơ hội doanh nghiệp').toString().replaceAll('\n', ' ').trim(),
    status: status,
    companyName: name,
    companyId: (customer['customer_id'] ?? '').toString(),
    opportunityCount: tasks.isEmpty ? 1 : tasks.length,
    branchStatusCounts: _branchStatusCounts(status),
    nextAction: (raw['next_best_actions'] as List? ?? []).isNotEmpty
        ? (raw['next_best_actions'] as List).first['title']?.toString() ?? 'Xem xét hồ sơ'
        : 'Xem xét hồ sơ',
    sla: 'SLA',
    updatedAt: _parseDate(raw['updated_at']),
  );
}

List<OpportunityCard> _projectOpportunities(Map<String, dynamic> raw) {
  final workflow = raw['workflow'] as Map<String, dynamic>? ?? {};
  final tasks = (workflow['tasks'] as List? ?? []);
  if (tasks.isEmpty) {
    final product = (raw['product_result'] as Map<String, dynamic>? ?? {});
    final title = (product['product_name'] ?? 'Sản phẩm đề xuất').toString();
    return [
      OpportunityCard(
        opportunityId: 'OPP-DEFAULT',
        product: title,
        productId: (product['product_id'] ?? 'PROD-DEFAULT').toString(),
        customer: _customerName(raw['context']?['customer'] ?? {}),
        caseId: raw['case_id'] ?? '',
        status: OpportunityStatus.ready,
        businessNeed: (raw['request']?['text'] ?? '').toString(),
        signals: const [],
        productFit: const [],
        evidence: const [],
        missingInfo: const [],
        risk: const [],
        nextBestAction: 'Chuẩn bị hồ sơ duyệt',
        owner: kDemoRmName,
        sla: 'SLA',
        expectedOutcome: '',
      ),
    ];
  }
  return tasks.map<OpportunityCard>((t) {
    final m = t as Map<String, dynamic>;
    final taskStatus = (m['status'] ?? 'pending').toString();
    final oppStatus = switch (taskStatus) {
      'blocked' || 'failed' => OpportunityStatus.blocked,
      'completed' => OpportunityStatus.ready,
      'pending' => OpportunityStatus.needInfo,
      _ => OpportunityStatus.reviewRequired,
    };
    return OpportunityCard(
      opportunityId: m['task_id'] ?? 'OPP',
      product: (m['task_type'] ?? 'Cơ hội').toString(),
      productId: m['task_id'] ?? '',
      customer: _customerName(raw['context']?['customer'] ?? {}),
      caseId: raw['case_id'] ?? '',
      status: oppStatus,
      businessNeed: (m['task_type'] ?? '').toString(),
      signals: const [],
      productFit: const [],
      evidence: const [],
      missingInfo: const [],
      risk: const [],
      nextBestAction: 'Thực hiện ${m['task_type'] ?? 'nhiệm vụ'}',
      owner: (m['owner'] ?? kDemoRmName).toString(),
      sla: 'SLA',
      expectedOutcome: '',
    );
  }).toList();
}

CaseDetail projectDetail(Map<String, dynamic> raw) {
  final ctx = raw['context'] as Map<String, dynamic>? ?? {};
  final customer = ctx['customer'] as Map<String, dynamic>? ?? {};
  final attrs = customer['attributes'] as Map<String, dynamic>? ?? {};
  final request = raw['request'] as Map<String, dynamic>? ?? {};
  final name = _customerName(customer);
  return CaseDetail(
    caseId: raw['case_id'] ?? '',
    caseNumber: raw['case_id'] ?? '',
    title: (request['text'] ?? 'Decision Brief').toString().replaceAll('\n', ' ').trim(),
    description: (raw['next_best_actions'] as List? ?? []).isNotEmpty
        ? (raw['next_best_actions'] as List).first['title']?.toString() ?? ''
        : (request['text'] ?? '').toString(),
    companyName: name,
    companyId: (customer['customer_id'] ?? '').toString(),
    segment: (attrs['segment'] ?? attrs['industry'] ?? '').toString(),
    industry: (attrs['industry'] ?? '').toString(),
    rmId: kDemoEmployeeId,
    rmName: kDemoRmName,
    updatedAt: _parseDate(raw['updated_at']),
    needFacts: const [],
    opportunities: _projectOpportunities(raw),
    missingDocuments: const [],
    evidence: const [],
    emailDraft: '',
    checklist: const [
      ChecklistItem(id: 'c1', text: 'Xác nhận phạm vi hành động đúng chính sách', owner: kDemoRmName, sla: 'Trước duyệt', completed: false),
      ChecklistItem(id: 'c2', text: 'Payload đã qua RBAC, evidence và idempotency gate', owner: 'Hệ thống', sla: 'Tự động', completed: false),
    ],
  );
}

DateTime _parseDate(dynamic v) {
  if (v == null) return DateTime.now();
  if (v is String) return DateTime.tryParse(v) ?? DateTime.now();
  return DateTime.now();
}
