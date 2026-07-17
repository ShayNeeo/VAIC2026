import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';

/// S2: Case Decision Workspace — mirrors SHB Opportunity OS workspace screen
class CaseDetailScreen extends StatefulWidget {
  final String caseId;
  const CaseDetailScreen({super.key, required this.caseId});

  @override
  State<CaseDetailScreen> createState() => _CaseDetailScreenState();
}

class _CaseDetailScreenState extends State<CaseDetailScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<CaseDetailController>().loadCase(widget.caseId, useMock: true);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CaseDetailController>(
      builder: (context, ctrl, _) => Scaffold(
        backgroundColor: AppColors.background,
        body: CustomScrollView(
          slivers: [
            _TopBar(caseId: widget.caseId, onBack: () => context.go('/queue'), onApprove: () => context.go('/approval/${widget.caseId}')),
            if (ctrl.isLoading)
              const SliverFillRemaining(child: Center(child: CircularProgressIndicator()))
            else if (ctrl.error != null)
              SliverToBoxAdapter(child: Padding(padding: const EdgeInsets.all(24), child: Text('Lỗi: ${ctrl.error}')))
            else if (ctrl.caseDetail == null)
              const SliverToBoxAdapter(child: Padding(padding: EdgeInsets.all(24), child: Text('Không có dữ liệu')))
            else
              SliverToBoxAdapter(child: _Body(detail: ctrl.caseDetail!, caseId: widget.caseId)),
          ],
        ),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  final String caseId;
  final VoidCallback onBack;
  final VoidCallback onApprove;
  const _TopBar({required this.caseId, required this.onBack, required this.onApprove});

  @override
  Widget build(BuildContext context) {
    return SliverAppBar(
      pinned: true,
      backgroundColor: AppColors.navy900,
      foregroundColor: Colors.white,
      leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: onBack),
      title: Text('Decision Brief · $caseId', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
      actions: [
        ElevatedButton.icon(
          icon: const Icon(Icons.shield, size: 16),
          label: const Text('Phê duyệt', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900)),
          onPressed: onApprove,
          style: ElevatedButton.styleFrom(backgroundColor: AppColors.orange, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
        ),
        const SizedBox(width: 12),
      ],
    );
  }
}

class _Body extends StatelessWidget {
  final CaseDetail detail;
  final String caseId;
  const _Body({required this.detail, required this.caseId});

  @override
  Widget build(BuildContext context) {
    final logo = detail.companyName.isNotEmpty ? detail.companyName.substring(0, detail.companyName.length >= 3 ? 3 : detail.companyName.length).toUpperCase() : '?';
    return Column(
      children: [
        Container(
          margin: const EdgeInsets.all(14),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(gradient: const LinearGradient(colors: [AppColors.navy900, Color(0xFF0B315E)]), borderRadius: BorderRadius.circular(18)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                Container(width: 42, height: 42, decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)), child: Center(child: Text(logo, style: const TextStyle(color: AppColors.navy900, fontWeight: FontWeight.w900, fontSize: 11)))),
                const SizedBox(width: 11),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(detail.companyName, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w700)),
                  Text('${detail.caseId} · ${detail.segment} · ${detail.industry}', style: const TextStyle(color: Color(0xFFAEC3D8), fontSize: 10)),
                ])),
              ]),
              const SizedBox(height: 12),
              Wrap(spacing: 6, runSpacing: 6, children: [
                _Tag('RM: ${detail.rmName}'),
                _Tag('Case: ${detail.caseId}'),
                if (detail.segment.isNotEmpty) _Tag(detail.segment),
              ]),
              const SizedBox(height: 12),
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                Row(children: [Container(width: 7, height: 7, decoration: const BoxDecoration(color: Color(0xFF47D98D), shape: BoxShape.circle)), const SizedBox(width: 6), const Text('Dữ liệu cập nhật gần đây', style: TextStyle(color: Color(0xFFAAC0D5), fontSize: 9))]),
                IconButton(icon: const Icon(Icons.smart_toy_outlined, color: Colors.white), onPressed: () {}, padding: EdgeInsets.zero, constraints: const BoxConstraints(), iconSize: 18),
              ]),
            ],
          ),
        ),
        _DecisionCard(detail: detail),
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 4, 14, 0),
          child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('Opportunity cần duyệt', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.navy900)),
            TextButton(onPressed: () {}, child: const Text('Chọn tất cả', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppColors.blue))),
          ]),
        ),
        ...detail.opportunities.map((o) => _OpportunityCard(card: o)),
        const SizedBox(height: 88),
      ],
    );
  }
}

class _Tag extends StatelessWidget {
  final String text;
  const _Tag(this.text);
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
    decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.09), border: Border.all(color: Colors.white.withValues(alpha: 0.1)), borderRadius: BorderRadius.circular(8)),
    child: Text(text, style: const TextStyle(color: Color(0xFFDCE8F3), fontSize: 9)),
  );
}

class _DecisionCard extends StatelessWidget {
  final CaseDetail detail;
  const _DecisionCard({required this.detail});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(14, 11, 14, 0),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(17)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('DECISION BRIEF · RM REVIEW', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.muted, letterSpacing: 1)),
        const SizedBox(height: 5),
        Text(detail.title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.navy900, letterSpacing: -0.3)),
        const SizedBox(height: 5),
        Text(detail.description, style: const TextStyle(fontSize: 11, color: AppColors.muted)),
      ]),
    );
  }
}

class _OpportunityCard extends StatelessWidget {
  final OpportunityCard card;
  const _OpportunityCard({required this.card});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(14, 10, 14, 0),
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(16)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text(card.product, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.ink))),
          StatusBadge(status: card.status),
        ]),
        const SizedBox(height: 6),
        Text(card.businessNeed, style: const TextStyle(fontSize: 10, color: AppColors.muted)),
        const SizedBox(height: 10),
        Container(padding: const EdgeInsets.all(9), decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(10)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Next-best-action', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.ink2)),
          const SizedBox(height: 2),
          Text(card.nextBestAction, style: const TextStyle(fontSize: 9, color: AppColors.muted)),
        ])),
        const SizedBox(height: 8),
        Wrap(spacing: 8, children: [
          TextButton(onPressed: () {}, child: const Text('Bằng chứng', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800))),
          TextButton(onPressed: () {}, child: const Text('Chi tiết', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800))),
        ]),
      ]),
    );
  }
}
