import 'package:freezed_annotation/freezed_annotation.dart';

part 'case_models.freezed.dart';
part 'case_models.g.dart';

/// Queue list item (S1 screen)
@freezed
class CaseQueueItem with _$CaseQueueItem {
  const factory CaseQueueItem({
    required String caseId,
    required String caseNumber,
    required String title,
    required String status,
    required String companyName,
    required String companyId,
    required int opportunityCount,
    required Map<String, int> branchStatusCounts, // ready, need_info, review, blocked
    required String nextAction,
    required String sla,
    required DateTime updatedAt,
  }) = _CaseQueueItem;

  factory CaseQueueItem.fromJson(Map<String, dynamic> json) => _$CaseQueueItemFromJson(json);
}

/// Full case detail (S2 screen)
@freezed
class CaseDetail with _$CaseDetail {
  const factory CaseDetail({
    required String caseId,
    required String caseNumber,
    required String title,
    required String description,
    required String companyName,
    required String companyId,
    required String segment,
    required String industry,
    required String rmId,
    required String rmName,
    required DateTime updatedAt,
    required List<NeedFact> needFacts,
    required List<OpportunityCard> opportunities,
    required List<MissingDocument> missingDocuments,
    required List<EvidenceRef> evidence,
    required String emailDraft,
    required List<ChecklistItem> checklist,
  }) = _CaseDetail;

  factory CaseDetail.fromJson(Map<String, dynamic> json) => _$CaseDetailFromJson(json);
}

/// Need fact with source + confidence (brief §3)
@freezed
class NeedFact with _$NeedFact {
  const factory NeedFact({
    required String field,
    required String value,
    required String source,      // CRM / RM note / AI inference
    required double confidence,  // 0-1
    required bool confirmed,     // RM confirmed
    required DateTime freshness, // data age
  }) = _NeedFact;

  factory NeedFact.fromJson(Map<String, dynamic> json) => _$NeedFactFromJson(json);
}

/// Opportunity card (brief §3-4)
@freezed
class OpportunityCard with _$OpportunityCard {
  const factory OpportunityCard({
    required String opportunityId,
    required String product,
    required String productId,
    required String customer,
    required String caseId,
    required OpportunityStatus status,
    required String businessNeed,
    required List<Signal> signals,
    required List<String> productFit,
    required List<EvidenceRef> evidence,
    required List<String> missingInfo,
    required List<String> risk,
    required String nextBestAction,
    required String owner,
    required String sla,
    required String expectedOutcome,
  }) = _OpportunityCard;

  factory OpportunityCard.fromJson(Map<String, dynamic> json) => _$OpportunityCardFromJson(json);
}

@freezed
class Signal with _$Signal {
  const factory Signal({
    required String fact,
    required String source,
    required double strength,
  }) = _Signal;

  factory Signal.fromJson(Map<String, dynamic> json) => _$SignalFromJson(json);
}

@freezed
class EvidenceRef with _$EvidenceRef {
  const factory EvidenceRef({
    required String id,
    required String document,
    required String section,
    required String effectiveDate,
    required String owner,
    required String tier,
  }) = _EvidenceRef;

  factory EvidenceRef.fromJson(Map<String, dynamic> json) => _$EvidenceRefFromJson(json);
}

@freezed
class MissingDocument with _$MissingDocument {
  const factory MissingDocument({
    required String documentType,
    required String description,
    required String reason,
    required String responsibleParty,
  }) = _MissingDocument;

  factory MissingDocument.fromJson(Map<String, dynamic> json) => _$MissingDocumentFromJson(json);
}

@freezed
class ChecklistItem with _$ChecklistItem {
  const factory ChecklistItem({
    required String id,
    required String text,
    required String owner,
    required String sla,
    required bool completed,
  }) = _ChecklistItem;

  factory ChecklistItem.fromJson(Map<String, dynamic> json) => _$ChecklistItemFromJson(json);
}

/// Approval payload (S3)
@freezed
class ApprovalPayload with _$ApprovalPayload {
  const factory ApprovalPayload({
    required List<String> selectedOpportunityIds,
    required List<PayloadDiff> diff,
    required List<String> rmCommitments,
  }) = _ApprovalPayload;

  factory ApprovalPayload.fromJson(Map<String, dynamic> json) => _$ApprovalPayloadFromJson(json);
}

@freezed
class PayloadDiff with _$PayloadDiff {
  const factory PayloadDiff({
    required String object,
    required String action,
  }) = _PayloadDiff;

  factory PayloadDiff.fromJson(Map<String, dynamic> json) => _$PayloadDiffFromJson(json);
}

/// Opportunity status enum
///
/// Accepts both the brief mock values (snake_case) and the live backend
/// values (camelCase) via @JsonValue so Enum decode never throws.
enum OpportunityStatus {
  @JsonValue('ready')
  @JsonValue('new')
  @JsonValue('draft')
  @JsonValue('pending_approval')
  @JsonValue('in_review')
  @JsonValue('completed')
  ready,           // xanh - sẵn sàng
  @JsonValue('needInfo')
  @JsonValue('need_info')
  @JsonValue('need info')
  @JsonValue('getInfo')
  @JsonValue('pending_information')
  needInfo,        // vàng - thiếu thông tin
  @JsonValue('reviewRequired')
  @JsonValue('review_required')
  reviewRequired,  // đỏ - cần chuyên gia
  @JsonValue('blocked')
  @JsonValue('failed')
  blocked,         // đỏ - bị chặn
  @JsonValue('aiCta')
  @JsonValue('AICta')
  aiCta,           // xám - AI đề xuất
}

/// Extension for display
extension OpportunityStatusX on OpportunityStatus {
  String get label {
    switch (this) {
      case OpportunityStatus.ready: return 'Sẵn sàng';
      case OpportunityStatus.needInfo: return 'Thiếu thông tin';
      case OpportunityStatus.reviewRequired: return 'Cần chuyên gia';
      case OpportunityStatus.blocked: return 'Bị chặn';
      case OpportunityStatus.aiCta: return 'AI đề xuất';
    }
  }
}