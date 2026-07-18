import 'package:flutter/material.dart';
import '../api_client.dart';

/// Drives the README §4 multi-agent sales-case lifecycle against the live
/// v2 backend: draft → upload → process → confirm → run-analysis → review → approval.
class SalesCaseController extends ChangeNotifier {
  final ApiClient api;
  List<Map<String, dynamic>> _cases = [];
  Map<String, dynamic>? _active;
  String? _activeId;
  int _activeStage = 0;
  final Set<int> _doneStages = {};
  bool _isLoading = false;
  bool _isBusy = false;
  String? _error;
  String? _info;

  SalesCaseController({ApiClient? apiClient}) : api = apiClient ?? ApiClient();

  List<Map<String, dynamic>> get cases => _cases;
  Map<String, dynamic>? get active => _active;
  String? get activeId => _activeId;
  int get activeStage => _activeStage;
  Set<int> get doneStages => _doneStages;
  bool get isLoading => _isLoading;
  bool get isBusy => _isBusy;
  String? get error => _error;
  String? get info => _info;

  static const _stages = ['draft', 'files_uploaded', 'extraction_completed', 'profile_confirmed', 'analysis_completed', 'approval_issued'];

  void _stageFromStatus(String status) {
    final idx = _stages.indexOf(status);
    if (idx >= 0) {
      _activeStage = idx;
      _doneStages.addAll({for (int i = 0; i <= idx; i++) i});
    }
  }

  Future<void> loadCases() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _cases = await api.listSalesCases();
    } catch (e) {
      _error = e.toString();
      _cases = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> openCase(String caseId) async {
    _isLoading = true;
    _error = null;
    _info = null;
    _activeId = caseId;
    notifyListeners();
    try {
      final found = _cases.where((c) => c['case_id'] == caseId).firstOrNull;
      _active = found;
      if (found != null) _stageFromStatus((found['intake_status'] ?? 'draft').toString());
      if (_activeStage < 1) {
        // try to pull profile/analysis status
        try {
          final prof = await api.extractedProfile(caseId);
          if (prof['profile'] != null) _stageFromStatus('extraction_completed');
        } catch (_) {}
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void closeActive() {
    _active = null;
    _activeId = null;
    _activeStage = 0;
    _doneStages.clear();
    notifyListeners();
  }

  Future<void> createCase({
    required String companyName,
    required String needText,
    String? taxCode,
    String? industry,
    String priority = 'normal',
  }) async {
    _isBusy = true;
    _error = null;
    _info = null;
    notifyListeners();
    try {
      final created = await api.createSalesCase({
        'company_name': companyName,
        'need_text': needText,
        'tax_code': taxCode,
        'industry': industry,
        'priority': priority,
      });
      final caseId = (created['case_id'] ?? created['intake_id'] ?? '').toString();
      _info = 'Đã tạo case $caseId';
      await loadCases();
      if (caseId.isNotEmpty) await openCase(caseId);
    } catch (e) {
      _error = e.toString();
    } finally {
      _isBusy = false;
      notifyListeners();
    }
  }

  Future<void> runProcess() async {
    if (_activeId == null) return;
    _isBusy = true;
    _error = null;
    notifyListeners();
    try {
      await api.processDocuments(_activeId!);
      _info = 'Đã chạy Document Intelligence — đang trích xuất hồ sơ';
      _activeStage = 2;
      _doneStages.addAll({0, 1, 2});
      _active = await api.extractedProfile(_activeId!);
    } catch (e) {
      _error = e.toString();
    } finally {
      _isBusy = false;
      notifyListeners();
    }
  }

  Future<void> confirmProfile() async {
    if (_activeId == null) return;
    final version = (_active?['version'] as int?) ?? 1;
    _isBusy = true;
    _error = null;
    notifyListeners();
    try {
      await api.confirmProfile(_activeId!, version);
      _info = 'Đã xác nhận Customer Business Snapshot (Confirmation Gate)';
      _activeStage = 3;
      _doneStages.addAll({0, 1, 2, 3});
      await loadCases();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isBusy = false;
      notifyListeners();
    }
  }

  Future<void> runAnalysis() async {
    if (_activeId == null) return;
    final version = (_active?['version'] as int?) ?? 1;
    _isBusy = true;
    _error = null;
    _info = 'Các agent đang phân tích: Planner → Product → Compliance → Operations → Risk Gate…';
    notifyListeners();
    try {
      final res = await api.runAnalysis(_activeId!, version);
      _info = 'Phân tích end-to-end hoàn tất.';
      _activeStage = 4;
      _doneStages.addAll({0, 1, 2, 3, 4});
      _active = res['state'] as Map<String, dynamic>? ?? _active;
      await loadCases();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isBusy = false;
      notifyListeners();
    }
  }
}
