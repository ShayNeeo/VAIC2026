// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'api_client.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

ApprovalTokenResponse _$ApprovalTokenResponseFromJson(
    Map<String, dynamic> json) {
  return _ApprovalTokenResponse.fromJson(json);
}

/// @nodoc
mixin _$ApprovalTokenResponse {
  String get caseId => throw _privateConstructorUsedError;
  int get stateVersion => throw _privateConstructorUsedError;
  String get approvalToken => throw _privateConstructorUsedError;
  int get expiresAt => throw _privateConstructorUsedError;

  /// Serializes this ApprovalTokenResponse to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ApprovalTokenResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ApprovalTokenResponseCopyWith<ApprovalTokenResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApprovalTokenResponseCopyWith<$Res> {
  factory $ApprovalTokenResponseCopyWith(ApprovalTokenResponse value,
          $Res Function(ApprovalTokenResponse) then) =
      _$ApprovalTokenResponseCopyWithImpl<$Res, ApprovalTokenResponse>;
  @useResult
  $Res call(
      {String caseId, int stateVersion, String approvalToken, int expiresAt});
}

/// @nodoc
class _$ApprovalTokenResponseCopyWithImpl<$Res,
        $Val extends ApprovalTokenResponse>
    implements $ApprovalTokenResponseCopyWith<$Res> {
  _$ApprovalTokenResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ApprovalTokenResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? caseId = null,
    Object? stateVersion = null,
    Object? approvalToken = null,
    Object? expiresAt = null,
  }) {
    return _then(_value.copyWith(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      stateVersion: null == stateVersion
          ? _value.stateVersion
          : stateVersion // ignore: cast_nullable_to_non_nullable
              as int,
      approvalToken: null == approvalToken
          ? _value.approvalToken
          : approvalToken // ignore: cast_nullable_to_non_nullable
              as String,
      expiresAt: null == expiresAt
          ? _value.expiresAt
          : expiresAt // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ApprovalTokenResponseImplCopyWith<$Res>
    implements $ApprovalTokenResponseCopyWith<$Res> {
  factory _$$ApprovalTokenResponseImplCopyWith(
          _$ApprovalTokenResponseImpl value,
          $Res Function(_$ApprovalTokenResponseImpl) then) =
      __$$ApprovalTokenResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String caseId, int stateVersion, String approvalToken, int expiresAt});
}

/// @nodoc
class __$$ApprovalTokenResponseImplCopyWithImpl<$Res>
    extends _$ApprovalTokenResponseCopyWithImpl<$Res,
        _$ApprovalTokenResponseImpl>
    implements _$$ApprovalTokenResponseImplCopyWith<$Res> {
  __$$ApprovalTokenResponseImplCopyWithImpl(_$ApprovalTokenResponseImpl _value,
      $Res Function(_$ApprovalTokenResponseImpl) _then)
      : super(_value, _then);

  /// Create a copy of ApprovalTokenResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? caseId = null,
    Object? stateVersion = null,
    Object? approvalToken = null,
    Object? expiresAt = null,
  }) {
    return _then(_$ApprovalTokenResponseImpl(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      stateVersion: null == stateVersion
          ? _value.stateVersion
          : stateVersion // ignore: cast_nullable_to_non_nullable
              as int,
      approvalToken: null == approvalToken
          ? _value.approvalToken
          : approvalToken // ignore: cast_nullable_to_non_nullable
              as String,
      expiresAt: null == expiresAt
          ? _value.expiresAt
          : expiresAt // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ApprovalTokenResponseImpl implements _ApprovalTokenResponse {
  const _$ApprovalTokenResponseImpl(
      {required this.caseId,
      required this.stateVersion,
      required this.approvalToken,
      required this.expiresAt});

  factory _$ApprovalTokenResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApprovalTokenResponseImplFromJson(json);

  @override
  final String caseId;
  @override
  final int stateVersion;
  @override
  final String approvalToken;
  @override
  final int expiresAt;

  @override
  String toString() {
    return 'ApprovalTokenResponse(caseId: $caseId, stateVersion: $stateVersion, approvalToken: $approvalToken, expiresAt: $expiresAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalTokenResponseImpl &&
            (identical(other.caseId, caseId) || other.caseId == caseId) &&
            (identical(other.stateVersion, stateVersion) ||
                other.stateVersion == stateVersion) &&
            (identical(other.approvalToken, approvalToken) ||
                other.approvalToken == approvalToken) &&
            (identical(other.expiresAt, expiresAt) ||
                other.expiresAt == expiresAt));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, caseId, stateVersion, approvalToken, expiresAt);

  /// Create a copy of ApprovalTokenResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ApprovalTokenResponseImplCopyWith<_$ApprovalTokenResponseImpl>
      get copyWith => __$$ApprovalTokenResponseImplCopyWithImpl<
          _$ApprovalTokenResponseImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ApprovalTokenResponseImplToJson(
      this,
    );
  }
}

abstract class _ApprovalTokenResponse implements ApprovalTokenResponse {
  const factory _ApprovalTokenResponse(
      {required final String caseId,
      required final int stateVersion,
      required final String approvalToken,
      required final int expiresAt}) = _$ApprovalTokenResponseImpl;

  factory _ApprovalTokenResponse.fromJson(Map<String, dynamic> json) =
      _$ApprovalTokenResponseImpl.fromJson;

  @override
  String get caseId;
  @override
  int get stateVersion;
  @override
  String get approvalToken;
  @override
  int get expiresAt;

  /// Create a copy of ApprovalTokenResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ApprovalTokenResponseImplCopyWith<_$ApprovalTokenResponseImpl>
      get copyWith => throw _privateConstructorUsedError;
}

ApprovalResult _$ApprovalResultFromJson(Map<String, dynamic> json) {
  return _ApprovalResult.fromJson(json);
}

/// @nodoc
mixin _$ApprovalResult {
  String get caseId => throw _privateConstructorUsedError;
  int get stateVersion => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  String get result => throw _privateConstructorUsedError;

  /// Serializes this ApprovalResult to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ApprovalResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ApprovalResultCopyWith<ApprovalResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApprovalResultCopyWith<$Res> {
  factory $ApprovalResultCopyWith(
          ApprovalResult value, $Res Function(ApprovalResult) then) =
      _$ApprovalResultCopyWithImpl<$Res, ApprovalResult>;
  @useResult
  $Res call({String caseId, int stateVersion, String status, String result});
}

/// @nodoc
class _$ApprovalResultCopyWithImpl<$Res, $Val extends ApprovalResult>
    implements $ApprovalResultCopyWith<$Res> {
  _$ApprovalResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ApprovalResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? caseId = null,
    Object? stateVersion = null,
    Object? status = null,
    Object? result = null,
  }) {
    return _then(_value.copyWith(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      stateVersion: null == stateVersion
          ? _value.stateVersion
          : stateVersion // ignore: cast_nullable_to_non_nullable
              as int,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      result: null == result
          ? _value.result
          : result // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ApprovalResultImplCopyWith<$Res>
    implements $ApprovalResultCopyWith<$Res> {
  factory _$$ApprovalResultImplCopyWith(_$ApprovalResultImpl value,
          $Res Function(_$ApprovalResultImpl) then) =
      __$$ApprovalResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String caseId, int stateVersion, String status, String result});
}

/// @nodoc
class __$$ApprovalResultImplCopyWithImpl<$Res>
    extends _$ApprovalResultCopyWithImpl<$Res, _$ApprovalResultImpl>
    implements _$$ApprovalResultImplCopyWith<$Res> {
  __$$ApprovalResultImplCopyWithImpl(
      _$ApprovalResultImpl _value, $Res Function(_$ApprovalResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of ApprovalResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? caseId = null,
    Object? stateVersion = null,
    Object? status = null,
    Object? result = null,
  }) {
    return _then(_$ApprovalResultImpl(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      stateVersion: null == stateVersion
          ? _value.stateVersion
          : stateVersion // ignore: cast_nullable_to_non_nullable
              as int,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      result: null == result
          ? _value.result
          : result // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ApprovalResultImpl implements _ApprovalResult {
  const _$ApprovalResultImpl(
      {required this.caseId,
      required this.stateVersion,
      required this.status,
      required this.result});

  factory _$ApprovalResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApprovalResultImplFromJson(json);

  @override
  final String caseId;
  @override
  final int stateVersion;
  @override
  final String status;
  @override
  final String result;

  @override
  String toString() {
    return 'ApprovalResult(caseId: $caseId, stateVersion: $stateVersion, status: $status, result: $result)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalResultImpl &&
            (identical(other.caseId, caseId) || other.caseId == caseId) &&
            (identical(other.stateVersion, stateVersion) ||
                other.stateVersion == stateVersion) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.result, result) || other.result == result));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, caseId, stateVersion, status, result);

  /// Create a copy of ApprovalResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ApprovalResultImplCopyWith<_$ApprovalResultImpl> get copyWith =>
      __$$ApprovalResultImplCopyWithImpl<_$ApprovalResultImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ApprovalResultImplToJson(
      this,
    );
  }
}

abstract class _ApprovalResult implements ApprovalResult {
  const factory _ApprovalResult(
      {required final String caseId,
      required final int stateVersion,
      required final String status,
      required final String result}) = _$ApprovalResultImpl;

  factory _ApprovalResult.fromJson(Map<String, dynamic> json) =
      _$ApprovalResultImpl.fromJson;

  @override
  String get caseId;
  @override
  int get stateVersion;
  @override
  String get status;
  @override
  String get result;

  /// Create a copy of ApprovalResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ApprovalResultImplCopyWith<_$ApprovalResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ApprovalPreview _$ApprovalPreviewFromJson(Map<String, dynamic> json) {
  return _ApprovalPreview.fromJson(json);
}

/// @nodoc
mixin _$ApprovalPreview {
  String get caseId => throw _privateConstructorUsedError;
  int get stateVersion => throw _privateConstructorUsedError;
  String get action => throw _privateConstructorUsedError;
  String get target => throw _privateConstructorUsedError;
  String get payloadHash => throw _privateConstructorUsedError;
  bool get reversible => throw _privateConstructorUsedError;

  /// Serializes this ApprovalPreview to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ApprovalPreview
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ApprovalPreviewCopyWith<ApprovalPreview> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ApprovalPreviewCopyWith<$Res> {
  factory $ApprovalPreviewCopyWith(
          ApprovalPreview value, $Res Function(ApprovalPreview) then) =
      _$ApprovalPreviewCopyWithImpl<$Res, ApprovalPreview>;
  @useResult
  $Res call(
      {String caseId,
      int stateVersion,
      String action,
      String target,
      String payloadHash,
      bool reversible});
}

/// @nodoc
class _$ApprovalPreviewCopyWithImpl<$Res, $Val extends ApprovalPreview>
    implements $ApprovalPreviewCopyWith<$Res> {
  _$ApprovalPreviewCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ApprovalPreview
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? caseId = null,
    Object? stateVersion = null,
    Object? action = null,
    Object? target = null,
    Object? payloadHash = null,
    Object? reversible = null,
  }) {
    return _then(_value.copyWith(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      stateVersion: null == stateVersion
          ? _value.stateVersion
          : stateVersion // ignore: cast_nullable_to_non_nullable
              as int,
      action: null == action
          ? _value.action
          : action // ignore: cast_nullable_to_non_nullable
              as String,
      target: null == target
          ? _value.target
          : target // ignore: cast_nullable_to_non_nullable
              as String,
      payloadHash: null == payloadHash
          ? _value.payloadHash
          : payloadHash // ignore: cast_nullable_to_non_nullable
              as String,
      reversible: null == reversible
          ? _value.reversible
          : reversible // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ApprovalPreviewImplCopyWith<$Res>
    implements $ApprovalPreviewCopyWith<$Res> {
  factory _$$ApprovalPreviewImplCopyWith(_$ApprovalPreviewImpl value,
          $Res Function(_$ApprovalPreviewImpl) then) =
      __$$ApprovalPreviewImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String caseId,
      int stateVersion,
      String action,
      String target,
      String payloadHash,
      bool reversible});
}

/// @nodoc
class __$$ApprovalPreviewImplCopyWithImpl<$Res>
    extends _$ApprovalPreviewCopyWithImpl<$Res, _$ApprovalPreviewImpl>
    implements _$$ApprovalPreviewImplCopyWith<$Res> {
  __$$ApprovalPreviewImplCopyWithImpl(
      _$ApprovalPreviewImpl _value, $Res Function(_$ApprovalPreviewImpl) _then)
      : super(_value, _then);

  /// Create a copy of ApprovalPreview
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? caseId = null,
    Object? stateVersion = null,
    Object? action = null,
    Object? target = null,
    Object? payloadHash = null,
    Object? reversible = null,
  }) {
    return _then(_$ApprovalPreviewImpl(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      stateVersion: null == stateVersion
          ? _value.stateVersion
          : stateVersion // ignore: cast_nullable_to_non_nullable
              as int,
      action: null == action
          ? _value.action
          : action // ignore: cast_nullable_to_non_nullable
              as String,
      target: null == target
          ? _value.target
          : target // ignore: cast_nullable_to_non_nullable
              as String,
      payloadHash: null == payloadHash
          ? _value.payloadHash
          : payloadHash // ignore: cast_nullable_to_non_nullable
              as String,
      reversible: null == reversible
          ? _value.reversible
          : reversible // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ApprovalPreviewImpl implements _ApprovalPreview {
  const _$ApprovalPreviewImpl(
      {required this.caseId,
      required this.stateVersion,
      required this.action,
      required this.target,
      required this.payloadHash,
      required this.reversible});

  factory _$ApprovalPreviewImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApprovalPreviewImplFromJson(json);

  @override
  final String caseId;
  @override
  final int stateVersion;
  @override
  final String action;
  @override
  final String target;
  @override
  final String payloadHash;
  @override
  final bool reversible;

  @override
  String toString() {
    return 'ApprovalPreview(caseId: $caseId, stateVersion: $stateVersion, action: $action, target: $target, payloadHash: $payloadHash, reversible: $reversible)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalPreviewImpl &&
            (identical(other.caseId, caseId) || other.caseId == caseId) &&
            (identical(other.stateVersion, stateVersion) ||
                other.stateVersion == stateVersion) &&
            (identical(other.action, action) || other.action == action) &&
            (identical(other.target, target) || other.target == target) &&
            (identical(other.payloadHash, payloadHash) ||
                other.payloadHash == payloadHash) &&
            (identical(other.reversible, reversible) ||
                other.reversible == reversible));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, caseId, stateVersion, action,
      target, payloadHash, reversible);

  /// Create a copy of ApprovalPreview
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ApprovalPreviewImplCopyWith<_$ApprovalPreviewImpl> get copyWith =>
      __$$ApprovalPreviewImplCopyWithImpl<_$ApprovalPreviewImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ApprovalPreviewImplToJson(
      this,
    );
  }
}

abstract class _ApprovalPreview implements ApprovalPreview {
  const factory _ApprovalPreview(
      {required final String caseId,
      required final int stateVersion,
      required final String action,
      required final String target,
      required final String payloadHash,
      required final bool reversible}) = _$ApprovalPreviewImpl;

  factory _ApprovalPreview.fromJson(Map<String, dynamic> json) =
      _$ApprovalPreviewImpl.fromJson;

  @override
  String get caseId;
  @override
  int get stateVersion;
  @override
  String get action;
  @override
  String get target;
  @override
  String get payloadHash;
  @override
  bool get reversible;

  /// Create a copy of ApprovalPreview
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ApprovalPreviewImplCopyWith<_$ApprovalPreviewImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$ProductSearchResult {
  String get query => throw _privateConstructorUsedError;
  List<ProductMatch> get results => throw _privateConstructorUsedError;

  /// Create a copy of ProductSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ProductSearchResultCopyWith<ProductSearchResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ProductSearchResultCopyWith<$Res> {
  factory $ProductSearchResultCopyWith(
          ProductSearchResult value, $Res Function(ProductSearchResult) then) =
      _$ProductSearchResultCopyWithImpl<$Res, ProductSearchResult>;
  @useResult
  $Res call({String query, List<ProductMatch> results});
}

/// @nodoc
class _$ProductSearchResultCopyWithImpl<$Res, $Val extends ProductSearchResult>
    implements $ProductSearchResultCopyWith<$Res> {
  _$ProductSearchResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ProductSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? query = null,
    Object? results = null,
  }) {
    return _then(_value.copyWith(
      query: null == query
          ? _value.query
          : query // ignore: cast_nullable_to_non_nullable
              as String,
      results: null == results
          ? _value.results
          : results // ignore: cast_nullable_to_non_nullable
              as List<ProductMatch>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ProductSearchResultImplCopyWith<$Res>
    implements $ProductSearchResultCopyWith<$Res> {
  factory _$$ProductSearchResultImplCopyWith(_$ProductSearchResultImpl value,
          $Res Function(_$ProductSearchResultImpl) then) =
      __$$ProductSearchResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String query, List<ProductMatch> results});
}

/// @nodoc
class __$$ProductSearchResultImplCopyWithImpl<$Res>
    extends _$ProductSearchResultCopyWithImpl<$Res, _$ProductSearchResultImpl>
    implements _$$ProductSearchResultImplCopyWith<$Res> {
  __$$ProductSearchResultImplCopyWithImpl(_$ProductSearchResultImpl _value,
      $Res Function(_$ProductSearchResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of ProductSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? query = null,
    Object? results = null,
  }) {
    return _then(_$ProductSearchResultImpl(
      query: null == query
          ? _value.query
          : query // ignore: cast_nullable_to_non_nullable
              as String,
      results: null == results
          ? _value._results
          : results // ignore: cast_nullable_to_non_nullable
              as List<ProductMatch>,
    ));
  }
}

/// @nodoc

class _$ProductSearchResultImpl implements _ProductSearchResult {
  const _$ProductSearchResultImpl(
      {required this.query, required final List<ProductMatch> results})
      : _results = results;

  @override
  final String query;
  final List<ProductMatch> _results;
  @override
  List<ProductMatch> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  String toString() {
    return 'ProductSearchResult(query: $query, results: $results)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ProductSearchResultImpl &&
            (identical(other.query, query) || other.query == query) &&
            const DeepCollectionEquality().equals(other._results, _results));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType, query, const DeepCollectionEquality().hash(_results));

  /// Create a copy of ProductSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ProductSearchResultImplCopyWith<_$ProductSearchResultImpl> get copyWith =>
      __$$ProductSearchResultImplCopyWithImpl<_$ProductSearchResultImpl>(
          this, _$identity);
}

abstract class _ProductSearchResult implements ProductSearchResult {
  const factory _ProductSearchResult(
      {required final String query,
      required final List<ProductMatch> results}) = _$ProductSearchResultImpl;

  @override
  String get query;
  @override
  List<ProductMatch> get results;

  /// Create a copy of ProductSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ProductSearchResultImplCopyWith<_$ProductSearchResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ProductMatch _$ProductMatchFromJson(Map<String, dynamic> json) {
  return _ProductMatch.fromJson(json);
}

/// @nodoc
mixin _$ProductMatch {
  String get productId => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  double get score => throw _privateConstructorUsedError;

  /// Serializes this ProductMatch to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ProductMatch
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ProductMatchCopyWith<ProductMatch> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ProductMatchCopyWith<$Res> {
  factory $ProductMatchCopyWith(
          ProductMatch value, $Res Function(ProductMatch) then) =
      _$ProductMatchCopyWithImpl<$Res, ProductMatch>;
  @useResult
  $Res call({String productId, String name, String description, double score});
}

/// @nodoc
class _$ProductMatchCopyWithImpl<$Res, $Val extends ProductMatch>
    implements $ProductMatchCopyWith<$Res> {
  _$ProductMatchCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ProductMatch
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? productId = null,
    Object? name = null,
    Object? description = null,
    Object? score = null,
  }) {
    return _then(_value.copyWith(
      productId: null == productId
          ? _value.productId
          : productId // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ProductMatchImplCopyWith<$Res>
    implements $ProductMatchCopyWith<$Res> {
  factory _$$ProductMatchImplCopyWith(
          _$ProductMatchImpl value, $Res Function(_$ProductMatchImpl) then) =
      __$$ProductMatchImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String productId, String name, String description, double score});
}

/// @nodoc
class __$$ProductMatchImplCopyWithImpl<$Res>
    extends _$ProductMatchCopyWithImpl<$Res, _$ProductMatchImpl>
    implements _$$ProductMatchImplCopyWith<$Res> {
  __$$ProductMatchImplCopyWithImpl(
      _$ProductMatchImpl _value, $Res Function(_$ProductMatchImpl) _then)
      : super(_value, _then);

  /// Create a copy of ProductMatch
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? productId = null,
    Object? name = null,
    Object? description = null,
    Object? score = null,
  }) {
    return _then(_$ProductMatchImpl(
      productId: null == productId
          ? _value.productId
          : productId // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ProductMatchImpl implements _ProductMatch {
  const _$ProductMatchImpl(
      {required this.productId,
      required this.name,
      required this.description,
      required this.score});

  factory _$ProductMatchImpl.fromJson(Map<String, dynamic> json) =>
      _$$ProductMatchImplFromJson(json);

  @override
  final String productId;
  @override
  final String name;
  @override
  final String description;
  @override
  final double score;

  @override
  String toString() {
    return 'ProductMatch(productId: $productId, name: $name, description: $description, score: $score)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ProductMatchImpl &&
            (identical(other.productId, productId) ||
                other.productId == productId) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.score, score) || other.score == score));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, productId, name, description, score);

  /// Create a copy of ProductMatch
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ProductMatchImplCopyWith<_$ProductMatchImpl> get copyWith =>
      __$$ProductMatchImplCopyWithImpl<_$ProductMatchImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ProductMatchImplToJson(
      this,
    );
  }
}

abstract class _ProductMatch implements ProductMatch {
  const factory _ProductMatch(
      {required final String productId,
      required final String name,
      required final String description,
      required final double score}) = _$ProductMatchImpl;

  factory _ProductMatch.fromJson(Map<String, dynamic> json) =
      _$ProductMatchImpl.fromJson;

  @override
  String get productId;
  @override
  String get name;
  @override
  String get description;
  @override
  double get score;

  /// Create a copy of ProductMatch
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ProductMatchImplCopyWith<_$ProductMatchImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
