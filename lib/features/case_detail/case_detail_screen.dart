import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';

/// S2: Case Decision Workspace (three-column per brief §5)
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
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/queue'),
          tooltip: 'Quay lại hàng đợi',
        ),
        title: Text('Chi tiết case ${widget.caseId}'),
        actions: [
          ElevatedButton.icon(
            icon: const Icon(Icons.approval),
            label: const Text('Phê duyệt'),
            onPressed: () => context.go('/approval/${widget.caseId}'),
          ),
          const SizedBox(width: 12),
        ],
      ),
      body: Consumer<CaseDetailController>(
        builder: (context, ctrl, _) {
          if (ctrl.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (ctrl.error != null) {
            return Center(child: Text('Lỗi: ${ctrl.error}'));
          }
          final detail = ctrl.caseDetail;
          if (detail == null) {
            return const Center(child: Text('Không có dữ liệu'));
          }
          return _ThreeColumnBody(detail: detail);
        },
      ),
    );
  }
}

class _ThreeColumnBody extends StatelessWidget {
  final CaseDetail detail;
  const _ThreeColumnBody({required this.detail});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth >= 1100;
        if (isWide) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                width: 320,
                child: _ContextHeader(detail: detail),
              ),
              Expanded(
                child: _OpportunityList(detail: detail),
              ),
              SizedBox(
                width: 340,
                child: _EvidenceActionDrawer(detail: detail),
              ),
            ],
          );
        }
        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              _ContextHeader(detail: detail),
              const SizedBox(height: 16),
              _OpportunityList(detail: detail),
              const SizedBox(height: 16),
              _EvidenceActionDrawer(detail: detail),
            ],
          ),
        );
      },
    );
  }
}

class _ContextHeader extends StatelessWidget {
  final CaseDetail detail;
  const _ContextHeader({required this.detail});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(detail.companyName,
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(detail.segment,
                style: Theme.of(context).textTheme.bodySmall),
            const Divider(height: 24),
            Text('Bối cảnh nhu cầu',
                style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            ...detail.needFacts.map((f) => _NeedFactRow(fact: f)),
          ],
        ),
      ),
    );
  }
}

class _NeedFactRow extends StatelessWidget {
  final NeedFact fact;
  const _NeedFactRow({required this.fact});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(fact.field,
                    style: const TextStyle(fontWeight: FontWeight.w600)),
                Text(fact.value,
                    style: Theme.of(context).textTheme.bodySmall),
                Text('Nguồn: ${fact.source} • ${(fact.confidence * 100).toInt()}%',
                    style: Theme.of(context)
                        .textTheme
                        .labelSmall
                        ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant)),
                if (!fact.confirmed)
                  const StatusBadge(status: OpportunityStatus.needInfo, label: 'Chưa xác nhận'),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _OpportunityList extends StatelessWidget {
  final CaseDetail detail;
  const _OpportunityList({required this.detail});

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.all(12),
      itemCount: detail.opportunities.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, i) => _OpportunityCardView(card: detail.opportunities[i]),
    );
  }
}

class _OpportunityCardView extends StatelessWidget {
  final OpportunityCard card;
  const _OpportunityCardView({required this.card});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(card.product,
                      style: Theme.of(context).textTheme.titleMedium),
                ),
                StatusBadge(status: card.status),
              ],
            ),
            const SizedBox(height: 8),
            Text(card.businessNeed),
            const SizedBox(height: 8),
            Text('Hành động tiếp theo: ${card.nextBestAction}',
                style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 4),
            Text('Dự kiến: ${card.expectedOutcome}',
                style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }
}

class _EvidenceActionDrawer extends StatelessWidget {
  final CaseDetail detail;
  const _EvidenceActionDrawer({required this.detail});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Minh chứng', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            ...detail.evidence.map((e) => ListTile(
                  dense: true,
                  leading: const Icon(Icons.description, size: 18),
                  title: Text(e.document),
                  subtitle: Text('${e.section} • ${e.tier}'),
                )),
            const Divider(height: 24),
            Text('Thiếu tài liệu', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            ...detail.missingDocuments.map((m) => ListTile(
                  dense: true,
                  leading: const Icon(Icons.warning_amber, size: 18, color: Colors.orange),
                  title: Text(m.documentType),
                  subtitle: Text(m.description),
                )),
          ],
        ),
      ),
    );
  }
}
