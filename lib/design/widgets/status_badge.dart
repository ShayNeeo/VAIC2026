import 'package:flutter/material.dart';
import '../../core/models/case_models.dart';
import '../theme/app_theme.dart';

/// Status badge — maps OpportunityStatus to Agent-OS neon tokens.
class StatusBadge extends StatelessWidget {
  final OpportunityStatus status;
  final String? label;
  const StatusBadge({super.key, required this.status, this.label});

  @override
  Widget build(BuildContext context) {
    final (fg, bg, icon, def) = _cfg(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999), border: Border.all(color: fg.withValues(alpha: 0.4))),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 12, color: fg),
        const SizedBox(width: 4),
        Text(label ?? def, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: fg, letterSpacing: 0.2)),
      ]),
    );
  }
}

(Color, Color, IconData, String) _cfg(OpportunityStatus s) => switch (s) {
      OpportunityStatus.ready => (AppColors.ready, AppColors.readyBg, Icons.check_circle_outline, 'Sẵn sàng'),
      OpportunityStatus.needInfo => (AppColors.needInfo, AppColors.needInfoBg, Icons.info_outline, 'Thiếu thông tin'),
      OpportunityStatus.reviewRequired => (AppColors.block, AppColors.blockBg, Icons.gavel, 'Cần chuyên gia'),
      OpportunityStatus.blocked => (AppColors.block, AppColors.blockBg, Icons.block, 'Bị chặn'),
      OpportunityStatus.aiCta => (AppColors.review, AppColors.reviewBg, Icons.smart_toy_outlined, 'AI đề xuất'),
    };

class StatusChip extends StatelessWidget {
  final OpportunityStatus status;
  const StatusChip({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final (fg, bg, icon, def) = _cfg(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 10, color: fg),
        const SizedBox(width: 4),
        Text(def, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: fg)),
      ]),
    );
  }
}
