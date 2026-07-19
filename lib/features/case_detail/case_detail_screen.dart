import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';
import '../../design/theme/app_theme.dart';
import '../../design/widgets/agent_os.dart';
import '../../design/widgets/nav_sidebar.dart';

/// S2 — Agent Case Workspace: live multi-agent state for one sales-case.
class CaseDetailScreen extends StatefulWidget {
  final String caseId;
  const CaseDetailScreen({super.key, required this.caseId});

  @override
  State<CaseDetailScreen> createState() => _CaseDetailScreenState();
}

class _CaseDetailScreenState extends State<CaseDetailScreen> {
  final _ctrl = SalesCaseController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _ctrl.openCase(widget.caseId));
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider.value(
      value: _ctrl,
      child: Consumer<SalesCaseController>(
        builder: (context, ctrl, _) => AgentMeshBackground(
          child: Scaffold(
            backgroundColor: Colors.transparent,
            drawer: Drawer(child: SafeArea(child: NavSidebar(current: 'case', employeeId: ctrl.activeId ?? 'CASE', roleLabel: 'Case'))),
            appBar: AppBar(
              backgroundColor: Colors.transparent,
              elevation: 0,
              leading: IconButton(icon: const Icon(Icons.arrow_back, color: AppColors.txt2), onPressed: () => context.go('/queue')),
              title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Case ${widget.caseId}', style: GoogleFonts.beVietnamPro(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.txt)),
                const Text('Multi-Agent Decision Workspace', style: TextStyle(fontSize: 11, color: AppColors.cyanSoft)),
              ]),
              actions: [
                FilledButton.tonalIcon(
                  onPressed: ctrl.isBusy ? null : ctrl.activeStage < 2 ? ctrl.runProcess : (ctrl.activeStage == 2 ? ctrl.confirmProfile : ctrl.runAnalysis),
                  icon: Icon(ctrl.activeStage < 2 ? Icons.auto_awesome_outlined : (ctrl.activeStage == 2 ? Icons.verified_user_outlined : Icons.hub_outlined)),
                  label: Text(ctrl.activeStage < 2 ? 'Chạy Intake' : (ctrl.activeStage == 2 ? 'Xác nhận' : 'Chạy Agents')),
                ),
                const SizedBox(width: 10),
              ],
            ),
            body: _Body(ctrl: ctrl),
          ),
        ),
      ),
    );
  }
}

class _Body extends StatelessWidget {
  final SalesCaseController ctrl;
  const _Body({required this.ctrl});

  @override
  Widget build(BuildContext context) {
    if (ctrl.isLoading) return const Center(child: CircularProgressIndicator(color: AppColors.cyan));
    final c = ctrl.active;
    final stage = ctrl.activeStage;
    final name = ((c?['company_name'] ?? c?['customer_id']) ?? 'Khách hàng').toString();
    return SingleChildScrollView(
      padding: responsivePadding(context),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        GlassCard(
          glow: AppColors.cyan,
          child: Row(children: [
            Container(width: 50, height: 50, decoration: BoxDecoration(gradient: const LinearGradient(colors: [AppColors.cyan, AppColors.violet]), borderRadius: BorderRadius.circular(13)), child: Center(child: Text(name.isNotEmpty ? name.substring(0, name.length >= 2 ? 2 : 1).toUpperCase() : '?', style: const TextStyle(color: AppColors.ink900, fontWeight: FontWeight.w800)))),
            const SizedBox(width: 14),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.txt)),
              Text(widget_caseId(ctrl), style: GoogleFonts.jetBrainsMono(fontSize: 11, color: AppColors.muted)),
            ])),
            if (ctrl.info != null) StatusToken(status: AgentStatus.ready, label: 'Live'),
          ]),
        ),
        const SizedBox(height: 16),
        AgentPipeline(activeStage: stage, doneStages: ctrl.doneStages),
        const SizedBox(height: 16),
        if (ctrl.info != null)
          Container(margin: const EdgeInsets.only(bottom: 12), padding: const EdgeInsets.all(12), decoration: BoxDecoration(color: AppColors.cyan.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12), border: Border.all(color: AppColors.cyan.withValues(alpha: 0.4))), child: Row(children: [const Icon(Icons.auto_awesome_outlined, color: AppColors.cyan, size: 16), const SizedBox(width: 8), Expanded(child: Text(ctrl.info!, style: const TextStyle(fontSize: 12, color: AppColors.cyanSoft)))])),
        if (ctrl.error != null)
          Container(margin: const EdgeInsets.only(bottom: 12), padding: const EdgeInsets.all(12), decoration: BoxDecoration(color: AppColors.blockBg, borderRadius: BorderRadius.circular(12), border: Border.all(color: AppColors.block.withValues(alpha: 0.5))), child: Text(ctrl.error!, style: const TextStyle(color: AppColors.block, fontSize: 12))),
        GlassCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const SectionHeader(title: 'AI Decision Log', caption: 'Agent trace · model · cost · latency', icon: Icons.terminal_outlined),
            const SizedBox(height: 12),
            ..._agentLogs(ctrl),
          ]),
        ),
        const SizedBox(height: 16),
        if (stage >= 4)
          GlassCard(
            glow: AppColors.lime,
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const AgentKicker(label: 'Approval Gate', icon: Icons.gavel_outlined),
              const SizedBox(height: 10),
              const Text('Case đã qua Risk Gate. Chuyển đến màn hình duyệt để RM ký payload.', style: TextStyle(fontSize: 13, color: AppColors.txt2)),
              const SizedBox(height: 12),
              SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: () => context.go('/approval/${ctrl.activeId}'), icon: const Icon(Icons.gavel), label: const Text('Mở Approval'))),
            ]),
          ),
        const SizedBox(height: 24),
      ]),
    );
  }

  String widget_caseId(SalesCaseController ctrl) => ctrl.activeId ?? '';

  List<Widget> _agentLogs(SalesCaseController ctrl) {
    final c = ctrl.active ?? {};
    final aiLog = (c['ai_decision_log'] as List?) ?? [];
    if (aiLog.isEmpty) {
      return [const Text('Chưa có agent trace — chạy Intake / Agents để bắt đầu.', style: TextStyle(color: AppColors.muted, fontSize: 12))];
    }
    return aiLog.map((e) {
      final m = e as Map<String, dynamic>;
      return Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(margin: const EdgeInsets.only(top: 4), width: 7, height: 7, decoration: const BoxDecoration(color: AppColors.lime, shape: BoxShape.circle)),
          const SizedBox(width: 10),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text((m['component'] ?? 'agent').toString(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.txt)),
            if (m['summary'] != null) Text(m['summary'].toString(), style: const TextStyle(fontSize: 11, color: AppColors.muted)),
          ])),
        ]),
      );
    }).toList();
  }
}
