import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';
import '../../design/widgets/nav_sidebar.dart';

/// S2: Case Decision Workspace (brief §2-§8)
/// Three columns: [Context + Need] | [Decision Brief / Opportunities] | [Action Center]
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
      context.read<CaseDetailController>().loadCase(widget.caseId, useMock: false);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CaseDetailController>(
      builder: (context, ctrl, _) => LayoutScaffold(
        sidebar: const NavSidebar(current: 'case'),
        endDrawer: ctrl.caseDetail == null ? null : _EvidenceDrawer(detail: ctrl.caseDetail!),
        body: _Body(detail: ctrl.caseDetail, isLoading: ctrl.isLoading, error: ctrl.error, caseId: widget.caseId),
      ),
    );
  }
}

class _Body extends StatelessWidget {
  final CaseDetail? detail;
  final bool isLoading;
  final String? error;
  final String caseId;
  const _Body({required this.detail, required this.isLoading, required this.error, required this.caseId});

  @override
  Widget build(BuildContext context) {
    if (isLoading) return const Center(child: CircularProgressIndicator());
    if (error != null) return Center(child: Text('Lỗi: $error'));
    if (detail == null) return const Center(child: Text('Không có dữ liệu'));

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.navy900,
        foregroundColor: Colors.white,
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.go('/queue')),
        title: Text('Decision Brief · ${detail!.caseId}', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, fontFamily: 'Sora')),
        actions: [
          IconButton(icon: const Icon(Icons.verified_outlined), tooltip: 'Bằng chứng', onPressed: () => Scaffold.of(context).openEndDrawer()),
          ElevatedButton.icon(
            icon: const Icon(Icons.shield, size: 16),
            label: const Text('Phê duyệt', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800)),
            onPressed: () => context.go('/approval/${detail!.caseId}'),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.gold, foregroundColor: AppColors.navy900, padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9)),
          ),
          const SizedBox(width: 12),
        ],
      ),
      body: ThreeColumnLayout(
        left: _LeftColumn(detail: detail!),
        center: _CenterColumn(detail: detail!, onEvidence: () => Scaffold.of(context).openEndDrawer()),
        right: _ActionCenter(detail: detail!, onApprove: () => context.go('/approval/${detail!.caseId}')),
      ),
    );
  }
}

/* ----------------------------- LEFT COLUMN ----------------------------- */

class _LeftColumn extends StatelessWidget {
  final CaseDetail detail;
  const _LeftColumn({required this.detail});

  @override
  Widget build(BuildContext context) {
    final logo = detail.companyName.isNotEmpty ? detail.companyName.substring(0, detail.companyName.length >= 3 ? 3 : detail.companyName.length).toUpperCase() : '?';
    final fresh = _relTime(detail.updatedAt);
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(gradient: const LinearGradient(colors: [AppColors.navy900, Color(0xFF0B315E)]), borderRadius: BorderRadius.circular(18)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Container(width: 42, height: 42, decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)), child: Center(child: Text(logo, style: const TextStyle(color: AppColors.navy900, fontWeight: FontWeight.w800, fontSize: 12)))),
                  const SizedBox(width: 11),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(detail.companyName, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w700)),
                    Text('${detail.companyId} · ${detail.segment}', style: const TextStyle(color: Color(0xFFAEC3D8), fontSize: 10)),
                  ])),
                ]),
                const SizedBox(height: 12),
                Wrap(spacing: 6, runSpacing: 6, children: [
                  _Tag('RM: ${detail.rmName}'),
                  _Tag('Case: ${detail.caseId}'),
                  _Tag(detail.industry),
                ]),
                const SizedBox(height: 10),
                Row(children: [
                  Container(width: 7, height: 7, decoration: const BoxDecoration(color: Color(0xFF47D98D), shape: BoxShape.circle)),
                  const SizedBox(width: 6),
                  const Text('Dữ liệu cập nhật gần đây', style: TextStyle(color: Color(0xFFAAC0D5), fontSize: 9)),
                  const Spacer(),
                  Text(fresh, style: const TextStyle(color: Color(0xFFAAC0D5), fontSize: 9)),
                ]),
              ],
            ),
          ),
          const SizedBox(height: 14),
          const _SectionTitle('NHU CẦU ĐÃ ĐƯỢC HIỂU', icon: Icons.psychology_outlined),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(13),
            decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(14)),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(detail.description, style: const TextStyle(fontSize: 12, color: AppColors.ink2, height: 1.45)),
                const SizedBox(height: 10),
                const Text('MỤC TIÊU KINH DOANH', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.subtle, letterSpacing: 0.6)),
                const SizedBox(height: 4),
                Text(_businessGoal(detail), style: const TextStyle(fontSize: 11, color: AppColors.muted, height: 1.4)),
              ],
            ),
          ),
          const SizedBox(height: 14),
          const _SectionTitle('FACT & NGUỒN', icon: Icons.table_chart_outlined),
          const SizedBox(height: 8),
          ...detail.needFacts.map((f) => _FactRow(f: f)),
        ],
      ),
    );
  }

  String _businessGoal(CaseDetail d) =>
      'Giảm công việc thủ công trong chi lương và thanh toán nhà cung cấp, '
      'tập trung dòng tiền và bảo đảm thanh khoản mùa cao điểm.';
}

class _FactRow extends StatelessWidget {
  final NeedFact f;
  const _FactRow({required this.f});

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(11),
        decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(12)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Text(f.field, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppColors.muted, letterSpacing: 0.4))),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
              decoration: BoxDecoration(color: f.confirmed ? AppColors.statusReady100 : AppColors.statusAiCta100, borderRadius: BorderRadius.circular(999)),
              child: Text(f.confirmed ? 'RM xác nhận' : _sourceLabel(f.source), style: TextStyle(fontSize: 8, fontWeight: FontWeight.w800, color: f.confirmed ? AppColors.statusReady : AppColors.statusAiCta)),
            ),
          ]),
          const SizedBox(height: 5),
          Text(f.value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.ink)),
          const SizedBox(height: 5),
          Row(children: [
            Icon(_sourceIcon(f.source), size: 12, color: AppColors.subtle),
            const SizedBox(width: 4),
            Text(f.source, style: const TextStyle(fontSize: 9, color: AppColors.subtle)),
            const Spacer(),
            Text('${(f.confidence * 100).toInt()}% tin cậy', style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.blue)),
          ]),
        ]),
      );
}

/* ----------------------------- CENTER COLUMN ----------------------------- */

class _CenterColumn extends StatelessWidget {
  final CaseDetail detail;
  final VoidCallback onEvidence;
  const _CenterColumn({required this.detail, required this.onEvidence});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(16)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('DECISION BRIEF · RM REVIEW', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.muted, letterSpacing: 1)),
              const SizedBox(height: 5),
              Text(detail.title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.navy900, letterSpacing: -0.3, fontFamily: 'Sora')),
              const SizedBox(height: 6),
              Text('${detail.opportunities.length} cơ hội được phát hiện từ yêu cầu hiện tại · ${(detail.opportunities).where((o) => o.status == OpportunityStatus.ready).length} sẵn sàng, ${(detail.opportunities).where((o) => o.status == OpportunityStatus.needInfo).length} chờ bổ sung hồ sơ.', style: const TextStyle(fontSize: 11, color: AppColors.muted)),
            ]),
          ),
          const SizedBox(height: 14),
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('OPPORTUNITY', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: AppColors.navy900, letterSpacing: 0.5)),
            TextButton.icon(onPressed: onEvidence, icon: const Icon(Icons.verified_outlined, size: 14), label: const Text('Bằng chứng', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppColors.blue))),
          ]),
          ...detail.opportunities.map((o) => _OpportunityCard(card: o)),
        ],
      ),
    );
  }
}

class _OpportunityCard extends StatelessWidget {
  final OpportunityCard card;
  const _OpportunityCard({required this.card});

  @override
  Widget build(BuildContext context) {
    final blocked = card.status == OpportunityStatus.needInfo || card.status == OpportunityStatus.blocked || card.status == OpportunityStatus.reviewRequired;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(13),
            decoration: BoxDecoration(
              color: blocked ? AppColors.statusNeedInfo100 : AppColors.gold100,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
            ),
            child: Row(children: [
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(card.product, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.navy900)),
                const SizedBox(height: 2),
                Text(card.productId, style: const TextStyle(fontSize: 9, color: AppColors.muted)),
              ])),
              StatusBadge(status: card.status),
            ]),
          ),
          Padding(
            padding: const EdgeInsets.all(13),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(card.businessNeed, style: const TextStyle(fontSize: 11, color: AppColors.ink2)),
              const SizedBox(height: 10),
              if (card.signals.isNotEmpty) ...[
                const _FieldLabel('TÍN HIỆU MẠNH'),
                const SizedBox(height: 5),
                ...card.signals.take(3).map((s) => _SignalRow(s: s)),
                const SizedBox(height: 8),
              ],
              const _FieldLabel('SẢN PHẨM PHÙ HỢP'),
              const SizedBox(height: 5),
              Wrap(spacing: 6, runSpacing: 6, children: card.productFit.map((p) => Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4), decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(8)), child: Text(p, style: const TextStyle(fontSize: 9, color: AppColors.ink2)))).toList()),
              const SizedBox(height: 9),
              if (card.missingInfo.isNotEmpty) ...[
                const _FieldLabel('THÔNG TIN THIẾU', danger: true),
                const SizedBox(height: 4),
                ...card.missingInfo.map((m) => _Bullet(text: m, danger: true)),
                const SizedBox(height: 8),
              ],
              if (card.risk.isNotEmpty) ...[
                const _FieldLabel('RỦI RO', danger: true),
                const SizedBox(height: 4),
                ...card.risk.map((r) => _Bullet(text: r, danger: true)),
                const SizedBox(height: 8),
              ],
              Row(children: [
                Expanded(child: Container(padding: const EdgeInsets.all(9), decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(10)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('NEXT-BEST-ACTION', style: TextStyle(fontSize: 8, fontWeight: FontWeight.w800, color: AppColors.subtle, letterSpacing: 0.6)),
                  const SizedBox(height: 2),
                  Text(card.nextBestAction, style: const TextStyle(fontSize: 10, color: AppColors.ink2)),
                ]))),
              ]),
              const SizedBox(height: 8),
              Row(children: [
                const Icon(Icons.person_outline, size: 13, color: AppColors.subtle),
                const SizedBox(width: 4),
                Text(card.owner, style: const TextStyle(fontSize: 10, color: AppColors.muted)),
                const SizedBox(width: 14),
                const Icon(Icons.timer_outlined, size: 13, color: AppColors.subtle),
                const SizedBox(width: 4),
                Text('SLA ${card.sla}', style: const TextStyle(fontSize: 10, color: AppColors.muted)),
              ]),
            ]),
          ),
        ],
      ),
    );
  }
}

/* ----------------------------- RIGHT COLUMN (ACTION CENTER) ----------------------------- */

class _ActionCenter extends StatelessWidget {
  final CaseDetail detail;
  final VoidCallback onApprove;
  const _ActionCenter({required this.detail, required this.onApprove});

  @override
  Widget build(BuildContext context) {
    final ready = detail.opportunities.where((o) => o.status == OpportunityStatus.ready).length;
    final pending = detail.opportunities.length - ready;
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionTitle('SAU KHI DUYỆT, HỆ THỐNG SẼ', icon: Icons.playlist_add_check, color: AppColors.gold),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(13),
            decoration: BoxDecoration(color: AppColors.surface, border: Border.all(color: AppColors.line), borderRadius: BorderRadius.circular(14)),
            child: Column(children: [
              _ActionRow(icon: Icons.add_task, text: 'Tạo $ready opportunity trong CRM', positive: true),
              _ActionRow(icon: Icons.task_alt, text: 'Tạo ${detail.checklist.length} task nội bộ', positive: true),
              const _ActionRow(icon: Icons.description, text: 'Lưu draft email cho khách hàng', positive: true),
              if (pending > 0) _ActionRow(icon: Icons.hourglass_empty, text: 'Giữ $pending nhánh ở trạng thái chờ hồ sơ', positive: false),
              const _ActionRow(icon: Icons.block, text: 'Không gửi email tự động', positive: false),
              const _ActionRow(icon: Icons.credit_card_off, text: 'Không cam kết hạn mức', positive: false),
            ]),
          ),
          const SizedBox(height: 14),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              icon: const Icon(Icons.shield, size: 16),
              label: const Text('Duyệt và tạo draft', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
              onPressed: onApprove,
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.navy900, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 14)),
            ),
          ),
          const SizedBox(height: 8),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: onApprove,
              child: const Text('Yêu cầu chỉnh sửa', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionRow extends StatelessWidget {
  final IconData icon;
  final String text;
  final bool positive;
  const _ActionRow({required this.icon, required this.text, required this.positive});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 7),
        child: Row(children: [
          Icon(icon, size: 16, color: positive ? AppColors.statusReady : AppColors.statusBlocked),
          const SizedBox(width: 9),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 11, color: AppColors.ink2))),
        ]),
      );
}

/* ----------------------------- EVIDENCE DRAWER ----------------------------- */

class _EvidenceDrawer extends StatelessWidget {
  final CaseDetail detail;
  const _EvidenceDrawer({required this.detail});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('BẰNG CHỨNG & NGUỒN', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppColors.navy900, fontFamily: 'Sora')),
            const SizedBox(height: 4),
            const Text('Mọi claim đều có evidence. Mở drawer để kiểm tra.', style: TextStyle(fontSize: 10, color: AppColors.muted)),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.separated(
                itemCount: detail.evidence.length + detail.opportunities.length,
                separatorBuilder: (_, __) => const Divider(),
                itemBuilder: (context, i) {
                  if (i < detail.evidence.length) {
                    final e = detail.evidence[i];
                    return _EvidenceItem(doc: e.document, section: e.section, date: e.effectiveDate, owner: e.owner, tier: e.tier);
                  }
                  final o = detail.opportunities[i - detail.evidence.length];
                  return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(o.product, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.ink)),
                    ...o.evidence.map((e) => _EvidenceItem(doc: e.document, section: e.section, date: e.effectiveDate, owner: e.owner, tier: e.tier)),
                  ]);
                },
              ),
            ),
          ]),
        ),
      ),
    );
  }
}

class _EvidenceItem extends StatelessWidget {
  final String doc, section, date, owner, tier;
  const _EvidenceItem({required this.doc, required this.section, required this.date, required this.owner, required this.tier});

  @override
  Widget build(BuildContext context) {
    final syntheticPolicy = tier.startsWith('SYNTHETIC_DEMO_DATA');
    if (syntheticPolicy) {
      return ExpansionTile(
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(left: 23, right: 4, bottom: 8),
        leading: const Icon(Icons.policy_outlined, size: 17, color: AppColors.statusBlocked),
        title: Text(doc, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.ink)),
        subtitle: Text('$section · hiệu lực $date\n$tier', style: const TextStyle(fontSize: 9, color: AppColors.subtle)),
        children: [Align(alignment: Alignment.centerLeft, child: Text('Trích dẫn: “$owner”', style: const TextStyle(fontSize: 10, color: AppColors.ink2, height: 1.4)))],
      );
    }
    return Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Icon(Icons.verified_outlined, size: 15, color: AppColors.statusReady),
          const SizedBox(width: 8),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(doc, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.ink)),
            Text('$section · hiệu lực $date · $owner · $tier', style: const TextStyle(fontSize: 9, color: AppColors.subtle)),
          ])),
        ]),
      );
  }
}

/* ----------------------------- SHARED BITS ----------------------------- */

class _SectionTitle extends StatelessWidget {
  final String text;
  final IconData icon;
  final Color color;
  const _SectionTitle(this.text, {required this.icon, this.color = AppColors.blue});

  @override
  Widget build(BuildContext context) => Row(children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 7),
        Text(text, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppColors.navy900, letterSpacing: 0.6)),
      ]);
}

class _FieldLabel extends StatelessWidget {
  final String text;
  final bool danger;
  const _FieldLabel(this.text, {this.danger = false});

  @override
  Widget build(BuildContext context) => Text(text, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: danger ? AppColors.statusBlocked : AppColors.subtle, letterSpacing: 0.6));
}

class _Bullet extends StatelessWidget {
  final String text;
  final bool danger;
  const _Bullet({required this.text, this.danger = false});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 3, left: 2),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('• ', style: TextStyle(color: danger ? AppColors.statusBlocked : AppColors.subtle, fontSize: 11)),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 10, color: AppColors.ink2))),
        ]),
      );
}

class _SignalRow extends StatelessWidget {
  final Signal s;
  const _SignalRow({required this.s});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: Row(children: [
          Expanded(child: Text(s.fact, style: const TextStyle(fontSize: 10, color: AppColors.ink2))),
          const SizedBox(width: 8),
          Container(padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2), decoration: BoxDecoration(color: AppColors.blue100, borderRadius: BorderRadius.circular(999)), child: Text('${(s.strength * 100).toInt()}%', style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: AppColors.navy700))),
        ]),
      );
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

String _relTime(DateTime d) {
  final diff = DateTime.now().difference(d);
  if (diff.inMinutes < 60) return '${diff.inMinutes} phút trước';
  if (diff.inHours < 24) return '${diff.inHours} giờ trước';
  return '${diff.inDays} ngày trước';
}

String _sourceLabel(String s) => s.toLowerCase().contains('rm') ? 'RM nhập' : s.toLowerCase().contains('crm') ? 'CRM' : 'AI suy luận';
IconData _sourceIcon(String s) => s.toLowerCase().contains('rm') ? Icons.edit_note : s.toLowerCase().contains('crm') ? Icons.storage : Icons.smart_toy_outlined;
