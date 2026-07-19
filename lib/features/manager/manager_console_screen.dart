import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/rm_workspace_core.dart';
import '../../design/theme/app_theme.dart';
import '../../design/widgets/agent_os.dart';
import '../../design/widgets/nav_sidebar.dart';
import '../../design/design.dart';

// ignore_for_file: avoid_types_on_closure_parameters

/// Branch Manager console — aggregate team workload only.
class ManagerConsoleScreen extends StatefulWidget {
  const ManagerConsoleScreen({super.key});

  @override
  State<ManagerConsoleScreen> createState() => _ManagerConsoleScreenState();
}

class _ManagerConsoleScreenState extends State<ManagerConsoleScreen> {
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
      builder: (context, ctrl, _) => AgentMeshBackground(
        child: Scaffold(
          backgroundColor: Colors.transparent,
          drawer: Drawer(child: SafeArea(child: NavSidebar(current: 'manager', employeeId: ctrl.context?.employeeId ?? 'MGR', roleLabel: 'Branch Manager'))),
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Branch Console', style: GoogleFonts.beVietnamPro(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.txt)),
              const Text('HN01 · Aggregate team workload', style: TextStyle(fontSize: 11, color: AppColors.orange)),
            ]),
            actions: [
              if (ctrl.context != null) Padding(padding: const EdgeInsets.only(right: 6), child: Center(child: Text(ctrl.context!.employeeId, style: const TextStyle(color: AppColors.txt2, fontWeight: FontWeight.w700)))),
              IconButton(icon: const Icon(Icons.logout, color: AppColors.txt2), onPressed: () { ctrl.logout(); context.go('/login'); }),
              const SizedBox(width: 8),
            ],
          ),
          body: ctrl.isLoading
              ? const Center(child: CircularProgressIndicator(color: AppColors.orange))
              : ctrl.error != null
                  ? _Error(message: ctrl.error!, onRetry: ctrl.refresh)
                  : _Body(ctrl: ctrl),
        ),
      ),
    );
  }
}

class _Error extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _Error({required this.message, required this.onRetry});
  @override
  Widget build(BuildContext context) => Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.error_outline, size: 44, color: AppColors.block),
          const SizedBox(height: 12),
          Text(message, style: const TextStyle(color: AppColors.block)),
          const SizedBox(height: 12),
          OutlinedButton(onPressed: onRetry, child: const Text('Thử lại')),
        ]),
      );
}

class _Body extends StatelessWidget {
  final EmployeeWorkspaceController ctrl;
  const _Body({required this.ctrl});

  @override
  Widget build(BuildContext context) {
    final wl = ctrl.teamWorkload ?? {};
    final m = (wl['aggregate_metrics'] as Map?)?.cast<String, dynamic>() ?? {};
    final blocked = (m['blocked_cases'] ?? 0) as int;
    final sla = (m['sla_risks'] ?? 0) as int;
    final total = (m['total_cases'] ?? 0) as int;
    return SingleChildScrollView(
      padding: responsivePadding(context),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        GlassCard(
          glow: AppColors.violet,
          child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            AgentKicker(label: 'Manager Console', icon: Icons.shield_outlined),
            SizedBox(height: 10),
            Text('Chỉ hiển thị số liệu tổng hợp — không có preference/habit cá nhân của từng RM.', style: TextStyle(fontSize: 12, color: AppColors.muted)),
          ]),
        ),
        const SizedBox(height: 16),
        LayoutBuilder(
          builder: (context, c) {
            final cols = c.maxWidth >= 720 ? 3 : (c.maxWidth >= 420 ? 2 : 1);
            final w = (c.maxWidth - (cols - 1) * 12) / cols;
            return Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                SizedBox(width: w, child: const NeonMetric(label: 'Tổng cases', value: '0', icon: Icons.cases_outlined, accent: AppColors.navy, sub: 'live pipeline')),
                SizedBox(width: w, child: NeonMetric(label: 'Đang mở', value: '$total', icon: Icons.timelapse_outlined, accent: AppColors.orange, sub: 'in workflow')),
                SizedBox(width: w, child: NeonMetric(label: 'Chặn / SLA', value: '$blocked / $sla', icon: Icons.warning_amber_outlined, accent: AppColors.block, sub: 'needs attention')),
              ],
            );
          },
        ),
        const SizedBox(height: 18),
        GlassCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const SectionHeader(title: 'Team Workload', caption: 'Aggregate view · role-isolated', icon: Icons.insights_outlined),
            const SizedBox(height: 12),
            _Row(label: 'Case bị chặn', value: '$blocked', color: AppColors.block),
            const Divider(height: 1),
            _Row(label: 'Rủi ro SLA', value: '$sla', color: AppColors.needInfo),
            const Divider(height: 1),
            _Row(label: 'Tổng case', value: '$total', color: AppColors.cyan),
          ]),
        ),
        const SizedBox(height: 24),
      ]),
    );
  }
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _Row({required this.label, required this.value, required this.color});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 9),
        child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text(label, style: const TextStyle(fontSize: 13, color: AppColors.txt2)),
          Container(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5), decoration: BoxDecoration(color: color.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(999)), child: Text(value, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: color))),
        ]),
      );
}
