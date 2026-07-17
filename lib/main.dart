import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:rm_workspace_core/rm_workspace_core.dart' hide CaseDetailScreen;
import 'package:rm_workspace_design/design.dart';
import 'features/case_detail/case_detail_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => CaseDetailController(apiClient: buildApiClient())),
      ],
      child: const CaseDetailApp(),
    ),
  );
}

class CaseDetailApp extends StatelessWidget {
  const CaseDetailApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'RM Workspace - Case Detail',
      debugShowCheckedModeBanner: false,
      theme: lightTheme(),
      darkTheme: darkTheme(),
      routerConfig: _router,
    );
  }
}

final GoRouter _router = GoRouter(
  initialLocation: '/case/CORP-2026-001',
  routes: [
    GoRoute(
      path: '/case/:caseId',
      name: 'case-detail',
      builder: (context, state) =>
          CaseDetailScreen(caseId: state.pathParameters['caseId']!),
    ),
  ],
);
