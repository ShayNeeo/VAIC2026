import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';

/// S1: Opportunity Queue Screen
class QueueScreen extends StatefulWidget {
  const QueueScreen({super.key});

  @override
  State<QueueScreen> createState() => _QueueScreenState();
}

class _QueueScreenState extends State<QueueScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<CaseController>().loadCases(useMock: true);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Hàng đợi cơ hội'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<CaseController>().loadCases(useMock: true),
            tooltip: 'Làm mới',
          ),
        ],
      ),
      body: Consumer<CaseController>(
        builder: (context, controller, _) {
          if (controller.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (controller.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.red),
                  const SizedBox(height: 16),
                  Text('Lỗi: ${controller.error}'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => controller.loadCases(useMock: true),
                    child: const Text('Thử lại'),
                  ),
                ],
              ),
            );
          }
          return _QueueListView(controller: controller);
        },
      ),
    );
  }
}

class _QueueListView extends StatelessWidget {
  final CaseController controller;
  const _QueueListView({required this.controller});

  @override
  Widget build(BuildContext context) {
    final cases = controller.filteredCases;
    if (cases.isEmpty) {
      return const Center(child: Text('Không có case nào'));
    }
    return Column(
      children: [
        _FilterChipsRow(controller: controller),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: cases.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final c = cases[index];
              return _QueueListItem(caseItem: c);
            },
          ),
        ),
      ],
    );
  }
}

class _FilterChipsRow extends StatelessWidget {
  final CaseController controller;
  const _FilterChipsRow({required this.controller});

  @override
  Widget build(BuildContext context) {
    final filters = ['all', 'ready', 'need_info', 'review_required', 'blocked'];
    final labels = {'all': 'Tất cả', 'ready': 'Sẵn sàng', 'need_info': 'Thiếu TL', 'review_required': 'Cần chuyên gia', 'blocked': 'Bị chặn'};

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: filters.map((f) {
          final selected = controller.filter == f;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: Text(labels[f]!),
              selected: selected,
              onSelected: (_) => controller.setFilter(f),
              selectedColor: Theme.of(context).colorScheme.primaryContainer,
              checkmarkColor: Theme.of(context).colorScheme.primary,
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _QueueListItem extends StatelessWidget {
  final CaseQueueItem caseItem;
  const _QueueListItem({required this.caseItem});

  @override
  Widget build(BuildContext context) {
    final counts = caseItem.branchStatusCounts;
    return Card(
      child: InkWell(
        onTap: () => context.go('/case/${caseItem.caseId}'),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(caseItem.companyName, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                        const SizedBox(height: 4),
                        Text(caseItem.title, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant)),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text('${caseItem.opportunityCount} cơ hội', style: Theme.of(context).textTheme.labelLarge),
                      const SizedBox(height: 4),
                      Text(caseItem.sla, style: Theme.of(context).textTheme.labelSmall?.copyWith(color: Theme.of(context).colorScheme.primary)),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 4,
                children: [
                  if ((counts['ready'] ?? 0) > 0) StatusChip(status: OpportunityStatus.ready),
                  if ((counts['need_info'] ?? 0) > 0) StatusChip(status: OpportunityStatus.needInfo),
                  if ((counts['review_required'] ?? 0) > 0) StatusChip(status: OpportunityStatus.reviewRequired),
                  if ((counts['blocked'] ?? 0) > 0) StatusChip(status: OpportunityStatus.blocked),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.arrow_forward, size: 16, color: Theme.of(context).colorScheme.onSurfaceVariant),
                  const SizedBox(width: 4),
                  Expanded(child: Text(caseItem.nextAction, style: Theme.of(context).textTheme.bodySmall)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}