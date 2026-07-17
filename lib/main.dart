import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:rm_workspace_core/rm_workspace_core.dart';
import 'package:rm_workspace_design/design.dart';
import 'features/queue/queue_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => CaseController(apiClient: buildApiClient())),
      ],
      child: const QueueApp(),
    ),
  );
}

class QueueApp extends StatelessWidget {
  const QueueApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'RM Workspace - Queue',
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
      path: '/queue',
      name: 'queue',
      builder: (context, state) => const QueueScreen(),
    ),
    // S2/S3 will be in main app, not here
  ],
);