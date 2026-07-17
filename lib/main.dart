import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:rm_workspace_core/rm_workspace_core.dart' hide ApprovalScreen;
import 'package:rm_workspace_design/design.dart';
import 'features/approval/approval_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => CaseDetailController(apiClient: buildApiClient())),
      ],
      child: const ApprovalApp(),
    ),
  );
}

class ApprovalApp extends StatelessWidget {
  const ApprovalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'RM Workspace - Approval',
      debugShowCheckedModeBanner: false,
      theme: lightTheme(),
      darkTheme: darkTheme(),
      routerConfig: _router,
    );
  }
}

final GoRouter _router = GoRouter(
  initialLocation: '/approval/CORP-2026-001',
  routes: [
    GoRoute(
      path: '/approval/:caseId',
      name: 'approval',
      builder: (context, state) =>
          ApprovalScreen(caseId: state.pathParameters['caseId']!),
    ),
  ],
);
