/// Plain (non-freezed) models for the Role-Aware Employee Copilot API
/// (/api/v2/me/*, /api/v2/recommendations/*).
///
/// Hand-written rather than @freezed on purpose: the freezed/json_serializable
/// generated part files (api_client.freezed.dart / api_client.g.dart) are
/// checked-in, pre-generated code this change cannot safely regenerate
/// (no Flutter/Dart SDK available in the environment this was written in --
/// see docs/ROLE_AWARE_P0_FIX_IMPLEMENTATION_REPORT.md "Flutter wiring"
/// section for the exact verification status of this file).
library employee_models;

class AuthorizationContext {
  final bool identityVerified;
  final List<String> roles;
  final List<String> permissions;
  final List<String> customerScope;

  AuthorizationContext({
    required this.identityVerified,
    required this.roles,
    required this.permissions,
    required this.customerScope,
  });

  factory AuthorizationContext.fromJson(Map<String, dynamic> json) => AuthorizationContext(
        identityVerified: json['identity_verified'] as bool? ?? false,
        roles: (json['roles'] as List? ?? []).map((e) => e.toString()).toList(),
        permissions: (json['permissions'] as List? ?? []).map((e) => e.toString()).toList(),
        customerScope: (json['customer_scope'] as List? ?? []).map((e) => e.toString()).toList(),
      );

  String get primaryRole => roles.isNotEmpty ? roles.first : 'unknown';
}

class PersonalizationContext {
  final bool enabled;
  final Map<String, dynamic> preferences;
  final bool personalizationDegraded;

  PersonalizationContext({
    required this.enabled,
    required this.preferences,
    required this.personalizationDegraded,
  });

  factory PersonalizationContext.fromJson(Map<String, dynamic> json) => PersonalizationContext(
        enabled: json['enabled'] as bool? ?? false,
        preferences: (json['preferences'] as Map?)?.cast<String, dynamic>() ?? {},
        personalizationDegraded: json['personalization_degraded'] as bool? ?? false,
      );
}

class EmployeeContext {
  final String employeeId;
  final AuthorizationContext authorizationContext;
  final PersonalizationContext personalizationContext;
  final List<String> pendingTaskIds;

  EmployeeContext({
    required this.employeeId,
    required this.authorizationContext,
    required this.personalizationContext,
    required this.pendingTaskIds,
  });

  factory EmployeeContext.fromJson(Map<String, dynamic> json) => EmployeeContext(
        employeeId: json['employee_id'] as String? ?? '',
        authorizationContext:
            AuthorizationContext.fromJson((json['authorization_context'] as Map?)?.cast<String, dynamic>() ?? {}),
        personalizationContext:
            PersonalizationContext.fromJson((json['personalization_context'] as Map?)?.cast<String, dynamic>() ?? {}),
        pendingTaskIds: ((json['work_context'] as Map?)?['pending_task_ids'] as List? ?? [])
            .map((e) => e.toString())
            .toList(),
      );
}

class WorkQueueItem {
  final String workItemId;
  final String title;
  final double priorityScore;
  final String priority; // "high" | "medium" | "low"
  final List<String> reasons;
  final List<String> excludedActions;
  final String recommendedAction;

  WorkQueueItem({
    required this.workItemId,
    required this.title,
    required this.priorityScore,
    required this.priority,
    required this.reasons,
    required this.excludedActions,
    required this.recommendedAction,
  });

  factory WorkQueueItem.fromJson(Map<String, dynamic> json) => WorkQueueItem(
        workItemId: json['work_item_id'] as String? ?? '',
        title: json['title'] as String? ?? '',
        priorityScore: (json['priority_score'] as num?)?.toDouble() ?? 0.0,
        priority: json['priority'] as String? ?? 'low',
        reasons: (json['reasons'] as List? ?? []).map((e) => e.toString()).toList(),
        excludedActions: (json['excluded_actions'] as List? ?? []).map((e) => e.toString()).toList(),
        recommendedAction: json['recommended_action'] as String? ?? '',
      );

  bool get requiresApproval => excludedActions.contains('execute_crm_action');
}
