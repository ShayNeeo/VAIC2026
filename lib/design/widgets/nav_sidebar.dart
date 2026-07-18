import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/app_theme.dart';

/// Left navigation sidebar — mirrors SHB Opportunity OS demo (navy rail,
/// gradient logo, sectioned nav, agent/perf links).
class NavSidebar extends StatelessWidget {
  final String current;

  const NavSidebar({super.key, this.current = 'queue'});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.navy950,
      child: Column(
        children: [
          _brand(),
          const SizedBox(height: 8),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _sectionLabel('Workspace'),
                  _item(icon: Icons.view_agenda_outlined, label: 'Cơ hội hôm nay', route: '/queue', active: current == 'queue'),
                  _item(icon: Icons.account_tree_outlined, label: 'Agent trace', route: '/queue', active: false),
                  _item(icon: Icons.verified_outlined, label: 'Bằng chứng', route: '/queue', active: false),
                  const SizedBox(height: 14),
                  _sectionLabel('Vận hành'),
                  _item(icon: Icons.insights_outlined, label: 'Hiệu suất & kiểm soát', route: '/queue', active: false),
                  _item(icon: Icons.gavel_outlined, label: 'Duyệt hành động', route: '/queue', active: false),
                  _item(icon: Icons.description_outlined, label: 'Tài liệu', route: '/queue', active: false),
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
                gradient: const LinearGradient(colors: [AppColors.blue, AppColors.navy700]),
                borderRadius: BorderRadius.circular(11),
              ),
              child: const Center(child: Icon(Icons.shield_outlined, color: Colors.white, size: 20)),
            ),
            const SizedBox(width: 11),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('SHB Opportunity OS', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800, letterSpacing: -0.3)),
                  Text('RM Enterprise Workspace', style: TextStyle(color: Color(0xFF9FB4CC), fontSize: 10.5)),
                ],
              ),
            ),
          ],
        ),
      );

  Widget _sectionLabel(String t) => Padding(
        padding: const EdgeInsets.fromLTRB(10, 6, 10, 6),
        child: Text(t.toUpperCase(), style: const TextStyle(color: Color(0xFF6E86A3), fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 0.8)),
      );

  Widget _item({
    required IconData icon,
    required String label,
    required String route,
    required bool active,
  }) =>
      Builder(
        builder: (context) => InkWell(
          onTap: () => context.go(route),
          borderRadius: BorderRadius.circular(10),
          child: Container(
            margin: const EdgeInsets.only(bottom: 3),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: active ? AppColors.blue.withValues(alpha: 0.16) : Colors.transparent,
              borderRadius: BorderRadius.circular(10),
              border: active ? Border.all(color: AppColors.blue.withValues(alpha: 0.5)) : null,
            ),
            child: Row(
              children: [
                Icon(icon, size: 18, color: active ? AppColors.blue : const Color(0xFFA9BDD1)),
                const SizedBox(width: 11),
                Expanded(child: Text(label, style: TextStyle(color: active ? Colors.white : const Color(0xFFC7D6E6), fontSize: 13, fontWeight: active ? FontWeight.w700 : FontWeight.w500))),
              ],
            ),
          ),
        ),
      );

  Widget _footnote() => Container(
        padding: const EdgeInsets.all(14),
        decoration: const BoxDecoration(border: Border(top: BorderSide(color: Color(0x33FFFFFF)))),
        child: const Row(
          children: [
            CircleAvatar(radius: 15, backgroundColor: Colors.white, child: Text('NA', style: TextStyle(color: AppColors.navy900, fontSize: 10, fontWeight: FontWeight.w800))),
            SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Nguyễn An', style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700)),
                  Text('RM Doanh nghiệp', style: TextStyle(color: Color(0xFF9FB4CC), fontSize: 10)),
                ],
              ),
            ),
            Icon(Icons.settings_outlined, size: 16, color: Color(0xFF9FB4CC)),
          ],
        ),
      );
}
