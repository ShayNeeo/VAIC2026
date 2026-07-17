// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'api_client.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ApprovalTokenResponseImpl _$$ApprovalTokenResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$ApprovalTokenResponseImpl(
      caseId: json['caseId'] as String,
      approvalToken: json['approvalToken'] as String,
      expiresIn: (json['expiresIn'] as num).toInt(),
    );

Map<String, dynamic> _$$ApprovalTokenResponseImplToJson(
        _$ApprovalTokenResponseImpl instance) =>
    <String, dynamic>{
      'caseId': instance.caseId,
      'approvalToken': instance.approvalToken,
      'expiresIn': instance.expiresIn,
    };

_$ApprovalResultImpl _$$ApprovalResultImplFromJson(Map<String, dynamic> json) =>
    _$ApprovalResultImpl(
      caseId: json['caseId'] as String,
      approvalStatus: json['approvalStatus'] as String,
      finalStatus: json['finalStatus'] as String,
      actionsExecuted: json['actionsExecuted'] as List<dynamic>,
    );

Map<String, dynamic> _$$ApprovalResultImplToJson(
        _$ApprovalResultImpl instance) =>
    <String, dynamic>{
      'caseId': instance.caseId,
      'approvalStatus': instance.approvalStatus,
      'finalStatus': instance.finalStatus,
      'actionsExecuted': instance.actionsExecuted,
    };

_$ProductSearchResultImpl _$$ProductSearchResultImplFromJson(
        Map<String, dynamic> json) =>
    _$ProductSearchResultImpl(
      results: (json['results'] as List<dynamic>)
          .map((e) => ProductMatch.fromJson(e as Map<String, dynamic>))
          .toList(),
    );

Map<String, dynamic> _$$ProductSearchResultImplToJson(
        _$ProductSearchResultImpl instance) =>
    <String, dynamic>{
      'results': instance.results,
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
