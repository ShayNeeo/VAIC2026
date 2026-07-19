import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/controllers/employee_workspace_controller.dart';
import '../../design/theme/app_theme.dart';
import '../../design/widgets/agent_os.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _employee = TextEditingController(text: 'RM-999');
  final _password = TextEditingController(text: 'demo1234');
  final _personas = const [
    ('USER-MP-001', 'Customer', 'Khách hàng doanh nghiệp', Icons.business_outlined, AppColors.blue, 'customer'),
    ('RM-999', 'Relationship Manager', 'Quản lý quan hệ', Icons.handshake_outlined, AppColors.orange, 'rm'),
    ('MGR-HN-01', 'Branch Manager', 'Quản lý chi nhánh', Icons.shield_outlined, AppColors.violet, 'manager'),
  ];
  String _selected = 'RM-999';

  @override
  void dispose() {
    _employee.dispose();
    _password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<EmployeeWorkspaceController>(
      builder: (context, controller, _) => AgentMeshBackground(
        child: Scaffold(
          backgroundColor: Colors.transparent,
          body: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 460),
                child: _Panel(controller: controller, employee: _employee, password: _password, personas: _personas, selected: _selected, onPick: (p) => setState(() => _selected = p), onSubmit: () => _submit(context)),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _submit(BuildContext context) async {
    final controller = context.read<EmployeeWorkspaceController>();
    await controller.login(_employee.text.trim().toUpperCase(), _password.text);
    if (!mounted) return;
    if (controller.isAuthenticated) {
      final role = controller.context?.authorizationContext.primaryRole ?? 'relationship_manager';
      if (role == 'customer_user') {
        context.go('/customer');
      } else if (role == 'manager') {
        context.go('/manager');
      } else {
        context.go('/employee-workspace');
      }
    }
  }
}

class _Panel extends StatelessWidget {
  final EmployeeWorkspaceController controller;
  final TextEditingController employee;
  final TextEditingController password;
  final List<(String, String, String, IconData, Color, String)> personas;
  final String selected;
  final ValueChanged<String> onPick;
  final VoidCallback onSubmit;

  const _Panel({required this.controller, required this.employee, required this.password, required this.personas, required this.selected, required this.onPick, required this.onSubmit});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(26),
      glow: AppColors.navy,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(children: [
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                color: AppColors.navy,
                borderRadius: BorderRadius.circular(13),
                
              ),
              child: const Center(child: Icon(Icons.bolt_outlined, color: Colors.white, size: 24)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('VAIC Agent OS', style: GoogleFonts.beVietnamPro(fontSize: 19, fontWeight: FontWeight.w700, color: AppColors.txt)),
                const Text('Corporate Sales Copilot', style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
              ]),
            ),
          ]),
          const SizedBox(height: 20),
          const AgentKicker(label: 'Verified Identity', icon: Icons.verified_user_outlined),
          const SizedBox(height: 18),
          TextField(
            controller: employee,
            textCapitalization: TextCapitalization.characters,
            style: const TextStyle(color: AppColors.txt, fontFamily: 'BeVietnamPro'),
            decoration: const InputDecoration(labelText: 'Employee ID', prefixIcon: Icon(Icons.badge_outlined)),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: password,
            obscureText: true,
            style: const TextStyle(color: AppColors.txt, fontFamily: 'BeVietnamPro'),
            decoration: const InputDecoration(labelText: 'Mật khẩu', prefixIcon: Icon(Icons.lock_outline)),
          ),
          const SizedBox(height: 16),
          const Text('HOẶC CHỌN PERSONA DEMO', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 0.6, color: AppColors.muted)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: personas.map((p) {
              final active = selected == p.$1;
              return InkWell(
                onTap: () {
                  onPick(p.$1);
                  employee.text = p.$1;
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
                  decoration: BoxDecoration(
                    color: active ? p.$5.withValues(alpha: 0.16) : AppColors.ink800,
                    borderRadius: BorderRadius.circular(11),
                    border: Border.all(color: active ? p.$5 : AppColors.line),
                  ),
                  child: Row(mainAxisSize: MainAxisSize.min, children: [
                    Icon(p.$4, size: 16, color: active ? p.$5 : AppColors.muted),
                    const SizedBox(width: 7),
                    Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(p.$1, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: active ? AppColors.txt : AppColors.txt2)),
                      Text(p.$3, style: const TextStyle(fontSize: 9, color: AppColors.muted)),
                    ]),
                  ]),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 20),
          if (controller.error != null) ...[
            Container(
              padding: const EdgeInsets.all(11),
              decoration: BoxDecoration(color: AppColors.blockBg, borderRadius: BorderRadius.circular(11), border: Border.all(color: AppColors.block.withValues(alpha: 0.5))),
              child: Text(controller.error!, style: const TextStyle(color: AppColors.block, fontSize: 12)),
            ),
            const SizedBox(height: 14),
          ],
          FilledButton.icon(
            onPressed: controller.isLoading ? null : onSubmit,
            icon: controller.isLoading
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.ink900))
                : const Icon(Icons.login),
            label: Text(controller.isLoading ? 'Đang xác thực…' : 'Đăng nhập Workspace'),
          ),
          const SizedBox(height: 12),
          const Text('Demo mode · RM-999 / demo1234 · dữ liệu synthetic', textAlign: TextAlign.center, style: TextStyle(fontSize: 11, color: AppColors.muted)),
        ],
      ),
    );
  }
}
