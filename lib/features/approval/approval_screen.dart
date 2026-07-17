import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';

/// S3: Approval & Receipt (brief §11)
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
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/case/${widget.caseId}'),
          tooltip: 'Quay lại',
        ),
        title: Text('Phê duyệt ${widget.caseId}'),
      ),
      body: Consumer<CaseDetailController>(
        builder: (context, ctrl, _) {
          if (ctrl.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          final detail = ctrl.caseDetail;
          if (detail == null) {
            return const Center(child: Text('Không có dữ liệu'));
          }
          if (_submitted) {
            return _Receipt(detail: detail, selected: _selected);
          }
          return _ApprovalForm(
            detail: detail,
            selected: _selected,
            commitments: _commitments,
            escalated: _escalated,
            onToggleOpportunity: (id) => setState(() =>
                _selected.contains(id) ? _selected.remove(id) : _selected.add(id)),
            onToggleCommitment: (id) => setState(() =>
                _commitments.contains(id) ? _commitments.remove(id) : _commitments.add(id)),
            onSubmit: _submit,
            onEscalate: _escalate,
          );
        },
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
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 720),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Payload thay đổi',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ...detail.opportunities.map((o) {
              final checked = selected.contains(o.opportunityId);
              return CheckboxListTile(
                value: checked,
                onChanged: (_) => onToggleOpportunity(o.opportunityId),
                title: Text(o.product),
                subtitle: Text('${o.nextBestAction} • ${o.expectedOutcome}'),
                secondary: StatusBadge(status: o.status),
              );
            }),
            const Divider(height: 24),
            Text('Cam kết RM (kiểm toán)',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ...detail.checklist.map((c) => CheckboxListTile(
                  value: commitments.contains(c.id),
                  onChanged: (_) => onToggleCommitment(c.id),
                  title: Text(c.text),
                  subtitle: Text('Owner: ${c.owner} • ${c.sla}'),
                )),
            const SizedBox(height: 16),
            if (escalated)
              const StatusBadge(
                  status: OpportunityStatus.reviewRequired,
                  label: 'Đã chuyển chuyên gia kiểm tra'),
            const SizedBox(height: 12),
            Row(
              children: [
                ElevatedButton.icon(
                  icon: const Icon(Icons.check),
                  label: const Text('Ký phê duyệt'),
                  onPressed: canSubmit ? onSubmit : null,
                  style: ElevatedButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primary),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  icon: const Icon(Icons.gavel),
                  label: const Text('Chuyển chuyên gia kiểm tra'),
                  onPressed: onEscalate,
                ),
              ],
            ),
            if (!canSubmit)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text('Chọn ít nhất 1 cơ hội và xác nhận mọi cam kết.',
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: Theme.of(context).colorScheme.error)),
              ),
          ],
        ),
      ),
    );
  }
}

class _Receipt extends StatelessWidget {
  final CaseDetail detail;
  final Set<String> selected;
  const _Receipt({required this.detail, required this.selected});

  @override
  Widget build(BuildContext context) {
    final token = 'APR-${detail.caseId}-${selected.length}';
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 720),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.verified, size: 48, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 12),
            Text('Đã phê duyệt', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text('Mã biên lai: $token',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 16),
            Text('Cơ hội được duyệt:',
                style: Theme.of(context).textTheme.titleSmall),
            ...detail.opportunities
                .where((o) => selected.contains(o.opportunityId))
                .map((o) => ListTile(
                      leading: const Icon(Icons.check_circle, color: Colors.green),
                      title: Text(o.product),
                    )),
            const Divider(height: 24),
            Text('Nhật ký kiểm toán',
                style: Theme.of(context).textTheme.titleSmall),
            _AuditRow(step: 'Tạo case', actor: detail.rmName, time: detail.updatedAt),
            _AuditRow(step: 'Xem xét decision brief', actor: detail.rmName, time: detail.updatedAt),
            _AuditRow(step: 'Ký phê duyệt', actor: detail.rmName, time: DateTime.now()),
          ],
        ),
      ),
    );
  }
}

class _AuditRow extends StatelessWidget {
  final String step;
  final String actor;
  final DateTime time;
  const _AuditRow({required this.step, required this.actor, required this.time});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      leading: const Icon(Icons.history, size: 18),
      title: Text(step),
      subtitle: Text('$actor • ${time.toLocal()}'),
    );
  }
}
