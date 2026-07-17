import 'package:flutter_test/flutter_test.dart';
import 'package:rm_workspace_core/main.dart';

void main() {
  testWidgets('core demo app builds without throwing', (tester) async {
    await tester.pumpWidget(const RMWorkspaceApp());
    expect(find.byType(RMWorkspaceApp), findsOneWidget);
  });
}
