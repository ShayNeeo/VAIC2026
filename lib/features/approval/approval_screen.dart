import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';
import '../../design/theme/app_theme.dart';
import '../../design/widgets/agent_os.dart';
import '../../design/widgets/nav_sidebar.dart';

/// S3 — Approval Gate: preview frozen payload, issue one-time token, execute.
class ApprovalScreen extends StatefulWidget {
  final String caseId;
  const ApprovalScreen({super.key, required this.caseId});

  @override
  State<ApprovalScreen> createState() => _ApprovalScreenState();
}

class _ApprovalScreenState extends State<ApprovalScreen> {
  ApprovalPreview? _preview;
  String? _token;
  Map<String, dynamic>? _result;
  bool _isBusy = false;
  String? _error;
  bool _done = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadPreview());
  }

  Future<void> _loadPreview() async {
    setState(() => _isBusy = true);
    try {
      final api = context.read<EmployeeWorkspaceController>().api;
      _preview = await api.previewApproval(widget.caseId);
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _isBusy = false);
    }
  }

  Future<void> _issueAndExecute() async {
    setState(() => _isBusy = true);
    try {
      final api = context.read<EmployeeWorkspaceController>().api;
      final issued = await api.issueApprovalToken(widget.caseId);
      _token = issued.approvalToken;
      final rm = context.read<EmployeeWorkspaceController>().context?.employeeId ?? 'RM-999';
      _result = (await api.approveCase(widget.caseId, rm, _token!, comments: 'RM phê duyệt qua Agent OS')).toJson();
      _done = true;
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _isBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<EmployeeWorkspaceController>(
      builder: (context, ctrl, _) => AgentMeshBackground(
        child: Scaffold(
          backgroundColor: Colors.transparent,
          drawer: Drawer(child: SafeArea(child: NavSidebar(current: 'approval', employeeId: ctrl.context?.employeeId ?? 'RM', roleLabel: 'Approval'))),
          appBar: AppBar(
            backgroundColor: Colors.transparent,
            elevation: 0,
            leading: IconButton(icon: const Icon(Icons.arrow_back, color: AppColors.txt2), onPressed: () => context.go('/case/${widget.caseId}')),
            title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Approval Gate', style: GoogleFonts.beVietnamPro(fontSize: 17, fontWeight: FontWeight.w700, color: AppColors.txt)),
              Text('Case ${widget.caseId}', style: GoogleFonts.jetBrainsMono(fontSize: 11, color: AppColors.cyanSoft)),
            ]),
          ),
          body: _isBusy && !_done
              ? const Center(child: CircularProgressIndicator(color: AppColors.cyan))
              : _done
                  ? _Receipt()
                  : _Form(),
        ),
      ),
    );
  }

  Widget _Form() => SingleChildScrollView(
        padding: responsivePadding(context),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          GlassCard(
            glow: AppColors.lime,
            child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              AgentKicker(label: 'Frozen Payload', icon: Icons.gavel_outlined),
              SizedBox(height: 8),
              Text('Payload đã bị đóng băng (hash-chained). RM ký duyệt bằng one-time token.', style: TextStyle(fontSize: 12, color: AppColors.muted)),
            ]),
          ),
          const SizedBox(height: 16),
          GlassCard(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const SectionHeader(title: 'Payload Diff', caption: 'Action · target · hash · reversible', icon: Icons.schema_outlined),
              const SizedBox(height: 12),
              if (_preview == null)
                const Text('Không tải được preview.', style: TextStyle(color: AppColors.muted))
              else ...[
                _Row('Action', _preview!.action),
                _Row('Target', _preview!.target),
                _Row('Payload Hash', _preview!.payloadHash, mono: true),
                _Row('Reversible', _preview!.reversible.toString()),
              ],
            ]),
          ),
          if (_error != null) ...[
            const SizedBox(height: 14),
            Container(padding: const EdgeInsets.all(12), decoration: BoxDecoration(color: AppColors.blockBg, borderRadius: BorderRadius.circular(12), border: Border.all(color: AppColors.block.withValues(alpha: 0.5))), child: Text(_error!, style: const TextStyle(color: AppColors.block, fontSize: 12))),
          ],
          const SizedBox(height: 18),
          SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: _isBusy ? null : _issueAndExecute, icon: const Icon(Icons.lock), label: Text(_isBusy ? 'Đang ký…' : 'RM phê duyệt & thực thi'))),
          const SizedBox(height: 24),
        ]),
      );

  Widget _Receipt() => Center(
        child: SingleChildScrollView(
          padding: responsivePadding(context),
          child: GlassCard(
            glow: AppColors.ready,
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Container(width: 56, height: 56, decoration: const BoxDecoration(color: AppColors.ready, shape: BoxShape.circle), child: const Icon(Icons.check, color: AppColors.ink900, size: 32)),
              const SizedBox(height: 16),
              const Text('Đã phê duyệt an toàn', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w800, color: AppColors.txt)),
              const SizedBox(height: 6),
              Text('Case ${widget.caseId} · thực thi trên CRM mock (idempotent)', style: const TextStyle(fontSize: 12, color: AppColors.muted)),
              const SizedBox(height: 16),
              if (_result != null) ...[
                _Row('Status', (_result!['status'] ?? '').toString()),
                _Row('Result', (_result!['result'] ?? '').toString()),
                _Row('State Version', (_result!['state_version'] ?? '').toString()),
              ],
              const SizedBox(height: 16),
              FilledButton.tonal(onPressed: () => context.go('/queue'), child: const Text('Về Command Center')),
            ]),
          ),
        ),
      );
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  final bool mono;
  const _Row(this.label, this.value, {this.mono = false});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(width: 130, child: Text(label, style: const TextStyle(fontSize: 12, color: AppColors.muted))),
          Expanded(child: SelectableText(value, style: mono ? GoogleFonts.jetBrainsMono(fontSize: 11, color: AppColors.txt2) : const TextStyle(fontSize: 12, color: AppColors.txt))),
        ]),
      );
}
