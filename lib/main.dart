import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:rm_workspace_core/rm_workspace_core.dart';
import 'package:rm_workspace_design/design.dart';

// Note: QueueScreen is implemented in the S1 package, not in core.
// This demo app wires the placeholder detail/approval screens.

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => CaseController()),
      ],
      child: const RMWorkspaceApp(),
    ),
  );
}

class RMWorkspaceApp extends StatelessWidget {
  const RMWorkspaceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'RM Workspace',
      debugShowCheckedModeBanner: false,
      theme: lightTheme(),
      darkTheme: darkTheme(),
      routerConfig: _router,
    );
  }
}

final GoRouter _router = GoRouter(
  initialLocation: '/queue',
  routes: [
    GoRoute(
      path: '/case/:caseId',
      name: 'case-detail',
      builder: (context, state) {
        final caseId = state.pathParameters['caseId']!;
        return CaseDetailScreen(caseId: caseId);
      },
    ),
    GoRoute(
      path: '/approval/:caseId',
      name: 'approval',
      builder: (context, state) {
        final caseId = state.pathParameters['caseId']!;
        return ApprovalScreen(caseId: caseId);
      },
    ),
  ],
);