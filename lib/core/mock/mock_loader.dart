import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/case_models.dart';

/// Mock data loader for synthetic cases (brief §11)
class MockLoader {
  static Future<List<CaseQueueItem>> loadQueue() async {
    final jsonString = await rootBundle.loadString('assets/mock/cases.json');
    final data = jsonDecode(jsonString) as Map<String, dynamic>;
    return (data['queue'] as List).map((e) => CaseQueueItem.fromJson(e)).toList();
  }

  static Future<CaseDetail> loadCase(String caseId) async {
    final jsonString = await rootBundle.loadString('assets/mock/cases.json');
    final data = jsonDecode(jsonString) as Map<String, dynamic>;
    final caseData = (data['details'] as List).firstWhere((e) => e['caseId'] == caseId);
    return CaseDetail.fromJson(caseData);
  }
}