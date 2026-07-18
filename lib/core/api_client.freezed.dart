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
  String get approvalToken => throw _privateConstructorUsedError;
  int get expiresIn => throw _privateConstructorUsedError;

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
  $Res call({String caseId, String approvalToken, int expiresIn});
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
    Object? approvalToken = null,
    Object? expiresIn = null,
  }) {
    return _then(_value.copyWith(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      approvalToken: null == approvalToken
          ? _value.approvalToken
          : approvalToken // ignore: cast_nullable_to_non_nullable
              as String,
      expiresIn: null == expiresIn
          ? _value.expiresIn
          : expiresIn // ignore: cast_nullable_to_non_nullable
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
  $Res call({String caseId, String approvalToken, int expiresIn});
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
    Object? approvalToken = null,
    Object? expiresIn = null,
  }) {
    return _then(_$ApprovalTokenResponseImpl(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      approvalToken: null == approvalToken
          ? _value.approvalToken
          : approvalToken // ignore: cast_nullable_to_non_nullable
              as String,
      expiresIn: null == expiresIn
          ? _value.expiresIn
          : expiresIn // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ApprovalTokenResponseImpl implements _ApprovalTokenResponse {
  const _$ApprovalTokenResponseImpl(
      {required this.caseId,
      required this.approvalToken,
      required this.expiresIn});

  factory _$ApprovalTokenResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApprovalTokenResponseImplFromJson(json);

  @override
  final String caseId;
  @override
  final String approvalToken;
  @override
  final int expiresIn;

  @override
  String toString() {
    return 'ApprovalTokenResponse(caseId: $caseId, approvalToken: $approvalToken, expiresIn: $expiresIn)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalTokenResponseImpl &&
            (identical(other.caseId, caseId) || other.caseId == caseId) &&
            (identical(other.approvalToken, approvalToken) ||
                other.approvalToken == approvalToken) &&
            (identical(other.expiresIn, expiresIn) ||
                other.expiresIn == expiresIn));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, caseId, approvalToken, expiresIn);

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
      required final String approvalToken,
      required final int expiresIn}) = _$ApprovalTokenResponseImpl;

  factory _ApprovalTokenResponse.fromJson(Map<String, dynamic> json) =
      _$ApprovalTokenResponseImpl.fromJson;

  @override
  String get caseId;
  @override
  String get approvalToken;
  @override
  int get expiresIn;

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
  String get approvalStatus => throw _privateConstructorUsedError;
  String get finalStatus => throw _privateConstructorUsedError;
  List<dynamic> get actionsExecuted => throw _privateConstructorUsedError;

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
  $Res call(
      {String caseId,
      String approvalStatus,
      String finalStatus,
      List<dynamic> actionsExecuted});
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
    Object? approvalStatus = null,
    Object? finalStatus = null,
    Object? actionsExecuted = null,
  }) {
    return _then(_value.copyWith(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      approvalStatus: null == approvalStatus
          ? _value.approvalStatus
          : approvalStatus // ignore: cast_nullable_to_non_nullable
              as String,
      finalStatus: null == finalStatus
          ? _value.finalStatus
          : finalStatus // ignore: cast_nullable_to_non_nullable
              as String,
      actionsExecuted: null == actionsExecuted
          ? _value.actionsExecuted
          : actionsExecuted // ignore: cast_nullable_to_non_nullable
              as List<dynamic>,
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
  $Res call(
      {String caseId,
      String approvalStatus,
      String finalStatus,
      List<dynamic> actionsExecuted});
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
    Object? approvalStatus = null,
    Object? finalStatus = null,
    Object? actionsExecuted = null,
  }) {
    return _then(_$ApprovalResultImpl(
      caseId: null == caseId
          ? _value.caseId
          : caseId // ignore: cast_nullable_to_non_nullable
              as String,
      approvalStatus: null == approvalStatus
          ? _value.approvalStatus
          : approvalStatus // ignore: cast_nullable_to_non_nullable
              as String,
      finalStatus: null == finalStatus
          ? _value.finalStatus
          : finalStatus // ignore: cast_nullable_to_non_nullable
              as String,
      actionsExecuted: null == actionsExecuted
          ? _value._actionsExecuted
          : actionsExecuted // ignore: cast_nullable_to_non_nullable
              as List<dynamic>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ApprovalResultImpl implements _ApprovalResult {
  const _$ApprovalResultImpl(
      {required this.caseId,
      required this.approvalStatus,
      required this.finalStatus,
      required final List<dynamic> actionsExecuted})
      : _actionsExecuted = actionsExecuted;

  factory _$ApprovalResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$ApprovalResultImplFromJson(json);

  @override
  final String caseId;
  @override
  final String approvalStatus;
  @override
  final String finalStatus;
  final List<dynamic> _actionsExecuted;
  @override
  List<dynamic> get actionsExecuted {
    if (_actionsExecuted is EqualUnmodifiableListView) return _actionsExecuted;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_actionsExecuted);
  }

  @override
  String toString() {
    return 'ApprovalResult(caseId: $caseId, approvalStatus: $approvalStatus, finalStatus: $finalStatus, actionsExecuted: $actionsExecuted)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ApprovalResultImpl &&
            (identical(other.caseId, caseId) || other.caseId == caseId) &&
            (identical(other.approvalStatus, approvalStatus) ||
                other.approvalStatus == approvalStatus) &&
            (identical(other.finalStatus, finalStatus) ||
                other.finalStatus == finalStatus) &&
            const DeepCollectionEquality()
                .equals(other._actionsExecuted, _actionsExecuted));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, caseId, approvalStatus,
      finalStatus, const DeepCollectionEquality().hash(_actionsExecuted));

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
      required final String approvalStatus,
      required final String finalStatus,
      required final List<dynamic> actionsExecuted}) = _$ApprovalResultImpl;

  factory _ApprovalResult.fromJson(Map<String, dynamic> json) =
      _$ApprovalResultImpl.fromJson;

  @override
  String get caseId;
  @override
  String get approvalStatus;
  @override
  String get finalStatus;
  @override
  List<dynamic> get actionsExecuted;

  /// Create a copy of ApprovalResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ApprovalResultImplCopyWith<_$ApprovalResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ProductSearchResult _$ProductSearchResultFromJson(Map<String, dynamic> json) {
  return _ProductSearchResult.fromJson(json);
}

/// @nodoc
mixin _$ProductSearchResult {
  List<ProductMatch> get results => throw _privateConstructorUsedError;

  /// Serializes this ProductSearchResult to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

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
  $Res call({List<ProductMatch> results});
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
    Object? results = null,
  }) {
    return _then(_value.copyWith(
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
  $Res call({List<ProductMatch> results});
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
    Object? results = null,
  }) {
    return _then(_$ProductSearchResultImpl(
      results: null == results
          ? _value._results
          : results // ignore: cast_nullable_to_non_nullable
              as List<ProductMatch>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ProductSearchResultImpl implements _ProductSearchResult {
  const _$ProductSearchResultImpl({required final List<ProductMatch> results})
      : _results = results;

  factory _$ProductSearchResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$ProductSearchResultImplFromJson(json);

  final List<ProductMatch> _results;
  @override
  List<ProductMatch> get results {
    if (_results is EqualUnmodifiableListView) return _results;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_results);
  }

  @override
  String toString() {
    return 'ProductSearchResult(results: $results)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ProductSearchResultImpl &&
            const DeepCollectionEquality().equals(other._results, _results));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, const DeepCollectionEquality().hash(_results));

  /// Create a copy of ProductSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ProductSearchResultImplCopyWith<_$ProductSearchResultImpl> get copyWith =>
      __$$ProductSearchResultImplCopyWithImpl<_$ProductSearchResultImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ProductSearchResultImplToJson(
      this,
    );
  }
}

abstract class _ProductSearchResult implements ProductSearchResult {
  const factory _ProductSearchResult(
      {required final List<ProductMatch> results}) = _$ProductSearchResultImpl;

  factory _ProductSearchResult.fromJson(Map<String, dynamic> json) =
      _$ProductSearchResultImpl.fromJson;

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
