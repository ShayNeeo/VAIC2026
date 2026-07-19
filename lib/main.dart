import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'core/rm_workspace_core.dart';
import 'design/design.dart';
import 'features/queue/queue_screen.dart';
import 'features/case_detail/case_detail_screen.dart';
import 'features/approval/approval_screen.dart';
import 'features/employee_workspace/employee_workspace_screen.dart';
import 'features/customer/customer_workspace_screen.dart';
import 'features/manager/manager_console_screen.dart';
import 'features/auth/login_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => CaseController()),
        ChangeNotifierProvider(create: (_) => CaseDetailController()),
        ChangeNotifierProvider(create: (_) => EmployeeWorkspaceController()),
      ],
      child: const AgentApp(),
    ),
  );
}

class AgentApp extends StatelessWidget {
  const AgentApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'VAIC Agent OS',
      debugShowCheckedModeBanner: false,
      theme: lightAgentTheme(),
      darkTheme: agentTheme(Brightness.dark),
      themeMode: ThemeMode.light,
      routerConfig: _router,
    );
  }
}

final GoRouter _router = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      name: 'login',
      builder: (context, state) => const LoginScreen(),
    ),
    GoRoute(
      path: '/queue',
      name: 'queue',
      builder: (context, state) => const QueueScreen(),
    ),
    GoRoute(
      path: '/case/:caseId',
      name: 'case-detail',
      builder: (context, state) => CaseDetailScreen(caseId: state.pathParameters['caseId']!),
    ),
    GoRoute(
      path: '/approval/:caseId',
      name: 'approval',
      builder: (context, state) => ApprovalScreen(caseId: state.pathParameters['caseId']!),
    ),
    GoRoute(
      path: '/employee-workspace',
      name: 'employee-workspace',
      builder: (context, state) => const EmployeeWorkspaceScreen(),
    ),
    GoRoute(
      path: '/customer',
      name: 'customer',
      builder: (context, state) => const CustomerWorkspaceScreen(),
    ),
    GoRoute(
      path: '/manager',
      name: 'manager',
      builder: (context, state) => const ManagerConsoleScreen(),
    ),
  ],
);
