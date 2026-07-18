import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'models/case_models.dart';
import 'models/v2_projection.dart';

part 'api_client.freezed.dart';
part 'api_client.g.dart';

/// Default backend endpoint. Override via constructor (e.g. local CF tunnel).
const String kDefaultBaseUrl = 'https://vaic-api.w9.nu';

/// API client for the live VAIC2026 backend (v2 contract, plan_v2).
class ApiClient {
  final String baseUrl;
  final http.Client _client;
  String? _authToken;

  ApiClient({this.baseUrl = kDefaultBaseUrl, http.Client? client})
      : _client = client ?? http.Client();

  void setAuthToken(String token) => _authToken = token;
  void clearAuthToken() => _authToken = null;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'x-employee-id': kDemoEmployeeId,
        'x-session-id': kDemoSessionId,
        if (_authToken != null) 'Authorization': 'Bearer $_authToken',
      };

  Future<T> _request<T>(Future<http.Response> Function() call, T Function(Map<String, dynamic>) parser) async {
    try {
      final response = await call().timeout(const Duration(seconds: 30));
      if (response.statusCode >= 200 && response.statusCode < 300) {
        final data = jsonDecode(response.body);
        if (data is Map<String, dynamic>) return parser(data);
        throw ApiException(statusCode: response.statusCode, message: 'Unexpected response format');
      }
      throw ApiException(statusCode: response.statusCode, message: _parseError(response.body));
    } on TimeoutException {
      throw const NetworkException('Request timeout');
    } on FormatException {
      throw const ApiException(statusCode: 500, message: 'Invalid response format');
    } catch (e) {
      if (e is ApiException || e is NetworkException || e is AuthException) rethrow;
      throw NetworkException(e.toString());
    }
  }

  String _parseError(String body) {
    try {
      final data = jsonDecode(body);
      return data['detail']?.toString() ?? body;
    } catch (_) {
      return body;
    }
  }

  // GET /api/v2/cases -> list of SharedCaseState -> demo queue items
  Future<List<CaseQueueItem>> getCases({Map<String, String>? query}) async {
    final uri = Uri.parse('$baseUrl/api/v2/cases').replace(queryParameters: query);
    final response = await _client.get(uri, headers: _headers).timeout(const Duration(seconds: 30));
    if (response.statusCode >= 200 && response.statusCode < 300) {
      final data = jsonDecode(response.body);
      if (data is List) return [for (final e in data) projectQueueItem(e as Map<String, dynamic>)];
      return [];
    }
    throw ApiException(statusCode: response.statusCode, message: _parseError(response.body));
  }

  // GET /api/v2/cases/{caseId} -> SharedCaseState -> demo detail
  Future<CaseDetail> getCase(String caseId) async {
    final uri = Uri.parse('$baseUrl/api/v2/cases/$caseId');
    final response = await _client.get(uri, headers: _headers).timeout(const Duration(seconds: 30));
    if (response.statusCode >= 200 && response.statusCode < 300) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return projectDetail(data);
    }
    throw ApiException(statusCode: response.statusCode, message: _parseError(response.body));
  }

  // POST /api/v2/cases/{caseId}/approval-preview -> payload diff
  Future<ApprovalPreview> previewApproval(String caseId) async {
    final uri = Uri.parse('$baseUrl/api/v2/cases/$caseId/approval-preview');
    return _request(
      () => _client.post(uri, headers: _headers),
      (data) => ApprovalPreview.fromJson(data),
    );
  }

  // POST /api/v2/cases/{caseId}/approve -> issues approval token
  Future<ApprovalTokenResponse> issueApprovalToken(String caseId) async {
    final uri = Uri.parse('$baseUrl/api/v2/cases/$caseId/approve');
    return _request(
      () => _client.post(uri, headers: _headers, body: jsonEncode({'expected_state_version': 1})),
      (data) => ApprovalTokenResponse.fromJson(data),
    );
  }

  // POST /api/v2/cases/{caseId}/execute -> run actions with token
  Future<ApprovalResult> approveCase(String caseId, String rmId, String token, {String? comments}) async {
    final uri = Uri.parse('$baseUrl/api/v2/cases/$caseId/execute');
    return _request(
      () => _client.post(
        uri,
        headers: {..._headers, 'x-approval-token': token},
        body: jsonEncode({'expected_state_version': 1, 'idempotency_key': 'ipk-$caseId-${DateTime.now().microsecondsSinceEpoch}'}),
      ),
      (data) => ApprovalResult.fromJson(data),
    );
  }

  // POST /api/v2/cases/{caseId}/reject
  Future<ApprovalResult> rejectCase(String caseId, String rmId, String reason) async {
    final uri = Uri.parse('$baseUrl/api/v2/cases/$caseId/reject');
    return _request(
      () => _client.post(uri, headers: _headers, body: jsonEncode({'expected_state_version': 1, 'reason': reason})),
      (data) => ApprovalResult.fromJson(data),
    );
  }

  // GET /api/v2/knowledge/products/search -> {query, hits[]}
  Future<ProductSearchResult> searchProducts(String query, {int topK = 5}) async {
    final uri = Uri.parse('$baseUrl/api/v2/knowledge/products/search').replace(queryParameters: {'q': query, 'top_k': topK.toString()});
    return _request(
      () => _client.get(uri, headers: _headers),
      (data) => ProductSearchResult.fromJson(data),
    );
  }

  void dispose() => _client.close();
}

class ApiException implements Exception {
  final int statusCode;
  final String message;
  const ApiException({required this.statusCode, required this.message});
  @override String toString() => 'ApiException($statusCode): $message';
}

class NetworkException implements Exception {
  final String message;
  const NetworkException(this.message);
  @override String toString() => 'NetworkException: $message';
}

class AuthException implements Exception {
  final String message;
  const AuthException(this.message);
  @override String toString() => 'AuthException: $message';
}

/// Response models
@freezed
class ApprovalTokenResponse with _$ApprovalTokenResponse {
  const factory ApprovalTokenResponse({
    required String caseId,
    required int stateVersion,
    required String approvalToken,
    required int expiresAt,
  }) = _ApprovalTokenResponse;
  factory ApprovalTokenResponse.fromJson(Map<String, dynamic> json) => _$ApprovalTokenResponseFromJson(json);
}

@freezed
class ApprovalResult with _$ApprovalResult {
  const factory ApprovalResult({
    required String caseId,
    required int stateVersion,
    required String status,
    required String result,
  }) = _ApprovalResult;
  factory ApprovalResult.fromJson(Map<String, dynamic> json) => _$ApprovalResultFromJson(json);
}

@freezed
class ApprovalPreview with _$ApprovalPreview {
  const factory ApprovalPreview({
    required String caseId,
    required int stateVersion,
    required String action,
    required String target,
    required String payloadHash,
    required bool reversible,
  }) = _ApprovalPreview;
  factory ApprovalPreview.fromJson(Map<String, dynamic> json) => _$ApprovalPreviewFromJson(json);
}

@freezed
class ProductSearchResult with _$ProductSearchResult {
  const factory ProductSearchResult({
    required String query,
    required List<ProductMatch> results,
  }) = _ProductSearchResult;
  factory ProductSearchResult.fromJson(Map<String, dynamic> json) {
    final hits = (json['hits'] as List? ?? [])
        .map((e) => ProductMatch.fromJson(e as Map<String, dynamic>))
        .toList();
    return ProductSearchResult(query: json['query']?.toString() ?? '', results: hits);
  }
}

@freezed
class ProductMatch with _$ProductMatch {
  const factory ProductMatch({
    required String productId,
    required String name,
    required String description,
    required double score,
  }) = _ProductMatch;
  factory ProductMatch.fromJson(Map<String, dynamic> json) => _$ProductMatchFromJson(json);
}
