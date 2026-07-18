import 'package:flutter/material.dart';
import '../api_client.dart';
import '../models/case_models.dart';
import '../mock/mock_loader.dart';

/// Simple controller for case queue/list
class CaseController extends ChangeNotifier {
  final ApiClient api;
  List<CaseQueueItem> _cases = [];
  String _filter = 'all'; // all, ready, need_info, review_required, blocked
  bool _isLoading = false;
  String? _error;

  CaseController({ApiClient? apiClient}) : api = apiClient ?? ApiClient();

  List<CaseQueueItem> get cases => _cases;
  String get filter => _filter;
  bool get isLoading => _isLoading;
  String? get error => _error;

  List<CaseQueueItem> get filteredCases {
    if (_filter == 'all') return _cases;
    return _cases.where((c) => _hasStatus(c, _filter)).toList();
  }

  bool _hasStatus(CaseQueueItem c, String f) {
    final counts = c.branchStatusCounts;
    switch (f) {
      case 'ready': return (counts['ready'] ?? 0) > 0;
      case 'need_info': return (counts['need_info'] ?? 0) > 0;
      case 'review_required': return (counts['review_required'] ?? 0) > 0;
      case 'blocked': return (counts['blocked'] ?? 0) > 0;
      default: return false;
    }
  }

  Future<void> loadCases({bool useMock = true}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      if (useMock) {
        _cases = await MockLoader.loadQueue();
      } else {
        try {
          final live = await api.getCases();
          if (live.isEmpty) {
            _cases = await MockLoader.loadQueue();
          } else {
            _cases = live;
          }
        } catch (e) {
          // Live backend unavailable -> fall back to synthetic mock so the
          // RM demo never shows a hard error.
          _cases = await MockLoader.loadQueue();
          _error = null;
        }
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void setFilter(String f) {
    _filter = f;
    notifyListeners();
  }
}

/// Controller for case detail (S2)
class CaseDetailController extends ChangeNotifier {
  final ApiClient api;
  CaseDetail? _case;
  bool _isLoading = false;
  String? _error;

  CaseDetailController({ApiClient? apiClient}) : api = apiClient ?? ApiClient();

  CaseDetail? get caseDetail => _case;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> loadCase(String caseId, {bool useMock = true}) async {
    _isLoading = true;
    _error = null;
    _case = null;
    notifyListeners();

    try {
      if (useMock) {
        _case = await MockLoader.loadCase(caseId);
      } else {
        try {
          _case = await api.getCase(caseId);
        } catch (e) {
          _case = await MockLoader.loadCase(caseId);
          _error = null;
        }
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}