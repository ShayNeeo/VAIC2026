import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/controllers/employee_workspace_controller.dart';
import '../../core/models/employee_models.dart';
import '../../design/design.dart';

/// Role-Aware Employee Copilot workspace: real /api/v2/me/* calls, not
/// the /api/v1 case-queue mock path the rest of this app currently uses.
/// See docs/ROLE_AWARE_P0_FIX_IMPLEMENTATION_REPORT.md "Flutter wiring".
class EmployeeWorkspaceScreen extends StatefulWidget {
  const EmployeeWorkspaceScreen({super.key});

  @override
  State<EmployeeWorkspaceScreen> createState() => _EmployeeWorkspaceScreenState();
}

class _EmployeeWorkspaceScreenState extends State<EmployeeWorkspaceScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<EmployeeWorkspaceController>().refresh();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<EmployeeWorkspaceController>(
      builder: (context, controller, _) => Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          backgroundColor: AppColors.navy900,
          foregroundColor: Colors.white,
          title: const Text('Employee Copilot'),
          actions: [
            PopupMenuButton<String>(
              icon: const Icon(Icons.person_outline),
              onSelected: (token) => controller.switchPersona(token),
              itemBuilder: (context) => kDemoPersonas.entries
                  .map((e) => PopupMenuItem(value: e.key, child: Text(e.value)))
                  .toList(),
            ),
          ],
        ),
        body: RefreshIndicator(
          onRefresh: controller.refresh,
          child: controller.isLoading
              ? const Center(child: CircularProgressIndicator())
              : controller.error != null
                  ? _ErrorView(message: controller.error!, onRetry: controller.refresh)
                  : _WorkspaceBody(controller: controller),
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        const SizedBox(height: 80),
        const Icon(Icons.error_outline, size: 48, color: AppColors.statusBlocked),
        const SizedBox(height: 12),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Text(message, textAlign: TextAlign.center),
        ),
        const SizedBox(height: 12),
        Center(child: OutlinedButton(onPressed: onRetry, child: const Text('Thử lại'))),
      ],
    );
  }
}

class _WorkspaceBody extends StatelessWidget {
  final EmployeeWorkspaceController controller;
  const _WorkspaceBody({required this.controller});

  @override
  Widget build(BuildContext context) {
    final ctx = controller.context;
    if (ctx == null) return const SizedBox.shrink();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _IdentityCard(ctx: ctx),
        const SizedBox(height: 16),
        if (controller.isManager)
          _ManagerDashboard(workload: controller.teamWorkload)
        else
          _WorkQueueSection(controller: controller),
      ],
    );
  }
}

class _IdentityCard extends StatelessWidget {
  final EmployeeContext ctx;
  const _IdentityCard({required this.ctx});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(ctx.employeeId, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            const SizedBox(height: 4),
            Text('Vai trò: ${ctx.authorizationContext.primaryRole}'),
            Text('Phạm vi khách hàng: ${ctx.authorizationContext.customerScope.join(", ")}'),
            if (ctx.personalizationContext.personalizationDegraded)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Chip(
                  label: const Text('Personalization đang ở chế độ mặc định (store lỗi)'),
                  backgroundColor: AppColors.statusNeedInfo100,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _WorkQueueSection extends StatelessWidget {
  final EmployeeWorkspaceController controller;
  const _WorkQueueSection({required this.controller});

  @override
  Widget build(BuildContext context) {
    if (controller.workQueue.isEmpty) {
      return const Padding(
        padding: EdgeInsets.only(top: 32),
        child: Center(child: Text('Không có việc cần ưu tiên.')),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Next Best Work', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        ...controller.workQueue.map((item) => _WorkItemCard(item: item, controller: controller)),
      ],
    );
  }
}

class _WorkItemCard extends StatelessWidget {
  final WorkQueueItem item;
  final EmployeeWorkspaceController controller;
  const _WorkItemCard({required this.item, required this.controller});

  Color get _priorityColor {
    switch (item.priority) {
      case 'high':
        return AppColors.statusBlocked;
      case 'medium':
        return AppColors.statusNeedInfo;
      default:
        return AppColors.statusAiCta;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: _priorityColor,
          child: Text(item.priorityScore.toStringAsFixed(0), style: const TextStyle(color: Colors.white, fontSize: 12)),
        ),
        title: Text(item.title),
        subtitle: Text(item.reasons.isNotEmpty ? item.reasons.first : ''),
        trailing: item.requiresApproval
            ? const Tooltip(message: 'Cần RM phê duyệt trước khi thực thi', child: Icon(Icons.lock_outline))
            : IconButton(
                icon: const Icon(Icons.check_circle_outline),
                onPressed: () => controller.submitFeedback(item.workItemId, 'accepted'),
              ),
      ),
    );
  }
}

class _ManagerDashboard extends StatelessWidget {
  final Map<String, dynamic>? workload;
  const _ManagerDashboard({required this.workload});

  @override
  Widget build(BuildContext context) {
    if (workload == null) return const SizedBox.shrink();
    final metrics = (workload!['aggregate_metrics'] as Map?)?.cast<String, dynamic>() ?? {};
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Aggregate Team Workload', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 8),
            Text('Case bị chặn: ${metrics['blocked_cases'] ?? 0}'),
            Text('Rủi ro SLA: ${metrics['sla_risks'] ?? 0}'),
            const SizedBox(height: 8),
            const Text(
              'Chỉ hiển thị số liệu tổng hợp — không có preference/habit cá nhân của từng RM.',
              style: TextStyle(fontStyle: FontStyle.italic, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}
