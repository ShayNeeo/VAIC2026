import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';

import '../../core/controllers/employee_workspace_controller.dart';
import '../../design/theme/app_theme.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _employeeController = TextEditingController(text: 'RM-999');
  final _passwordController = TextEditingController(text: 'demo1234');

  @override
  void dispose() {
    _employeeController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<EmployeeWorkspaceController>(
      builder: (context, controller, _) => Scaffold(
        backgroundColor: AppColors.navy950,
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 430),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Container(
                          width: 48,
                          height: 48,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(color: AppColors.orange, borderRadius: BorderRadius.circular(14)),
                          child: const Text('S', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900)),
                        ),
                        const SizedBox(height: 18),
                        const Text('Đăng nhập Workspace', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
                        const SizedBox(height: 8),
                        const Text('Đăng nhập để hệ thống nhận diện role và mở đúng workspace mobile.'),
                        const SizedBox(height: 24),
                        TextField(
                          controller: _employeeController,
                          textCapitalization: TextCapitalization.characters,
                          decoration: const InputDecoration(labelText: 'Employee ID', prefixIcon: Icon(Icons.badge_outlined)),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _passwordController,
                          obscureText: true,
                          decoration: const InputDecoration(labelText: 'Mật khẩu', prefixIcon: Icon(Icons.lock_outline)),
                        ),
                        if (controller.error != null) ...[
                          const SizedBox(height: 12),
                          Text(controller.error!, style: const TextStyle(color: AppColors.error)),
                        ],
                        const SizedBox(height: 20),
                        FilledButton.icon(
                          onPressed: controller.isLoading
                              ? null
                              : () => _submit(context),
                          icon: controller.isLoading
                              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                              : const Icon(Icons.login),
                          label: Text(controller.isLoading ? 'Đang xác thực...' : 'Đăng nhập'),
                        ),
                        const SizedBox(height: 12),
                        const Text('Demo local: RM-999 / demo1234', textAlign: TextAlign.center, style: TextStyle(fontSize: 12)),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _submit(BuildContext context) async {
    final controller = context.read<EmployeeWorkspaceController>();
    await controller.login(_employeeController.text, _passwordController.text);
    if (!mounted) return;
    if (controller.isAuthenticated) context.go('/employee-workspace');
  }
}
