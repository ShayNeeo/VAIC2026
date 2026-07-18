import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:rm_workspace_core/main.dart';
import 'package:rm_workspace_core/core/rm_workspace_core.dart';

void main() {
  testWidgets('core demo app builds without throwing', (tester) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => CaseController()),
          ChangeNotifierProvider(create: (_) => CaseDetailController()),
        ],
        child: const RMWorkspaceApp(),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.byType(RMWorkspaceApp), findsOneWidget);
  });
}
