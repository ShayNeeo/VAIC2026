import 'package:flutter/material.dart';
import '../api_client.dart';
import '../api_config.dart';
import '../models/employee_models.dart';

/// Demo personas mapped to backend Bearer tokens -- see
/// docs/ROLE_AWARE_P0_FIX_IMPLEMENTATION_REPORT.md for how the backend
/// resolves "demo-*" tokens to a verified identity via SSOPort/IAMPort.
/// Never a real credential; DEMO_AUTH_ENABLED must be true on the backend
/// for these to work (the default outside APP_ENV=production).
const Map<String, String> kDemoPersonas = {
  'demo-rm-999': 'RM · Nguyễn Văn A (RM-999)',
  'demo-spec-legal-001': 'Legal Specialist (SPEC-LEGAL-001)',
  'demo-spec-prod-001': 'Product Specialist (SPEC-PROD-001)',
  'demo-spec-ops-001': 'Operations Specialist (SPEC-OPS-001)',
  'demo-mgr-hn-01': 'Manager · Chi nhánh HN (MGR-HN-01)',
};

/// Drives the Role-Aware Employee Copilot workspace: context, work queue,
/// personalization, and (for managers) the team aggregate dashboard.
class EmployeeWorkspaceController extends ChangeNotifier {
  final ApiClient api;
  String currentEmployeeId = '';
  bool isAuthenticated = false;

  EmployeeContext? context;
  List<WorkQueueItem> workQueue = [];
  Map<String, dynamic>? teamWorkload;
  bool isLoading = false;
  String? error;

  EmployeeWorkspaceController({ApiClient? apiClient}) : api = apiClient ?? buildApiClient();

  bool get isManager => context?.authorizationContext.primaryRole == 'manager';

  Future<void> login(String employeeId, String password) async {
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      await api.login(employeeId.trim().toUpperCase(), password);
      currentEmployeeId = employeeId.trim().toUpperCase();
      isAuthenticated = true;
      await _refreshAuthenticated();
    } catch (e) {
      isAuthenticated = false;
      error = e.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  void logout() {
    api.clearAuthToken();
    currentEmployeeId = '';
    isAuthenticated = false;
    context = null;
    workQueue = [];
    teamWorkload = null;
    error = null;
    notifyListeners();
  }

  Future<void> switchPersona(String demoToken) async {
    // Kept for backwards compatibility with older internal navigation.
    final employeeId = demoToken.replaceFirst('demo-', '').toUpperCase();
    final password = 'demo1234';
    await login(employeeId, password);
  }

  Future<void> _refreshAuthenticated() async {
    await refresh();
  }

  Future<void> refresh() async {
    isLoading = true;
    error = null;
    notifyListeners();
    try {
      context = await api.getMyContext();
      if (isManager) {
        teamWorkload = await api.getTeamWorkload();
        workQueue = [];
      } else {
        workQueue = await api.getMyWorkQueue();
        teamWorkload = null;
      }
    } catch (e) {
      error = e.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> submitFeedback(String workItemId, String feedback) async {
    try {
      await api.submitRecommendationFeedback(workItemId, feedback);
      await refresh();
    } catch (e) {
      error = e.toString();
      notifyListeners();
    }
  }

  Future<void> togglePersonalization(bool enabled) async {
    try {
      await api.setPersonalizationEnabled(enabled);
      await refresh();
    } catch (e) {
      error = e.toString();
      notifyListeners();
    }
  }
}
