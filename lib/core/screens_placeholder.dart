import 'package:flutter/material.dart';

/// Screen widgets (stubs - S1/S2/S3 writers implement)
class QueueScreen extends StatelessWidget {
  const QueueScreen({super.key});
  @override Widget build(BuildContext context) => const Scaffold(body: Center(child: Text('QueueScreen - S1 implements')));
}

class CaseDetailScreen extends StatelessWidget {
  final String caseId;
  const CaseDetailScreen({super.key, required this.caseId});
  @override Widget build(BuildContext context) => Scaffold(body: Center(child: Text('CaseDetailScreen: $caseId - S2 implements')));
}

class ApprovalScreen extends StatelessWidget {
  final String caseId;
  const ApprovalScreen({super.key, required this.caseId});
  @override Widget build(BuildContext context) => Scaffold(body: Center(child: Text('ApprovalScreen: $caseId - S3 implements')));
}