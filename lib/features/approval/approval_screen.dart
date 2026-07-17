import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';

/// S3: Approval & Receipt — mirrors SHB Opportunity OS approval sheet + receipt
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
  bool _escalated = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<CaseDetailController>().loadCase(widget.caseId, useMock: true);
    });
  }

  void _submit() {
    if (_selected.isEmpty || _commitments.isEmpty) return;
    setState(() => _submitted = true);
  }

  void _escalate() => setState(() => _escalated = true);

  @override
  Widget build(BuildContext context) {
    return Consumer<CaseDetailController>(
      builder: (context, ctrl, _) => Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          backgroundColor: AppColors.navy900,
          foregroundColor: Colors.white,
          leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.go('/case/${widget.caseId}')),
          title: Text(_submitted ? 'Execution Receipt' : 'Duyệt phạm vi hành động', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
        ),
        body: ctrl.isLoading
            ? const Center(child: CircularProgressIndicator())
            : ctrl.caseDetail == null
                ? const Center(child: Text('Không có dữ liệu'))
                : _submitted
                    ? _Receipt(detail: ctrl.caseDetail!, selected: _selected, onBack: () => context.go('/queue'))
                    : _ApprovalForm(
                        detail: ctrl.caseDetail!,
                        selected: _selected,
                        commitments: _commitments,
                        escalated: _escalated,
                        onToggleOpportunity: (id) => setState(() => _selected.contains(id) ? _selected.remove(id) : _selected.add(id)),
                        onToggleCommitment: (id) => setState(() => _commitments.contains(id) ? _commitments.remove(id) : _commitments.add(id)),
                        onSubmit: _submit,
                        onEscalate: _escalate,
                      ),
      ),
    );
  }
}

class _ApprovalForm extends StatelessWidget {
  final CaseDetail detail;
  final Set<String> selected;
  final Set<String> commitments;
  final bool escalated;
  final void Function(String) onToggleOpportunity;
  final void Function(String) onToggleCommitment;
  final VoidCallback onSubmit;
  final VoidCallback onEscalate;

  const _ApprovalForm({
    required this.detail,
    required this.selected,
    required this.commitments,
    required this.escalated,
    required this.onToggleOpportunity,
    required this.onToggleCommitment,
    required this.onSubmit,
    required this.onEscalate,
  });

  @override
  Widget build(BuildContext context) {
    final canSubmit = selected.isNotEmpty && commitments.isNotEmpty;
    final ready = detail.opportunities.where((o) => !selected.contains(o.opportunityId) || o.status != OpportunityStatus.needInfo).length;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(14),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(16)),
          child: Row(children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _SummaryCell('${selected.length}', 'Opportunity'),
              const SizedBox(height: 8),
              _SummaryCell('$ready', 'Sẵn sàng'),
            ])),
            Container(width: 1, height: 48, color: AppColors.line),
            Expanded(child: _SummaryCell('${selected.length - ready}', 'Chờ hồ sơ')),
          ]),
        ),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(13)),
          child: Column(children: [
            ...detail.opportunities.map((o) {
              final checked = selected.contains(o.opportunityId);
              return InkWell(
                onTap: () => onToggleOpportunity(o.opportunityId),
                child: Padding(
                  padding: const EdgeInsets.all(10),
                  child: Row(children: [
                    Container(width: 22, height: 22, decoration: BoxDecoration(color: checked ? AppColors.blue : Colors.white, border: Border.all(color: checked ? AppColors.blue : const Color(0xFFBDC8D5)), borderRadius: BorderRadius.circular(7)), child: checked ? const Icon(Icons.check, size: 16, color: Colors.white) : null),
                    const SizedBox(width: 10),
                    Expanded(child: Text(o.product, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.ink))),
                    StatusBadge(status: o.status),
                  ]),
                ),
              );
            }),
          ]),
        ),
        const SizedBox(height: 14),
        const Text('XÁC NHẬN TRÁCH NHIỆM', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.muted, letterSpacing: 1)),
        ...detail.checklist.map((c) => _ConfirmRow(id: c.id, title: c.text, subtitle: '${c.owner} · ${c.sla}', checked: commitments.contains(c.id), onToggle: onToggleCommitment)),
        const SizedBox(height: 12),
        if (escalated) const StatusBadge(status: OpportunityStatus.reviewRequired, label: 'Đã chuyển chuyên gia kiểm tra'),
        const SizedBox(height: 10),
        Row(children: [
          Expanded(child: OutlinedButton(onPressed: onEscalate, child: const Text('Chuyên gia kiểm tra'))),
          const SizedBox(width: 8),
          Expanded(child: ElevatedButton.icon(icon: const Icon(Icons.shield, size: 16), label: const Text('Xác nhận'), onPressed: canSubmit ? onSubmit : null)),
        ]),
        if (!canSubmit) const Padding(padding: EdgeInsets.only(top: 8), child: Text('Chọn ít nhất 1 cơ hội và xác nhận mọi cam kết.', style: TextStyle(fontSize: 10, color: AppColors.statusBlocked))),
      ]),
    );
  }
}

class _SummaryCell extends StatelessWidget {
  final String value, label;
  const _SummaryCell(this.value, this.label);
  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.symmetric(horizontal: 8), child: Column(children: [Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: AppColors.navy900)), Text(label, style: const TextStyle(fontSize: 8, color: AppColors.muted))]));
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
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(12)),
      child: Row(children: [
        Checkbox(value: checked, onChanged: (_) => onToggle(id), activeColor: AppColors.blue),
        const SizedBox(width: 8),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.ink2)),
          Text(subtitle, style: const TextStyle(fontSize: 8, color: AppColors.muted)),
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
    return SingleChildScrollView(
      padding: const EdgeInsets.all(18),
      child: Column(children: [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(18)),
          child: Column(children: [
            Container(width: 54, height: 54, decoration: BoxDecoration(color: AppColors.statusReady100, borderRadius: BorderRadius.circular(18)), child: const Icon(Icons.check, color: AppColors.statusReady, size: 30)),
            const SizedBox(height: 10),
            const Text('Đã phê duyệt an toàn', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.navy900)),
            const SizedBox(height: 5),
            const Text('Payload đã qua RBAC, evidence, payload binding và idempotency gate.', style: TextStyle(fontSize: 10, color: AppColors.muted)),
            const SizedBox(height: 12),
            Container(width: double.infinity, padding: const EdgeInsets.all(7), decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(9)), child: Text(token, style: const TextStyle(fontSize: 9, color: AppColors.muted, fontFamily: 'monospace'))),
          ]),
        ),
        const SizedBox(height: 13),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(13)),
          child: Column(children: [
            ...detail.opportunities.where((o) => selected.contains(o.opportunityId)).map((o) => _ReceiptRow(label: o.product, state: o.status == OpportunityStatus.needInfo ? 'PENDING' : 'CREATED')),
            const _ReceiptRow(label: 'Email được lưu dạng draft', state: 'NOT_SENT'),
            const _ReceiptRow(label: 'Task được tạo/tái sử dụng', state: 'IDEMPOTENT'),
          ]),
        ),
        const SizedBox(height: 13),
        SizedBox(width: double.infinity, child: OutlinedButton(onPressed: onBack, child: const Text('Quay về Opportunity Queue'))),
      ]),
    );
  }
}

class _ReceiptRow extends StatelessWidget {
  final String label, state;
  const _ReceiptRow({required this.label, required this.state});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Row(children: [
      const Icon(Icons.check, color: AppColors.statusReady, size: 16),
      const SizedBox(width: 8),
      Expanded(child: Text(label, style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w600, color: AppColors.ink2))),
      Text(state, style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.muted)),
    ]),
  );
}
