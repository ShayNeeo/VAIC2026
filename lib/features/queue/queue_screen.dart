import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';
import '../../design/widgets/nav_sidebar.dart';

/// S1: Opportunity Queue — Decision Brief list (brief §11)
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
      context.read<CaseController>().loadCases(useMock: false);
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
      builder: (context, controller, _) => LayoutScaffold(
        sidebar: const NavSidebar(current: 'queue'),
        body: Builder(
          builder: (context) {
            final desktop = isDesktop(context);
            if (desktop) {
              return Container(
                color: AppColors.background,
                child: _Content(controller: controller, search: _search),
              );
            }
            return Scaffold(
              backgroundColor: AppColors.background,
              body: CustomScrollView(
                slivers: [
                  _TopBar(onRefresh: () => controller.loadCases(useMock: false)),
                  if (controller.isLoading)
                    const SliverFillRemaining(child: Center(child: CircularProgressIndicator()))
                  else
                    SliverToBoxAdapter(child: _Body(controller: controller, search: _search)),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _Content extends StatelessWidget {
  final CaseController controller;
  final TextEditingController search;
  const _Content({required this.controller, required this.search});

  @override
  Widget build(BuildContext context) {
    if (controller.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    return SingleChildScrollView(
      padding: responsivePadding(context),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _Notice(),
          const SizedBox(height: 16),
          _DesktopHeader(controller: controller, search: search),
          const SizedBox(height: 18),
          _Body(controller: controller, search: search),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

class _DesktopHeader extends StatelessWidget {
  final CaseController controller;
  final TextEditingController search;
  const _DesktopHeader({required this.controller, required this.search});

  @override
  Widget build(BuildContext context) {
    final cases = controller.filteredCases;
    final total = cases.length;
    final ready = cases.where((e) => (e.branchStatusCounts['ready'] ?? 0) > 0).length;
    final need = cases.where((e) => (e.branchStatusCounts['need_info'] ?? 0) > 0).length;
    final blocked = cases.where((e) => (e.branchStatusCounts['blocked'] ?? 0) > 0 || (e.branchStatusCounts['review_required'] ?? 0) > 0).length;
    final opps = cases.fold<int>(0, (s, e) => s + e.opportunityCount);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Cơ hội hôm nay', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: AppColors.navy900, letterSpacing: -0.8, fontFamily: 'Sora')),
              const SizedBox(height: 4),
              const Text('Decision Brief theo từng nhánh · duyệt nhanh, có trách nhiệm, có audit', style: TextStyle(fontSize: 13, color: AppColors.muted)),
              const SizedBox(height: 12),
              Wrap(
                spacing: 18,
                runSpacing: 10,
                children: [
                  _HeaderStat(value: '$total', label: 'Case đang mở', color: AppColors.navy900),
                  _HeaderStat(value: '$opps', label: 'Opportunity', color: AppColors.blue),
                  _HeaderStat(value: '$ready', label: 'Sẵn sàng', color: AppColors.statusReady),
                  _HeaderStat(value: '$need', label: 'Thiếu hồ sơ', color: AppColors.statusNeedInfo),
                  _HeaderStat(value: '$blocked', label: 'Chờ/chặn', color: AppColors.statusBlocked),
                ],
              ),
            ],
          ),
        ),
        SizedBox(
          width: 300,
          child: TextField(
            controller: search,
            decoration: const InputDecoration(hintText: 'Tìm doanh nghiệp, case, MST…', prefixIcon: Icon(Icons.search, color: AppColors.subtle)),
          ),
        ),
      ],
    );
  }
}

class _HeaderStat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _HeaderStat({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) => Row(
        children: [
          Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: color, fontFamily: 'Sora')),
          const SizedBox(width: 5),
          Text(label, style: const TextStyle(fontSize: 11, color: AppColors.muted)),
        ],
      );
}

class _TopBar extends StatelessWidget {
  final VoidCallback onRefresh;
  const _TopBar({required this.onRefresh});

  @override
  Widget build(BuildContext context) => SliverAppBar(
        pinned: true,
        backgroundColor: AppColors.navy900,
        foregroundColor: Colors.white,
        expandedHeight: 84,
        flexibleSpace: const FlexibleSpaceBar(
          titlePadding: EdgeInsets.only(left: 16, bottom: 14),
          title: Column(
            mainAxisAlignment: MainAxisAlignment.end,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Cơ hội hôm nay', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700, letterSpacing: -0.5, fontFamily: 'Sora')),
              Text('Decision Brief theo từng nhánh', style: TextStyle(fontSize: 11, color: Color(0xFFA9BDD1))),
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

class _Notice extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.fromLTRB(0, 4, 0, 0),
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

    final head = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!isDesktop(context)) _Notice(),
        if (!isDesktop(context)) _Metrics(open: open, ready: ready, need: need),
        if (!isDesktop(context)) _SearchField(controller: search),
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
      ],
    );

    if (visible.isEmpty) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          head,
          const Padding(padding: EdgeInsets.all(24), child: Text('Không có case phù hợp bộ lọc.')),
        ],
      );
    }

    if (isDesktop(context)) {
      final cols = gridColumns(context).clamp(2, 4);
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          head,
          const SizedBox(height: 8),
          Wrap(
            spacing: 14,
            runSpacing: 14,
            children: visible.map((c) => SizedBox(width: _cardWidth(context, cols), child: _CaseCard(c: c))).toList(),
          ),
          const SizedBox(height: 24),
        ],
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        head,
        ...visible.map((c) => _CaseCard(c: c)),
        const SizedBox(height: 24),
      ],
    );
  }

  double _cardWidth(BuildContext context, int cols) {
    final pad = responsivePadding(context).left + responsivePadding(context).right;
    final w = MediaQuery.of(context).size.width - 280 - pad;
    return (w - 14 * (cols - 1)) / cols;
  }

  int _readyCount(List<CaseQueueItem> c) => c.where((e) => (e.branchStatusCounts['ready'] ?? 0) > 0).length;
  int _needCount(List<CaseQueueItem> c) => c.where((e) => (e.branchStatusCounts['need_info'] ?? 0) > 0).length;
}

class _Metrics extends StatelessWidget {
  final int open, ready, need;
  const _Metrics({required this.open, required this.ready, required this.need});

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 14),
        child: Row(
          children: [
            _Metric(label: 'Cơ hội đang mở', value: '$open', sub: '+3 trong 7 ngày gần nhất', icon: Icons.cases_outlined, color: AppColors.blue, bg: AppColors.blue100),
            _Metric(label: 'Sẵn sàng tiếp cận', value: '$ready', sub: '61% opportunity pipeline', icon: Icons.check_circle, color: AppColors.statusReady, bg: AppColors.statusReady100),
            _Metric(label: 'Cần bổ sung hồ sơ', value: '$need', sub: '2 case gần quá SLA', icon: Icons.description, color: AppColors.statusNeedInfo, bg: AppColors.statusNeedInfo100),
          ],
        ),
      );
}

class _Metric extends StatelessWidget {
  final String label, value, sub;
  final IconData icon;
  final Color color, bg;
  const _Metric({required this.label, required this.value, required this.sub, required this.icon, required this.color, required this.bg});

  @override
  Widget build(BuildContext context) => Container(
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
            Text(value, style: const TextStyle(fontSize: 27, fontWeight: FontWeight.w800, color: AppColors.navy900, letterSpacing: -1, fontFamily: 'Sora')),
            Text(sub, style: const TextStyle(fontSize: 10, color: AppColors.muted)),
          ],
        ),
      );
}

class _SearchField extends StatelessWidget {
  final TextEditingController controller;
  const _SearchField({required this.controller});

  @override
  Widget build(BuildContext context) => Padding(
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
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: selected ? AppColors.navy900 : AppColors.surface,
                  border: Border.all(color: selected ? AppColors.navy900 : AppColors.line),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(labels[f]!, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: selected ? Colors.white : AppColors.muted)),
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
      margin: const EdgeInsets.fromLTRB(14, 0, 14, 12),
      decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () => context.go('/case/${c.caseId}'),
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(width: 44, height: 44, decoration: BoxDecoration(gradient: const LinearGradient(colors: [AppColors.navy800, AppColors.blue]), borderRadius: BorderRadius.circular(12)), child: Center(child: Text(logo, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 12)))),
                  const SizedBox(width: 11),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(c.companyName, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.ink)),
                    const SizedBox(height: 2),
                    Text(c.title, style: const TextStyle(fontSize: 10, color: AppColors.muted)),
                  ])),
                  Container(padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5), decoration: BoxDecoration(color: AppColors.gold100, borderRadius: BorderRadius.circular(9)), child: Text('${c.opportunityCount}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: AppColors.gold))),
                ],
              ),
              const SizedBox(height: 12),
              _BranchBar(counts: counts),
              const SizedBox(height: 11),
              Wrap(spacing: 6, runSpacing: 6, children: [
                if ((counts['ready'] ?? 0) > 0) const StatusChip(status: OpportunityStatus.ready),
                if ((counts['need_info'] ?? 0) > 0) const StatusChip(status: OpportunityStatus.needInfo),
                if ((counts['review_required'] ?? 0) > 0) const StatusChip(status: OpportunityStatus.reviewRequired),
                if ((counts['blocked'] ?? 0) > 0) const StatusChip(status: OpportunityStatus.blocked),
              ]),
              const SizedBox(height: 11),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('NEXT-BEST-ACTION', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.subtle, letterSpacing: 0.6)),
                  const SizedBox(height: 2),
                  Text(c.nextAction, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.ink2)),
                ])),
                Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(999)), child: Text('SLA ${c.sla}', style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.subtle))),
              ]),
              const SizedBox(height: 10),
              Container(
                width: double.infinity,
                alignment: Alignment.center,
                padding: const EdgeInsets.symmetric(vertical: 9),
                decoration: BoxDecoration(color: AppColors.navy900, borderRadius: BorderRadius.circular(10)),
                child: const Row(mainAxisAlignment: MainAxisAlignment.center, mainAxisSize: MainAxisSize.min, children: [Flexible(child: Text('Mở Decision Brief', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w800), overflow: TextOverflow.ellipsis)), SizedBox(width: 6), Icon(Icons.arrow_forward, color: Colors.white, size: 14)]),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Branch-status mini bar: visual share of ready / need_info / review / blocked
class _BranchBar extends StatelessWidget {
  final Map<String, int> counts;
  const _BranchBar({required this.counts});

  @override
  Widget build(BuildContext context) {
    final total = (counts['ready'] ?? 0) + (counts['need_info'] ?? 0) + (counts['review_required'] ?? 0) + (counts['blocked'] ?? 0);
    if (total == 0) return const SizedBox.shrink();
    final segs = <Color, int>{
      AppColors.statusReady: counts['ready'] ?? 0,
      AppColors.statusNeedInfo: counts['need_info'] ?? 0,
      AppColors.statusBlocked: (counts['review_required'] ?? 0) + (counts['blocked'] ?? 0),
    };
    return Container(
      height: 6,
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(999), color: AppColors.line),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(999),
        child: Row(
          children: segs.entries.where((e) => e.value > 0).map((e) {
            return Expanded(flex: e.value, child: Container(color: e.key));
          }).toList(),
        ),
      ),
    );
  }
}
