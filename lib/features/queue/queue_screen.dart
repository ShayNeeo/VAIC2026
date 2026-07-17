import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';

/// S1: Opportunity Queue — mirrors SHB Opportunity OS mobile/index.html
class QueueScreen extends StatefulWidget {
  const QueueScreen({super.key});

  @override
  State<QueueScreen> createState() => _QueueScreenState();
}

class _QueueScreenState extends State<QueueScreen> {
  final TextEditingController _search = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<CaseController>().loadCases(useMock: true);
    });
    _search.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CaseController>(
      builder: (context, controller, _) => Scaffold(
        backgroundColor: AppColors.background,
        body: CustomScrollView(
          slivers: [
            _TopBar(subtitle: 'Ưu tiên theo giá trị, độ sẵn sàng và SLA', onRefresh: () => controller.loadCases(useMock: true)),
            if (controller.isLoading)
              const SliverFillRemaining(child: Center(child: CircularProgressIndicator()))
            else if (controller.error != null)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: Colors.red),
                      const SizedBox(height: 16),
                      Text('Lỗi: ${controller.error}'),
                      const SizedBox(height: 16),
                      ElevatedButton(onPressed: () => controller.loadCases(useMock: true), child: const Text('Thử lại')),
                    ],
                  ),
                ),
              )
            else
              SliverToBoxAdapter(child: _Body(controller: controller, search: _search)),
          ],
        ),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  final String subtitle;
  final VoidCallback onRefresh;
  const _TopBar({required this.subtitle, required this.onRefresh});

  @override
  Widget build(BuildContext context) {
    return SliverAppBar(
      pinned: true,
      backgroundColor: AppColors.navy900,
      foregroundColor: Colors.white,
      expandedHeight: 92,
      flexibleSpace: FlexibleSpaceBar(
        titlePadding: const EdgeInsets.only(left: 16, bottom: 14),
        title: Column(
          mainAxisAlignment: MainAxisAlignment.end,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Cơ hội hôm nay', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700, letterSpacing: -0.5)),
            Text(subtitle, style: const TextStyle(fontSize: 11, color: Color(0xFFA9BDD1))),
          ],
        ),
      ),
      actions: [
        IconButton(icon: const Icon(Icons.notifications_outlined), onPressed: () {}),
        IconButton(icon: const Icon(Icons.refresh), onPressed: onRefresh),
        const SizedBox(width: 8),
        const CircleAvatar(radius: 16, backgroundColor: Colors.white, child: Text('NA', style: TextStyle(color: AppColors.navy900, fontSize: 11, fontWeight: FontWeight.w800))),
        const SizedBox(width: 12),
      ],
    );
  }
}

class _Body extends StatelessWidget {
  final CaseController controller;
  final TextEditingController search;
  const _Body({required this.controller, required this.search});

  @override
  Widget build(BuildContext context) {
    final cases = controller.filteredCases;
    final q = search.text.toLowerCase();
    final visible = cases.where((c) => '${c.companyName} ${c.title}'.toLowerCase().contains(q)).toList();
    final open = cases.length;
    final ready = _readyCount(cases);
    final need = _needCount(cases);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _Notice(),
        _Metrics(open: open, ready: ready, need: need),
        _SearchField(controller: search),
        _FilterChips(controller: controller),
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 4, 14, 0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Case ưu tiên', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.navy900)),
              TextButton(onPressed: () {}, child: const Text('Xem agent trace', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppColors.blue))),
            ],
          ),
        ),
        if (visible.isEmpty)
          const Padding(padding: EdgeInsets.all(24), child: Text('Không có case phù hợp bộ lọc.'))
        else
          ...visible.map((c) => _CaseCard(c: c)),
        const SizedBox(height: 24),
      ],
    );
  }

  int _readyCount(List<CaseQueueItem> c) => c.where((e) => (e.branchStatusCounts['ready'] ?? 0) > 0).length;
  int _needCount(List<CaseQueueItem> c) => c.where((e) => (e.branchStatusCounts['need_info'] ?? 0) > 0).length;
}

class _Notice extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(14, 14, 14, 12),
      padding: const EdgeInsets.all(11),
      decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(13)),
      child: const Row(
        children: [
          Icon(Icons.info_outline, color: AppColors.blue, size: 18),
          SizedBox(width: 9),
          Expanded(child: Text('Chế độ demo an toàn · Dữ liệu, chính sách và hành động đều synthetic; không kết nối hệ thống SHB thật.', style: TextStyle(fontSize: 11, color: AppColors.muted))),
        ],
      ),
    );
  }
}

class _Metrics extends StatelessWidget {
  final int open, ready, need;
  const _Metrics({required this.open, required this.ready, required this.need});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 14),
      child: Row(
        children: [
          _Metric(label: 'Cơ hội đang mở', value: '$open', sub: '+4 trong 7 ngày gần nhất', icon: Icons.cases_outlined, color: AppColors.blue, bg: AppColors.blue100),
          _Metric(label: 'Sẵn sàng tiếp cận', value: '$ready', sub: '61% opportunity pipeline', icon: Icons.check_circle, color: AppColors.statusReady, bg: AppColors.statusReady100),
          _Metric(label: 'Cần bổ sung hồ sơ', value: '$need', sub: '2 case gần quá SLA', icon: Icons.description, color: AppColors.statusNeedInfo, bg: AppColors.statusNeedInfo100),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  final String label, value, sub;
  final IconData icon;
  final Color color, bg;
  const _Metric({required this.label, required this.value, required this.sub, required this.icon, required this.color, required this.bg});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 200,
      margin: const EdgeInsets.only(right: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text(label.toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppColors.muted, letterSpacing: 0.5)),
            Container(width: 32, height: 32, decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: color, size: 18)),
          ]),
          const SizedBox(height: 7),
          Text(value, style: const TextStyle(fontSize: 27, fontWeight: FontWeight.w900, color: AppColors.navy900, letterSpacing: -1)),
          Text(sub, style: const TextStyle(fontSize: 10, color: AppColors.muted)),
        ],
      ),
    );
  }
}

class _SearchField extends StatelessWidget {
  final TextEditingController controller;
  const _SearchField({required this.controller});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),
      child: TextField(
        controller: controller,
        decoration: const InputDecoration(
          hintText: 'Tìm doanh nghiệp, case, MST…',
          prefixIcon: Icon(Icons.search, color: AppColors.subtle),
        ),
      ),
    );
  }
}

class _FilterChips extends StatelessWidget {
  final CaseController controller;
  const _FilterChips({required this.controller});

  @override
  Widget build(BuildContext context) {
    const filters = ['all', 'ready', 'need_info', 'review_required', 'blocked'];
    final labels = {'all': 'Tất cả', 'ready': 'Sẵn sàng', 'need_info': 'Thiếu hồ sơ', 'review_required': 'Cần chuyên gia', 'blocked': 'Bị chặn'};
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
      child: Row(
        children: filters.map((f) {
          final selected = controller.filter == f;
          return Padding(
            padding: const EdgeInsets.only(right: 7),
            child: InkWell(
              onTap: () => controller.setFilter(f),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
                decoration: BoxDecoration(
                  color: selected ? AppColors.navy900 : AppColors.surface,
                  border: Border.all(color: selected ? AppColors.navy900 : AppColors.line),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(labels[f]!, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: selected ? Colors.white : AppColors.muted)),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _CaseCard extends StatelessWidget {
  final CaseQueueItem c;
  const _CaseCard({required this.c});

  @override
  Widget build(BuildContext context) {
    final counts = c.branchStatusCounts;
    final logo = c.companyName.isNotEmpty ? c.companyName.substring(0, c.companyName.length >= 3 ? 3 : c.companyName.length).toUpperCase() : '?';
    return Container(
      margin: const EdgeInsets.fromLTRB(14, 0, 14, 10),
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () => context.go('/case/${c.caseId}'),
        borderRadius: BorderRadius.circular(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(width: 42, height: 42, decoration: BoxDecoration(gradient: const LinearGradient(colors: [AppColors.navy800, AppColors.blue]), borderRadius: BorderRadius.circular(12)), child: Center(child: Text(logo, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 11)))),
                const SizedBox(width: 11),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(c.companyName, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.ink)),
                  const SizedBox(height: 2),
                  Text(c.title, style: const TextStyle(fontSize: 10, color: AppColors.muted)),
                ])),
                Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5), decoration: BoxDecoration(color: AppColors.blue100, borderRadius: BorderRadius.circular(9)), child: Text('${c.opportunityCount}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: AppColors.navy900))),
              ],
            ),
            const SizedBox(height: 11),
            Wrap(spacing: 6, runSpacing: 6, children: [
              if ((counts['ready'] ?? 0) > 0) const StatusChip(status: OpportunityStatus.ready),
              if ((counts['need_info'] ?? 0) > 0) const StatusChip(status: OpportunityStatus.needInfo),
              if ((counts['review_required'] ?? 0) > 0) const StatusChip(status: OpportunityStatus.reviewRequired),
              if ((counts['blocked'] ?? 0) > 0) const StatusChip(status: OpportunityStatus.blocked),
              Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3), decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(999)), child: const Text('SLA', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.subtle))),
            ]),
            const SizedBox(height: 10),
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Next-best-action', style: TextStyle(fontSize: 10, color: AppColors.muted)),
                const SizedBox(height: 2),
                Text(c.nextAction, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.ink2)),
              ])),
              Container(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9), decoration: BoxDecoration(color: AppColors.navy900, borderRadius: BorderRadius.circular(10)), child: const Row(children: [Text('Mở', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w800)), SizedBox(width: 6), Icon(Icons.arrow_forward, color: Colors.white, size: 14)])),
            ]),
          ],
        ),
      ),
    );
  }
}
