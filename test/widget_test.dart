import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:rm_workspace_core/core/rm_workspace_core.dart';

import '../lib/main.dart';

void main() {
  testWidgets('agent app builds without throwing', (tester) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => CaseController()),
          ChangeNotifierProvider(create: (_) => CaseDetailController()),
          ChangeNotifierProvider(create: (_) => EmployeeWorkspaceController()),
        ],
        child: const AgentApp(),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byType(AgentApp), findsOneWidget);
  });
}
