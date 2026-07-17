// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'case_models.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

CaseQueueItem _$CaseQueueItemFromJson(Map<String, dynamic> json) {
  return _CaseQueueItem.fromJson(json);
}

/// @nodoc
mixin _$CaseQueueItem {
  String get caseId => throw _privateConstructorUsedError;
  String get caseNumber => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  String get companyName => throw _privateConstructorUsedError;
  String get companyId => throw _privateConstructorUsedError;
  int get opportunityCount => throw _privateConstructorUsedError;
  Map<String, int> get branchStatusCounts =>
      throw _privateConstructorUsedError; // ready, need_info, review, blocked
  String get nextAction => throw _privateConstructorUsedError;
  String get sla => throw _privateConstructorUsedError;
  DateTime get updatedAt => throw _privateConstructorUsedError;

  /// Serializes this CaseQueueItem to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CaseQueueItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CaseQueueItemCopyWith<CaseQueueItem> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CaseQueueItemCopyWith<$Res> {
  factory $CaseQueueItemCopyWith(
          CaseQueueItem value, $Res Function(CaseQueueItem) then) =
      _$CaseQueueItemCopyWithImpl<$Res, CaseQueueItem>;
  @useResult
  $Res call(
      {String caseId,
      String caseNumber,
      String title,
      String status,
      String companyName,
      String companyId,
      int opportunityCount,
      Map<String, int> branchStatusCounts,
      String nextAction,
      String sla,
      DateTime updatedAt});
}

/// @nodoc
class _$CaseQueueItemCopyWithImpl<$Res, $Val extends CaseQueueItem>
    implements $CaseQueueItemCopyWith<$Res> {
  _$CaseQueueItemCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CaseQueueItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? caseId = null,
    Object? caseNumber = null,
    Object? title = null,
    Object? status = null,
    Object? companyName = null,
    Object? companyId = null,
    Object? opportunityCount = null,
    Object? branchStatusCounts = null,
    Object? nextAction = null,
    Object? sla = null,
    Object? updatedAt = null,
  }) {
    return _then(_value.copyWith(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      caseNumber: null == caseNumber
          ? _value.caseNumber
          : caseNumber // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      companyName: null == companyName
          ? _value.companyName
          : companyName // ignore: cast_nullable_to_non_nullable
              as String,
      companyId: null == companyId
          ? _value.companyId
          : companyId // ignore: cast_nullable_to_non_nullable
              as String,
      opportunityCount: null == opportunityCount
          ? _value.opportunityCount
          : opportunityCount // ignore: cast_nullable_to_non_nullable
              as int,
      branchStatusCounts: null == branchStatusCounts
          ? _value.branchStatusCounts
          : branchStatusCounts // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      nextAction: null == nextAction
          ? _value.nextAction
          : nextAction // ignore: cast_nullable_to_non_nullable
              as String,
      sla: null == sla
          ? _value.sla
          : sla // ignore: cast_nullable_to_non_nullable
              as String,
      updatedAt: null == updatedAt
          ? _value.updatedAt
          : updatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CaseQueueItemImplCopyWith<$Res>
    implements $CaseQueueItemCopyWith<$Res> {
  factory _$$CaseQueueItemImplCopyWith(
          _$CaseQueueItemImpl value, $Res Function(_$CaseQueueItemImpl) then) =
      __$$CaseQueueItemImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String caseId,
      String caseNumber,
      String title,
      String status,
      String companyName,
      String companyId,
      int opportunityCount,
      Map<String, int> branchStatusCounts,
      String nextAction,
      String sla,
      DateTime updatedAt});
}

/// @nodoc
class __$$CaseQueueItemImplCopyWithImpl<$Res>
    extends _$CaseQueueItemCopyWithImpl<$Res, _$CaseQueueItemImpl>
    implements _$$CaseQueueItemImplCopyWith<$Res> {
  __$$CaseQueueItemImplCopyWithImpl(
      _$CaseQueueItemImpl _value, $Res Function(_$CaseQueueItemImpl) _then)
      : super(_value, _then);

  /// Create a copy of CaseQueueItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? caseId = null,
    Object? caseNumber = null,
    Object? title = null,
    Object? status = null,
    Object? companyName = null,
    Object? companyId = null,
    Object? opportunityCount = null,
    Object? branchStatusCounts = null,
    Object? nextAction = null,
    Object? sla = null,
    Object? updatedAt = null,
  }) {
    return _then(_$CaseQueueItemImpl(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      caseNumber: null == caseNumber
          ? _value.caseNumber
          : caseNumber // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      companyName: null == companyName
          ? _value.companyName
          : companyName // ignore: cast_nullable_to_non_nullable
              as String,
      companyId: null == companyId
          ? _value.companyId
          : companyId // ignore: cast_nullable_to_non_nullable
              as String,
      opportunityCount: null == opportunityCount
          ? _value.opportunityCount
          : opportunityCount // ignore: cast_nullable_to_non_nullable
              as int,
      branchStatusCounts: null == branchStatusCounts
          ? _value._branchStatusCounts
          : branchStatusCounts // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
      nextAction: null == nextAction
          ? _value.nextAction
          : nextAction // ignore: cast_nullable_to_non_nullable
              as String,
      sla: null == sla
          ? _value.sla
          : sla // ignore: cast_nullable_to_non_nullable
              as String,
      updatedAt: null == updatedAt
          ? _value.updatedAt
          : updatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CaseQueueItemImpl implements _CaseQueueItem {
  const _$CaseQueueItemImpl(
      {required this.caseId,
      required this.caseNumber,
      required this.title,
      required this.status,
      required this.companyName,
      required this.companyId,
      required this.opportunityCount,
      required final Map<String, int> branchStatusCounts,
      required this.nextAction,
      required this.sla,
      required this.updatedAt})
      : _branchStatusCounts = branchStatusCounts;

  factory _$CaseQueueItemImpl.fromJson(Map<String, dynamic> json) =>
      _$$CaseQueueItemImplFromJson(json);

  @override
  final String caseId;
  @override
  final String caseNumber;
  @override
  final String title;
  @override
  final String status;
  @override
  final String companyName;
  @override
  final String companyId;
  @override
  final int opportunityCount;
  final Map<String, int> _branchStatusCounts;
  @override
  Map<String, int> get branchStatusCounts {
    if (_branchStatusCounts is EqualUnmodifiableMapView)
      return _branchStatusCounts;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_branchStatusCounts);
  }

// ready, need_info, review, blocked
  @override
  final String nextAction;
  @override
  final String sla;
  @override
  final DateTime updatedAt;

  @override
  String toString() {
    return 'CaseQueueItem(caseId: $caseId, caseNumber: $caseNumber, title: $title, status: $status, companyName: $companyName, companyId: $companyId, opportunityCount: $opportunityCount, branchStatusCounts: $branchStatusCounts, nextAction: $nextAction, sla: $sla, updatedAt: $updatedAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CaseQueueItemImpl &&
            (identical(other.caseId, caseId) || other.caseId == caseId) &&
            (identical(other.caseNumber, caseNumber) ||
                other.caseNumber == caseNumber) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.companyName, companyName) ||
                other.companyName == companyName) &&
            (identical(other.companyId, companyId) ||
                other.companyId == companyId) &&
            (identical(other.opportunityCount, opportunityCount) ||
                other.opportunityCount == opportunityCount) &&
            const DeepCollectionEquality()
                .equals(other._branchStatusCounts, _branchStatusCounts) &&
            (identical(other.nextAction, nextAction) ||
                other.nextAction == nextAction) &&
            (identical(other.sla, sla) || other.sla == sla) &&
            (identical(other.updatedAt, updatedAt) ||
                other.updatedAt == updatedAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      caseId,
      caseNumber,
      title,
      status,
      companyName,
      companyId,
      opportunityCount,
      const DeepCollectionEquality().hash(_branchStatusCounts),
      nextAction,
      sla,
      updatedAt);

  /// Create a copy of CaseQueueItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CaseQueueItemImplCopyWith<_$CaseQueueItemImpl> get copyWith =>
      __$$CaseQueueItemImplCopyWithImpl<_$CaseQueueItemImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CaseQueueItemImplToJson(
      this,
    );
  }
}

abstract class _CaseQueueItem implements CaseQueueItem {
  const factory _CaseQueueItem(
      {required final String caseId,
      required final String caseNumber,
      required final String title,
      required final String status,
      required final String companyName,
      required final String companyId,
      required final int opportunityCount,
      required final Map<String, int> branchStatusCounts,
      required final String nextAction,
      required final String sla,
      required final DateTime updatedAt}) = _$CaseQueueItemImpl;

  factory _CaseQueueItem.fromJson(Map<String, dynamic> json) =
      _$CaseQueueItemImpl.fromJson;

  @override
  String get caseId;
  @override
  String get caseNumber;
  @override
  String get title;
  @override
  String get status;
  @override
  String get companyName;
  @override
  String get companyId;
  @override
  int get opportunityCount;
  @override
  Map<String, int> get branchStatusCounts; // ready, need_info, review, blocked
  @override
  String get nextAction;
  @override
  String get sla;
  @override
  DateTime get updatedAt;

  /// Create a copy of CaseQueueItem
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CaseQueueItemImplCopyWith<_$CaseQueueItemImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CaseDetail _$CaseDetailFromJson(Map<String, dynamic> json) {
  return _CaseDetail.fromJson(json);
}

/// @nodoc
mixin _$CaseDetail {
  String get caseId => throw _privateConstructorUsedError;
  String get caseNumber => throw _privateConstructorUsedError;
  String get title => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get companyName => throw _privateConstructorUsedError;
  String get companyId => throw _privateConstructorUsedError;
  String get segment => throw _privateConstructorUsedError;
  String get industry => throw _privateConstructorUsedError;
  String get rmId => throw _privateConstructorUsedError;
  String get rmName => throw _privateConstructorUsedError;
  DateTime get updatedAt => throw _privateConstructorUsedError;
  List<NeedFact> get needFacts => throw _privateConstructorUsedError;
  List<OpportunityCard> get opportunities => throw _privateConstructorUsedError;
  List<MissingDocument> get missingDocuments =>
      throw _privateConstructorUsedError;
  List<EvidenceRef> get evidence => throw _privateConstructorUsedError;
  String get emailDraft => throw _privateConstructorUsedError;
  List<ChecklistItem> get checklist => throw _privateConstructorUsedError;

  /// Serializes this CaseDetail to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CaseDetail
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CaseDetailCopyWith<CaseDetail> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CaseDetailCopyWith<$Res> {
  factory $CaseDetailCopyWith(
          CaseDetail value, $Res Function(CaseDetail) then) =
      _$CaseDetailCopyWithImpl<$Res, CaseDetail>;
  @useResult
  $Res call(
      {String caseId,
      String caseNumber,
      String title,
      String description,
      String companyName,
      String companyId,
      String segment,
      String industry,
      String rmId,
      String rmName,
      DateTime updatedAt,
      List<NeedFact> needFacts,
      List<OpportunityCard> opportunities,
      List<MissingDocument> missingDocuments,
      List<EvidenceRef> evidence,
      String emailDraft,
      List<ChecklistItem> checklist});
}

/// @nodoc
class _$CaseDetailCopyWithImpl<$Res, $Val extends CaseDetail>
    implements $CaseDetailCopyWith<$Res> {
  _$CaseDetailCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CaseDetail
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? caseId = null,
    Object? caseNumber = null,
    Object? title = null,
    Object? description = null,
    Object? companyName = null,
    Object? companyId = null,
    Object? segment = null,
    Object? industry = null,
    Object? rmId = null,
    Object? rmName = null,
    Object? updatedAt = null,
    Object? needFacts = null,
    Object? opportunities = null,
    Object? missingDocuments = null,
    Object? evidence = null,
    Object? emailDraft = null,
    Object? checklist = null,
  }) {
    return _then(_value.copyWith(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      caseNumber: null == caseNumber
          ? _value.caseNumber
          : caseNumber // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      companyName: null == companyName
          ? _value.companyName
          : companyName // ignore: cast_nullable_to_non_nullable
              as String,
      companyId: null == companyId
          ? _value.companyId
          : companyId // ignore: cast_nullable_to_non_nullable
              as String,
      segment: null == segment
          ? _value.segment
          : segment // ignore: cast_nullable_to_non_nullable
              as String,
      industry: null == industry
          ? _value.industry
          : industry // ignore: cast_nullable_to_non_nullable
              as String,
      rmId: null == rmId
          ? _value.rmId
          : rmId // ignore: cast_nullable_to_non_nullable
              as String,
      rmName: null == rmName
          ? _value.rmName
          : rmName // ignore: cast_nullable_to_non_nullable
              as String,
      updatedAt: null == updatedAt
          ? _value.updatedAt
          : updatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      needFacts: null == needFacts
          ? _value.needFacts
          : needFacts // ignore: cast_nullable_to_non_nullable
              as List<NeedFact>,
      opportunities: null == opportunities
          ? _value.opportunities
          : opportunities // ignore: cast_nullable_to_non_nullable
              as List<OpportunityCard>,
      missingDocuments: null == missingDocuments
          ? _value.missingDocuments
          : missingDocuments // ignore: cast_nullable_to_non_nullable
              as List<MissingDocument>,
      evidence: null == evidence
          ? _value.evidence
          : evidence // ignore: cast_nullable_to_non_nullable
              as List<EvidenceRef>,
      emailDraft: null == emailDraft
          ? _value.emailDraft
          : emailDraft // ignore: cast_nullable_to_non_nullable
              as String,
      checklist: null == checklist
          ? _value.checklist
          : checklist // ignore: cast_nullable_to_non_nullable
              as List<ChecklistItem>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CaseDetailImplCopyWith<$Res>
    implements $CaseDetailCopyWith<$Res> {
  factory _$$CaseDetailImplCopyWith(
          _$CaseDetailImpl value, $Res Function(_$CaseDetailImpl) then) =
      __$$CaseDetailImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String caseId,
      String caseNumber,
      String title,
      String description,
      String companyName,
      String companyId,
      String segment,
      String industry,
      String rmId,
      String rmName,
      DateTime updatedAt,
      List<NeedFact> needFacts,
      List<OpportunityCard> opportunities,
      List<MissingDocument> missingDocuments,
      List<EvidenceRef> evidence,
      String emailDraft,
      List<ChecklistItem> checklist});
}

/// @nodoc
class __$$CaseDetailImplCopyWithImpl<$Res>
    extends _$CaseDetailCopyWithImpl<$Res, _$CaseDetailImpl>
    implements _$$CaseDetailImplCopyWith<$Res> {
  __$$CaseDetailImplCopyWithImpl(
      _$CaseDetailImpl _value, $Res Function(_$CaseDetailImpl) _then)
      : super(_value, _then);

  /// Create a copy of CaseDetail
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? caseId = null,
    Object? caseNumber = null,
    Object? title = null,
    Object? description = null,
    Object? companyName = null,
    Object? companyId = null,
    Object? segment = null,
    Object? industry = null,
    Object? rmId = null,
    Object? rmName = null,
    Object? updatedAt = null,
    Object? needFacts = null,
    Object? opportunities = null,
    Object? missingDocuments = null,
    Object? evidence = null,
    Object? emailDraft = null,
    Object? checklist = null,
  }) {
    return _then(_$CaseDetailImpl(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      caseNumber: null == caseNumber
          ? _value.caseNumber
          : caseNumber // ignore: cast_nullable_to_non_nullable
              as String,
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      companyName: null == companyName
          ? _value.companyName
          : companyName // ignore: cast_nullable_to_non_nullable
              as String,
      companyId: null == companyId
          ? _value.companyId
          : companyId // ignore: cast_nullable_to_non_nullable
              as String,
      segment: null == segment
          ? _value.segment
          : segment // ignore: cast_nullable_to_non_nullable
              as String,
      industry: null == industry
          ? _value.industry
          : industry // ignore: cast_nullable_to_non_nullable
              as String,
      rmId: null == rmId
          ? _value.rmId
          : rmId // ignore: cast_nullable_to_non_nullable
              as String,
      rmName: null == rmName
          ? _value.rmName
          : rmName // ignore: cast_nullable_to_non_nullable
              as String,
      updatedAt: null == updatedAt
          ? _value.updatedAt
          : updatedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      needFacts: null == needFacts
          ? _value._needFacts
          : needFacts // ignore: cast_nullable_to_non_nullable
              as List<NeedFact>,
      opportunities: null == opportunities
          ? _value._opportunities
          : opportunities // ignore: cast_nullable_to_non_nullable
              as List<OpportunityCard>,
      missingDocuments: null == missingDocuments
          ? _value._missingDocuments
          : missingDocuments // ignore: cast_nullable_to_non_nullable
              as List<MissingDocument>,
      evidence: null == evidence
          ? _value._evidence
          : evidence // ignore: cast_nullable_to_non_nullable
              as List<EvidenceRef>,
      emailDraft: null == emailDraft
          ? _value.emailDraft
          : emailDraft // ignore: cast_nullable_to_non_nullable
              as String,
      checklist: null == checklist
          ? _value._checklist
          : checklist // ignore: cast_nullable_to_non_nullable
              as List<ChecklistItem>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CaseDetailImpl implements _CaseDetail {
  const _$CaseDetailImpl(
      {required this.caseId,
      required this.caseNumber,
      required this.title,
      required this.description,
      required this.companyName,
      required this.companyId,
      required this.segment,
      required this.industry,
      required this.rmId,
      required this.rmName,
      required this.updatedAt,
      required final List<NeedFact> needFacts,
      required final List<OpportunityCard> opportunities,
      required final List<MissingDocument> missingDocuments,
      required final List<EvidenceRef> evidence,
      required this.emailDraft,
      required final List<ChecklistItem> checklist})
      : _needFacts = needFacts,
        _opportunities = opportunities,
        _missingDocuments = missingDocuments,
        _evidence = evidence,
        _checklist = checklist;

  factory _$CaseDetailImpl.fromJson(Map<String, dynamic> json) =>
      _$$CaseDetailImplFromJson(json);

  @override
  final String caseId;
  @override
  final String caseNumber;
  @override
  final String title;
  @override
  final String description;
  @override
  final String companyName;
  @override
  final String companyId;
  @override
  final String segment;
  @override
  final String industry;
  @override
  final String rmId;
  @override
  final String rmName;
  @override
  final DateTime updatedAt;
  final List<NeedFact> _needFacts;
  @override
  List<NeedFact> get needFacts {
    if (_needFacts is EqualUnmodifiableListView) return _needFacts;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_needFacts);
  }

  final List<OpportunityCard> _opportunities;
  @override
  List<OpportunityCard> get opportunities {
    if (_opportunities is EqualUnmodifiableListView) return _opportunities;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_opportunities);
  }

  final List<MissingDocument> _missingDocuments;
  @override
  List<MissingDocument> get missingDocuments {
    if (_missingDocuments is EqualUnmodifiableListView)
      return _missingDocuments;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_missingDocuments);
  }

  final List<EvidenceRef> _evidence;
  @override
  List<EvidenceRef> get evidence {
    if (_evidence is EqualUnmodifiableListView) return _evidence;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_evidence);
  }

  @override
  final String emailDraft;
  final List<ChecklistItem> _checklist;
  @override
  List<ChecklistItem> get checklist {
    if (_checklist is EqualUnmodifiableListView) return _checklist;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_checklist);
  }

  @override
  String toString() {
    return 'CaseDetail(caseId: $caseId, caseNumber: $caseNumber, title: $title, description: $description, companyName: $companyName, companyId: $companyId, segment: $segment, industry: $industry, rmId: $rmId, rmName: $rmName, updatedAt: $updatedAt, needFacts: $needFacts, opportunities: $opportunities, missingDocuments: $missingDocuments, evidence: $evidence, emailDraft: $emailDraft, checklist: $checklist)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CaseDetailImpl &&
            (identical(other.caseId, caseId) || other.caseId == caseId) &&
            (identical(other.caseNumber, caseNumber) ||
                other.caseNumber == caseNumber) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.companyName, companyName) ||
                other.companyName == companyName) &&
            (identical(other.companyId, companyId) ||
                other.companyId == companyId) &&
            (identical(other.segment, segment) || other.segment == segment) &&
            (identical(other.industry, industry) ||
                other.industry == industry) &&
            (identical(other.rmId, rmId) || other.rmId == rmId) &&
            (identical(other.rmName, rmName) || other.rmName == rmName) &&
            (identical(other.updatedAt, updatedAt) ||
                other.updatedAt == updatedAt) &&
            const DeepCollectionEquality()
                .equals(other._needFacts, _needFacts) &&
            const DeepCollectionEquality()
                .equals(other._opportunities, _opportunities) &&
            const DeepCollectionEquality()
                .equals(other._missingDocuments, _missingDocuments) &&
            const DeepCollectionEquality().equals(other._evidence, _evidence) &&
            (identical(other.emailDraft, emailDraft) ||
                other.emailDraft == emailDraft) &&
            const DeepCollectionEquality()
                .equals(other._checklist, _checklist));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      caseId,
      caseNumber,
      title,
      description,
      companyName,
      companyId,
      segment,
      industry,
      rmId,
      rmName,
      updatedAt,
      const DeepCollectionEquality().hash(_needFacts),
      const DeepCollectionEquality().hash(_opportunities),
      const DeepCollectionEquality().hash(_missingDocuments),
      const DeepCollectionEquality().hash(_evidence),
      emailDraft,
      const DeepCollectionEquality().hash(_checklist));

  /// Create a copy of CaseDetail
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CaseDetailImplCopyWith<_$CaseDetailImpl> get copyWith =>
      __$$CaseDetailImplCopyWithImpl<_$CaseDetailImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CaseDetailImplToJson(
      this,
    );
  }
}

abstract class _CaseDetail implements CaseDetail {
  const factory _CaseDetail(
      {required final String caseId,
      required final String caseNumber,
      required final String title,
      required final String description,
      required final String companyName,
      required final String companyId,
      required final String segment,
      required final String industry,
      required final String rmId,
      required final String rmName,
      required final DateTime updatedAt,
      required final List<NeedFact> needFacts,
      required final List<OpportunityCard> opportunities,
      required final List<MissingDocument> missingDocuments,
      required final List<EvidenceRef> evidence,
      required final String emailDraft,
      required final List<ChecklistItem> checklist}) = _$CaseDetailImpl;

  factory _CaseDetail.fromJson(Map<String, dynamic> json) =
      _$CaseDetailImpl.fromJson;

  @override
  String get caseId;
  @override
  String get caseNumber;
  @override
  String get title;
  @override
  String get description;
  @override
  String get companyName;
  @override
  String get companyId;
  @override
  String get segment;
  @override
  String get industry;
  @override
  String get rmId;
  @override
  String get rmName;
  @override
  DateTime get updatedAt;
  @override
  List<NeedFact> get needFacts;
  @override
  List<OpportunityCard> get opportunities;
  @override
  List<MissingDocument> get missingDocuments;
  @override
  List<EvidenceRef> get evidence;
  @override
  String get emailDraft;
  @override
  List<ChecklistItem> get checklist;

  /// Create a copy of CaseDetail
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CaseDetailImplCopyWith<_$CaseDetailImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

NeedFact _$NeedFactFromJson(Map<String, dynamic> json) {
  return _NeedFact.fromJson(json);
}

/// @nodoc
mixin _$NeedFact {
  String get field => throw _privateConstructorUsedError;
  String get value => throw _privateConstructorUsedError;
  String get source =>
      throw _privateConstructorUsedError; // CRM / RM note / AI inference
  double get confidence => throw _privateConstructorUsedError; // 0-1
  bool get confirmed => throw _privateConstructorUsedError; // RM confirmed
  DateTime get freshness => throw _privateConstructorUsedError;

  /// Serializes this NeedFact to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of NeedFact
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $NeedFactCopyWith<NeedFact> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $NeedFactCopyWith<$Res> {
  factory $NeedFactCopyWith(NeedFact value, $Res Function(NeedFact) then) =
      _$NeedFactCopyWithImpl<$Res, NeedFact>;
  @useResult
  $Res call(
      {String field,
      String value,
      String source,
      double confidence,
      bool confirmed,
      DateTime freshness});
}

/// @nodoc
class _$NeedFactCopyWithImpl<$Res, $Val extends NeedFact>
    implements $NeedFactCopyWith<$Res> {
  _$NeedFactCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of NeedFact
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? field = null,
    Object? value = null,
    Object? source = null,
    Object? confidence = null,
    Object? confirmed = null,
    Object? freshness = null,
  }) {
    return _then(_value.copyWith(
      field: null == field
          ? _value.field
          : field // ignore: cast_nullable_to_non_nullable
              as String,
      value: null == value
          ? _value.value
          : value // ignore: cast_nullable_to_non_nullable
              as String,
      source: null == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as String,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      confirmed: null == confirmed
          ? _value.confirmed
          : confirmed // ignore: cast_nullable_to_non_nullable
              as bool,
      freshness: null == freshness
          ? _value.freshness
          : freshness // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$NeedFactImplCopyWith<$Res>
    implements $NeedFactCopyWith<$Res> {
  factory _$$NeedFactImplCopyWith(
          _$NeedFactImpl value, $Res Function(_$NeedFactImpl) then) =
      __$$NeedFactImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String field,
      String value,
      String source,
      double confidence,
      bool confirmed,
      DateTime freshness});
}

/// @nodoc
class __$$NeedFactImplCopyWithImpl<$Res>
    extends _$NeedFactCopyWithImpl<$Res, _$NeedFactImpl>
    implements _$$NeedFactImplCopyWith<$Res> {
  __$$NeedFactImplCopyWithImpl(
      _$NeedFactImpl _value, $Res Function(_$NeedFactImpl) _then)
      : super(_value, _then);

  /// Create a copy of NeedFact
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? field = null,
    Object? value = null,
    Object? source = null,
    Object? confidence = null,
    Object? confirmed = null,
    Object? freshness = null,
  }) {
    return _then(_$NeedFactImpl(
      field: null == field
          ? _value.field
          : field // ignore: cast_nullable_to_non_nullable
              as String,
      value: null == value
          ? _value.value
          : value // ignore: cast_nullable_to_non_nullable
              as String,
      source: null == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as String,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      confirmed: null == confirmed
          ? _value.confirmed
          : confirmed // ignore: cast_nullable_to_non_nullable
              as bool,
      freshness: null == freshness
          ? _value.freshness
          : freshness // ignore: cast_nullable_to_non_nullable
              as DateTime,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$NeedFactImpl implements _NeedFact {
  const _$NeedFactImpl(
      {required this.field,
      required this.value,
      required this.source,
      required this.confidence,
      required this.confirmed,
      required this.freshness});

  factory _$NeedFactImpl.fromJson(Map<String, dynamic> json) =>
      _$$NeedFactImplFromJson(json);

  @override
  final String field;
  @override
  final String value;
  @override
  final String source;
// CRM / RM note / AI inference
  @override
  final double confidence;
// 0-1
  @override
  final bool confirmed;
// RM confirmed
  @override
  final DateTime freshness;

  @override
  String toString() {
    return 'NeedFact(field: $field, value: $value, source: $source, confidence: $confidence, confirmed: $confirmed, freshness: $freshness)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$NeedFactImpl &&
            (identical(other.field, field) || other.field == field) &&
            (identical(other.value, value) || other.value == value) &&
            (identical(other.source, source) || other.source == source) &&
            (identical(other.confidence, confidence) ||
                other.confidence == confidence) &&
            (identical(other.confirmed, confirmed) ||
                other.confirmed == confirmed) &&
            (identical(other.freshness, freshness) ||
                other.freshness == freshness));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, field, value, source, confidence, confirmed, freshness);

  /// Create a copy of NeedFact
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$NeedFactImplCopyWith<_$NeedFactImpl> get copyWith =>
      __$$NeedFactImplCopyWithImpl<_$NeedFactImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$NeedFactImplToJson(
      this,
    );
  }
}

abstract class _NeedFact implements NeedFact {
  const factory _NeedFact(
      {required final String field,
      required final String value,
      required final String source,
      required final double confidence,
      required final bool confirmed,
      required final DateTime freshness}) = _$NeedFactImpl;

  factory _NeedFact.fromJson(Map<String, dynamic> json) =
      _$NeedFactImpl.fromJson;

  @override
  String get field;
  @override
  String get value;
  @override
  String get source; // CRM / RM note / AI inference
  @override
  double get confidence; // 0-1
  @override
  bool get confirmed; // RM confirmed
  @override
  DateTime get freshness;

  /// Create a copy of NeedFact
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$NeedFactImplCopyWith<_$NeedFactImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

OpportunityCard _$OpportunityCardFromJson(Map<String, dynamic> json) {
  return _OpportunityCard.fromJson(json);
}

/// @nodoc
mixin _$OpportunityCard {
  String get opportunityId => throw _privateConstructorUsedError;
  String get product => throw _privateConstructorUsedError;
  String get productId => throw _privateConstructorUsedError;
  String get customer => throw _privateConstructorUsedError;
  String get caseId => throw _privateConstructorUsedError;
  OpportunityStatus get status => throw _privateConstructorUsedError;
  String get businessNeed => throw _privateConstructorUsedError;
  List<Signal> get signals => throw _privateConstructorUsedError;
  List<String> get productFit => throw _privateConstructorUsedError;
  List<EvidenceRef> get evidence => throw _privateConstructorUsedError;
  List<String> get missingInfo => throw _privateConstructorUsedError;
  List<String> get risk => throw _privateConstructorUsedError;
  String get nextBestAction => throw _privateConstructorUsedError;
  String get owner => throw _privateConstructorUsedError;
  String get sla => throw _privateConstructorUsedError;
  String get expectedOutcome => throw _privateConstructorUsedError;

  /// Serializes this OpportunityCard to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of OpportunityCard
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $OpportunityCardCopyWith<OpportunityCard> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $OpportunityCardCopyWith<$Res> {
  factory $OpportunityCardCopyWith(
          OpportunityCard value, $Res Function(OpportunityCard) then) =
      _$OpportunityCardCopyWithImpl<$Res, OpportunityCard>;
  @useResult
  $Res call(
      {String opportunityId,
      String product,
      String productId,
      String customer,
      String caseId,
      OpportunityStatus status,
      String businessNeed,
      List<Signal> signals,
      List<String> productFit,
      List<EvidenceRef> evidence,
      List<String> missingInfo,
      List<String> risk,
      String nextBestAction,
      String owner,
      String sla,
      String expectedOutcome});
}

/// @nodoc
class _$OpportunityCardCopyWithImpl<$Res, $Val extends OpportunityCard>
    implements $OpportunityCardCopyWith<$Res> {
  _$OpportunityCardCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of OpportunityCard
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? opportunityId = null,
    Object? product = null,
    Object? productId = null,
    Object? customer = null,
    Object? caseId = null,
    Object? status = null,
    Object? businessNeed = null,
    Object? signals = null,
    Object? productFit = null,
    Object? evidence = null,
    Object? missingInfo = null,
    Object? risk = null,
    Object? nextBestAction = null,
    Object? owner = null,
    Object? sla = null,
    Object? expectedOutcome = null,
  }) {
    return _then(_value.copyWith(
      opportunityId: null == opportunityId
          ? _value.opportunityId
          : opportunityId // ignore: cast_nullable_to_non_nullable
              as String,
      product: null == product
          ? _value.product
          : product // ignore: cast_nullable_to_non_nullable
              as String,
      productId: null == productId
          ? _value.productId
          : productId // ignore: cast_nullable_to_non_nullable
              as String,
      customer: null == customer
          ? _value.customer
          : customer // ignore: cast_nullable_to_non_nullable
              as String,
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as OpportunityStatus,
      businessNeed: null == businessNeed
          ? _value.businessNeed
          : businessNeed // ignore: cast_nullable_to_non_nullable
              as String,
      signals: null == signals
          ? _value.signals
          : signals // ignore: cast_nullable_to_non_nullable
              as List<Signal>,
      productFit: null == productFit
          ? _value.productFit
          : productFit // ignore: cast_nullable_to_non_nullable
              as List<String>,
      evidence: null == evidence
          ? _value.evidence
          : evidence // ignore: cast_nullable_to_non_nullable
              as List<EvidenceRef>,
      missingInfo: null == missingInfo
          ? _value.missingInfo
          : missingInfo // ignore: cast_nullable_to_non_nullable
              as List<String>,
      risk: null == risk
          ? _value.risk
          : risk // ignore: cast_nullable_to_non_nullable
              as List<String>,
      nextBestAction: null == nextBestAction
          ? _value.nextBestAction
          : nextBestAction // ignore: cast_nullable_to_non_nullable
              as String,
      owner: null == owner
          ? _value.owner
          : owner // ignore: cast_nullable_to_non_nullable
              as String,
      sla: null == sla
          ? _value.sla
          : sla // ignore: cast_nullable_to_non_nullable
              as String,
      expectedOutcome: null == expectedOutcome
          ? _value.expectedOutcome
          : expectedOutcome // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$OpportunityCardImplCopyWith<$Res>
    implements $OpportunityCardCopyWith<$Res> {
  factory _$$OpportunityCardImplCopyWith(_$OpportunityCardImpl value,
          $Res Function(_$OpportunityCardImpl) then) =
      __$$OpportunityCardImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String opportunityId,
      String product,
      String productId,
      String customer,
      String caseId,
      OpportunityStatus status,
      String businessNeed,
      List<Signal> signals,
      List<String> productFit,
      List<EvidenceRef> evidence,
      List<String> missingInfo,
      List<String> risk,
      String nextBestAction,
      String owner,
      String sla,
      String expectedOutcome});
}

/// @nodoc
class __$$OpportunityCardImplCopyWithImpl<$Res>
    extends _$OpportunityCardCopyWithImpl<$Res, _$OpportunityCardImpl>
    implements _$$OpportunityCardImplCopyWith<$Res> {
  __$$OpportunityCardImplCopyWithImpl(
      _$OpportunityCardImpl _value, $Res Function(_$OpportunityCardImpl) _then)
      : super(_value, _then);

  /// Create a copy of OpportunityCard
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? opportunityId = null,
    Object? product = null,
    Object? productId = null,
    Object? customer = null,
    Object? caseId = null,
    Object? status = null,
    Object? businessNeed = null,
    Object? signals = null,
    Object? productFit = null,
    Object? evidence = null,
    Object? missingInfo = null,
    Object? risk = null,
    Object? nextBestAction = null,
    Object? owner = null,
    Object? sla = null,
    Object? expectedOutcome = null,
  }) {
    return _then(_$OpportunityCardImpl(
      opportunityId: null == opportunityId
          ? _value.opportunityId
          : opportunityId // ignore: cast_nullable_to_non_nullable
              as String,
      product: null == product
          ? _value.product
          : product // ignore: cast_nullable_to_non_nullable
              as String,
      productId: null == productId
          ? _value.productId
          : productId // ignore: cast_nullable_to_non_nullable
              as String,
      customer: null == customer
          ? _value.customer
          : customer // ignore: cast_nullable_to_non_nullable
              as String,
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as OpportunityStatus,
      businessNeed: null == businessNeed
          ? _value.businessNeed
          : businessNeed // ignore: cast_nullable_to_non_nullable
              as String,
      signals: null == signals
          ? _value._signals
          : signals // ignore: cast_nullable_to_non_nullable
              as List<Signal>,
      productFit: null == productFit
          ? _value._productFit
          : productFit // ignore: cast_nullable_to_non_nullable
              as List<String>,
      evidence: null == evidence
          ? _value._evidence
          : evidence // ignore: cast_nullable_to_non_nullable
              as List<EvidenceRef>,
      missingInfo: null == missingInfo
          ? _value._missingInfo
          : missingInfo // ignore: cast_nullable_to_non_nullable
              as List<String>,
      risk: null == risk
          ? _value._risk
          : risk // ignore: cast_nullable_to_non_nullable
              as List<String>,
      nextBestAction: null == nextBestAction
          ? _value.nextBestAction
          : nextBestAction // ignore: cast_nullable_to_non_nullable
              as String,
      owner: null == owner
          ? _value.owner
          : owner // ignore: cast_nullable_to_non_nullable
              as String,
      sla: null == sla
          ? _value.sla
          : sla // ignore: cast_nullable_to_non_nullable
              as String,
      expectedOutcome: null == expectedOutcome
          ? _value.expectedOutcome
          : expectedOutcome // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$OpportunityCardImpl implements _OpportunityCard {
  const _$OpportunityCardImpl(
      {required this.opportunityId,
      required this.product,
      required this.productId,
      required this.customer,
      required this.caseId,
      required this.status,
      required this.businessNeed,
      required final List<Signal> signals,
      required final List<String> productFit,
      required final List<EvidenceRef> evidence,
      required final List<String> missingInfo,
      required final List<String> risk,
      required this.nextBestAction,
      required this.owner,
      required this.sla,
      required this.expectedOutcome})
      : _signals = signals,
        _productFit = productFit,
        _evidence = evidence,
        _missingInfo = missingInfo,
        _risk = risk;

  factory _$OpportunityCardImpl.fromJson(Map<String, dynamic> json) =>
      _$$OpportunityCardImplFromJson(json);

  @override
  final String opportunityId;
  @override
  final String product;
  @override
  final String productId;
  @override
  final String customer;
  @override
  final String caseId;
  @override
  final OpportunityStatus status;
  @override
  final String businessNeed;
  final List<Signal> _signals;
  @override
  List<Signal> get signals {
    if (_signals is EqualUnmodifiableListView) return _signals;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_signals);
  }

  final List<String> _productFit;
  @override
  List<String> get productFit {
    if (_productFit is EqualUnmodifiableListView) return _productFit;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_productFit);
  }

  final List<EvidenceRef> _evidence;
  @override
  List<EvidenceRef> get evidence {
    if (_evidence is EqualUnmodifiableListView) return _evidence;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_evidence);
  }

  final List<String> _missingInfo;
  @override
  List<String> get missingInfo {
    if (_missingInfo is EqualUnmodifiableListView) return _missingInfo;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_missingInfo);
  }

  final List<String> _risk;
  @override
  List<String> get risk {
    if (_risk is EqualUnmodifiableListView) return _risk;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_risk);
  }

  @override
  final String nextBestAction;
  @override
  final String owner;
  @override
  final String sla;
  @override
  final String expectedOutcome;

  @override
  String toString() {
    return 'OpportunityCard(opportunityId: $opportunityId, product: $product, productId: $productId, customer: $customer, caseId: $caseId, status: $status, businessNeed: $businessNeed, signals: $signals, productFit: $productFit, evidence: $evidence, missingInfo: $missingInfo, risk: $risk, nextBestAction: $nextBestAction, owner: $owner, sla: $sla, expectedOutcome: $expectedOutcome)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$OpportunityCardImpl &&
            (identical(other.opportunityId, opportunityId) ||
                other.opportunityId == opportunityId) &&
            (identical(other.product, product) || other.product == product) &&
            (identical(other.productId, productId) ||
                other.productId == productId) &&
            (identical(other.customer, customer) ||
                other.customer == customer) &&
            (identical(other.caseId, caseId) || other.caseId == caseId) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.businessNeed, businessNeed) ||
                other.businessNeed == businessNeed) &&
            const DeepCollectionEquality().equals(other._signals, _signals) &&
            const DeepCollectionEquality()
                .equals(other._productFit, _productFit) &&
            const DeepCollectionEquality().equals(other._evidence, _evidence) &&
            const DeepCollectionEquality()
                .equals(other._missingInfo, _missingInfo) &&
            const DeepCollectionEquality().equals(other._risk, _risk) &&
            (identical(other.nextBestAction, nextBestAction) ||
                other.nextBestAction == nextBestAction) &&
            (identical(other.owner, owner) || other.owner == owner) &&
            (identical(other.sla, sla) || other.sla == sla) &&
            (identical(other.expectedOutcome, expectedOutcome) ||
                other.expectedOutcome == expectedOutcome));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      opportunityId,
      product,
      productId,
      customer,
      caseId,
      status,
      businessNeed,
      const DeepCollectionEquality().hash(_signals),
      const DeepCollectionEquality().hash(_productFit),
      const DeepCollectionEquality().hash(_evidence),
      const DeepCollectionEquality().hash(_missingInfo),
      const DeepCollectionEquality().hash(_risk),
      nextBestAction,
      owner,
      sla,
      expectedOutcome);

  /// Create a copy of OpportunityCard
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$OpportunityCardImplCopyWith<_$OpportunityCardImpl> get copyWith =>
      __$$OpportunityCardImplCopyWithImpl<_$OpportunityCardImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$OpportunityCardImplToJson(
      this,
    );
  }
}

abstract class _OpportunityCard implements OpportunityCard {
  const factory _OpportunityCard(
      {required final String opportunityId,
      required final String product,
      required final String productId,
      required final String customer,
      required final String caseId,
      required final OpportunityStatus status,
      required final String businessNeed,
      required final List<Signal> signals,
      required final List<String> productFit,
      required final List<EvidenceRef> evidence,
      required final List<String> missingInfo,
      required final List<String> risk,
      required final String nextBestAction,
      required final String owner,
      required final String sla,
      required final String expectedOutcome}) = _$OpportunityCardImpl;

  factory _OpportunityCard.fromJson(Map<String, dynamic> json) =
      _$OpportunityCardImpl.fromJson;

  @override
  String get opportunityId;
  @override
  String get product;
  @override
  String get productId;
  @override
  String get customer;
  @override
  String get caseId;
  @override
  OpportunityStatus get status;
  @override
  String get businessNeed;
  @override
  List<Signal> get signals;
  @override
  List<String> get productFit;
  @override
  List<EvidenceRef> get evidence;
  @override
  List<String> get missingInfo;
  @override
  List<String> get risk;
  @override
  String get nextBestAction;
  @override
  String get owner;
  @override
  String get sla;
  @override
  String get expectedOutcome;

  /// Create a copy of OpportunityCard
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$OpportunityCardImplCopyWith<_$OpportunityCardImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

Signal _$SignalFromJson(Map<String, dynamic> json) {
  return _Signal.fromJson(json);
}

/// @nodoc
mixin _$Signal {
  String get fact => throw _privateConstructorUsedError;
  String get source => throw _privateConstructorUsedError;
  double get strength => throw _privateConstructorUsedError;

  /// Serializes this Signal to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of Signal
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $SignalCopyWith<Signal> get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SignalCopyWith<$Res> {
  factory $SignalCopyWith(Signal value, $Res Function(Signal) then) =
      _$SignalCopyWithImpl<$Res, Signal>;
  @useResult
  $Res call({String fact, String source, double strength});
}

/// @nodoc
class _$SignalCopyWithImpl<$Res, $Val extends Signal>
    implements $SignalCopyWith<$Res> {
  _$SignalCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of Signal
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? fact = null,
    Object? source = null,
    Object? strength = null,
  }) {
    return _then(_value.copyWith(
      fact: null == fact
          ? _value.fact
          : fact // ignore: cast_nullable_to_non_nullable
              as String,
      source: null == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as String,
      strength: null == strength
          ? _value.strength
          : strength // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SignalImplCopyWith<$Res> implements $SignalCopyWith<$Res> {
  factory _$$SignalImplCopyWith(
          _$SignalImpl value, $Res Function(_$SignalImpl) then) =
      __$$SignalImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String fact, String source, double strength});
}

/// @nodoc
class __$$SignalImplCopyWithImpl<$Res>
    extends _$SignalCopyWithImpl<$Res, _$SignalImpl>
    implements _$$SignalImplCopyWith<$Res> {
  __$$SignalImplCopyWithImpl(
      _$SignalImpl _value, $Res Function(_$SignalImpl) _then)
      : super(_value, _then);

  /// Create a copy of Signal
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? fact = null,
    Object? source = null,
    Object? strength = null,
  }) {
    return _then(_$SignalImpl(
      fact: null == fact
          ? _value.fact
          : fact // ignore: cast_nullable_to_non_nullable
              as String,
      source: null == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as String,
      strength: null == strength
          ? _value.strength
          : strength // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$SignalImpl implements _Signal {
  const _$SignalImpl(
      {required this.fact, required this.source, required this.strength});

  factory _$SignalImpl.fromJson(Map<String, dynamic> json) =>
      _$$SignalImplFromJson(json);

  @override
  final String fact;
  @override
  final String source;
  @override
  final double strength;

  @override
  String toString() {
    return 'Signal(fact: $fact, source: $source, strength: $strength)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SignalImpl &&
            (identical(other.fact, fact) || other.fact == fact) &&
            (identical(other.source, source) || other.source == source) &&
            (identical(other.strength, strength) ||
                other.strength == strength));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, fact, source, strength);

  /// Create a copy of Signal
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$SignalImplCopyWith<_$SignalImpl> get copyWith =>
      __$$SignalImplCopyWithImpl<_$SignalImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$SignalImplToJson(
      this,
    );
  }
}

abstract class _Signal implements Signal {
  const factory _Signal(
      {required final String fact,
      required final String source,
      required final double strength}) = _$SignalImpl;

  factory _Signal.fromJson(Map<String, dynamic> json) = _$SignalImpl.fromJson;

  @override
  String get fact;
  @override
  String get source;
  @override
  double get strength;

  /// Create a copy of Signal
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$SignalImplCopyWith<_$SignalImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

EvidenceRef _$EvidenceRefFromJson(Map<String, dynamic> json) {
  return _EvidenceRef.fromJson(json);
}

/// @nodoc
mixin _$EvidenceRef {
  String get id => throw _privateConstructorUsedError;
  String get document => throw _privateConstructorUsedError;
  String get section => throw _privateConstructorUsedError;
  String get effectiveDate => throw _privateConstructorUsedError;
  String get owner => throw _privateConstructorUsedError;
  String get tier => throw _privateConstructorUsedError;

  /// Serializes this EvidenceRef to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of EvidenceRef
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $EvidenceRefCopyWith<EvidenceRef> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $EvidenceRefCopyWith<$Res> {
  factory $EvidenceRefCopyWith(
          EvidenceRef value, $Res Function(EvidenceRef) then) =
      _$EvidenceRefCopyWithImpl<$Res, EvidenceRef>;
  @useResult
  $Res call(
      {String id,
      String document,
      String section,
      String effectiveDate,
      String owner,
      String tier});
}

/// @nodoc
class _$EvidenceRefCopyWithImpl<$Res, $Val extends EvidenceRef>
    implements $EvidenceRefCopyWith<$Res> {
  _$EvidenceRefCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of EvidenceRef
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? document = null,
    Object? section = null,
    Object? effectiveDate = null,
    Object? owner = null,
    Object? tier = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      document: null == document
          ? _value.document
          : document // ignore: cast_nullable_to_non_nullable
              as String,
      section: null == section
          ? _value.section
          : section // ignore: cast_nullable_to_non_nullable
              as String,
      effectiveDate: null == effectiveDate
          ? _value.effectiveDate
          : effectiveDate // ignore: cast_nullable_to_non_nullable
              as String,
      owner: null == owner
          ? _value.owner
          : owner // ignore: cast_nullable_to_non_nullable
              as String,
      tier: null == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$EvidenceRefImplCopyWith<$Res>
    implements $EvidenceRefCopyWith<$Res> {
  factory _$$EvidenceRefImplCopyWith(
          _$EvidenceRefImpl value, $Res Function(_$EvidenceRefImpl) then) =
      __$$EvidenceRefImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String document,
      String section,
      String effectiveDate,
      String owner,
      String tier});
}

/// @nodoc
class __$$EvidenceRefImplCopyWithImpl<$Res>
    extends _$EvidenceRefCopyWithImpl<$Res, _$EvidenceRefImpl>
    implements _$$EvidenceRefImplCopyWith<$Res> {
  __$$EvidenceRefImplCopyWithImpl(
      _$EvidenceRefImpl _value, $Res Function(_$EvidenceRefImpl) _then)
      : super(_value, _then);

  /// Create a copy of EvidenceRef
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? document = null,
    Object? section = null,
    Object? effectiveDate = null,
    Object? owner = null,
    Object? tier = null,
  }) {
    return _then(_$EvidenceRefImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      document: null == document
          ? _value.document
          : document // ignore: cast_nullable_to_non_nullable
              as String,
      section: null == section
          ? _value.section
          : section // ignore: cast_nullable_to_non_nullable
              as String,
      effectiveDate: null == effectiveDate
          ? _value.effectiveDate
          : effectiveDate // ignore: cast_nullable_to_non_nullable
              as String,
      owner: null == owner
          ? _value.owner
          : owner // ignore: cast_nullable_to_non_nullable
              as String,
      tier: null == tier
          ? _value.tier
          : tier // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$EvidenceRefImpl implements _EvidenceRef {
  const _$EvidenceRefImpl(
      {required this.id,
      required this.document,
      required this.section,
      required this.effectiveDate,
      required this.owner,
      required this.tier});

  factory _$EvidenceRefImpl.fromJson(Map<String, dynamic> json) =>
      _$$EvidenceRefImplFromJson(json);

  @override
  final String id;
  @override
  final String document;
  @override
  final String section;
  @override
  final String effectiveDate;
  @override
  final String owner;
  @override
  final String tier;

  @override
  String toString() {
    return 'EvidenceRef(id: $id, document: $document, section: $section, effectiveDate: $effectiveDate, owner: $owner, tier: $tier)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$EvidenceRefImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.document, document) ||
                other.document == document) &&
            (identical(other.section, section) || other.section == section) &&
            (identical(other.effectiveDate, effectiveDate) ||
                other.effectiveDate == effectiveDate) &&
            (identical(other.owner, owner) || other.owner == owner) &&
            (identical(other.tier, tier) || other.tier == tier));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, id, document, section, effectiveDate, owner, tier);

  /// Create a copy of EvidenceRef
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$EvidenceRefImplCopyWith<_$EvidenceRefImpl> get copyWith =>
      __$$EvidenceRefImplCopyWithImpl<_$EvidenceRefImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$EvidenceRefImplToJson(
      this,
    );
  }
}

abstract class _EvidenceRef implements EvidenceRef {
  const factory _EvidenceRef(
      {required final String id,
      required final String document,
      required final String section,
      required final String effectiveDate,
      required final String owner,
      required final String tier}) = _$EvidenceRefImpl;

  factory _EvidenceRef.fromJson(Map<String, dynamic> json) =
      _$EvidenceRefImpl.fromJson;

  @override
  String get id;
  @override
  String get document;
  @override
  String get section;
  @override
  String get effectiveDate;
  @override
  String get owner;
  @override
  String get tier;

  /// Create a copy of EvidenceRef
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$EvidenceRefImplCopyWith<_$EvidenceRefImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

MissingDocument _$MissingDocumentFromJson(Map<String, dynamic> json) {
  return _MissingDocument.fromJson(json);
}

/// @nodoc
mixin _$MissingDocument {
  String get documentType => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get reason => throw _privateConstructorUsedError;
  String get responsibleParty => throw _privateConstructorUsedError;

  /// Serializes this MissingDocument to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of MissingDocument
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MissingDocumentCopyWith<MissingDocument> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MissingDocumentCopyWith<$Res> {
  factory $MissingDocumentCopyWith(
          MissingDocument value, $Res Function(MissingDocument) then) =
      _$MissingDocumentCopyWithImpl<$Res, MissingDocument>;
  @useResult
  $Res call(
      {String documentType,
      String description,
      String reason,
      String responsibleParty});
}

/// @nodoc
class _$MissingDocumentCopyWithImpl<$Res, $Val extends MissingDocument>
    implements $MissingDocumentCopyWith<$Res> {
  _$MissingDocumentCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MissingDocument
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? documentType = null,
    Object? description = null,
    Object? reason = null,
    Object? responsibleParty = null,
  }) {
    return _then(_value.copyWith(
      documentType: null == documentType
          ? _value.documentType
          : documentType // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      reason: null == reason
          ? _value.reason
          : reason // ignore: cast_nullable_to_non_nullable
              as String,
      responsibleParty: null == responsibleParty
          ? _value.responsibleParty
          : responsibleParty // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$MissingDocumentImplCopyWith<$Res>
    implements $MissingDocumentCopyWith<$Res> {
  factory _$$MissingDocumentImplCopyWith(_$MissingDocumentImpl value,
          $Res Function(_$MissingDocumentImpl) then) =
      __$$MissingDocumentImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String documentType,
      String description,
      String reason,
      String responsibleParty});
}

/// @nodoc
class __$$MissingDocumentImplCopyWithImpl<$Res>
    extends _$MissingDocumentCopyWithImpl<$Res, _$MissingDocumentImpl>
    implements _$$MissingDocumentImplCopyWith<$Res> {
  __$$MissingDocumentImplCopyWithImpl(
      _$MissingDocumentImpl _value, $Res Function(_$MissingDocumentImpl) _then)
      : super(_value, _then);

  /// Create a copy of MissingDocument
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? documentType = null,
    Object? description = null,
    Object? reason = null,
    Object? responsibleParty = null,
  }) {
    return _then(_$MissingDocumentImpl(
      documentType: null == documentType
          ? _value.documentType
          : documentType // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      reason: null == reason
          ? _value.reason
          : reason // ignore: cast_nullable_to_non_nullable
              as String,
      responsibleParty: null == responsibleParty
          ? _value.responsibleParty
          : responsibleParty // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$MissingDocumentImpl implements _MissingDocument {
  const _$MissingDocumentImpl(
      {required this.documentType,
      required this.description,
      required this.reason,
      required this.responsibleParty});

  factory _$MissingDocumentImpl.fromJson(Map<String, dynamic> json) =>
      _$$MissingDocumentImplFromJson(json);

  @override
  final String documentType;
  @override
  final String description;
  @override
  final String reason;
  @override
  final String responsibleParty;

  @override
  String toString() {
    return 'MissingDocument(documentType: $documentType, description: $description, reason: $reason, responsibleParty: $responsibleParty)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MissingDocumentImpl &&
            (identical(other.documentType, documentType) ||
                other.documentType == documentType) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.reason, reason) || other.reason == reason) &&
            (identical(other.responsibleParty, responsibleParty) ||
                other.responsibleParty == responsibleParty));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, documentType, description, reason, responsibleParty);

  /// Create a copy of MissingDocument
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MissingDocumentImplCopyWith<_$MissingDocumentImpl> get copyWith =>
      __$$MissingDocumentImplCopyWithImpl<_$MissingDocumentImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$MissingDocumentImplToJson(
      this,
    );
  }
}

abstract class _MissingDocument implements MissingDocument {
  const factory _MissingDocument(
      {required final String documentType,
      required final String description,
      required final String reason,
      required final String responsibleParty}) = _$MissingDocumentImpl;

  factory _MissingDocument.fromJson(Map<String, dynamic> json) =
      _$MissingDocumentImpl.fromJson;

  @override
  String get documentType;
  @override
  String get description;
  @override
  String get reason;
  @override
  String get responsibleParty;

  /// Create a copy of MissingDocument
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MissingDocumentImplCopyWith<_$MissingDocumentImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ChecklistItem _$ChecklistItemFromJson(Map<String, dynamic> json) {
  return _ChecklistItem.fromJson(json);
}

/// @nodoc
mixin _$ChecklistItem {
  String get id => throw _privateConstructorUsedError;
  String get text => throw _privateConstructorUsedError;
  String get owner => throw _privateConstructorUsedError;
  String get sla => throw _privateConstructorUsedError;
  bool get completed => throw _privateConstructorUsedError;

  /// Serializes this ChecklistItem to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ChecklistItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ChecklistItemCopyWith<ChecklistItem> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ChecklistItemCopyWith<$Res> {
  factory $ChecklistItemCopyWith(
          ChecklistItem value, $Res Function(ChecklistItem) then) =
      _$ChecklistItemCopyWithImpl<$Res, ChecklistItem>;
  @useResult
  $Res call({String id, String text, String owner, String sla, bool completed});
}

/// @nodoc
class _$ChecklistItemCopyWithImpl<$Res, $Val extends ChecklistItem>
    implements $ChecklistItemCopyWith<$Res> {
  _$ChecklistItemCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ChecklistItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? text = null,
    Object? owner = null,
    Object? sla = null,
    Object? completed = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      text: null == text
          ? _value.text
          : text // ignore: cast_nullable_to_non_nullable
              as String,
      owner: null == owner
          ? _value.owner
          : owner // ignore: cast_nullable_to_non_nullable
              as String,
      sla: null == sla
          ? _value.sla
          : sla // ignore: cast_nullable_to_non_nullable
              as String,
      completed: null == completed
          ? _value.completed
          : completed // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ChecklistItemImplCopyWith<$Res>
    implements $ChecklistItemCopyWith<$Res> {
  factory _$$ChecklistItemImplCopyWith(
          _$ChecklistItemImpl value, $Res Function(_$ChecklistItemImpl) then) =
      __$$ChecklistItemImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String id, String text, String owner, String sla, bool completed});
}

/// @nodoc
class __$$ChecklistItemImplCopyWithImpl<$Res>
    extends _$ChecklistItemCopyWithImpl<$Res, _$ChecklistItemImpl>
    implements _$$ChecklistItemImplCopyWith<$Res> {
  __$$ChecklistItemImplCopyWithImpl(
      _$ChecklistItemImpl _value, $Res Function(_$ChecklistItemImpl) _then)
      : super(_value, _then);

  /// Create a copy of ChecklistItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? text = null,
    Object? owner = null,
    Object? sla = null,
    Object? completed = null,
  }) {
    return _then(_$ChecklistItemImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      text: null == text
          ? _value.text
          : text // ignore: cast_nullable_to_non_nullable
              as String,
      owner: null == owner
          ? _value.owner
          : owner // ignore: cast_nullable_to_non_nullable
              as String,
      sla: null == sla
          ? _value.sla
          : sla // ignore: cast_nullable_to_non_nullable
              as String,
      completed: null == completed
          ? _value.completed
          : completed // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ChecklistItemImpl implements _ChecklistItem {
  const _$ChecklistItemImpl(
      {required this.id,
      required this.text,
      required this.owner,
      required this.sla,
      required this.completed});

  factory _$ChecklistItemImpl.fromJson(Map<String, dynamic> json) =>
      _$$ChecklistItemImplFromJson(json);

  @override
  final String id;
  @override
  final String text;
  @override
  final String owner;
  @override
  final String sla;
  @override
  final bool completed;

  @override
  String toString() {
    return 'ChecklistItem(id: $id, text: $text, owner: $owner, sla: $sla, completed: $completed)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ChecklistItemImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.text, text) || other.text == text) &&
            (identical(other.owner, owner) || other.owner == owner) &&
            (identical(other.sla, sla) || other.sla == sla) &&
            (identical(other.completed, completed) ||
                other.completed == completed));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, text, owner, sla, completed);

  /// Create a copy of ChecklistItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ChecklistItemImplCopyWith<_$ChecklistItemImpl> get copyWith =>
      __$$ChecklistItemImplCopyWithImpl<_$ChecklistItemImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ChecklistItemImplToJson(
      this,
    );
  }
}

abstract class _ChecklistItem implements ChecklistItem {
  const factory _ChecklistItem(
      {required final String id,
      required final String text,
      required final String owner,
      required final String sla,
      required final bool completed}) = _$ChecklistItemImpl;

  factory _ChecklistItem.fromJson(Map<String, dynamic> json) =
      _$ChecklistItemImpl.fromJson;

  @override
  String get id;
  @override
  String get text;
  @override
  String get owner;
  @override
  String get sla;
  @override
  bool get completed;

  /// Create a copy of ChecklistItem
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ChecklistItemImplCopyWith<_$ChecklistItemImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ApprovalPayload _$ApprovalPayloadFromJson(Map<String, dynamic> json) {
  return _ApprovalPayload.fromJson(json);
}

/// @nodoc
mixin _$ApprovalPayload {
  List<String> get selectedOpportunityIds => throw _privateConstructorUsedError;
  List<PayloadDiff> get diff => throw _privateConstructorUsedError;
  List<String> get rmCommitments => throw _privateConstructorUsedError;

  /// Serializes this ApprovalPayload to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ApprovalPayload
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ApprovalPayloadCopyWith<ApprovalPayload> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApprovalPayloadCopyWith<$Res> {
  factory $ApprovalPayloadCopyWith(
          ApprovalPayload value, $Res Function(ApprovalPayload) then) =
      _$ApprovalPayloadCopyWithImpl<$Res, ApprovalPayload>;
  @useResult
  $Res call(
      {List<String> selectedOpportunityIds,
      List<PayloadDiff> diff,
      List<String> rmCommitments});
}

/// @nodoc
class _$ApprovalPayloadCopyWithImpl<$Res, $Val extends ApprovalPayload>
    implements $ApprovalPayloadCopyWith<$Res> {
  _$ApprovalPayloadCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ApprovalPayload
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? selectedOpportunityIds = null,
    Object? diff = null,
    Object? rmCommitments = null,
  }) {
    return _then(_value.copyWith(
      selectedOpportunityIds: null == selectedOpportunityIds
          ? _value.selectedOpportunityIds
          : selectedOpportunityIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      diff: null == diff
          ? _value.diff
          : diff // ignore: cast_nullable_to_non_nullable
              as List<PayloadDiff>,
      rmCommitments: null == rmCommitments
          ? _value.rmCommitments
          : rmCommitments // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ApprovalPayloadImplCopyWith<$Res>
    implements $ApprovalPayloadCopyWith<$Res> {
  factory _$$ApprovalPayloadImplCopyWith(_$ApprovalPayloadImpl value,
          $Res Function(_$ApprovalPayloadImpl) then) =
      __$$ApprovalPayloadImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<String> selectedOpportunityIds,
      List<PayloadDiff> diff,
      List<String> rmCommitments});
}

/// @nodoc
class __$$ApprovalPayloadImplCopyWithImpl<$Res>
    extends _$ApprovalPayloadCopyWithImpl<$Res, _$ApprovalPayloadImpl>
    implements _$$ApprovalPayloadImplCopyWith<$Res> {
  __$$ApprovalPayloadImplCopyWithImpl(
      _$ApprovalPayloadImpl _value, $Res Function(_$ApprovalPayloadImpl) _then)
      : super(_value, _then);

  /// Create a copy of ApprovalPayload
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? selectedOpportunityIds = null,
    Object? diff = null,
    Object? rmCommitments = null,
  }) {
    return _then(_$ApprovalPayloadImpl(
      selectedOpportunityIds: null == selectedOpportunityIds
          ? _value._selectedOpportunityIds
          : selectedOpportunityIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      diff: null == diff
          ? _value._diff
          : diff // ignore: cast_nullable_to_non_nullable
              as List<PayloadDiff>,
      rmCommitments: null == rmCommitments
          ? _value._rmCommitments
          : rmCommitments // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ApprovalPayloadImpl implements _ApprovalPayload {
  const _$ApprovalPayloadImpl(
      {required final List<String> selectedOpportunityIds,
      required final List<PayloadDiff> diff,
      required final List<String> rmCommitments})
      : _selectedOpportunityIds = selectedOpportunityIds,
        _diff = diff,
        _rmCommitments = rmCommitments;

  factory _$ApprovalPayloadImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApprovalPayloadImplFromJson(json);

  final List<String> _selectedOpportunityIds;
  @override
  List<String> get selectedOpportunityIds {
    if (_selectedOpportunityIds is EqualUnmodifiableListView)
      return _selectedOpportunityIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_selectedOpportunityIds);
  }

  final List<PayloadDiff> _diff;
  @override
  List<PayloadDiff> get diff {
    if (_diff is EqualUnmodifiableListView) return _diff;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_diff);
  }

  final List<String> _rmCommitments;
  @override
  List<String> get rmCommitments {
    if (_rmCommitments is EqualUnmodifiableListView) return _rmCommitments;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_rmCommitments);
  }

  @override
  String toString() {
    return 'ApprovalPayload(selectedOpportunityIds: $selectedOpportunityIds, diff: $diff, rmCommitments: $rmCommitments)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalPayloadImpl &&
            const DeepCollectionEquality().equals(
                other._selectedOpportunityIds, _selectedOpportunityIds) &&
            const DeepCollectionEquality().equals(other._diff, _diff) &&
            const DeepCollectionEquality()
                .equals(other._rmCommitments, _rmCommitments));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_selectedOpportunityIds),
      const DeepCollectionEquality().hash(_diff),
      const DeepCollectionEquality().hash(_rmCommitments));

  /// Create a copy of ApprovalPayload
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ApprovalPayloadImplCopyWith<_$ApprovalPayloadImpl> get copyWith =>
      __$$ApprovalPayloadImplCopyWithImpl<_$ApprovalPayloadImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ApprovalPayloadImplToJson(
      this,
    );
  }
}

abstract class _ApprovalPayload implements ApprovalPayload {
  const factory _ApprovalPayload(
      {required final List<String> selectedOpportunityIds,
      required final List<PayloadDiff> diff,
      required final List<String> rmCommitments}) = _$ApprovalPayloadImpl;

  factory _ApprovalPayload.fromJson(Map<String, dynamic> json) =
      _$ApprovalPayloadImpl.fromJson;

  @override
  List<String> get selectedOpportunityIds;
  @override
  List<PayloadDiff> get diff;
  @override
  List<String> get rmCommitments;

  /// Create a copy of ApprovalPayload
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ApprovalPayloadImplCopyWith<_$ApprovalPayloadImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PayloadDiff _$PayloadDiffFromJson(Map<String, dynamic> json) {
  return _PayloadDiff.fromJson(json);
}

/// @nodoc
mixin _$PayloadDiff {
  String get object => throw _privateConstructorUsedError;
  String get action => throw _privateConstructorUsedError;

  /// Serializes this PayloadDiff to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of PayloadDiff
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $PayloadDiffCopyWith<PayloadDiff> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PayloadDiffCopyWith<$Res> {
  factory $PayloadDiffCopyWith(
          PayloadDiff value, $Res Function(PayloadDiff) then) =
      _$PayloadDiffCopyWithImpl<$Res, PayloadDiff>;
  @useResult
  $Res call({String object, String action});
}

/// @nodoc
class _$PayloadDiffCopyWithImpl<$Res, $Val extends PayloadDiff>
    implements $PayloadDiffCopyWith<$Res> {
  _$PayloadDiffCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of PayloadDiff
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? object = null,
    Object? action = null,
  }) {
    return _then(_value.copyWith(
      object: null == object
          ? _value.object
          : object // ignore: cast_nullable_to_non_nullable
              as String,
      action: null == action
          ? _value.action
          : action // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PayloadDiffImplCopyWith<$Res>
    implements $PayloadDiffCopyWith<$Res> {
  factory _$$PayloadDiffImplCopyWith(
          _$PayloadDiffImpl value, $Res Function(_$PayloadDiffImpl) then) =
      __$$PayloadDiffImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String object, String action});
}

/// @nodoc
class __$$PayloadDiffImplCopyWithImpl<$Res>
    extends _$PayloadDiffCopyWithImpl<$Res, _$PayloadDiffImpl>
    implements _$$PayloadDiffImplCopyWith<$Res> {
  __$$PayloadDiffImplCopyWithImpl(
      _$PayloadDiffImpl _value, $Res Function(_$PayloadDiffImpl) _then)
      : super(_value, _then);

  /// Create a copy of PayloadDiff
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? object = null,
    Object? action = null,
  }) {
    return _then(_$PayloadDiffImpl(
      object: null == object
          ? _value.object
          : object // ignore: cast_nullable_to_non_nullable
              as String,
      action: null == action
          ? _value.action
          : action // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PayloadDiffImpl implements _PayloadDiff {
  const _$PayloadDiffImpl({required this.object, required this.action});

  factory _$PayloadDiffImpl.fromJson(Map<String, dynamic> json) =>
      _$$PayloadDiffImplFromJson(json);

  @override
  final String object;
  @override
  final String action;

  @override
  String toString() {
    return 'PayloadDiff(object: $object, action: $action)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PayloadDiffImpl &&
            (identical(other.object, object) || other.object == object) &&
            (identical(other.action, action) || other.action == action));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, object, action);

  /// Create a copy of PayloadDiff
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$PayloadDiffImplCopyWith<_$PayloadDiffImpl> get copyWith =>
      __$$PayloadDiffImplCopyWithImpl<_$PayloadDiffImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PayloadDiffImplToJson(
      this,
    );
  }
}

abstract class _PayloadDiff implements PayloadDiff {
  const factory _PayloadDiff(
      {required final String object,
      required final String action}) = _$PayloadDiffImpl;

  factory _PayloadDiff.fromJson(Map<String, dynamic> json) =
      _$PayloadDiffImpl.fromJson;

  @override
  String get object;
  @override
  String get action;

  /// Create a copy of PayloadDiff
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$PayloadDiffImplCopyWith<_$PayloadDiffImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
