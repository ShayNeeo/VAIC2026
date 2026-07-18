import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';

/// S1 — Agent Command Center: live sales-case queue + multi-agent pipeline.
class QueueScreen extends StatefulWidget {
  const QueueScreen({super.key});

  @override
  State<QueueScreen> createState() => _QueueScreenState();
}

class _QueueScreenState extends State<QueueScreen> {
  final _search = TextEditingController();
  final _company = TextEditingController();
  final _need = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SalesCaseController>().loadCases();
    });
    _search.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _search.dispose();
    _company.dispose();
    _need.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<SalesCaseController>(
      builder: (context, ctrl, _) => AgentMeshBackground(
        child: Scaffold(
          backgroundColor: Colors.transparent,
          drawer: Drawer(child: SafeArea(child: NavSidebar(current: 'queue'))),
          appBar: _appBar(context, ctrl),
          floatingActionButton: FloatingActionButton.extended(
            onPressed: () => _showCreate(context, ctrl),
            backgroundColor: AppColors.cyan,
            foregroundColor: AppColors.ink900,
            icon: const Icon(Icons.add),
            label: const Text('Tạo sales case', style: TextStyle(fontWeight: FontWeight.w800)),
          ),
          body: _Body(ctrl: ctrl, search: _search),
        ),
      ),
    );
  }

  PreferredSizeWidget _appBar(BuildContext context, SalesCaseController ctrl) => AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Row(children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(gradient: const LinearGradient(colors: [AppColors.cyan, AppColors.violet]), borderRadius: BorderRadius.circular(11)),
            child: const Icon(Icons.bolt_outlined, color: AppColors.ink900, size: 18),
          ),
          const SizedBox(width: 12),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Command Center', style: GoogleFonts.spaceGrotesk(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.txt)),
            const Text('Multi-Agent Sales Workflow', style: TextStyle(fontSize: 11, color: AppColors.cyanSoft)),
          ]),
        ]),
        actions: [
          IconButton(icon: const Icon(Icons.refresh, color: AppColors.txt2), onPressed: ctrl.isLoading ? null : ctrl.loadCases),
          const SizedBox(width: 8),
        ],
      );

  void _showCreate(BuildContext context, SalesCaseController ctrl) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.ink800,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        contentPadding: const EdgeInsets.all(22),
        content: SizedBox(
          width: 440,
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            const AgentKicker(label: 'New Intake', icon: Icons.upload_file_outlined),
            const SizedBox(height: 14),
            TextField(
              controller: _company,
              style: const TextStyle(color: AppColors.txt, fontFamily: 'Hanken Grotesk'),
              decoration: const InputDecoration(labelText: 'Tên doanh nghiệp', prefixIcon: Icon(Icons.business_outlined)),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _need,
              maxLines: 3,
              style: const TextStyle(color: AppColors.txt, fontFamily: 'Hanken Grotesk'),
              decoration: const InputDecoration(labelText: 'Nhu cầu tín dụng / sản phẩm', prefixIcon: Icon(Icons.edit_note_outlined)),
            ),
            const SizedBox(height: 18),
            if (ctrl.error != null)
              Padding(padding: const EdgeInsets.only(bottom: 10), child: Text(ctrl.error!, style: const TextStyle(color: AppColors.block, fontSize: 12))),
            Row(mainAxisAlignment: MainAxisAlignment.end, children: [
              TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Huỷ')),
              const SizedBox(width: 10),
              FilledButton(
                onPressed: ctrl.isBusy
                    ? null
                    : () async {
                        await ctrl.createCase(companyName: _company.text.trim(), needText: _need.text.trim());
                        if (mounted) Navigator.of(context).pop();
                      },
                child: ctrl.isBusy ? const Text('Đang tạo…') : const Text('Tạo case'),
              ),
            ]),
          ]),
        ),
      ),
    );
  }
}

class _Body extends StatelessWidget {
  final SalesCaseController ctrl;
  final TextEditingController search;
  const _Body({required this.ctrl, required this.search});

  @override
  Widget build(BuildContext context) {
    final q = search.text.toLowerCase();
    final visible = ctrl.cases.where((c) {
      final name = ((c['company_name'] ?? c['customer_id']) ?? '').toString().toLowerCase();
      return name.contains(q);
    }).toList();

    return SingleChildScrollView(
      padding: responsivePadding(context),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        AgentPipeline(activeStage: 0, doneStages: const {0}),
        const SizedBox(height: 18),
        _Metrics(ctrl: ctrl),
        const SizedBox(height: 18),
        GlassCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              const SectionHeader(title: 'Sales Cases', caption: 'Intake → Confirmation → Agents → Risk Gate → Approval', icon: Icons.view_agenda_outlined),
              const Spacer(),
              SizedBox(width: 220, child: TextField(
                controller: search,
                style: const TextStyle(color: AppColors.txt, fontSize: 13, fontFamily: 'Hanken Grotesk'),
                decoration: const InputDecoration(hintText: 'Tìm doanh nghiệp…', prefixIcon: Icon(Icons.search, size: 18), contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
              )),
            ]),
            const SizedBox(height: 12),
            if (ctrl.isLoading)
              const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator(color: AppColors.cyan)))
            else if (visible.isEmpty)
              _Empty(ctrl: ctrl)
            else
              ...visible.map((c) => _CaseTile(c: c)),
          ]),
        ),
        const SizedBox(height: 24),
      ]),
    );
  }
}

class _Metrics extends StatelessWidget {
  final SalesCaseController ctrl;
  const _Metrics({required this.ctrl});

  @override
  Widget build(BuildContext context) {
    final cases = ctrl.cases;
    final open = cases.length;
    final blocked = cases.where((c) => (c['intake_status'] ?? '') == 'processing_failed').length;
    final inAnalysis = cases.where((c) => ['extraction_completed', 'profile_confirmed', 'analysis_running'].contains(c['intake_status'])).length;
    return LayoutBuilder(
      builder: (context, c) {
        final cols = c.maxWidth >= 720 ? 4 : (c.maxWidth >= 420 ? 2 : 1);
        final w = (c.maxWidth - (cols - 1) * 12) / cols;
        return Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            SizedBox(width: w, child: const NeonMetric(label: 'Cases', value: '0', icon: Icons.cases_outlined, accent: AppColors.cyan, sub: 'live v2 queue')),
            SizedBox(width: w, child: NeonMetric(label: 'Đang mở', value: '$open', icon: Icons.timelapse_outlined, accent: AppColors.violet, sub: 'intake + analysis')),
            SizedBox(width: w, child: NeonMetric(label: 'In Analysis', value: '$inAnalysis', icon: Icons.hub_outlined, accent: AppColors.lime, sub: 'agents running')),
            SizedBox(width: w, child: NeonMetric(label: 'Failed', value: '$blocked', icon: Icons.error_outline, accent: AppColors.block, sub: 'needs review')),
          ],
        );
      },
    );
  }
}

class _Empty extends StatelessWidget {
  final SalesCaseController ctrl;
  const _Empty({required this.ctrl});
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(36),
          child: Column(children: [
            Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: AppColors.cyan.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(16)), child: const Icon(Icons.auto_awesome_outlined, size: 34, color: AppColors.cyan)),
            const SizedBox(height: 14),
            const Text('Chưa có sales case nào', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.txt)),
            const SizedBox(height: 6),
            const Text('Tạo case đầu tiên — hệ thống sẽ chạy intake, trích xuất và điều phối multi-agent.', style: TextStyle(fontSize: 12, color: AppColors.muted), textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.icon(onPressed: ctrl.loadCases, icon: const Icon(Icons.refresh), label: const Text('Tải lại')),
          ]),
        ),
      );
}

class _CaseTile extends StatelessWidget {
  final Map<String, dynamic> c;
  const _CaseTile({required this.c});

  @override
  Widget build(BuildContext context) {
    final id = (c['case_id'] ?? '').toString();
    final name = (c['company_name'] ?? c['customer_id'] ?? 'Khách hàng').toString();
    final status = (c['intake_status'] ?? 'draft').toString();
    final token = _token(status);
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        onTap: () => context.go('/case/$id'),
        borderRadius: BorderRadius.circular(14),
        child: GlassCard(
          padding: const EdgeInsets.all(15),
          child: Row(children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(gradient: const LinearGradient(colors: [AppColors.cyan, AppColors.violet]), borderRadius: BorderRadius.circular(12)),
              child: Center(child: Text(name.isNotEmpty ? name.substring(0, name.length >= 2 ? 2 : 1).toUpperCase() : '?', style: const TextStyle(color: AppColors.ink900, fontWeight: FontWeight.w800, fontSize: 14))),
            ),
            const SizedBox(width: 13),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.txt)),
              const SizedBox(height: 3),
              Text(id, style: GoogleFonts.jetBrainsMono(fontSize: 11, color: AppColors.muted)),
            ])),
            StatusToken(status: token.$1, label: token.$2),
            const SizedBox(width: 8),
            const Icon(Icons.chevron_right, color: AppColors.muted),
          ]),
        ),
      ),
    );
  }

  (AgentStatus, String) _token(String s) => switch (s) {
        'draft' => (AgentStatus.idle, 'Draft'),
        'files_uploaded' => (AgentStatus.idle, 'Uploaded'),
        'document_processing' => (AgentStatus.review, 'Processing'),
        'extraction_completed' => (AgentStatus.needInfo, 'Extracted'),
        'profile_review_required' => (AgentStatus.needInfo, 'Review'),
        'profile_confirmed' => (AgentStatus.ready, 'Confirmed'),
        'analysis_running' => (AgentStatus.review, 'Analyzing'),
        'analysis_completed' => (AgentStatus.review, 'Analyzed'),
        'processing_failed' => (AgentStatus.block, 'Failed'),
        _ => (AgentStatus.idle, s),
      };
}
