// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'case_models.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$CaseQueueItemImpl _$$CaseQueueItemImplFromJson(Map<String, dynamic> json) =>
    _$CaseQueueItemImpl(
      caseId: json['caseId'] as String,
      caseNumber: json['caseNumber'] as String,
      title: json['title'] as String,
      status: json['status'] as String,
      companyName: json['companyName'] as String,
      companyId: json['companyId'] as String,
      opportunityCount: (json['opportunityCount'] as num).toInt(),
      branchStatusCounts:
          Map<String, int>.from(json['branchStatusCounts'] as Map),
      nextAction: json['nextAction'] as String,
      sla: json['sla'] as String,
      updatedAt: DateTime.parse(json['updatedAt'] as String),
    );

Map<String, dynamic> _$$CaseQueueItemImplToJson(_$CaseQueueItemImpl instance) =>
    <String, dynamic>{
      'caseId': instance.caseId,
      'caseNumber': instance.caseNumber,
      'title': instance.title,
      'status': instance.status,
      'companyName': instance.companyName,
      'companyId': instance.companyId,
      'opportunityCount': instance.opportunityCount,
      'branchStatusCounts': instance.branchStatusCounts,
      'nextAction': instance.nextAction,
      'sla': instance.sla,
      'updatedAt': instance.updatedAt.toIso8601String(),
    };

_$CaseDetailImpl _$$CaseDetailImplFromJson(Map<String, dynamic> json) =>
    _$CaseDetailImpl(
      caseId: json['caseId'] as String,
      caseNumber: json['caseNumber'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      companyName: json['companyName'] as String,
      companyId: json['companyId'] as String,
      segment: json['segment'] as String,
      industry: json['industry'] as String,
      rmId: json['rmId'] as String,
      rmName: json['rmName'] as String,
      updatedAt: DateTime.parse(json['updatedAt'] as String),
      needFacts: (json['needFacts'] as List<dynamic>)
          .map((e) => NeedFact.fromJson(e as Map<String, dynamic>))
          .toList(),
      opportunities: (json['opportunities'] as List<dynamic>)
          .map((e) => OpportunityCard.fromJson(e as Map<String, dynamic>))
          .toList(),
      missingDocuments: (json['missingDocuments'] as List<dynamic>)
          .map((e) => MissingDocument.fromJson(e as Map<String, dynamic>))
          .toList(),
      evidence: (json['evidence'] as List<dynamic>)
          .map((e) => EvidenceRef.fromJson(e as Map<String, dynamic>))
          .toList(),
      emailDraft: json['emailDraft'] as String,
      checklist: (json['checklist'] as List<dynamic>)
          .map((e) => ChecklistItem.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$$CaseDetailImplToJson(_$CaseDetailImpl instance) =>
    <String, dynamic>{
      'caseId': instance.caseId,
      'caseNumber': instance.caseNumber,
      'title': instance.title,
      'description': instance.description,
      'companyName': instance.companyName,
      'companyId': instance.companyId,
      'segment': instance.segment,
      'industry': instance.industry,
      'rmId': instance.rmId,
      'rmName': instance.rmName,
      'updatedAt': instance.updatedAt.toIso8601String(),
      'needFacts': instance.needFacts,
      'opportunities': instance.opportunities,
      'missingDocuments': instance.missingDocuments,
      'evidence': instance.evidence,
      'emailDraft': instance.emailDraft,
      'checklist': instance.checklist,
    };

_$NeedFactImpl _$$NeedFactImplFromJson(Map<String, dynamic> json) =>
    _$NeedFactImpl(
      field: json['field'] as String,
      value: json['value'] as String,
      source: json['source'] as String,
      confidence: (json['confidence'] as num).toDouble(),
      confirmed: json['confirmed'] as bool,
      freshness: DateTime.parse(json['freshness'] as String),
    );

Map<String, dynamic> _$$NeedFactImplToJson(_$NeedFactImpl instance) =>
    <String, dynamic>{
      'field': instance.field,
      'value': instance.value,
      'source': instance.source,
      'confidence': instance.confidence,
      'confirmed': instance.confirmed,
      'freshness': instance.freshness.toIso8601String(),
    };

_$OpportunityCardImpl _$$OpportunityCardImplFromJson(
        Map<String, dynamic> json) =>
    _$OpportunityCardImpl(
      opportunityId: json['opportunityId'] as String,
      product: json['product'] as String,
      productId: json['productId'] as String,
      customer: json['customer'] as String,
      caseId: json['caseId'] as String,
      status: statusFromJson(json['status']),
      businessNeed: json['businessNeed'] as String,
      signals: (json['signals'] as List<dynamic>)
          .map((e) => Signal.fromJson(e as Map<String, dynamic>))
          .toList(),
      productFit: (json['productFit'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      evidence: (json['evidence'] as List<dynamic>)
          .map((e) => EvidenceRef.fromJson(e as Map<String, dynamic>))
          .toList(),
      missingInfo: (json['missingInfo'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      risk: (json['risk'] as List<dynamic>).map((e) => e as String).toList(),
      nextBestAction: json['nextBestAction'] as String,
      owner: json['owner'] as String,
      sla: json['sla'] as String,
      expectedOutcome: json['expectedOutcome'] as String,
    );

Map<String, dynamic> _$$OpportunityCardImplToJson(
        _$OpportunityCardImpl instance) =>
    <String, dynamic>{
      'opportunityId': instance.opportunityId,
      'product': instance.product,
      'productId': instance.productId,
      'customer': instance.customer,
      'caseId': instance.caseId,
      'status': statusToJson(instance.status),
      'businessNeed': instance.businessNeed,
      'signals': instance.signals,
      'productFit': instance.productFit,
      'evidence': instance.evidence,
      'missingInfo': instance.missingInfo,
      'risk': instance.risk,
      'nextBestAction': instance.nextBestAction,
      'owner': instance.owner,
      'sla': instance.sla,
      'expectedOutcome': instance.expectedOutcome,
    };

_$SignalImpl _$$SignalImplFromJson(Map<String, dynamic> json) => _$SignalImpl(
      fact: json['fact'] as String,
      source: json['source'] as String,
      strength: (json['strength'] as num).toDouble(),
    );

Map<String, dynamic> _$$SignalImplToJson(_$SignalImpl instance) =>
    <String, dynamic>{
      'fact': instance.fact,
      'source': instance.source,
      'strength': instance.strength,
    };

_$EvidenceRefImpl _$$EvidenceRefImplFromJson(Map<String, dynamic> json) =>
    _$EvidenceRefImpl(
      id: json['id'] as String,
      document: json['document'] as String,
      section: json['section'] as String,
      effectiveDate: json['effectiveDate'] as String,
      owner: json['owner'] as String,
      tier: json['tier'] as String,
    );

Map<String, dynamic> _$$EvidenceRefImplToJson(_$EvidenceRefImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'document': instance.document,
      'section': instance.section,
      'effectiveDate': instance.effectiveDate,
      'owner': instance.owner,
      'tier': instance.tier,
    };

_$MissingDocumentImpl _$$MissingDocumentImplFromJson(
        Map<String, dynamic> json) =>
    _$MissingDocumentImpl(
      documentType: json['documentType'] as String,
      description: json['description'] as String,
      reason: json['reason'] as String,
      responsibleParty: json['responsibleParty'] as String,
    );

Map<String, dynamic> _$$MissingDocumentImplToJson(
        _$MissingDocumentImpl instance) =>
    <String, dynamic>{
      'documentType': instance.documentType,
      'description': instance.description,
      'reason': instance.reason,
      'responsibleParty': instance.responsibleParty,
    };

_$ChecklistItemImpl _$$ChecklistItemImplFromJson(Map<String, dynamic> json) =>
    _$ChecklistItemImpl(
      id: json['id'] as String,
      text: json['text'] as String,
      owner: json['owner'] as String,
      sla: json['sla'] as String,
      completed: json['completed'] as bool,
    );

Map<String, dynamic> _$$ChecklistItemImplToJson(_$ChecklistItemImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'text': instance.text,
      'owner': instance.owner,
      'sla': instance.sla,
      'completed': instance.completed,
    };

_$ApprovalPayloadImpl _$$ApprovalPayloadImplFromJson(
        Map<String, dynamic> json) =>
    _$ApprovalPayloadImpl(
      selectedOpportunityIds: (json['selectedOpportunityIds'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
      diff: (json['diff'] as List<dynamic>)
          .map((e) => PayloadDiff.fromJson(e as Map<String, dynamic>))
          .toList(),
      rmCommitments: (json['rmCommitments'] as List<dynamic>)
          .map((e) => e as String)
          .toList(),
    );

Map<String, dynamic> _$$ApprovalPayloadImplToJson(
        _$ApprovalPayloadImpl instance) =>
    <String, dynamic>{
      'selectedOpportunityIds': instance.selectedOpportunityIds,
      'diff': instance.diff,
      'rmCommitments': instance.rmCommitments,
    };

_$PayloadDiffImpl _$$PayloadDiffImplFromJson(Map<String, dynamic> json) =>
    _$PayloadDiffImpl(
      object: json['object'] as String,
      action: json['action'] as String,
    );

Map<String, dynamic> _$$PayloadDiffImplToJson(_$PayloadDiffImpl instance) =>
    <String, dynamic>{
      'object': instance.object,
      'action': instance.action,
    };
