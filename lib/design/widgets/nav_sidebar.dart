import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/app_theme.dart';

/// Agent-OS left rail — neon brand, role-aware nav.
class NavSidebar extends StatelessWidget {
  final String current;
  final String employeeId;
  final String roleLabel;

  const NavSidebar({super.key, this.current = 'queue', this.employeeId = 'RM', this.roleLabel = 'Agent'});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.ink850,
        border: const Border(right: BorderSide(color: AppColors.lineSoft)),
      ),
      child: Column(
        children: [
          _brand(),
          const SizedBox(height: 6),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _sectionLabel('Workspace'),
                  _item(icon: Icons.view_agenda_outlined, label: 'Case Queue', route: '/queue', active: current == 'queue'),
                  _item(icon: Icons.auto_awesome_outlined, label: 'Agent Trace', route: '/queue', active: false),
                  _item(icon: Icons.gavel_outlined, label: 'Approval', route: '/queue', active: false),
                  const SizedBox(height: 14),
                  _sectionLabel('Vận hành'),
                  _item(icon: Icons.insights_outlined, label: 'Guardrails & Audit', route: '/queue', active: false),
                  _item(icon: Icons.dataset_outlined, label: 'Knowledge', route: '/queue', active: false),
                  _item(icon: Icons.person_outline, label: 'My Copilot', route: '/employee-workspace', active: current == 'employee-workspace'),
                ],
              ),
            ),
          ),
          _footnote(),
        ],
      ),
    );
  }

  Widget _brand() => Container(
        padding: const EdgeInsets.fromLTRB(18, 20, 18, 14),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [AppColors.cyan, AppColors.violet]),
                borderRadius: BorderRadius.circular(11),
                boxShadow: [BoxShadow(color: AppColors.cyan.withValues(alpha: 0.4), blurRadius: 14, offset: const Offset(0, 3))],
              ),
              child: const Center(child: Icon(Icons.bolt_outlined, color: Colors.white, size: 20)),
            ),
            const SizedBox(width: 11),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('VAIC', style: TextStyle(color: AppColors.txt, fontSize: 15, fontWeight: FontWeight.w800, letterSpacing: 1.2, fontFamily: 'BeVietnamPro')),
                  Text('Agent Sales Copilot', style: TextStyle(color: AppColors.cyanSoft, fontSize: 10)),
                ],
              ),
            ),
          ],
        ),
      );

  Widget _sectionLabel(String t) => Padding(
        padding: const EdgeInsets.fromLTRB(10, 6, 10, 6),
        child: Text(t.toUpperCase(), style: const TextStyle(color: AppColors.subtle, fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 0.9)),
      );

  Widget _item({required IconData icon, required String label, required String route, required bool active}) =>
      Builder(
        builder: (context) => InkWell(
          onTap: () => context.go(route),
          borderRadius: BorderRadius.circular(10),
          child: Container(
            margin: const EdgeInsets.only(bottom: 3),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: active ? AppColors.orange.withValues(alpha: 0.12) : Colors.transparent,
              borderRadius: BorderRadius.circular(10),
              border: active ? Border.all(color: AppColors.orange.withValues(alpha: 0.5)) : null,
            ),
            child: Row(
              children: [
                Icon(icon, size: 18, color: active ? AppColors.orange : AppColors.textSecondary),
                const SizedBox(width: 11),
                Expanded(child: Text(label, style: TextStyle(color: active ? AppColors.txt : AppColors.txt2, fontSize: 13, fontWeight: active ? FontWeight.w700 : FontWeight.w500))),
                if (active) Container(width: 6, height: 6, decoration: const BoxDecoration(color: AppColors.orange, shape: BoxShape.circle)),
              ],
            ),
          ),
        ),
      );

  Widget _footnote() => Container(
        padding: const EdgeInsets.all(14),
        decoration: const BoxDecoration(border: Border(top: BorderSide(color: AppColors.lineSoft))),
        child: Row(
          children: [
            CircleAvatar(radius: 15, backgroundColor: AppColors.navy, child: Text(employeeId.isNotEmpty ? employeeId[0] : 'A', style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w800))),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(employeeId, style: const TextStyle(color: AppColors.txt, fontSize: 12, fontWeight: FontWeight.w700)),
                  Text(roleLabel, style: const TextStyle(color: AppColors.muted, fontSize: 10)),
                ],
              ),
            ),
            const Icon(Icons.settings_outlined, size: 16, color: AppColors.muted),
          ],
        ),
      );
}
