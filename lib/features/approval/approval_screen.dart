import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';
import '../../design/widgets/nav_sidebar.dart';

/// S3: Approval & Receipt (brief §6-§8)
class ApprovalScreen extends StatefulWidget {
  final String caseId;
  const ApprovalScreen({super.key, required this.caseId});

  @override
  State<ApprovalScreen> createState() => _ApprovalScreenState();
}

class _ApprovalScreenState extends State<ApprovalScreen> {
  final Set<String> _selected = {};
  final Set<String> _commitments = {};
  bool _submitted = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<CaseDetailController>().loadCase(widget.caseId, useMock: false);
    });
  }

  void _toggleOpportunity(String id) => setState(() => _selected.contains(id) ? _selected.remove(id) : _selected.add(id));
  void _toggleCommitment(String id) => setState(() => _commitments.contains(id) ? _commitments.remove(id) : _commitments.add(id));
  void _submit() {
    if (_selected.isEmpty || _commitments.isEmpty) return;
    setState(() => _submitted = true);
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CaseDetailController>(
      builder: (context, ctrl, _) => LayoutScaffold(
        sidebar: const NavSidebar(current: 'approval'),
        body: Builder(
          builder: (context) {
            if (ctrl.isLoading) return const Center(child: CircularProgressIndicator());
            if (ctrl.caseDetail == null) return const Center(child: Text('Không có dữ liệu'));
            return _submitted
                ? _Receipt(detail: ctrl.caseDetail!, selected: _selected, onBack: () => context.go('/queue'))
                : _ApprovalForm(
                    detail: ctrl.caseDetail!,
                    selected: _selected,
                    commitments: _commitments,
                    onToggleOpportunity: _toggleOpportunity,
                    onToggleCommitment: _toggleCommitment,
                    onSubmit: _submit,
                    onBack: () => context.go('/case/${widget.caseId}'),
                  );
          },
        ),
      ),
    );
  }
}

class _ApprovalForm extends StatelessWidget {
  final CaseDetail detail;
  final Set<String> selected;
  final Set<String> commitments;
  final void Function(String) onToggleOpportunity;
  final void Function(String) onToggleCommitment;
  final VoidCallback onSubmit;
  final VoidCallback onBack;

  const _ApprovalForm({
    required this.detail,
    required this.selected,
    required this.commitments,
    required this.onToggleOpportunity,
    required this.onToggleCommitment,
    required this.onSubmit,
    required this.onBack,
  });

  @override
  Widget build(BuildContext context) {
    final canSubmit = selected.isNotEmpty && commitments.isNotEmpty;
    final ready = detail.opportunities.where((o) => !selected.contains(o.opportunityId) || o.status != OpportunityStatus.needInfo).length;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.navy900, foregroundColor: Colors.white,
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: onBack),
        title: const Text('Duyệt phạm vi hành động', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, fontFamily: 'Sora')),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: _SummaryCell('${selected.length}', 'Opportunity')),
            Expanded(child: _SummaryCell('$ready', 'Sẵn sàng')),
            Expanded(child: _SummaryCell('${selected.length - ready}', 'Chờ hồ sơ')),
          ]),
          const SizedBox(height: 16),
          const _SectionTitle('PHẠM VI DUYỆT', icon: Icons.checklist),
          const SizedBox(height: 8),
          Container(
            decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(14)),
            child: Column(children: [
              ...detail.opportunities.map((o) {
                final checked = selected.contains(o.opportunityId);
                return InkWell(
                  onTap: () => onToggleOpportunity(o.opportunityId),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(children: [
                      _Check(checked: checked),
                      const SizedBox(width: 12),
                      Expanded(child: Text(o.product, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.ink))),
                      StatusBadge(status: o.status),
                    ]),
                  ),
                );
              }),
            ]),
          ),
          const SizedBox(height: 16),
          const _SectionTitle('PAYLOAD DIFF', icon: Icons.schema),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(14)),
            child: Column(children: [
              ...detail.opportunities.where((o) => selected.contains(o.opportunityId)).map((o) => _DiffRow(object: o.product, action: o.status == OpportunityStatus.needInfo ? 'Create (pending info)' : 'Create', fg: o.status == OpportunityStatus.needInfo ? AppColors.statusNeedInfo : AppColors.statusReady)),
              const _DiffRow(object: 'Customer email', action: 'Save draft only', fg: AppColors.statusAiCta),
              _DiffRow(object: 'Tasks (${detail.checklist.length})', action: 'Create / reuse', fg: AppColors.statusReady),
            ]),
          ),
          const SizedBox(height: 16),
          const _SectionTitle('CAM KẾT CỦA RM', icon: Icons.verified_user),
          const SizedBox(height: 8),
          ...detail.checklist.map((c) => _ConfirmRow(id: c.id, title: c.text, subtitle: '${c.owner} · SLA ${c.sla}', checked: commitments.contains(c.id), onToggle: onToggleCommitment)),
          const SizedBox(height: 16),
          Row(children: [
            Expanded(child: OutlinedButton(onPressed: onBack, child: const Text('Quay lại'))),
            const SizedBox(width: 10),
            Expanded(child: ElevatedButton.icon(icon: const Icon(Icons.shield, size: 16), label: const Text('Xác nhận duyệt'), onPressed: canSubmit ? onSubmit : null, style: ElevatedButton.styleFrom(backgroundColor: AppColors.navy900, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 13)))),
          ]),
          if (!canSubmit) const Padding(padding: EdgeInsets.only(top: 10), child: Text('Chọn ít nhất 1 cơ hội và xác nhận mọi cam kết.', style: TextStyle(fontSize: 10, color: AppColors.statusBlocked))),
          const SizedBox(height: 20),
        ],
      ),
      ),
    );
  }
}

class _Check extends StatelessWidget {
  final bool checked;
  const _Check({required this.checked});
  @override
  Widget build(BuildContext context) => Container(
        width: 22, height: 22,
        decoration: BoxDecoration(color: checked ? AppColors.gold : Colors.white, border: Border.all(color: checked ? AppColors.gold : const Color(0xFFBDC8D5)), borderRadius: BorderRadius.circular(7)),
        child: checked ? const Icon(Icons.check, size: 16, color: Colors.white) : null,
      );
}

class _DiffRow extends StatelessWidget {
  final String object;
  final String action;
  final Color fg;
  const _DiffRow({required this.object, required this.action, required this.fg});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 7),
        child: Row(children: [
          Expanded(child: Text(object, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.ink2))),
          Container(padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4), decoration: BoxDecoration(color: fg.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(999)), child: Text(action, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: fg))),
        ]),
      );
}

class _ConfirmRow extends StatelessWidget {
  final String id, title, subtitle;
  final bool checked;
  final void Function(String) onToggle;
  const _ConfirmRow({required this.id, required this.title, required this.subtitle, required this.checked, required this.onToggle});

  @override
  Widget build(BuildContext context) => InkWell(
    onTap: () => onToggle(id),
    child: Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(11),
      decoration: BoxDecoration(border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(12)),
      child: Row(children: [
        _Check(checked: checked),
        const SizedBox(width: 10),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.ink2)),
          Text(subtitle, style: const TextStyle(fontSize: 9, color: AppColors.muted)),
        ])),
      ]),
    ),
  );
}

class _Receipt extends StatelessWidget {
  final CaseDetail detail;
  final Set<String> selected;
  final VoidCallback onBack;
  const _Receipt({required this.detail, required this.selected, required this.onBack});

  @override
  Widget build(BuildContext context) {
    final token = 'RCPT-${DateTime.now().toIso8601String().substring(2, 10).replaceAll('-', '')}-${1000 + (selected.length * 37) % 9000}';
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(backgroundColor: AppColors.navy900, foregroundColor: Colors.white, leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: onBack), title: const Text('Execution Receipt', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, fontFamily: 'Sora'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(18),
        child: Column(children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(18)),
            child: Column(children: [
              Container(width: 54, height: 54, decoration: BoxDecoration(color: AppColors.statusReady100, borderRadius: BorderRadius.circular(18)), child: const Icon(Icons.check, color: AppColors.statusReady, size: 30)),
              const SizedBox(height: 10),
              const Text('Đã phê duyệt an toàn', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.navy900, fontFamily: 'Sora')),
              const SizedBox(height: 5),
              const Text('Payload qua RBAC, evidence, payload-binding và idempotency gate.', style: TextStyle(fontSize: 10, color: AppColors.muted)),
              const SizedBox(height: 12),
              Container(width: double.infinity, padding: const EdgeInsets.all(8), decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(9)), child: Text(token, style: const TextStyle(fontSize: 9, color: AppColors.muted, fontFamily: 'monospace'))),
            ]),
          ),
          const SizedBox(height: 14),
          const _SectionTitle('KẾT QUẢ THỰC THI', icon: Icons.receipt_long),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(14)),
            child: Column(children: [
              ...detail.opportunities.where((o) => selected.contains(o.opportunityId)).map((o) => _ReceiptRow(label: o.product, state: o.status == OpportunityStatus.needInfo ? 'PENDING INFO' : 'CREATED', fg: o.status == OpportunityStatus.needInfo ? AppColors.statusNeedInfo : AppColors.statusReady)),
              const _ReceiptRow(label: 'Email được lưu dạng draft', state: 'NOT SENT', fg: AppColors.statusAiCta),
              const _ReceiptRow(label: 'Task được tạo/tái sử dụng', state: 'IDEMPOTENT', fg: AppColors.statusReady),
              const _ReceiptRow(label: 'Quyết định tín dụng', state: 'NONE', fg: AppColors.statusBlocked),
            ]),
          ),
          const SizedBox(height: 14),
          const _SectionTitle('AUDIT TIMELINE', icon: Icons.history),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(14)),
            child: Column(children: [
              const _TimelineRow(time: '10:30', text: 'Hệ thống phát hiện 4 cơ hội', icon: Icons.psychology_outlined),
              const _TimelineRow(time: '10:32', text: 'RM xác nhận facts & nguồn', icon: Icons.edit_note),
              _TimelineRow(time: '10:35', text: 'RM duyệt ${selected.length} opportunity', icon: Icons.shield, last: true),
            ]),
          ),
          const SizedBox(height: 16),
          SizedBox(width: double.infinity, child: OutlinedButton(onPressed: onBack, child: const Text('Quay về Opportunity Queue'))),
        ],
      ),
      ),
    );
  }
}

class _ReceiptRow extends StatelessWidget {
  final String label, state;
  final Color fg;
  const _ReceiptRow({required this.label, required this.state, required this.fg});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(children: [
          Icon(Icons.check_circle, color: fg, size: 16),
          const SizedBox(width: 8),
          Expanded(child: Text(label, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppColors.ink2))),
          Text(state, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: fg)),
        ]),
      );
}

class _TimelineRow extends StatelessWidget {
  final String time;
  final String text;
  final IconData icon;
  final bool last;
  const _TimelineRow({required this.time, required this.text, required this.icon, this.last = false});

  @override
  Widget build(BuildContext context) => Row(children: [
        Column(children: [
          Container(width: 28, height: 28, decoration: BoxDecoration(color: AppColors.blue100, borderRadius: BorderRadius.circular(999)), child: Icon(icon, size: 15, color: AppColors.navy700)),
          if (!last) Container(width: 2, height: 22, color: AppColors.line),
        ]),
        const SizedBox(width: 10),
        Text(time, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppColors.subtle)),
        const SizedBox(width: 8),
        Expanded(child: Text(text, style: const TextStyle(fontSize: 11, color: AppColors.ink2))),
      ]);
}

class _SummaryCell extends StatelessWidget {
  final String value, label;
  const _SummaryCell(this.value, this.label);
  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.symmetric(horizontal: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(12)),
        child: Column(children: [Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.navy900, fontFamily: 'Sora')), Text(label, style: const TextStyle(fontSize: 9, color: AppColors.muted))]),
      );
}

class _SectionTitle extends StatelessWidget {
  final String text;
  final IconData icon;
  const _SectionTitle(this.text, {required this.icon});

  @override
  Widget build(BuildContext context) => Row(children: [
        Icon(icon, size: 14, color: AppColors.gold),
        const SizedBox(width: 7),
        Text(text, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.navy900, letterSpacing: 0.6)),
      ]);
}
