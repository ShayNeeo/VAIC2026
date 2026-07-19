import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';
import '../../design/theme/app_theme.dart';
import '../../design/widgets/agent_os.dart';
import '../../design/widgets/nav_sidebar.dart';

/// Customer portal — submits intake, tracks own case (COMP-MP).
class CustomerWorkspaceScreen extends StatefulWidget {
  const CustomerWorkspaceScreen({super.key});

  @override
  State<CustomerWorkspaceScreen> createState() => _CustomerWorkspaceScreenState();
}

class _CustomerWorkspaceScreenState extends State<CustomerWorkspaceScreen> {
  final _company = TextEditingController(text: 'Minh Phát JSC');
  final _tax = TextEditingController(text: '0305123456');
  final _need = TextEditingController();
  final _controller = SalesCaseController();

  @override
  void initState() {
    super.initState();
    _controller.loadCases();
  }

  @override
  void dispose() {
    _company.dispose();
    _tax.dispose();
    _need.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider.value(
      value: _controller,
      child: Consumer<EmployeeWorkspaceController>(
        builder: (context, emp, _) => AgentMeshBackground(
          child: Scaffold(
            backgroundColor: Colors.transparent,
            drawer: Drawer(child: SafeArea(child: NavSidebar(current: 'customer', employeeId: emp.context?.employeeId ?? 'KH', roleLabel: 'Customer'))),
            appBar: AppBar(
              backgroundColor: Colors.transparent,
              elevation: 0,
              title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Customer Portal', style: GoogleFonts.spaceGrotesk(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.txt)),
                const Text('Gửi nhu cầu · Theo dõi hồ sơ', style: TextStyle(fontSize: 11, color: AppColors.lime)),
              ]),
              actions: [
                IconButton(icon: const Icon(Icons.logout, color: AppColors.txt2), onPressed: () { emp.logout(); context.go('/login'); }),
                const SizedBox(width: 8),
              ],
            ),
            body: Consumer<SalesCaseController>(
              builder: (context, ctrl, _) => _Body(ctrl: ctrl, company: _company, tax: _tax, need: _need),
            ),
          ),
        ),
      ),
    );
  }
}

class _Body extends StatelessWidget {
  final SalesCaseController ctrl;
  final TextEditingController company;
  final TextEditingController tax;
  final TextEditingController need;
  const _Body({required this.ctrl, required this.company, required this.tax, required this.need});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        GlassCard(
          glow: AppColors.lime,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const AgentKicker(label: 'Submit Intake', icon: Icons.upload_file_outlined),
            const SizedBox(height: 14),
            TextField(controller: company, style: const TextStyle(color: AppColors.txt, fontFamily: 'BeVietnamPro'), decoration: const InputDecoration(labelText: 'Tên doanh nghiệp', prefixIcon: Icon(Icons.business_outlined))),
            const SizedBox(height: 12),
            TextField(controller: tax, style: const TextStyle(color: AppColors.txt, fontFamily: 'BeVietnamPro'), decoration: const InputDecoration(labelText: 'Mã số thuế', prefixIcon: Icon(Icons.tag_outlined))),
            const SizedBox(height: 12),
            TextField(controller: need, maxLines: 3, style: const TextStyle(color: AppColors.txt, fontFamily: 'BeVietnamPro'), decoration: const InputDecoration(labelText: 'Nhu cầu tín dụng / sản phẩm', prefixIcon: Icon(Icons.edit_note_outlined))),
            const SizedBox(height: 16),
            if (ctrl.error != null) ...[
              Container(padding: const EdgeInsets.all(10), decoration: BoxDecoration(color: AppColors.blockBg, borderRadius: BorderRadius.circular(10), border: Border.all(color: AppColors.block.withValues(alpha: 0.5))), child: Text(ctrl.error!, style: const TextStyle(color: AppColors.block, fontSize: 12))),
              const SizedBox(height: 12),
            ],
            SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: ctrl.isBusy ? null : () => ctrl.createCase(companyName: company.text.trim(), taxCode: tax.text.trim(), needText: need.text.trim()), icon: const Icon(Icons.send), label: Text(ctrl.isBusy ? 'Đang gửi…' : 'Gửi yêu cầu'))),
          ]),
        ),
        const SizedBox(height: 18),
        const SectionHeader(title: 'Hồ sơ của bạn', caption: 'Được quản lý bởi RM · theo dõi trạng thái', icon: Icons.folder_outlined),
        const SizedBox(height: 12),
        if (ctrl.info != null)
          Padding(padding: const EdgeInsets.only(bottom: 10), child: Container(padding: const EdgeInsets.all(10), decoration: BoxDecoration(color: AppColors.cyan.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(10)), child: Text(ctrl.info!, style: const TextStyle(color: AppColors.cyanSoft, fontSize: 12)))),
        if (ctrl.isLoading)
          const Center(child: Padding(padding: EdgeInsets.all(30), child: CircularProgressIndicator(color: AppColors.lime)))
        else if (ctrl.cases.isEmpty)
          Center(child: Padding(padding: const EdgeInsets.all(30), child: Text('Chưa có hồ sơ nào.', style: TextStyle(color: AppColors.muted))))
        else
          ...ctrl.cases.map((c) => _CaseRow(c: c)),
        const SizedBox(height: 24),
      ]),
    );
  }
}

class _CaseRow extends StatelessWidget {
  final Map<String, dynamic> c;
  const _CaseRow({required this.c});

  @override
  Widget build(BuildContext context) {
    final id = (c['case_id'] ?? '').toString();
    final name = (c['company_name'] ?? c['customer_id'] ?? 'Khách hàng').toString();
    final status = (c['intake_status'] ?? 'draft').toString();
    final map = {
      'draft': AppColors.muted,
      'files_uploaded': AppColors.cyanSoft,
      'extraction_completed': AppColors.needInfo,
      'profile_confirmed': AppColors.ready,
      'analysis_completed': AppColors.review,
      'processing_failed': AppColors.block,
    };
    final labelMap = {
      'draft': 'Chờ gửi',
      'files_uploaded': 'Đã tải',
      'extraction_completed': 'Trích xuất',
      'profile_confirmed': 'Đã xác nhận',
      'analysis_completed': 'Đã phân tích',
      'processing_failed': 'Lỗi',
    };
    final fg = map[status] ?? AppColors.muted;
    final label = labelMap[status] ?? status;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        onTap: () => context.go('/case/$id'),
        child: GlassCard(
          padding: const EdgeInsets.all(15),
          child: Row(children: [
            Container(width: 42, height: 42, decoration: BoxDecoration(gradient: const LinearGradient(colors: [AppColors.lime, AppColors.cyan]), borderRadius: BorderRadius.circular(12)), child: Center(child: Text(name.isNotEmpty ? name.substring(0, 1).toUpperCase() : '?', style: const TextStyle(color: AppColors.ink900, fontWeight: FontWeight.w800)))),
            const SizedBox(width: 13),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.txt)),
              Text(id, style: GoogleFonts.jetBrainsMono(fontSize: 11, color: AppColors.muted)),
            ])),
            StatusToken(status: AgentStatus.idle, label: label),
          ]),
        ),
      ),
    );
  }
}
