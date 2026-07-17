import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'adapters/backend_adapter.dart';
import 'models/case_models.dart';

part 'api_client.freezed.dart';
part 'api_client.g.dart';

/// Default backend endpoint. Override via constructor (e.g. local CF tunnel).
const String kDefaultBaseUrl = 'https://vaic-api.w9.nu';

/// API client for RM Workspace backend
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
        if (_authToken != null) 'Authorization': 'Bearer $_authToken',
      };

  Future<T> _request<T>(Future<http.Response> Function() call, T Function(Map<String, dynamic>) parser) async {
    try {
      final response = await call().timeout(const Duration(seconds: 30));
      if (response.statusCode >= 200 && response.statusCode < 300) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return parser(data);
      }
      throw ApiException(
        statusCode: response.statusCode,
        message: _parseError(response.body),
      );
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

  // GET /api/v1/cases  -> backend returns List[SharedCaseState]
  Future<List<CaseQueueItem>> getCases({Map<String, String>? query}) async {
    final uri = Uri.parse('$baseUrl/api/v1/cases').replace(queryParameters: query);
    final response = await _client.get(uri, headers: _headers).timeout(const Duration(seconds: 30));
    if (response.statusCode >= 200 && response.statusCode < 300) {
      final data = jsonDecode(response.body);
      if (data is List) return mapQueue(data);
      if (data is Map && data['cases'] is List) return mapQueue(data['cases'] as List);
      return [];
    }
    throw ApiException(statusCode: response.statusCode, message: _parseError(response.body));
  }

  // GET /api/v1/cases/{caseId} -> backend returns SharedCaseState dict
  Future<CaseDetail> getCase(String caseId) async {
    final uri = Uri.parse('$baseUrl/api/v1/cases/$caseId');
    final response = await _client.get(uri, headers: _headers).timeout(const Duration(seconds: 30));
    if (response.statusCode >= 200 && response.statusCode < 300) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return mapDetail(data);
    }
    throw ApiException(statusCode: response.statusCode, message: _parseError(response.body));
  }

  // POST /api/v1/cases/{caseId}/approval-token
  Future<ApprovalTokenResponse> issueApprovalToken(String caseId, String rmId, {String? comments}) async {
    final uri = Uri.parse('$baseUrl/api/v1/cases/$caseId/approval-token');
    return _request(
      () => _client.post(uri, headers: _headers, body: jsonEncode({'rm_id': rmId, 'comments': comments})),
      (data) => ApprovalTokenResponse.fromJson(data),
    );
  }

  // POST /api/v1/cases/{caseId}/approve
  Future<ApprovalResult> approveCase(String caseId, String rmId, String token, {String? comments}) async {
    final uri = Uri.parse('$baseUrl/api/v1/cases/$caseId/approve');
    return _request(
      () => _client.post(
        uri,
        headers: {..._headers, 'x-approval-token': token},
        body: jsonEncode({'rm_id': rmId, 'comments': comments}),
      ),
      (data) => ApprovalResult.fromJson(data),
    );
  }

  // POST /api/v1/cases/{caseId}/reject
  Future<ApprovalResult> rejectCase(String caseId, String rmId, String reason) async {
    final uri = Uri.parse('$baseUrl/api/v1/cases/$caseId/reject');
    return _request(
      () => _client.post(uri, headers: _headers, body: jsonEncode({'rm_id': rmId, 'reason': reason})),
      (data) => ApprovalResult.fromJson(data),
    );
  }

  // GET /api/v1/search/products
  Future<ProductSearchResult> searchProducts(String query, {int topK = 5}) async {
    final uri = Uri.parse('$baseUrl/api/v1/search/products').replace(queryParameters: {'q': query, 'top_k': topK.toString()});
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
    required String approvalToken,
    required int expiresIn,
  }) = _ApprovalTokenResponse;
  factory ApprovalTokenResponse.fromJson(Map<String, dynamic> json) => _$ApprovalTokenResponseFromJson(json);
}

@freezed
class ApprovalResult with _$ApprovalResult {
  const factory ApprovalResult({
    required String caseId,
    required String approvalStatus,
    required String finalStatus,
    required List<dynamic> actionsExecuted,
  }) = _ApprovalResult;
  factory ApprovalResult.fromJson(Map<String, dynamic> json) => _$ApprovalResultFromJson(json);
}

@freezed
class ProductSearchResult with _$ProductSearchResult {
  const factory ProductSearchResult({
    required List<ProductMatch> results,
  }) = _ProductSearchResult;
  factory ProductSearchResult.fromJson(Map<String, dynamic> json) => _$ProductSearchResultFromJson(json);
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