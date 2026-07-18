import 'package:flutter/material.dart';
import '../../core/rm_workspace_core.dart';
import '../theme/app_theme.dart';

/// Status badge widget — used across S1, S2, S3
class StatusBadge extends StatelessWidget {
  final OpportunityStatus status;
  final String? label;
  final bool showIcon;
  final EdgeInsetsGeometry? padding;

  const StatusBadge({
    super.key,
    required this.status,
    this.label,
    this.showIcon = true,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final (fg, bg, icon, defaultLabel) = _statusConfig(status);
    final displayLabel = label ?? defaultLabel;

    return Container(
      padding: padding ?? const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (showIcon) ...[
            Icon(icon, size: 12, color: fg),
            const SizedBox(width: 4),
          ],
          Text(
            displayLabel,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              color: fg,
              letterSpacing: 0.2,
            ),
          ),
        ],
      ),
    );
  }

  (Color, Color, IconData, String) _statusConfig(OpportunityStatus s) {
    switch (s) {
      case OpportunityStatus.ready:
        return (AppColors.statusReady, AppColors.statusReady100, Icons.check_circle_outline, 'Sẵn sàng');
      case OpportunityStatus.needInfo:
        return (AppColors.statusNeedInfo, AppColors.statusNeedInfo100, Icons.info_outline, 'Thiếu thông tin');
      case OpportunityStatus.reviewRequired:
        return (AppColors.statusBlocked, AppColors.statusBlocked100, Icons.gavel, 'Cần chuyên gia');
      case OpportunityStatus.blocked:
        return (AppColors.statusBlocked, AppColors.statusBlocked100, Icons.block, 'Bị chặn');
      case OpportunityStatus.aiCta:
        return (AppColors.statusAiCta, AppColors.statusAiCta100, Icons.smart_toy_outlined, 'AI đề xuất');
    }
  }
}

/// Compact status chip for list rows
class StatusChip extends StatelessWidget {
  final OpportunityStatus status;
  const StatusChip({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final (fg, bg, icon, label) = _statusConfig(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 10, color: fg),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w800,
              color: fg,
            ),
          ),
        ],
      ),
    );
  }

  (Color, Color, IconData, String) _statusConfig(OpportunityStatus s) {
    switch (s) {
      case OpportunityStatus.ready:
        return (AppColors.statusReady, AppColors.statusReady100, Icons.check_circle, 'Ready');
      case OpportunityStatus.needInfo:
        return (AppColors.statusNeedInfo, AppColors.statusNeedInfo100, Icons.info, 'Need Info');
      case OpportunityStatus.reviewRequired:
        return (AppColors.statusBlocked, AppColors.statusBlocked100, Icons.gavel, 'Review');
      case OpportunityStatus.blocked:
        return (AppColors.statusBlocked, AppColors.statusBlocked100, Icons.block, 'Blocked');
      case OpportunityStatus.aiCta:
        return (AppColors.statusAiCta, AppColors.statusAiCta100, Icons.smart_toy, 'AI');
    }
  }
}