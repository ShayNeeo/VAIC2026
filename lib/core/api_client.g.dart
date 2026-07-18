// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_client.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ApprovalTokenResponseImpl _$$ApprovalTokenResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$ApprovalTokenResponseImpl(
      caseId: json['caseId'] as String,
      stateVersion: (json['stateVersion'] as num).toInt(),
      approvalToken: json['approvalToken'] as String,
      expiresAt: (json['expiresAt'] as num).toInt(),
    );

Map<String, dynamic> _$$ApprovalTokenResponseImplToJson(
        _$ApprovalTokenResponseImpl instance) =>
    <String, dynamic>{
      'caseId': instance.caseId,
      'stateVersion': instance.stateVersion,
      'approvalToken': instance.approvalToken,
      'expiresAt': instance.expiresAt,
    };

_$ApprovalResultImpl _$$ApprovalResultImplFromJson(Map<String, dynamic> json) =>
    _$ApprovalResultImpl(
      caseId: json['caseId'] as String,
      stateVersion: (json['stateVersion'] as num).toInt(),
      status: json['status'] as String,
      result: json['result'] as String,
    );

Map<String, dynamic> _$$ApprovalResultImplToJson(
        _$ApprovalResultImpl instance) =>
    <String, dynamic>{
      'caseId': instance.caseId,
      'stateVersion': instance.stateVersion,
      'status': instance.status,
      'result': instance.result,
    };

_$ApprovalPreviewImpl _$$ApprovalPreviewImplFromJson(
        Map<String, dynamic> json) =>
    _$ApprovalPreviewImpl(
      caseId: json['caseId'] as String,
      stateVersion: (json['stateVersion'] as num).toInt(),
      action: json['action'] as String,
      target: json['target'] as String,
      payloadHash: json['payloadHash'] as String,
      reversible: json['reversible'] as bool,
    );

Map<String, dynamic> _$$ApprovalPreviewImplToJson(
        _$ApprovalPreviewImpl instance) =>
    <String, dynamic>{
      'caseId': instance.caseId,
      'stateVersion': instance.stateVersion,
      'action': instance.action,
      'target': instance.target,
      'payloadHash': instance.payloadHash,
      'reversible': instance.reversible,
    };

_$ProductMatchImpl _$$ProductMatchImplFromJson(Map<String, dynamic> json) =>
    _$ProductMatchImpl(
      productId: json['productId'] as String,
      name: json['name'] as String,
      description: json['description'] as String,
      score: (json['score'] as num).toDouble(),
    );

Map<String, dynamic> _$$ProductMatchImplToJson(_$ProductMatchImpl instance) =>
    <String, dynamic>{
      'productId': instance.productId,
      'name': instance.name,
      'description': instance.description,
      'score': instance.score,
    };
